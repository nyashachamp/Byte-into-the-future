# Source code — implementation map

**Current documentation checkpoint:** 20 November 2026. The recovery branch contains both a tested deterministic prototype and files for a newer native watsonx multi-agent configuration.

## Which folder does what?

| Location | Role | What it does **not** prove |
|---|---|---|
| [`source-code/src/`](source-code/src/) | Deterministic Python pipeline, CLI entry point and Streamlit dashboard | Does not prove dashboard-to-Orchestrate connectivity |
| [`source-code/src/agents/`](source-code/src/agents/) | Python components implementing investigator, analyst, response and verification logic | Not native watsonx Orchestrate agent instances by themselves |
| [`source-code/agents/`](source-code/agents/) | Older logical agent/policy YAML design from prototype | Not the same as the root-native agent specs |
| [`../agents/`](../agents/) | Root-native watsonx agent YAML specs including supervisor and four specialists | Import/configuration is not a Live deployment test |
| [`../tools/`](../tools/) | Separate coded-tool packages used by Orchestrate agents | Code presence is not proof of a formal multi-agent PASS |
| [`source-code/tests/`](source-code/tests/) and [`../tests/`](../tests/) | Automated tests, consistency checks and fixtures | Not a substitute for saved agent evaluations |

The initial original prototype is also preserved on the separate [`ghazal-initial-code` branch](https://github.com/nyashachamp/Byte-into-the-future/tree/ghazal-initial-code/src/ghazal-project). The default `main` remains an older baseline.

## Running the local implementation

See [source-code/README.md](source-code/README.md) for local startup commands. The native IBM Bob/Orchestrate configuration and its evidence status are documented in the root [README](../README.md) and [current status](../docs/current-system-status-2026-11-20.md).

## Safety and branch handling

Do not merge or overwrite the recovery branch or local IBM Bob changes without reviewing synchronization and tests. Never commit secrets, credentials, or unredacted personal records. The project uses synthetic data only.
