"""Local Streamlit dashboard for the synthetic risk-analysis proof of concept."""

from pathlib import Path
import json

import yaml
import streamlit as st

try:
    # Works when launched as: python -m src.dashboard
    from .pipeline import analyze
except ImportError:
    # Works when launched by Streamlit as: streamlit run src/dashboard.py
    from pipeline import analyze


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agents"


def severity_color(severity: str) -> str:
    return {
        "critical": "#3A86FF",
        "high": "#FFD6E0",
        "medium": "#FFD6E0",
        "low": "#3A86FF",
    }.get(severity, "#3A86FF")


def handoff_markdown(finding) -> str:
    """Create a portable human-review handoff for the selected synthetic case."""
    lines = [
        f"# Human Handoff Report — {finding.case_id}",
        "",
        "## Case summary",
        f"- Asset: {finding.asset_name}",
        f"- Affected public service: {finding.affected_public_service}",
        f"- Severity: {finding.severity.upper()}",
        f"- Risk score: {finding.score}/12",
        f"- Confidence: {finding.confidence:.0%}",
        f"- Lifecycle status: {finding.lifecycle_status.replace('_', ' ').title()}",
        "",
        "## Evidence",
        *[f"- {item}" for item in finding.evidence],
        "",
        "## Completed AI work",
        *[f"- {item}" for item in finding.completed_ai_work],
        "",
        "## Outstanding human work",
        *[f"- {item}" for item in finding.outstanding_human_work],
        "",
        "## Decision points",
        *[f"- {item}" for item in finding.decision_points],
        "",
        "## Safety boundary",
        "This is a synthetic proof-of-concept report. No live systems, credentials, or citizen data were used.",
    ]
    return "\n".join(lines)


def load_agent_definitions() -> list[dict]:
    """Load the agent roles and safety rules from YAML definitions."""
    definitions = []
    for path in sorted(AGENT_DIR.glob("*.yaml")):
        definition = yaml.safe_load(path.read_text(encoding="utf-8"))
        definition["file"] = path.name
        definitions.append(definition)
    return definitions


def human_decision_panel(finding) -> None:
    """Simulate a human approval decision without changing any system state."""
    if "human_decisions" not in st.session_state:
        st.session_state.human_decisions = {}

    st.subheader("Human approval panel")
    st.caption(
        "Simulation only: this decision is stored in the current browser session. "
        "No live system or configuration is changed."
    )

    if finding.escalation_required:
        decision_options = [
            "Escalate to incident response",
            "Request more evidence",
        ]
    else:
        decision_options = [
            "Approve simulated remediation",
            "Request more evidence",
            "Escalate to incident response",
        ]

    decision = st.selectbox(
        "Human decision",
        decision_options,
        key=f"decision_{finding.case_id}",
    )
    notes = st.text_area(
        "Responder notes",
        placeholder="Explain the decision or identify the next owner.",
        key=f"notes_{finding.case_id}",
    )
    acknowledged = st.checkbox(
        "I understand this is synthetic data and no live action will be performed.",
        key=f"ack_{finding.case_id}",
    )

    if st.button("Record human decision", key=f"record_{finding.case_id}"):
        if not acknowledged:
            st.error("Please acknowledge the simulation boundary before recording a decision.")
        elif finding.escalation_required and decision == "Approve simulated remediation":
            st.error("Policy gate blocked this action because the finding requires immediate escalation.")
        else:
            st.session_state.human_decisions[finding.case_id] = {
                "decision": decision,
                "notes": notes,
                "status": "recorded",
            }
            st.success(f"Decision recorded: {decision}")

    saved_decision = st.session_state.human_decisions.get(finding.case_id)
    if saved_decision:
        st.info(
            f"Recorded decision: {saved_decision['decision']}\n\n"
            f"Notes: {saved_decision['notes'] or 'No notes provided.'}"
        )


