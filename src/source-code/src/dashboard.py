"""Streamlit view for the synthetic 12-case testing workflow.

The "Live watsonx Orchestrate" tab sends the selected case to the deployed
orchestrator_agent (which runs the civic_shield_pipeline flow) and shows its
reply. The "Local reference pipeline" tab is the offline deterministic
pipeline, kept for comparison; it does not call Orchestrate.
"""

from pathlib import Path
import csv
import html
import io
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

st.set_page_config(
    page_title="Civic Shield | Security Operations",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("""<style>
:root { color-scheme: dark; }
html, body, .stApp {
    background: #081320 !important; color: #e8f4fa !important;
    font-family: "Segoe UI", "IBM Plex Sans", Arial, sans-serif;
}
[data-testid="stHeader"] { background: #081320; }
.block-container { max-width: 1560px; padding: 1.3rem 2.4rem 3rem; }
[data-testid="stSidebar"] {
    background: #0b192b; border-right: 1px solid #1a3650;
}
[data-testid="stSidebar"] .block-container { padding-top: 1.6rem; }
[data-testid="stSidebar"] [role="radiogroup"] label {
    background: #10233a; margin-bottom: .4rem; padding: .65rem .5rem;
    border-radius: 9px; border: 1px solid #19344c; color: #c6e2ef;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover { border-color: #23cec7; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: inherit; }
h1,h2,h3 { color: #f0fbff !important; letter-spacing: -.02em; }
h1 { font-size: clamp(2rem, 3.4vw, 3.1rem) !important; }
h2 { font-size: 1.4rem !important; }
small, .stCaption { color: #90a9bf !important; }
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
    background: #10253a; color: #80e9e2; border: 1px solid #206070;
    border-radius: 11px; font-weight: 650; min-height: 41px;
}
div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover {
    border-color: #30e1d1; color: #cafffa;
}
div[data-testid="stButton"] button[kind="primary"] { background: #007f92; color: white; }
[data-testid="stMetric"] { border: 1px solid #26465e; border-radius: 12px; padding: 1rem; background:#102039; }
[data-testid="stMetricValue"] { color: #38e2d1; }
.stTabs [data-baseweb="tab-list"] { gap: 10px; border-bottom: 1px solid #223b53; }
.stTabs [data-baseweb="tab"] { color: #a7d2df; }
.stTabs [aria-selected="true"] { color: #44e7d6; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
.cs-sidebar-mark { font-weight: 800; letter-spacing: .17em; color:#5ce5de;
  font-size:1.08rem; border-bottom:1px solid #29465c; padding-bottom:1rem; margin-bottom:1rem; }
.cs-topbar { display:flex; justify-content:space-between; align-items:center;
  border-bottom:1px solid #1b324b; padding: .3rem 0 1.5rem; margin-bottom: 1.5rem; gap:1rem; }
.cs-brand { color:#63e8e0; font-size:.83rem; font-weight:800; letter-spacing:.15em; }
.cs-top-pill { font-size:.76rem; color:#a7c8d7; border:1px solid #225568;
  border-radius:30px; padding:.35rem .85rem; white-space:nowrap; }
.cs-title { font-size:clamp(2.1rem,3.4vw,3.2rem); font-weight:780;
  line-height:1.1; margin:.2rem 0 .4rem; color:#c8ffff; }
.cs-subtitle { color:#96b7c7; font-size:.94rem; margin-bottom:1.6rem; }
.cs-eyebrow { color:#5fe0de; font-size:.73rem; font-weight:800; letter-spacing:.16em; margin-bottom:.65rem; }
.cs-section { font-size:1.1rem; color:#efffff; font-weight:750; margin:1.5rem 0 .7rem; }
.cs-stat { min-height:128px; padding:1rem 1.2rem; background:#101f33;
  border:1px solid #223b52; border-radius:14px; box-shadow:0 10px 22px rgba(0,0,0,.08); }
.cs-stat-label { color:#a9c7d8; font-size:.83rem; }
.cs-stat-value { color:#42eddf; font-weight:800; font-size:clamp(1.9rem,2.9vw,2.65rem); margin:.3rem 0; }
.cs-stat-foot { color:#81a6ba; font-size:.74rem; }
.cs-panel { border:1px solid #233d55; background:#101f33;
  border-radius:14px; padding:1.1rem 1.2rem; min-height:300px; }
.cs-panel-head { color:#eaffff; font-size:1.03rem; font-weight:750; }
.cs-panel-sub { color:#779bb0; font-size:.76rem; margin:.35rem 0 1.1rem; }
.cs-chart-svg { width:100%; height:204px; display:block; }
.cs-donut { width:174px; height:174px; margin: 12px auto;
  border-radius:50%; display:grid; place-items:center; }
.cs-donut-hole { width:113px; height:113px; background:#101f33; border-radius:50%;
  display:flex; flex-direction:column; justify-content:center; align-items:center; }
.cs-donut-num { color:#e6ffff; font-size:2rem; font-weight:800; line-height:1.1; }
.cs-donut-label { color:#8daabb; font-size:.75rem; }
.cs-legend { display:flex; flex-wrap:wrap; gap:10px 15px; justify-content:center; color:#a5c2d2; font-size:.74rem; }
.cs-dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:5px; }
.cs-table-wrap { border:1px solid #233d55; border-radius:14px; background:#101f33;
  overflow-x:auto; margin-top:.4rem; }
.cs-table { width:100%; border-collapse:collapse; white-space:nowrap; font-size:.84rem; }
.cs-table th { text-transform:uppercase; font-size:.66rem; letter-spacing:.13em;
  color:#8cb7c9; background:#0d1a2b; text-align:left; padding:1rem; }
.cs-table td { border-top:1px solid #1f354b; color:#cfdfeb; padding:.88rem 1rem; }
.cs-table tr:nth-child(even) td { background: #13263d; }
.cs-status { border-radius:20px; padding:.25rem .55rem; font-size:.73rem;
  background:#163f3d; color:#5cf3bc; }
.cs-status-alert { background:#4b263c; color:#ff97b3; }
.cs-note { background:#102940; border:1px solid #226379; border-radius:10px;
  padding:.85rem 1rem; color:#acd9e8; font-size:.82rem; margin:1rem 0; }
.cs-flow { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin: 1.1rem 0 1.7rem; }
.cs-stage { border:1px solid #2a5165; border-radius:13px; background:#11263d; padding:1rem; }
.cs-stage small { color:#67dedb; font-size:.7rem; letter-spacing:.1em; font-weight:800; }
.cs-stage strong { display:block; color:#e6ffff; margin:.55rem 0 .35rem; font-size:.91rem; }
.cs-stage p { color:#98bacc; font-size:.79rem; margin:0; line-height:1.45; }
@media (max-width:1050px) { .cs-flow { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:720px) { .block-container {padding:1rem .8rem 2rem;}
  .cs-topbar { flex-wrap:wrap;} .cs-chart-svg {height:155px;} }
</style>""", unsafe_allow_html=True)


def render_live(case_id: str) -> None:
    st.markdown("#### Run a case in watsonx Orchestrate")
    st.caption("Live mode calls the existing orchestrator. This screen alone does not prove that all four specialist stages completed.")
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

    # Live requests consume team resources; do not expose them on a public URL.
    access_code = os.environ.get("DASHBOARD_ACCESS_CODE", "")
    if not access_code:
        st.warning("Live runs are disabled until DASHBOARD_ACCESS_CODE is configured as an environment variable.")
        return
    entered = st.text_input("Demo access code", type="password", key="civic_demo_access")
    if not hmac.compare_digest(entered.encode(), access_code.encode()):
        st.info("Enter the demo access code before running a case on the team Orchestrate instance.")
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
    st.download_button(
        "Save agent reply for demo evidence",
        data=outcome.text,
        file_name=f"civic-shield-live-{case_id}.md",
        mime="text/markdown",
        key=f"save_live_{case_id}",
    )
    if os.environ.get("CIVIC_SHIELD_DEBUG", "") == "1":
        with st.expander("Technical API response (review before recording)"):
            st.json(outcome.raw)
    st.caption("Agent replies require matching Orchestrate execution traces before claiming four-stage acceptance.")


def render_local(selected) -> None:
    st.markdown("#### Offline reference results")
    st.caption("The metrics below come from the original local synthetic Python pipeline, NOT from a watsonx Orchestrate execution.")
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


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _metric_card(label: str, value: str | int, detail: str) -> None:
    st.markdown(
        '<div class="cs-stat"><div class="cs-stat-label">' + _escape(label)
        + '</div><div class="cs-stat-value">' + _escape(value)
        + '</div><div class="cs-stat-foot">' + _escape(detail) + '</div></div>',
        unsafe_allow_html=True,
    )


def _export_csv(results) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Case", "Scenario", "Service", "Severity", "Priority score", "Assessment", "Outcome"])
    for item in results:
        writer.writerow([
            item.case_id, item.title, item.affected_public_service, item.severity,
            item.score if item.score is not None else "", item.assessment, item.outcome,
        ])
    return out.getvalue()


def _risk_visual(results) -> None:
    """Render the visual command-center panels using the 12 local synthetic fixtures."""
    scores = [max(0, min(100, int(item.score or 0))) for item in results]
    size = max(1, len(scores))
    points = [
        (24 + i * 632 / max(1, size - 1), 165 - 1.25 * score)
        for i, score in enumerate(scores)
    ]
    polyline = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    area = f"24,175 {polyline} 656,175"
    grid = "".join(
        f'<line x1="24" y1="{y}" x2="656" y2="{y}" stroke="#27435a" stroke-width="1" opacity=".48"/>'
        for y in (40, 75, 110, 145, 175)
    )
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="#75f2e6" stroke="#101f33" stroke-width="2"/>'
        for x, y in points
    )
    chart = (
        '<div class="cs-panel"><div class="cs-panel-head">Scenario risk profile</div>'
        '<div class="cs-panel-sub">Priority scores across the 12 synthetic test cases</div>'
        '<svg class="cs-chart-svg" viewBox="0 0 680 194" preserveAspectRatio="none" aria-label="Risk score by scenario">'
        '<defs><linearGradient id="cs-fill" x1="0" x2="0" y1="0" y2="1">'
        '<stop offset="0%" stop-color="#22dfcf" stop-opacity=".36"/>'
        '<stop offset="100%" stop-color="#166f8d" stop-opacity=".015"/>'
        '</linearGradient></defs>'
        + grid
        + f'<polygon points="{area}" fill="url(#cs-fill)"/>'
        + f'<polyline points="{polyline}" fill="none" stroke="#35e6d9" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>'
        + dots
        + '</svg><div class="cs-panel-sub" style="margin:0">C01 · C02 · C03 · C04 · C05 · C06 · C07 · C08 · C09 · C10 · C11 · C12</div>'
        '</div>'
    )
    color_map = {
        "critical": "#f65395", "high": "#9855ed", "medium": "#26cad5",
        "low": "#c7e75e", "none": "#39d4a7", "unknown": "#31556c",
    }
    distribution = {key: 0 for key in color_map}
    for item in results:
        distribution[item.severity.lower() if item.severity.lower() in distribution else "unknown"] += 1
    slices, cursor = [], 0.0
    for severity, color in color_map.items():
        proportion = 100.0 * distribution[severity] / max(1, len(results))
        if not proportion:
            continue
        slices.append(f"{color} {cursor:.3f}% {cursor + proportion:.3f}%")
        cursor += proportion
    gradient = "conic-gradient(" + ", ".join(slices) + ")"
    flagged = sum(item.severity in ("critical", "high", "medium", "low") for item in results)
    legend = " ".join(
        '<span><i class="cs-dot" style="background:' + color + '"></i>'
        + _escape(severity.title()) + " " + str(distribution[severity]) + '</span>'
        for severity, color in color_map.items() if distribution[severity]
    )
    donut = (
        '<div class="cs-panel"><div class="cs-panel-head">Alert severity</div>'
        '<div class="cs-panel-sub">Scenario classification breakdown</div>'
        f'<div class="cs-donut" style="background:{gradient}">'
        '<div class="cs-donut-hole"><span class="cs-donut-num">' + str(flagged)
        + '</span><span class="cs-donut-label">flagged cases</span></div></div>'
        '<div class="cs-legend">' + legend + '</div></div>'
    )
    left, right = st.columns([1.9, 1.0], gap="medium")
    with left:
        st.markdown(chart, unsafe_allow_html=True)
    with right:
        st.markdown(donut, unsafe_allow_html=True)


