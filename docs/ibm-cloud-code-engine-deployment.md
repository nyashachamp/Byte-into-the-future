# Deploying the Civic Shield dashboard on IBM Cloud Code Engine

The dashboard (`src/source-code/src/dashboard.py`) is a Streamlit app with two tabs:

| Tab | What it does | Calls Orchestrate? |
|---|---|---|
| **Live watsonx Orchestrate** | Sends `Investigate case Cxx` to the deployed `orchestrator_agent`, which runs the `civic_shield_pipeline` flow through the four specialist agents. Shows the agent's reply. | Yes (`POST {ORCHESTRATE_URL}/v1/orchestrate/{agent_id}/chat/completions`) |
| **Local reference pipeline** | The existing offline deterministic pipeline, kept for comparison. | No |

The dashboard does not re-implement the workflow. The agents, tools, and flow in `agents/` and `tools/` are unchanged.

## Configuration (environment variables, never committed)

| Variable | Value | Secret? |
|---|---|---|
| `ORCHESTRATE_URL` | `https://api.eu-gb.watson-orchestrate.cloud.ibm.com/instances/<instance-id>` (from `orchestrate env list` or the Orchestrate settings → API details page) | No |
| `ORCHESTRATE_AGENT_ID` | ID of the deployed `orchestrator_agent` (the 2026-11-21 traces record `44ae5731-563b-4e0b-b824-2bf4c53c07b0`; confirm with `orchestrate agents list -v` after `orchestrate env activate`) | No |
| `ORCHESTRATE_API_KEY` | IBM Cloud API key with access to the Orchestrate instance. A service ID key is better than a personal key. | **Yes** |
| `DASHBOARD_ACCESS_CODE` | Optional. If set, users must enter this code before triggering live runs, which protects Orchestrate usage on a public URL. | **Yes** |

## Option A: IBM Cloud console (no local Docker or CLI needed)

1. **Code Engine → Projects → Create**: choose region **London (eu-gb)**, the same region as the Orchestrate instance.
2. **Secrets and configmaps → Create → Secret** named `civic-shield-orchestrate`, with keys `ORCHESTRATE_API_KEY` and (optionally) `DASHBOARD_ACCESS_CODE`.
3. **Applications → Create**:
   - Choose **Source code**. Repository: `https://github.com/nyashachamp/Byte-into-the-future`. Branch: `recovery-five-agent-2026-11-19`. (A private repository also needs an SSH code-repo-access secret.)
   - Build: strategy **Dockerfile**, context directory `/`, Dockerfile `Dockerfile`. Use the default Code Engine-managed registry.
   - Listening port: **8080**. Resources: 0.5 vCPU / 1 GB.
   - Autoscaling: **min instances 1** during the demo (this avoids cold starts; set it to 0 afterwards to stop charges). Request timeout: **600 s**.
   - Environment variables: add literals `ORCHESTRATE_URL` and `ORCHESTRATE_AGENT_ID`, then **Reference full secret** `civic-shield-orchestrate`.
4. Click **Create**, wait for the build and the *Ready* status, then open the application URL.

## Option B: `ibmcloud` CLI

```sh
ibmcloud login --sso && ibmcloud target -r eu-gb -g <resource-group>
ibmcloud plugin install code-engine
ibmcloud ce project create --name civic-shield
# secrets.env (local, git-ignored): ORCHESTRATE_API_KEY=... and optionally DASHBOARD_ACCESS_CODE=...
ibmcloud ce secret create --name civic-shield-orchestrate --from-env-file secrets.env
ibmcloud ce application create --name civic-shield-dashboard \
  --build-source https://github.com/nyashachamp/Byte-into-the-future \
  --build-commit recovery-five-agent-2026-11-19 \
  --build-strategy dockerfile --port 8080 \
  --cpu 0.5 --memory 1G --min-scale 1 --request-timeout 600 \
  --env ORCHESTRATE_URL=https://api.eu-gb.watson-orchestrate.cloud.ibm.com/instances/<instance-id> \
  --env ORCHESTRATE_AGENT_ID=<orchestrator-agent-id> \
  --env-from-secret civic-shield-orchestrate
```

Code Engine builds from the pushed branch, so commit and push dashboard changes first. To redeploy after a push, run `ibmcloud ce application update --name civic-shield-dashboard --rebuild`, or click **Rebuild** in the console.

## Local check before deploying (optional)

```powershell
cd src/source-code
$env:ORCHESTRATE_URL="..."; $env:ORCHESTRATE_AGENT_ID="..."; $env:ORCHESTRATE_API_KEY="..."
..\..\venv\Scripts\python.exe -m streamlit run src/dashboard.py
```

## Evidence: what counts as what

Record these separately. Do not merge them into one claim.

1. **Cloud-hosted dashboard working**: the Code Engine URL loads, and the local reference tab renders cases. This proves hosting only.
2. **Live Orchestrate connectivity**: the Live tab returns a reply from the deployed agent (green banner, plus a thread ID). This proves the dashboard reaches the deployed orchestrator.
3. **Verified end-to-end four-stage execution**: for the same thread ID, the watsonx Orchestrate trace shows `civic_shield_pipeline` running all four specialists and `all_stages_complete=true`. The dashboard cannot prove this on its own, so capture the trace as evidence.

If the Live tab shows *not configured*, or a call fails, the deployment counts as (1) only.
