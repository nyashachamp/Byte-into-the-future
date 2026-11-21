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

st.set_page_config(
    page_title="Civic Shield | Public Service Risk Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown("""<style>
:root { color-scheme: dark; }
.stApp { background:#090f1b; color:#e9f0fb; font-family:"IBM Plex Sans",Arial,sans-serif; }
.block-container { max-width:1240px; padding-top:1.8rem; padding-bottom:3rem; }
[data-testid="stHeader"] { background:#090f1b; }
[data-testid="stSidebar"] { background:#111c2b; }
[data-testid="stMetric"] {
  background:#152236; padding:1.1rem 1.2rem; border:1px solid #2a3b55;
  border-radius:12px; min-height:118px;
}
[data-testid="stMetricLabel"] { color:#b9cbe2; }
[data-testid="stMetricValue"] { color:#7dc4ff; }
.stTabs [data-baseweb="tab-list"] { gap:12px; border-bottom:1px solid #2b3b52; }
.stTabs [data-baseweb="tab"] { padding:12px 18px; border-radius:8px 8px 0 0; }
div.stButton > button { border:1px solid #5a9de2; border-radius:8px; min-height:44px; }
div.stButton > button[kind="primary"] {
  background:#1672d5; color:white; border-color:#1672d5; font-weight:700;
}
.civic-hero {
  padding:2rem 2.2rem; margin-bottom:1.2rem; border:1px solid #2a4665;
  background:linear-gradient(115deg,#112844 0%,#112035 58%,#19243b 100%);
  border-radius:16px;
}
.civic-eyebrow { color:#80c6ff; letter-spacing:.14em; font-size:.76rem; font-weight:700; }
.civic-hero h1 { font-size:clamp(2rem,4vw,3.4rem); margin:.5rem 0 .35rem; color:#ffffff; }
.civic-hero p { color:#d1e0f2; max-width:760px; margin:0 0 1.1rem; line-height:1.5; }
.civic-pill {
  display:inline-block; margin-right:.4rem; margin-top:.4rem;
  background:#254264; border:1px solid #4979a5; color:#eef6ff;
  padding:.28rem .65rem; border-radius:20px; font-size:.79rem;
}
.civic-section { color:#8bbde8; text-transform:uppercase; letter-spacing:.12em; font-size:.76rem; font-weight:700; }
.civic-flow { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:16px 0 24px; }
.civic-stage { border:1px solid #2c4765; background:#122137; border-radius:12px; padding:16px; }
.civic-stage strong { display:block; font-size:.92rem; color:#f2f7ff; margin:8px 0 4px; }
.civic-stage small { color:#bfd0e6; line-height:1.35; }
.civic-step { color:#74bcff; letter-spacing:.08em; font-size:.75rem; font-weight:700; }
@media (max-width:770px) {
  .civic-hero { padding:1.35rem; }
  .civic-flow { grid-template-columns:repeat(2,minmax(0,1fr)); }
}
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
        st.warning("Live runs are disabled until DASHBOARD_ACCESS_CODE is configured as a Code Engine secret.")
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


def main() -> None:
    st.markdown("""
    <div class="civic-hero">
      <div class="civic-eyebrow">IBM SKILLSBUILD  /  BYTE INTO THE FUTURE</div>
      <h1>Civic Shield</h1>
      <p>Public-service risk intelligence with policy-gated simulation,
      independent verification and accountable human handoff.</p>
      <span class="civic-pill">12 synthetic scenarios</span>
      <span class="civic-pill">Orchestrator + four specialists</span>
      <span class="civic-pill">Human-controlled closure</span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Proof of concept • fictional government environment • in-memory actions only • no real remediation")
    results = analyze(DATASET)
    result_by_id = {item.case_id: item for item in results}

    st.markdown("### Select a demonstration case")
    selected_id = st.selectbox(
        "Synthetic scenario",
        list(result_by_id),
        format_func=lambda case_id: f"{case_id} — {result_by_id[case_id].title}",
        label_visibility="collapsed",
    )
    selected = result_by_id[selected_id]
    st.caption(
        f"Selected fixture: {selected.case_id} · {selected.affected_public_service}. "
        "The case description is from the synthetic dataset, not a live agent assessment."
    )
    st.markdown('<div class="civic-section">Configured specialist workflow · stages require trace verification</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="civic-flow">
      <div class="civic-stage"><span class="civic-step">01 / INVESTIGATE</span>
      <strong>Security Investigator</strong><small>Validate baseline deviations and collect evidence</small></div>
      <div class="civic-stage"><span class="civic-step">02 / ASSESS</span>
      <strong>Risk Analyst</strong><small>Map dependencies and prioritize impact</small></div>
      <div class="civic-stage"><span class="civic-step">03 / AUTHORIZE</span>
      <strong>Response Agent</strong><small>Enforce policy and simulate permitted actions</small></div>
      <div class="civic-stage"><span class="civic-step">04 / VERIFY</span>
      <strong>Verification &amp; Handoff</strong><small>Check post-action state and require human closure</small></div>
    </div>
    """, unsafe_allow_html=True)

    live_tab, local_tab = st.tabs(["● Live watsonx Orchestrate", "◷ Offline reference pipeline"])
    with live_tab:
        render_live(selected_id)
    with local_tab:
        render_local(selected)


if __name__ == "__main__":
    main()
