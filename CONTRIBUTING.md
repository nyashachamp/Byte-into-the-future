> **Current contribution note (2026-11-20):** The onboarding procedure below was prepared for an earlier phase of the team project. This repository is **already public**, `main` is an older baseline, and the current documented working branch is `recovery-five-agent-2026-11-19`. Review local-versus-remote divergence before any push; the recovery branch has documentation commits made directly on GitHub. Do not force-push, reset, merge, or publish code without an explicit review. Follow [current status](docs/current-system-status-2026-11-20.md) and [documentation guide](docs/README.md) for current project context.

# Contributing Guide

## For Ghazal: adding the VS Code project

Your existing work goes into `src/` exactly as it is. Nothing needs to be rebuilt or restructured.

**Before you start:** accept the GitHub invite from your email (or at https://github.com/nyashachamp/Byte-into-the-future/invitations).

### Step 1: Check for secrets first

Before uploading anything, look through your project for API keys, IBM Cloud credentials, tokens, or passwords written directly in code or config files. Move any you find into a file named `.env` in the project root. Use `.env.example` in this repo as the template. The `.gitignore` here already blocks `.env`, but it can't catch a key typed directly into a `.py` or `.json` file.

### Step 2: Get the repo into VS Code

1. In VS Code, press `Ctrl+Shift+P` (`Cmd+Shift+P` on Mac) and choose **Git: Clone**.
2. Paste `https://github.com/nyashachamp/Byte-into-the-future.git` and pick a folder. Sign in to GitHub if asked.
3. Open the cloned folder.

### Step 3: Create a branch

Click the branch name in the bottom-left corner of VS Code, choose **Create new branch**, and name it `add-agent-code`.

### Step 4: Copy your project in

Copy your existing project files into the `src/` folder of the cloned repo. Keep your folder layout as is. If your project has a `requirements.txt` or `package.json`, it can stay inside `src/`.

### Step 5: Commit and push

1. Open the **Source Control** panel (the branch icon on the left).
2. **Check the list of files.** If you see `.env`, any key files, `node_modules`, `.venv`, or large data files, stop and let Nyasha know.
3. Type a message like `Add agents, orchestration, and dashboard`, click **Commit**, then **Publish Branch**.

### Step 6: Open a pull request

On GitHub, click **Compare & pull request**, add a short description, and assign Nyasha as reviewer. Once it's reviewed, merge it into `main`.

### Step 7: Fill in setup instructions

Update the **Installation** section of `README.md` with how to install dependencies and run the agents and dashboard.

---

## Team workflow

**Branches**
- `main` always holds working, reviewed code.
- Create a short-lived branch for each piece of work: `add-agent-code`, `dataset-prep`, `docs-update`, `fix-dashboard-chart`.

**Pull requests**
- Every change goes into `main` through a pull request.
- The other teammate reviews it, mainly checking that no secrets are included and nothing breaks.

**Issues**
- Track tasks as GitHub Issues with labels: `agents`, `dashboard`, `data`, `testing`, `docs`, `ibm-deliverable`.
- Assign each issue to one person.

**Documentation responsibilities**

| Area | Owner |
|---|---|
| README overview, docs/, milestones, IBM deliverables | Nyasha |
| Installation steps, code comments, agent configuration notes | Ghazal |
| Dataset documentation and test results | Shared |

## Security rules

1. Never commit `.env`, API keys, IBM Cloud credentials, tokens, or passwords.
2. If a secret is ever committed by mistake, tell the team right away and **rotate the key in IBM Cloud immediately**. Deleting the file afterward does not remove it from Git history.
3. Use only synthetic or authorized data. No personal or citizen information.
4. The repository is now **public**. Review every proposed commit, screenshot, log, and Git history for leaked credentials, tokens, contact information, or other sensitive data. If exposed secrets are found, rotate/revoke them; removing a file does not erase repository history.
