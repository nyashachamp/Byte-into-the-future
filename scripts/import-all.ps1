#Requires -Version 5.1
<#
.SYNOPSIS
    Import all five-agent public-service-risk-analysis artefacts into the active
    watsonx Orchestrate environment in the correct bottom-up dependency order.

.DESCRIPTION
    Import order (bottom-up, as required by the ADK collaborators mechanism):

      Step 1  Sync all package copies (pipeline.py × 5, dataset × 5, agent modules × 4)
      Step 2  Run offline tests to confirm package integrity
      Step 3  Import specialist Python tools:
                investigate_case    (tools/investigator_pkg)
                analyse_impact      (tools/analyst_pkg)
                execute_response    (tools/response_pkg)
                verify_and_handoff  (tools/verifier_pkg)
      Step 4  Import original tool (preserved, re-imported for idempotency):
                analyze_risk_cases  (tools/risk_tool_pkg)
      Step 5  Import specialist agents (must exist before Orchestrator):
                security_investigator  (agents/security_investigator_agent.yaml)
                risk_analyst           (agents/risk_analyst_agent.yaml)
                response_agent         (agents/response_agent.yaml)
                verification_handoff_agent (agents/verification_handoff_agent.yaml)
      Step 6  Import Orchestrator last (all collaborators now present):
                orchestrator_agent  (agents/orchestrator_agent.yaml)
      Step 7  Import original agent (preserved, re-imported for idempotency):
                risk_analysis_agent (agents/risk_analysis_agent.yaml)

    Prerequisites:
      - venv present: python -m venv venv && venv\Scripts\pip install ibm-watsonx-orchestrate
      - Active WXO environment: orchestrate env list
      - Run from repository root

    Usage:
      # Normal import
      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
      .\scripts\import-all.ps1

      # Dry-run (print commands, no changes)
      .\scripts\import-all.ps1 -DryRun

.PARAMETER DryRun
    When set, prints every orchestrate command that would be run without
    executing any of them.  No environment changes are made.
#>

[CmdletBinding()]
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Write-Step {
    param([string]$Label)
    Write-Host ""
    Write-Host "=== $Label ===" -ForegroundColor Cyan
}

function Invoke-Step {
    <#
    .SYNOPSIS
        In live mode: run the command and abort on failure.
        In dry-run mode: print the command without executing it.
    #>
    param([string[]]$Cmd)
    $display = $Cmd -join ' '
    if ($DryRun) {
        Write-Host "  [DRY-RUN] $display" -ForegroundColor Yellow
    } else {
        Write-Host "  > $display"
        & $Cmd[0] $Cmd[1..($Cmd.Length - 1)]
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Command failed (exit $LASTEXITCODE): $display"
            exit $LASTEXITCODE
        }
    }
}

function Copy-BinaryFile {
    param([string]$Src, [string]$Dst)
    if ($DryRun) {
        Write-Host "  [DRY-RUN] Copy-Item $Src -> $Dst" -ForegroundColor Yellow
    } else {
        Write-Host "  Syncing: $Dst"
        [System.IO.File]::WriteAllBytes($Dst, [System.IO.File]::ReadAllBytes($Src))
    }
}

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------

Write-Step "Preflight checks"

# 1. Confirm venv exists
$venvActivate = Join-Path $repoRoot 'venv\Scripts\Activate.ps1'
if (-not (Test-Path $venvActivate)) {
    Write-Error "venv not found at $venvActivate.  Run: python -m venv venv && venv\Scripts\pip install ibm-watsonx-orchestrate"
    exit 1
}
Write-Host "  venv present: $venvActivate"

