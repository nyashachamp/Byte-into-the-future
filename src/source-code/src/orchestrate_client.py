"""Minimal client for the deployed watsonx Orchestrate orchestrator agent.

The dashboard does not re-implement the Civic Shield workflow. It sends a
case request to the deployed ``orchestrator_agent``, which runs the
``civic_shield_pipeline`` flow in watsonx Orchestrate, and displays the reply.

Configuration comes from environment variables only (never source control):

    ORCHESTRATE_URL        Instance API URL, e.g.
                           https://api.eu-gb.watson-orchestrate.cloud.ibm.com/instances/<instance-id>
    ORCHESTRATE_API_KEY    IBM Cloud API key with access to the instance
    ORCHESTRATE_AGENT_ID   ID of the deployed orchestrator_agent
    ORCHESTRATE_IAM_URL    Optional; defaults to the IBM Cloud IAM token endpoint
    ORCHESTRATE_TIMEOUT    Optional request timeout in seconds (default 240)

Standard library only, so the container needs no extra dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

DEFAULT_IAM_URL = "https://iam.cloud.ibm.com/identity/token"
REQUIRED_SETTINGS = ("ORCHESTRATE_URL", "ORCHESTRATE_API_KEY", "ORCHESTRATE_AGENT_ID")


class OrchestrateError(RuntimeError):
    """Raised when the deployed agent cannot be reached or returns an error."""


@dataclass
class OrchestrateReply:
    text: str
    thread_id: str | None
    elapsed_seconds: float
    raw: dict[str, Any]


def missing_settings() -> list[str]:
    return [name for name in REQUIRED_SETTINGS if not os.environ.get(name, "").strip()]


def is_configured() -> bool:
    return not missing_settings()


_token_cache: dict[str, Any] = {"token": None, "expires_at": 0.0}


def _post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise OrchestrateError(f"HTTP {exc.code} from {urllib.parse.urlsplit(url).netloc}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise OrchestrateError(f"Could not reach {urllib.parse.urlsplit(url).netloc}: {exc.reason}") from exc


def _iam_token() -> str:
    if _token_cache["token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["token"]
    body = urllib.parse.urlencode({
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
        "apikey": os.environ["ORCHESTRATE_API_KEY"].strip(),
    }).encode("utf-8")
    payload = _post(
        os.environ.get("ORCHESTRATE_IAM_URL", DEFAULT_IAM_URL),
        body,
        {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        timeout=30,
    )
    _token_cache["token"] = payload["access_token"]
    _token_cache["expires_at"] = float(payload.get("expiration", time.time() + 3000))
    return _token_cache["token"]


def _reply_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        return ""
    content = (choices[0].get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n\n".join(str(part.get("text", "")) for part in content if isinstance(part, dict)).strip()
    return ""


def run_case(case_id: str, thread_id: str | None = None) -> OrchestrateReply:
    """Ask the deployed orchestrator to investigate one case and return its reply."""
    missing = missing_settings()
    if missing:
        raise OrchestrateError(f"Missing configuration: {', '.join(missing)}")

    base_url = os.environ["ORCHESTRATE_URL"].strip().rstrip("/")
    agent_id = os.environ["ORCHESTRATE_AGENT_ID"].strip()
    headers = {
        "Authorization": f"Bearer {_iam_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if thread_id:
        headers["X-IBM-THREAD-ID"] = thread_id
    body = json.dumps({
        "messages": [{"role": "user", "content": f"Investigate case {case_id}"}],
        "stream": False,
    }).encode("utf-8")

    started = time.monotonic()
    payload = _post(
        f"{base_url}/v1/orchestrate/{urllib.parse.quote(agent_id)}/chat/completions",
        body,
        headers,
        timeout=float(os.environ.get("ORCHESTRATE_TIMEOUT", "240")),
    )
    return OrchestrateReply(
        text=_reply_text(payload),
        thread_id=payload.get("thread_id"),
        elapsed_seconds=round(time.monotonic() - started, 1),
        raw=payload,
    )
