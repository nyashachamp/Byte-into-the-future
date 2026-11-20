#Requires -Version 5.1
<#
.SYNOPSIS
    Remove ALL risk-analysis agents and tools from the active watsonx Orchestrate
    environment (both the five-agent deployment and the original single agent).

.DESCRIPTION
    Removal order (top-down, reverse of import):

      Step 1  Remove Orchestrator
                orchestrator_agent
      Step 2  Remove specialist agents:
                verification_handoff_agent
                response_agent
                risk_analyst
                security_investigator
      Step 3  Remove original single agent:
                risk_analysis_agent
      Step 4  Remove specialist Python tools:
                verify_and_handoff
                execute_response
                analyse_impact
                investigate_case
      Step 5  Remove original tool:
                analyze_risk_cases

    To remove ONLY the five-agent deployment while preserving the original
    risk_analysis_agent and analyze_risk_cases, use:
        .\scripts\delete-five-agents.ps1

    Prerequisites:
      - venv must be active or present at venv\Scripts\Activate.ps1
      - Run from repository root

    Usage:
      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
      .\scripts\delete-all.ps1

      # Dry-run (print commands, no changes)
      .\scripts\delete-all.ps1 -DryRun

.PARAMETER DryRun
    When set, prints every orchestrate command that would be run without
    executing any of them.  No environment changes are made.
#>

[CmdletBinding()]
param(
    [switch]$DryRun,

    # Pass -Force to bypass the interactive confirmation prompt.
    # Required for non-interactive / CI use; never pass in an interactive
    # session unless you have explicit team approval to wipe ALL deployments.
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'   # allow individual removals to fail (already-deleted items)

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
    param([string[]]$Cmd)
    $display = $Cmd -join ' '
    if ($DryRun) {
        Write-Host "  [DRY-RUN] $display" -ForegroundColor Yellow
    } else {
        Write-Host "  > $display"
        & $Cmd[0] $Cmd[1..($Cmd.Length - 1)]
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Command exited $($LASTEXITCODE) — item may already be absent: $display"
        }
    }
}

# ---------------------------------------------------------------------------
# Confirmation safeguard
# ---------------------------------------------------------------------------
# This script removes EVERYTHING, including the original risk_analysis_agent
# and analyze_risk_cases.  Require explicit opt-in unless -DryRun or -Force.

if (-not $DryRun) {
    Write-Host ""
    Write-Host "WARNING: delete-all.ps1 will remove ALL of the following from the" `
        -ForegroundColor Red
    Write-Host "         active watsonx Orchestrate environment:" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Agents (5 + 1 original):" -ForegroundColor Red
    Write-Host "    orchestrator_agent" -ForegroundColor Red
    Write-Host "    verification_handoff_agent" -ForegroundColor Red
    Write-Host "    response_agent" -ForegroundColor Red
    Write-Host "    risk_analyst" -ForegroundColor Red
    Write-Host "    security_investigator" -ForegroundColor Red
    Write-Host "    risk_analysis_agent  (ORIGINAL — preserved by delete-five-agents.ps1)" `
        -ForegroundColor Red
    Write-Host ""
    Write-Host "  Tools (4 specialist + 1 original):" -ForegroundColor Red
    Write-Host "    verify_and_handoff" -ForegroundColor Red
    Write-Host "    execute_response" -ForegroundColor Red
    Write-Host "    analyse_impact" -ForegroundColor Red
    Write-Host "    investigate_case" -ForegroundColor Red
    Write-Host "    analyze_risk_cases  (ORIGINAL — preserved by delete-five-agents.ps1)" `
        -ForegroundColor Red
    Write-Host ""
    Write-Host "  To remove ONLY the five-agent deployment (preserving the originals):" `
        -ForegroundColor Yellow
    Write-Host "    .\scripts\delete-five-agents.ps1" -ForegroundColor Yellow
    Write-Host ""

    if ($Force) {
        Write-Host "-Force flag detected — skipping interactive confirmation." `
            -ForegroundColor Yellow
    } else {
        $answer = Read-Host "Type exactly 'yes' to confirm full cleanup, or anything else to abort"
        if ($answer -ne 'yes') {
            Write-Host ""
            Write-Host "Aborted — no changes were made." -ForegroundColor Green
            exit 0
        }
    }
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Activate venv
# ---------------------------------------------------------------------------

$venvActivate = Join-Path $repoRoot 'venv\Scripts\Activate.ps1'
if (Test-Path $venvActivate) {
    if (-not $DryRun) { & $venvActivate }
} else {
    Write-Warning "venv not found — orchestrate CLI may not be available."
}

# ---------------------------------------------------------------------------
# Step 1 — Orchestrator
# ---------------------------------------------------------------------------

Write-Step "Step 1 — Remove Orchestrator"

Invoke-Step @('orchestrate', 'agents', 'remove',
    '--name', 'orchestrator_agent', '--kind', 'native')

# ---------------------------------------------------------------------------
# Step 2 — Specialist agents
# ---------------------------------------------------------------------------

Write-Step "Step 2 — Remove specialist agents"

Invoke-Step @('orchestrate', 'agents', 'remove',
    '--name', 'verification_handoff_agent', '--kind', 'native')

Invoke-Step @('orchestrate', 'agents', 'remove',
    '--name', 'response_agent', '--kind', 'native')

Invoke-Step @('orchestrate', 'agents', 'remove',
    '--name', 'risk_analyst', '--kind', 'native')

Invoke-Step @('orchestrate', 'agents', 'remove',
    '--name', 'security_investigator', '--kind', 'native')

# ---------------------------------------------------------------------------
# Step 3 — Original single agent
# ---------------------------------------------------------------------------

Write-Step "Step 3 — Remove original single agent (risk_analysis_agent)"

Invoke-Step @('orchestrate', 'agents', 'remove',
    '--name', 'risk_analysis_agent', '--kind', 'native')

# ---------------------------------------------------------------------------
# Step 4 — Specialist tools
# ---------------------------------------------------------------------------

Write-Step "Step 4 — Remove specialist Python tools"

Invoke-Step @('orchestrate', 'tools', 'remove', '-n', 'verify_and_handoff')
Invoke-Step @('orchestrate', 'tools', 'remove', '-n', 'execute_response')
Invoke-Step @('orchestrate', 'tools', 'remove', '-n', 'analyse_impact')
Invoke-Step @('orchestrate', 'tools', 'remove', '-n', 'investigate_case')

# ---------------------------------------------------------------------------
# Step 5 — Original tool
# ---------------------------------------------------------------------------

Write-Step "Step 5 — Remove original tool (analyze_risk_cases)"

Invoke-Step @('orchestrate', 'tools', 'remove', '-n', 'analyze_risk_cases')

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

Write-Host ""
if ($DryRun) {
    Write-Host "Dry-run complete — no changes were made to the WXO environment." -ForegroundColor Yellow
} else {
    Write-Host "Full cleanup complete." -ForegroundColor Green
}
Write-Host ""
Write-Host "Verify with:"
Write-Host "  orchestrate agents list"
Write-Host "  orchestrate tools list"