# 2. Confirm required YAML agent files exist
$agentFiles = @(
    'agents\security_investigator_agent.yaml',
    'agents\risk_analyst_agent.yaml',
    'agents\response_agent.yaml',
    'agents\verification_handoff_agent.yaml',
    'agents\orchestrator_agent.yaml',
    'agents\risk_analysis_agent.yaml'
)
foreach ($f in $agentFiles) {
    $full = Join-Path $repoRoot $f
    if (-not (Test-Path $full)) {
        Write-Error "Missing required agent file: $full"
        exit 1
    }
    Write-Host "  Found: $f"
}

# 3. Confirm required tool entry-point files exist
$toolFiles = @(
    'tools\investigator_pkg\investigate_case.py',
    'tools\analyst_pkg\analyse_impact.py',
    'tools\response_pkg\execute_response.py',
    'tools\verifier_pkg\verify_and_handoff.py',
    'tools\risk_tool_pkg\analyze_risk_cases.py'
)
foreach ($f in $toolFiles) {
    $full = Join-Path $repoRoot $f
    if (-not (Test-Path $full)) {
        Write-Error "Missing required tool file: $full"
        exit 1
    }
    Write-Host "  Found: $f"
}

# 4. Confirm orchestrate CLI is reachable
Write-Host "  Checking orchestrate CLI..."
if (-not $DryRun) {
    $null = Get-Command orchestrate -ErrorAction SilentlyContinue
    if ($null -eq (Get-Command orchestrate -ErrorAction SilentlyContinue)) {
        # Try activating venv first
        & $venvActivate
    }
    $cliCheck = & orchestrate env list 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "orchestrate env list failed — ensure a WXO environment is active.`n$cliCheck"
        exit 1
    }
    Write-Host "  orchestrate CLI: OK"
} else {
    Write-Host "  [DRY-RUN] orchestrate CLI check skipped"
}

Write-Host ""
Write-Host "Preflight checks passed." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Activate venv
# ---------------------------------------------------------------------------

