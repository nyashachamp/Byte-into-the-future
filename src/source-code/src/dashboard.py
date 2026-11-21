"""Streamlit view for the synthetic 12-case testing workflow.

The "Live watsonx Orchestrate" tab sends the selected case to the deployed
orchestrator_agent (which runs the civic_shield_pipeline flow) and shows its
reply. The "Local reference pipeline" tab is the offline deterministic
pipeline, kept for comparison; it does not call Orchestrate.
"""

from pathlib import Path
import hmac
import json
import os
import streamlit as st

try:
    from .pipeline import analyze
    from . import orchestrate_client
except ImportError:
    # `streamlit run src/dashboard.py` executes this file as a script, so load
    # the `src` package explicitly (pipeline.py uses package-relative imports).
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.pipeline import analyze
    from src import orchestrate_client


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DATASET = REPOSITORY_ROOT / "data" / "samples" / "public-service-risk-v1.json"

st.set_page_config(page_title="Civic Shield — Public Service Risk Dashboard", layout="wide")
st.markdown("""<style>
.stApp { background:#050505; color:#F7F7F7; }
[data-testid="stMetricValue"] { color:#3A86FF; }
div.stButton > button { border-color:#3A86FF; }
</style>""", unsafe_allow_html=True)


def render_live(case_id: str) -> None:
    st.markdown("#### Deployed watsonx Orchestrate workflow")
    st.caption(
        "Sends “Investigate case %s” to the deployed orchestrator_agent, which runs the "
        "civic_shield_pipeline flow through the four specialist agents. Results below are "
        "the agent's reply, not computed by this dashboard." % case_id
    )
    missing = orchestrate_client.missing_settings()
    if missing:
        st.warning(
            "Live integration is **not configured** in this deployment "
            f"(missing: {', '.join(missing)}). Only the local reference pipeline is available."
        )
        return

    access_code = os.environ.get("DASHBOARD_ACCESS_CODE", "")
    if access_code:
        entered = st.text_input("Demo access code", type="password")
        if not hmac.compare_digest(entered.encode(), access_code.encode()):
            st.info("Enter the demo access code to run live cases.")
            return

    results = st.session_state.setdefault("live_results", {})
    if st.button(f"Run {case_id} on watsonx Orchestrate", type="primary"):
        with st.spinner("Waiting for the orchestrator to complete the pipeline (can take 1–3 minutes)…"):
            try:
                results[case_id] = orchestrate_client.run_case(case_id)
            except orchestrate_client.OrchestrateError as exc:
                results[case_id] = exc

    outcome = results.get(case_id)
    if outcome is None:
        return
    if isinstance(outcome, Exception):
        st.error(f"Live call failed: {outcome}")
        return

    if "WORKFLOW INCOMPLETE" in outcome.text:
        st.warning("Orchestrate replied, but reported the workflow as incomplete.")
    elif "INCIDENT REPORT" in outcome.text or "compliant" in outcome.text.lower():
        st.success(f"Live reply received from the deployed orchestrator in {outcome.elapsed_seconds}s.")
    else:
        st.info(f"Orchestrate replied in {outcome.elapsed_seconds}s, but not in the expected report format.")
    st.markdown(outcome.text or "_Empty reply_")
    st.caption(
        f"Thread ID: `{outcome.thread_id or 'not returned'}`. Confirm that all four specialist "
        "stages executed by checking this thread's trace in watsonx Orchestrate."
    )
    with st.expander("Raw API response"):
        st.json(outcome.raw)


def render_local(selected) -> None:
    st.caption("Offline deterministic pipeline bundled with this app • does not call watsonx Orchestrate")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Assessment", selected.assessment.replace("_", " ").title())
    c2.metric("Priority score", "Unknown" if selected.score is None else selected.score)
    c3.metric("Severity", selected.severity.upper())
    c4.metric("Verification", selected.verification_result.replace("_", " ").title())

    st.subheader(f"{selected.case_id}: {selected.title}")
    st.write(f"**Asset:** `{selected.asset_id}` ({selected.asset_name})")
    st.write(f"**Affected public service:** {selected.affected_public_service}")
    st.write(f"**Finding:** {selected.finding}")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Evidence and baseline")
        st.write("**Observed finding evidence**")
        for item in selected.evidence:
            st.write(f"- {item}")
        st.write("**Baseline**")
        for item in selected.baseline_evidence:
            st.write(f"- {item}")
    with right:
        st.markdown("#### Action and human intervention")
        st.write(f"**Action:** `{selected.action_taken}`")
        st.write(f"**Attempts:** {selected.action_attempts}")
        st.write(f"**Tool result:** {selected.action_result}")
        st.write(f"**Workflow outcome:** `{selected.outcome}`")
        st.write(f"**Handoff required:** {'Yes' if selected.handoff_required else 'No'}")
        for item in selected.human_intervention:
            st.write(f"- {item}")

    st.markdown("#### Ordered execution events")
    st.dataframe(selected.events, width="stretch", hide_index=True)
    with st.expander("Completed AI work"):
        st.write(selected.completed_ai_work)
    with st.expander("Full result JSON"):
        st.json(selected.to_dict())
    st.download_button("Download selected result", json.dumps(selected.to_dict(), indent=2), file_name=f"{selected.case_id}.json", mime="application/json", width="stretch")


def main() -> None:
    st.title("Civic Shield — Public Service Risk Dashboard")
    st.caption("Synthetic test mode • in-memory actions only • human closure remains required")
    results = analyze(DATASET)
    selected_id = st.selectbox("Case", [item.case_id for item in results])
    selected = next(item for item in results if item.case_id == selected_id)

    live_tab, local_tab = st.tabs(["Live watsonx Orchestrate", "Local reference pipeline"])
    with live_tab:
        render_live(selected_id)
    with local_tab:
        render_local(selected)


if __name__ == "__main__":
    main()
