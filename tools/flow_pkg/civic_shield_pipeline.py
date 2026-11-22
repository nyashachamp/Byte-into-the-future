"""Civic Shield — four-specialist sequential pipeline as an ADK Agentic Workflow.

This flow replaces LLM-based delegation (which proved unreliable for C05) with a
deterministic edge graph enforced by the watsonx Orchestrate flow engine.

Each of the four existing native specialist agents is invoked as an Agent Node.
The flow engine sequences the nodes unconditionally; no LLM reasoning can skip a
stage. The notification gate is handled by a Script Node — pure Python, no LLM.

Import after the four specialist agents are already present in the environment:
    orchestrate tools import -k flow -f tools/flow_pkg/civic_shield_pipeline.py

Then add to orchestrator_agent.yaml:
    tools:
      - civic_shield_pipeline

The existing orchestrator YAML is NOT modified until this flow passes regression.

NOTE: Do NOT add 'from __future__ import annotations' to this file.
      The @flow decorator in ibm-watsonx-orchestrate inspects parameter annotations
      at decoration time using inspect.signature(). With PEP 563 deferred evaluation
      (__future__ annotations), all annotations become strings, causing the decorator
      to raise ValueError("Argument must be of type Flow").
"""

# NO 'from __future__ import annotations' — see note above.
import json
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from ibm_watsonx_orchestrate.flow_builder.flows import END, Flow, START, flow

# ---------------------------------------------------------------------------
# ── INPUT / OUTPUT SCHEMAS ──────────────────────────────────────────────────
# All schemas use only JSON-serialisable primitive types (str, bool, int,
# Optional[int], List[str]) so they survive agent-node LLM mediation intact.
# ---------------------------------------------------------------------------

class PipelineInput(BaseModel):
    """Input to the Civic Shield pipeline flow."""
    case_id: str = Field(description="Case identifier to analyse, e.g. 'C05'.")


# ── Stage 1: Security Investigator output ───────────────────────────────────

class RuleViolated(BaseModel):
    id: str = Field(description="Rule identifier, e.g. 'CFG-PUBLIC'.")
    field: str = Field(description="Snapshot field that violated the rule.")
    expected: str = Field(description="Expected value as string.")
    weight: int = Field(description="Rule weight for scoring.")

class InvestigatorOutput(BaseModel):
    assessment: str = Field(
        description="'confirmed' | 'compliant' | 'invalid_input' | 'error'."
    )
    rules_violated: List[str] = Field(
        default_factory=list,
        description="JSON-serialised list of violated rule dicts.",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Validation error strings (non-empty when assessment='invalid_input').",
    )
    evidence: List[str] = Field(
        default_factory=list,
        description="Human-readable evidence strings.",
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score: 1.0 when valid, 0.0 when invalid.",
    )
    investigator_result_json: str = Field(
        default="",
        description=(
            "Full investigator result dict serialised as a JSON string. "
            "Downstream agents must receive this string as their investigator_result argument."
        ),
    )


# ── Stage 2: Risk Analyst output ────────────────────────────────────────────

class AnalystOutput(BaseModel):
    """Output contract for the risk_analyst agent node."""
    score: Optional[int] = Field(
        default=None,
        description="Priority score (None when no service mapping exists).",
    )
    severity: str = Field(
        default="unknown",
        description="'critical' | 'high' | 'medium' | 'low' | 'none' | 'unknown'.",
    )
    notify_first: bool = Field(
        default=False,
        description="True when immediate human notification is required before action.",
    )
    public_restricted: bool = Field(
        default=False,
        description="True when the finding involves restricted-synthetic public exposure.",
    )
    service_ids: List[str] = Field(
        default_factory=list,
        description="Linked public-service IDs.",
    )
    affected_public_service: str = Field(
        default="Unknown service impact",
        description="Human-readable service name.",
    )
    analyst_result_json: str = Field(
        default="",
        description=(
            "Full analyst result dict serialised as a JSON string. "
            "Downstream agents must receive this string as their analyst_result argument."
        ),
    )