def main() -> None:
    st.set_page_config(
        page_title="Public Service Risk Dashboard",
        page_icon="🛡️",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .stApp {
            background-color: #000000;
            color: #FFFFFF;
        }
        h1, h2, h3 {
            color: #3A86FF !important;
        }
        [data-testid="stMetric"] {
            background-color: #FFD6E0;
            border: 1px solid #3A86FF;
            border-radius: 14px;
            padding: 12px;
        }
        [data-testid="stMetricLabel"] {
            color: #3A86FF;
        }
        [data-testid="stMetricValue"] {
            color: #3A86FF;
        }
        .stButton > button {
            background-color: #3A86FF;
            color: white;
            border: 0;
            border-radius: 10px;
        }
        .stSelectbox [data-baseweb="select"] > div {
            background-color: #111111;
            border-color: #3A86FF;
            color: #FFFFFF;
        }
        div[data-testid="stDataFrame"] {
            border: 2px solid #3A86FF;
            border-radius: 12px;
        }
        [data-testid="stSidebar"] {
            background-color: #000000;
            border-right: 1px solid #3A86FF;
        }
        .stMarkdown, .stCaption, label, p {
            color: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Public Service Risk Dashboard")
    st.caption("Synthetic proof of concept • Human approval remains required for serious actions")

    findings = analyze(ROOT / "data")
    severity_options = ["critical", "high", "medium", "low"]
    selected_severities = st.sidebar.multiselect(
        "Filter by severity",
        severity_options,
        default=severity_options,
    )
    filtered_findings = [
        item for item in findings if item.severity in selected_severities
    ]

    if not filtered_findings:
        st.warning("No findings match the selected severity filters.")
        st.stop()

    findings = filtered_findings
    critical_count = sum(item.severity == "critical" for item in findings)
    escalated_count = sum(item.escalation_required for item in findings)
    affected_services = len({item.affected_public_service for item in findings})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total findings", len(findings))
    col2.metric("Critical findings", critical_count)
    col3.metric("Needs escalation", escalated_count)
    col4.metric("Services affected", affected_services)

    st.divider()
    st.subheader("Findings overview")

    rows = [
        {
            "Case": item.case_id,
            "Asset": item.asset_name,
            "Public service": item.affected_public_service,
            "Severity": item.severity.upper(),
            "Score": item.score,
            "Escalation": "Required" if item.escalation_required else "Review",
            "Status": item.lifecycle_status.replace("_", " ").title(),
        }
        for item in findings
    ]
    st.dataframe(rows, width="stretch", hide_index=True)

    st.subheader("AI-to-human workflow")
    workflow_columns = st.columns(6)
    workflow_steps = [
        ("1", "Observe"),
        ("2", "Classify"),
        ("3", "Prioritize"),
        ("4", "Verify"),
        ("5", "Escalate"),
        ("6", "Human review"),
    ]
    for column, (number, label) in zip(workflow_columns, workflow_steps):
        with column:
            st.markdown(
                f"<div style='background:#3A86FF;padding:10px;border-radius:12px;"
                f"text-align:center;color:#FFFFFF'><b>{number}</b><br>{label}</div>",
                unsafe_allow_html=True,
            )

    st.subheader("Agent registry")
    st.caption("These roles and boundaries are loaded from the project's YAML definitions.")
    agents = load_agent_definitions()
    agent_columns = st.columns(2)
    for index, agent in enumerate(agents):
        with agent_columns[index % 2]:
            with st.expander(agent["name"].replace("_", " ").title()):
                st.write(f"**Purpose:** {agent.get('purpose', 'Not specified')}")
                st.write(f"**Definition:** `{agent['file']}`")
                permissions = agent.get("permissions", [])
                forbidden = agent.get("forbidden_actions", [])
                if permissions:
                    st.write("**Permitted:**", ", ".join(permissions))
                if forbidden:
                    st.write("**Forbidden:**", ", ".join(forbidden))
                if agent.get("immediate_escalation_triggers"):
                    st.write(
                        "**Escalation triggers:**",
                        ", ".join(agent["immediate_escalation_triggers"]),
                    )

    st.subheader("Selected case workflow")
    selected_workflow = [
        "Configuration Agent: compared observed settings with the baseline",
        "Dependency / Impact Agent: linked the asset to a public service",
        "Prioritization Agent: calculated a preliminary risk score",
        "Policy / Human Boundary Gate: evaluated escalation requirements",
        "Handoff / Reporting Agent: prepared human tasks and decision points",
        "Human Review: required before serious remediation or case closure",
    ]
    for index, step in enumerate(selected_workflow, start=1):
        st.write(f"**{index}.** {step}")

    st.subheader("Finding details")
    selected_case = st.selectbox("Select a case", [item.case_id for item in findings])
    selected = next(item for item in findings if item.case_id == selected_case)

    human_decision_panel(selected)

    st.markdown(
        f"### {selected.case_id} — {selected.asset_name} "
        f"<span style='color:{severity_color(selected.severity)}'>({selected.severity.upper()})</span>",
        unsafe_allow_html=True,
    )

    detail_left, detail_right = st.columns(2)
    with detail_left:
        st.write("**Affected public service:**", selected.affected_public_service)
        st.write("**Risk score:**", f"{selected.score}/12")
        st.write("**Confidence:**", f"{selected.confidence:.0%}")
        st.write("**Lifecycle status:**", selected.lifecycle_status.replace("_", " ").title())
    with detail_right:
        if selected.escalation_required:
            st.error("Immediate human escalation required")
        else:
            st.warning("Human review required before remediation")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Evidence", "AI work completed", "Human tasks", "Decision points"]
    )
    with tab1:
        for evidence in selected.evidence:
            st.write(f"- {evidence}")
    with tab2:
        for work in selected.completed_ai_work:
            st.write(f"- {work}")
    with tab3:
        for task in selected.outstanding_human_work:
            st.write(f"- {task}")
    with tab4:
        for decision in selected.decision_points:
            st.write(f"- {decision}")

    st.subheader("Export human handoff")
    report = handoff_markdown(selected)
    st.download_button(
        "Download Markdown handoff report",
        data=report,
        file_name=f"{selected.case_id}_human_handoff.md",
        mime="text/markdown",
    )
    st.download_button(
        "Download JSON finding",
        data=json.dumps(selected.to_dict(), indent=2),
        file_name=f"{selected.case_id}_finding.json",
        mime="application/json",
    )

    st.divider()
    st.caption(
        "Safety boundary: this prototype reads synthetic files only. "
        "It does not connect to live systems, use credentials, modify resources, or close incidents."
    )


if __name__ == "__main__":
    main()