Write-Step "Activating venv"
if (-not $DryRun) {
    & $venvActivate
    Write-Host "  venv activated."
} else {
    Write-Host "  [DRY-RUN] Would activate: $venvActivate" -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# Step 1 — Sync all package copies
# ---------------------------------------------------------------------------

Write-Step "Step 1 — Sync package copies"

# Monolithic pipeline → four specialist packages (risk_tool_pkg is the source)
$monolithPipeline = Join-Path $repoRoot 'tools\risk_tool_pkg\pipeline.py'
# The monolith copy is already the source; only sync the four new packages from it.
foreach ($target in @(
    'tools\investigator_pkg\pipeline.py',
    'tools\analyst_pkg\pipeline.py',
    'tools\response_pkg\pipeline.py',
    'tools\verifier_pkg\pipeline.py'
)) {
    Copy-BinaryFile -Src $monolithPipeline -Dst (Join-Path $repoRoot $target)
}

# Dataset → all five tool packages
$datasetSrc = Join-Path $repoRoot 'data\samples\public-service-risk-v1.json'
foreach ($target in @(
    'tools\risk_tool_pkg\data\public-service-risk-v1.json',
    'tools\investigator_pkg\data\public-service-risk-v1.json',
    'tools\analyst_pkg\data\public-service-risk-v1.json',
    'tools\response_pkg\data\public-service-risk-v1.json',
    'tools\verifier_pkg\data\public-service-risk-v1.json'
)) {
    Copy-BinaryFile -Src $datasetSrc -Dst (Join-Path $repoRoot $target)
}

# Agent modules → specialist packages
$agentModules = @(
    @{ Src = 'src\source-code\src\agents\investigator.py';   Dst = 'tools\investigator_pkg\agents\investigator.py' },
    @{ Src = 'src\source-code\src\agents\analyst.py';        Dst = 'tools\analyst_pkg\agents\analyst.py' },
    @{ Src = 'src\source-code\src\agents\response_agent.py'; Dst = 'tools\response_pkg\agents\response_agent.py' },
    @{ Src = 'src\source-code\src\agents\verifier.py';       Dst = 'tools\verifier_pkg\agents\verifier.py' }
)
foreach ($pair in $agentModules) {
    Copy-BinaryFile -Src (Join-Path $repoRoot $pair.Src) -Dst (Join-Path $repoRoot $pair.Dst)
}

# ---------------------------------------------------------------------------
# Step 2 — Offline sync + YAML tests
# ---------------------------------------------------------------------------

Write-Step "Step 2 — Offline tests (sync + YAML validation)"

$pytestExe = Join-Path $repoRoot 'venv\Scripts\python.exe'
Invoke-Step @($pytestExe, '-m', 'pytest',
    'tests\test_sync.py',
    'tests\test_agent_yaml.py',
    '-v', '--tb=short')

# ---------------------------------------------------------------------------
# Step 3 — Import specialist Python tools (in delegation order)
# ---------------------------------------------------------------------------

Write-Step "Step 3 — Import specialist Python tools"

Invoke-Step @('orchestrate', 'tools', 'import',
    '-k', 'python',
    '-f', 'tools/investigator_pkg/investigate_case.py',
    '--package-root', 'tools/investigator_pkg')

Invoke-Step @('orchestrate', 'tools', 'import',
    '-k', 'python',
    '-f', 'tools/analyst_pkg/analyse_impact.py',
    '--package-root', 'tools/analyst_pkg')

Invoke-Step @('orchestrate', 'tools', 'import',
    '-k', 'python',
    '-f', 'tools/response_pkg/execute_response.py',
    '--package-root', 'tools/response_pkg')

Invoke-Step @('orchestrate', 'tools', 'import',
    '-k', 'python',
    '-f', 'tools/verifier_pkg/verify_and_handoff.py',
    '--package-root', 'tools/verifier_pkg')

# ---------------------------------------------------------------------------
# Step 4 — Import original tool (preserved, idempotent re-import)
# ---------------------------------------------------------------------------

Write-Step "Step 4 — Import original tool (analyze_risk_cases — preserved)"

Invoke-Step @('orchestrate', 'tools', 'import',
    '-k', 'python',
    '-f', 'tools/risk_tool_pkg/analyze_risk_cases.py',
    '--package-root', 'tools/risk_tool_pkg')

# ---------------------------------------------------------------------------
# Step 5 — Import specialist agents (before Orchestrator)
# ---------------------------------------------------------------------------

Write-Step "Step 5 — Import specialist agents"

Invoke-Step @('orchestrate', 'agents', 'import',
    '-f', 'agents/security_investigator_agent.yaml')

Invoke-Step @('orchestrate', 'agents', 'import',
    '-f', 'agents/risk_analyst_agent.yaml')

Invoke-Step @('orchestrate', 'agents', 'import',
    '-f', 'agents/response_agent.yaml')

Invoke-Step @('orchestrate', 'agents', 'import',
    '-f', 'agents/verification_handoff_agent.yaml')

# ---------------------------------------------------------------------------
# Step 6 — Import Orchestrator LAST (all collaborators now present)
# ---------------------------------------------------------------------------

Write-Step "Step 6 — Import Orchestrator (all collaborators must be present)"

Invoke-Step @('orchestrate', 'agents', 'import',
    '-f', 'agents/orchestrator_agent.yaml')

# ---------------------------------------------------------------------------
# Step 7 — Import original agent (preserved, idempotent re-import)
# ---------------------------------------------------------------------------

Write-Step "Step 7 — Import original agent (risk_analysis_agent — preserved)"

Invoke-Step @('orchestrate', 'agents', 'import',
    '-f', 'agents/risk_analysis_agent.yaml')

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

Write-Host ""
if ($DryRun) {
    Write-Host "Dry-run complete — no changes were made to the WXO environment." -ForegroundColor Yellow
} else {
    Write-Host "Import complete." -ForegroundColor Green
}
Write-Host ""
Write-Host "Verify with:"
Write-Host "  orchestrate tools list"
Write-Host "  orchestrate agents list"