# ── Stage 3: Response Agent output ──────────────────────────────────────────

class ResponseOutput(BaseModel):
    """Output contract for the response_agent agent node."""
    action_taken: str = Field(
        default="none",
        description="'enable_audit_logging' or 'none'.",
    )
    action_attempts: int = Field(
        default=0,
        description="Number of action attempts made.",
    )
    action_result: str = Field(
        default="not_run",
        description="'success' | 'transient_failure' | 'not_run'.",
    )
    handoff: bool = Field(
        default=False,
        description="True when the case requires human handoff.",
    )
    outcome: str = Field(
        default="no_action",
        description="Outcome string from the response tool.",
    )
    response_result_json: str = Field(
        default="",
        description=(
            "Full response result dict serialised as a JSON string. "
            "The verification agent must receive this string as its response_result argument."
        ),
    )


# ── Stage 4: Verification & Handoff output ──────────────────────────────────

class VerifierOutput(BaseModel):
    """Output contract for the verification_handoff_agent agent node."""
    verification_result: str = Field(
        default="not_run",
        description="'passed' | 'failed' | 'not_run'.",
    )
    outcome: str = Field(
        default="",
        description="Final outcome string.",
    )
    handoff_required: bool = Field(
        default=True,
        description="True when human intervention is required.",
    )
    human_intervention: List[str] = Field(
        default_factory=list,
        description="Ordered list of human work items.",
    )
    completed_ai_work: List[str] = Field(
        default_factory=list,
        description="Summary of completed AI-assisted work.",
    )
    lifecycle_status: str = Field(
        default="human_handoff_required",
        description=(
            "'awaiting_human_closure' | 'awaiting_human_approval' | "
            "'human_handoff_required' | 'awaiting_human_review' | 'awaiting_corrected_data'."
        ),
    )


# ── Notification Script output ───────────────────────────────────────────────

class NotificationOutput(BaseModel):
    """Output of the notification Script Node."""
    notification_required: bool = Field(
        description="True when notify_first=True in the analyst result.",
    )
    notification_message: str = Field(
        default="",
        description="Notification message text, or empty string when not required.",
    )


# ── Consolidated pipeline output ─────────────────────────────────────────────

class PipelineOutput(BaseModel):
    """Consolidated output returned by the full pipeline flow."""
    case_id: str = Field(description="Case identifier.")
    # Stage results (top-level fields for orchestrator report assembly)
    assessment: str = Field(description="Investigation assessment.")
    evidence: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0)
    score: Optional[int] = Field(default=None)
    severity: str = Field(default="unknown")
    notify_first: bool = Field(default=False)
    public_restricted: bool = Field(default=False)
    service_ids: List[str] = Field(default_factory=list)
    affected_public_service: str = Field(default="")
    action_taken: str = Field(default="none")
    action_attempts: int = Field(default=0)
    action_result: str = Field(default="not_run")
    verification_result: str = Field(default="not_run")
    lifecycle_status: str = Field(default="human_handoff_required")
    handoff_required: bool = Field(default=True)
    human_intervention: List[str] = Field(default_factory=list)
    completed_ai_work: List[str] = Field(default_factory=list)
    notification_required: bool = Field(default=False)
    notification_message: str = Field(default="")
    # Raw JSON strings for orchestrator audit / downstream use
    investigator_result_json: str = Field(default="")
    analyst_result_json: str = Field(default="")
    response_result_json: str = Field(default="")
    # Fail-closed sentinel: set to False by final script only when all four
    # agent nodes produced results; orchestrator must check this before
    # reporting success or closure.
    all_stages_complete: bool = Field(
        default=False,
        description=(
            "True only when all four specialist agent nodes executed and returned "
            "results. When False, the orchestrator MUST report WORKFLOW INCOMPLETE."
        ),
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Any error messages encountered during the pipeline.",
    )