def _audit_rows(results) -> None:
    search_col, filter_col = st.columns([2, 1])
    with search_col:
        phrase = st.text_input(
            "Search activity", key="civic_audit_search",
            placeholder="Search by case, service, or scenario...",
        ).casefold().strip()
    with filter_col:
        chosen = st.selectbox(
            "Severity", ["All severities", "Critical", "High", "Medium", "Low", "None", "Unknown"],
            key="civic_severity_filter",
        ).lower()
    rows = [
        item for item in results
        if (chosen == "all severities" or item.severity.lower() == chosen)
        and (not phrase or phrase in " ".join([
            item.case_id, item.title, item.affected_public_service,
            item.severity, item.outcome,
        ]).casefold())
    ]
    body = []
    for item in rows:
        alert = item.severity in ("critical", "high")
        status_class = "cs-status cs-status-alert" if alert else "cs-status"
        body.append(
            '<tr><td><span class="' + status_class + '">' + _escape(item.severity.upper())
            + '</span></td><td>' + _escape(item.case_id)
            + '</td><td>' + _escape(item.title)
            + '</td><td>' + _escape(item.affected_public_service)
            + '</td><td>' + _escape(item.score if item.score is not None else "—")
            + '</td><td>' + _escape(item.outcome.replace("_", " ").title()) + '</td></tr>'
        )
    if not body:
        body = ['<tr><td colspan="6">No scenarios match these filters.</td></tr>']
    st.markdown(
        '<div class="cs-table-wrap"><table class="cs-table"><thead><tr>'
        '<th>Severity</th><th>Case</th><th>Scenario</th><th>Public service</th>'
        '<th>Score</th><th>Outcome</th></tr></thead><tbody>'
        + "".join(body) + '</tbody></table></div>',
        unsafe_allow_html=True,
    )
    st.caption("Synthetic training records · Results are calculated by the offline reference pipeline.")


def _workflow_strip() -> None:
    st.markdown(
        '<div class="cs-flow">'
        '<div class="cs-stage"><small>01 / INVESTIGATE</small><strong>Security Investigator</strong><p>Validate configuration evidence and baselines</p></div>'
        '<div class="cs-stage"><small>02 / ASSESS</small><strong>Risk Analyst</strong><p>Prioritize service impact and determine severity</p></div>'
        '<div class="cs-stage"><small>03 / AUTHORIZE</small><strong>Response Agent</strong><p>Apply action limits and sandbox authorization</p></div>'
        '<div class="cs-stage"><small>04 / VERIFY</small><strong>Verification &amp; Handoff</strong><p>Re-check state and require human closure</p></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def _section_header(title: str, subtitle: str) -> None:
    st.markdown(
        '<div class="cs-eyebrow">BYTE INTO THE FUTURE / CIVIC SHIELD</div>'
        + '<div class="cs-title">' + _escape(title) + '</div>'
        + '<div class="cs-subtitle">' + _escape(subtitle) + '</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    results = analyze(DATASET)
    st.sidebar.markdown('<div class="cs-sidebar-mark">◈ &nbsp; CIVIC SHIELD</div>', unsafe_allow_html=True)
    st.sidebar.caption("SECURITY OPERATIONS")
    page = st.sidebar.radio(
        "Workspace",
        ["Overview", "Case Investigator", "Audit Log", "Live Agent"],
        format_func=lambda value: {
            "Overview": "◫  Overview",
            "Case Investigator": "◇  Case Investigator",
            "Audit Log": "▤  Audit Log",
            "Live Agent": "◎  Live Agent",
        }[value],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.caption("IBM SkillsBuild · Byte into the Future")
    st.sidebar.caption("SYNTHETIC DATASET · 12 SCENARIOS")
    st.sidebar.caption("Human authorization required for closure")

    st.markdown(
        '<div class="cs-topbar"><span class="cs-brand">◈ CIVIC SHIELD / OPERATIONS</span>'
        '<span class="cs-top-pill">● &nbsp; SYNTHETIC DEMONSTRATION</span></div>',
        unsafe_allow_html=True,
    )

    if page == "Overview":
        _section_header(
            "Security Operations Overview",
            "Risk monitoring, policy decisions and accountable handoffs",
        )
        total = len(results)
        compliant = sum(item.assessment == "compliant" for item in results)
        alerts = sum(item.severity in ("critical", "high", "medium", "low") for item in results)
        review = sum(bool(item.handoff_required) for item in results)
        kpis = st.columns(4, gap="medium")
        with kpis[0]:
            _metric_card("Scenarios", total, "Synthetic cases in scope")
        with kpis[1]:
            _metric_card("Compliant", compliant, "No baseline deviation")
        with kpis[2]:
            _metric_card("Alerts", alerts, "Risk findings detected")
        with kpis[3]:
            _metric_card("Human handoffs", review, "Requires follow-up review")
        st.markdown('<div class="cs-section">Risk intelligence</div>', unsafe_allow_html=True)
        _risk_visual(results)
        st.markdown('<div class="cs-section">Audit log overview</div>', unsafe_allow_html=True)
        _audit_rows(results)
        st.markdown(
            '<div class="cs-note">Civic Shield is a simulated public-service risk MVP. '
            'The visual overview uses local synthetic cases; no live government data is shown.</div>',
            unsafe_allow_html=True,
        )

    elif page == "Case Investigator":
        _section_header("Case Investigator", "Select one synthetic scenario and inspect its evidence")
        selected_id = st.selectbox(
            "Scenario", [item.case_id for item in results],
            format_func=lambda case_id: next(
                f"{item.case_id} — {item.title}" for item in results if item.case_id == case_id
            ),
        )
        selected = next(item for item in results if item.case_id == selected_id)
        _workflow_strip()
        render_local(selected)

    elif page == "Audit Log":
        _section_header("Audit Log Overview", "Review case outcomes and searchable activity")
        _audit_rows(results)
        st.download_button(
            "Export case activity (CSV)", data=_export_csv(results),
            file_name="civic-shield-synthetic-case-audit.csv", mime="text/csv",
        )

    else:
        _section_header("Live Agent", "Connect to the team's watsonx Orchestrate workflow")
        _workflow_strip()
        selected_id = st.selectbox(
            "Case to investigate", [item.case_id for item in results],
            format_func=lambda case_id: next(
                f"{item.case_id} — {item.title}" for item in results if item.case_id == case_id
            ),
        )
        render_live(selected_id)


if __name__ == "__main__":
    main()