# ---------------------------------------------------------------------------
# ── FLOW DEFINITION ─────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@flow(
    name="civic_shield_pipeline",
    display_name="Civic Shield — Four-Specialist Pipeline",
    description=(
        "Deterministic four-stage public-service risk analysis pipeline. "
        "Invokes the Security Investigator, Risk Analyst, Response Agent, and "
        "Verification & Handoff specialist agents in fixed sequential order. "
        "No stage can be skipped — sequencing is enforced by the flow engine edge graph. "
        "All actions are in-memory simulations only. Human closure is always required."
    ),
    input_schema=PipelineInput,
    output_schema=PipelineOutput,
    suppress_agent_summarization=True,
    initiators=["orchestrator_agent"],
)
def build_civic_shield_pipeline(aflow: Flow) -> Flow:
    """Four-specialist Civic Shield pipeline.

    Node sequence (enforced by edge graph, not by LLM reasoning):
        START
          → Stage 1: security_investigator agent node
          → Stage 2: risk_analyst agent node
          → Notification Script (Python, no LLM)
          → Stage 3: response_agent agent node
          → Stage 4: verification_handoff_agent agent node
          → Final Aggregation Script (Python, no LLM)
        END
    """

    # ── Stage 1: Security Investigator ──────────────────────────────────────
    # The agent is called with a precise message that includes the case_id
    # and instructs it to return a JSON-serialised result dict.
    investigator_node = aflow.agent(
        name="stage1_security_investigator",
        display_name="Stage 1 — Security Investigator",
        agent="security_investigator",
        description=(
            "Validates the configuration snapshot for the requested case against "
            "the approved baseline. Returns assessment, rules_violated, evidence, "
            "and confidence. Also returns investigator_result_json — the full result "
            "serialised as a JSON string for downstream agents."
        ),
        message=(
            "Investigate case {case_id}. "
            "Call investigate_case with case_id='{case_id}'. "
            "Return the full result exactly as the tool returns it. "
            "In addition, include a field called 'investigator_result_json' that is the "
            "entire result dict serialised as a JSON string using json.dumps(). "
            "Do not summarise or omit any field."
        ),
        input_schema=PipelineInput,
        output_schema=InvestigatorOutput,
        thread_control_policy="CREATE_ALWAYS",
    )
    investigator_node.map_input(
        input_variable="case_id",
        expression="flow.input.case_id",
    )

    # ── Stage 2: Risk Analyst ────────────────────────────────────────────────
    analyst_node = aflow.agent(
        name="stage2_risk_analyst",
        display_name="Stage 2 — Risk Analyst",
        agent="risk_analyst",
        description=(
            "Computes priority score, severity, notification flag, and "
            "public_restricted status for a confirmed finding. "
            "Returns analyst_result_json — the full result serialised as a JSON string."
        ),
        message=(
            "Analyse case {case_id} using the investigator result provided. "
            "Call analyse_impact with case_id='{case_id}' and "
            "investigator_result='{investigator_result_json}'. "
            "Return the full result exactly as the tool returns it. "
            "In addition, include a field called 'analyst_result_json' that is the "
            "entire result dict serialised as a JSON string using json.dumps(). "
            "Do not summarise or omit any field."
        ),
        input_schema=InvestigatorOutput,
        output_schema=AnalystOutput,
        thread_control_policy="CREATE_ALWAYS",
    )
    analyst_node.map_input(
        input_variable="case_id",
        expression="flow.input.case_id",
    )
    analyst_node.map_input(
        input_variable="investigator_result_json",
        expression="flow.stage1_security_investigator.output.investigator_result_json",
    )

    # ── Notification Script ──────────────────────────────────────────────────
    # Pure Python. No LLM. Reads analyst output, produces notification text.
    # The script ALWAYS continues to the next node — it cannot terminate the flow.
    notification_node = aflow.script(
        name="notification_gate",
        display_name="Notification Gate (Script)",
        description=(
            "Checks notify_first from the analyst result. "
            "Produces the required notification message when True. "
            "Always continues to the Response Agent stage — this is a side-effect node, "
            "not a decision point. public_restricted=True does NOT stop the pipeline here."
        ),
        output_schema=NotificationOutput,
        script="""

# Read analyst output directly from the preceding node
notify_first = parent.stage2_risk_analyst.output.notify_first
case_id = parent.input.case_id

if notify_first:
    self.output.notification_required = True
    self.output.notification_message = (
        f"Immediate human notification required before any automated action "
        f"is taken for case {case_id}."
    )
else:
    self.output.notification_required = False
    self.output.notification_message = ""
""",
    )

    # ── Stage 3: Response Agent ──────────────────────────────────────────────
    # Mandatory for EVERY confirmed case — the agent itself enforces the six
    # authorization invariants and will return action_taken="none" for C05.
    response_node = aflow.agent(
        name="stage3_response_agent",
        display_name="Stage 3 — Response Agent",
        agent="response_agent",
        description=(
            "Applies the six-invariant authorization gate and executes the allowlisted "
            "simulated action if all guards pass. For public_restricted=True cases "
            "(e.g. C05) returns action_taken='none', action_result='not_run'. "
            "Returns response_result_json — the full result serialised as a JSON string."
        ),
        message=(
            "Execute the response for case {case_id}. "
            "Call execute_response with case_id='{case_id}', "
            "investigator_result='{investigator_result_json}', "
            "and analyst_result='{analyst_result_json}'. "
            "Return the full result exactly as the tool returns it. "
            "In addition, include a field called 'response_result_json' that is the "
            "entire result dict serialised as a JSON string using json.dumps(). "
            "Do not summarise or omit any field. "
            "If the tool returns action_taken='none', that is the correct result — "
            "do not retry or attempt an alternative action."
        ),
        input_schema=AnalystOutput,
        output_schema=ResponseOutput,
        thread_control_policy="CREATE_ALWAYS",
    )
    response_node.map_input(
        input_variable="case_id",
        expression="flow.input.case_id",
    )
    response_node.map_input(
        input_variable="investigator_result_json",
        expression="flow.stage1_security_investigator.output.investigator_result_json",
    )
    response_node.map_input(
        input_variable="analyst_result_json",
        expression="flow.stage2_risk_analyst.output.analyst_result_json",
    )

    # ── Stage 4: Verification & Handoff ─────────────────────────────────────
    # Mandatory for EVERY confirmed case — even when action_taken="none".
    # The verifier records the no-action human escalation path for C05.
    verifier_node = aflow.agent(
        name="stage4_verification_handoff",
        display_name="Stage 4 — Verification & Handoff",
        agent="verification_handoff_agent",
        description=(
            "Independently verifies the post-action state and assembles the human "
            "handoff packet. For no-action cases (e.g. C05) returns "
            "verification_result='not_run' and lifecycle_status='human_handoff_required'."
        ),
        message=(
            "Verify and hand off case {case_id}. "
            "Call verify_and_handoff with case_id='{case_id}', "
            "investigator_result='{investigator_result_json}', "
            "analyst_result='{analyst_result_json}', "
            "and response_result='{response_result_json}'. "
            "Return the full result exactly as the tool returns it. "
            "Do not summarise or omit any field. "
            "If response_result showed action_taken='none', verification_result "
            "should be 'not_run' — that is the correct and expected result."
        ),
        input_schema=ResponseOutput,
        output_schema=VerifierOutput,
        thread_control_policy="CREATE_ALWAYS",
    )
    verifier_node.map_input(
        input_variable="case_id",
        expression="flow.input.case_id",
    )
    verifier_node.map_input(
        input_variable="investigator_result_json",
        expression="flow.stage1_security_investigator.output.investigator_result_json",
    )
    verifier_node.map_input(
        input_variable="analyst_result_json",
        expression="flow.stage2_risk_analyst.output.analyst_result_json",
    )
    verifier_node.map_input(
        input_variable="response_result_json",
        expression="flow.stage3_response_agent.output.response_result_json",
    )

    # ── Final Aggregation Script ─────────────────────────────────────────────
    # Assembles all four stage outputs into the consolidated PipelineOutput.
    # Fail-closed: sets all_stages_complete=True only when all four nodes
    # produced non-empty results; leaves it False (default) otherwise.
    aggregation_node = aflow.script(
        name="aggregate_results",
        display_name="Aggregate Results (Script)",
        description=(
            "Assembles all four specialist stage outputs into the consolidated "
            "PipelineOutput. Sets all_stages_complete=True only when every required "
            "field is present. Never fabricates or infers field values."
        ),
        output_schema=PipelineOutput,
        script="""

inv  = parent.stage1_security_investigator.output
an   = parent.stage2_risk_analyst.output
notif = parent.notification_gate.output
resp = parent.stage3_response_agent.output
ver  = parent.stage4_verification_handoff.output

# Fail-closed check: all four agent node outputs must be non-trivial.
# If assessment is missing/empty the investigator did not complete.
errors = []
if inv.assessment == "confirmed" and not inv.evidence:
    errors.append("Stage 1: confirmed investigation has no evidence")
if an.notify_first and not notif.notification_required:
    errors.append("Notification Gate: required notification was not confirmed")
if an.public_restricted and (resp.action_taken != "none" or resp.action_result != "not_run" or (resp.action_attempts or 0) != 0):
    errors.append("Public restricted case: unauthorized response")
if an.public_restricted and (not ver.handoff_required or ver.verification_result != "not_run" or ver.lifecycle_status != "human_handoff_required"):
    errors.append("Public restricted case: invalid verification or handoff")

if not inv.assessment:
    errors.append("Stage 1 (security_investigator): no assessment returned.")
if not an.severity:
    errors.append("Stage 2 (risk_analyst): no severity returned.")
if not resp.action_result:
    errors.append("Stage 3 (response_agent): no action_result returned.")
if not ver.lifecycle_status:
    errors.append("Stage 4 (verification_handoff): no lifecycle_status returned.")

self.output.case_id              = parent.input.case_id
self.output.assessment           = inv.assessment
self.output.evidence             = list(inv.evidence or [])
self.output.confidence           = float(inv.confidence or 0)
self.output.score                = an.score
self.output.severity             = an.severity
self.output.notify_first         = bool(an.notify_first)
self.output.public_restricted    = bool(an.public_restricted)
self.output.service_ids          = list(an.service_ids or [])
self.output.affected_public_service = an.affected_public_service
self.output.action_taken         = resp.action_taken
self.output.action_attempts      = int(resp.action_attempts or 0)
self.output.action_result        = resp.action_result
self.output.verification_result  = ver.verification_result
self.output.lifecycle_status     = ver.lifecycle_status
self.output.handoff_required = bool(ver.handoff_required) or inv.assessment in ("invalid_input", "error")
self.output.human_intervention   = list(ver.human_intervention or [])
self.output.completed_ai_work    = list(ver.completed_ai_work or [])
self.output.notification_required = bool(notif.notification_required)
self.output.notification_message  = notif.notification_message
self.output.investigator_result_json = inv.investigator_result_json
self.output.analyst_result_json      = an.analyst_result_json
self.output.response_result_json     = resp.response_result_json
self.output.errors = list(errors) + (
    list(inv.errors or [])
    if inv.assessment in ("invalid_input", "error")
    else []
)
self.output.all_stages_complete  = len(errors) == 0
""",
    )

    # ── Edge graph (deterministic sequence) ─────────────────────────────────
    aflow.sequence(
        START,
        investigator_node,
        analyst_node,
        notification_node,
        response_node,
        verifier_node,
        aggregation_node,
        END,
    )

    # Map Aggregate Results directly to final workflow output
    for field_name in PipelineOutput.model_fields:
        aflow.map_output(
            output_variable=field_name,
            expression=f"flow.aggregate_results.output.{field_name}"
        )


    return aflow
