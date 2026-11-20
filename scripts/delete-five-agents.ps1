#Requires -Version 5.1
<#
.SYNOPSIS
    Remove only the five-agent deployment from the active watsonx Orchestrate
    environment.  The original risk_analysis_agent and analyze_risk_cases tool
    are NEVER touched by this script.

.DESCRIPTION
    Removal order (top-down, reverse of import):

      Step 1  Remove Orchestrator first (depends on all four collaborators)
                orchestrator_agent
      Step 2  Remove specialist agents (top-down):
                verification_handoff_agent
                response_agent
                risk_analyst
                security_investigator
      Step 3  Remove specialist Python tools:
                verify_and_handoff
                execute_response
                analyse_impact
                investigate_case

    PRESERVED (this script will NOT remove):
      - risk_analysis_agent      (original single agent)
      - analyze_risk_cases       (original tool)

    Prerequisites:
      - venv must be active or present at venv\Scripts\Activate.ps1
      - Run from repository root

    Usage:
      # Rollback the five-agent deployment
      Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
      .\scripts\delete-five-agents.ps1

      # Dry-run (print commands, no changes)
      .\scripts\delete-five-agents.ps1 -DryRun

.PARAMETER DryRun
    When set, prints every orchestrate command that would be run without
    executing any of them.  No environment changes are made.
#>

[CmdletBinding()]
param(
    [switch]$DryRun
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

function Assert-NotProtected {
    <#
    .SYNOPSIS
        Abort immediately if the name passed to a remove command is one of the
        permanently protected items.  This guard runs in both live and dry-run
        mode so that even a dry-run surface the problem.
    #>
    param([string]$Name)
    $script:_protected = @('risk_analysis_agent', 'analyze_risk_cases')
    if ($script:_protected -contains $Name) {
        Write-Error (
            "SAFETY ABORT: '$Name' is a protected item and must never be " +
            "removed by delete-five-agents.ps1.  " +
            "Use delete-all.ps1 for full cleanup only after explicit team approval."
        )
        exit 2
    }
}

function Invoke-Step {
    param(
        [string[]]$Cmd,
        # Optional: the logical name of the resource being removed.
        # When provided, Assert-NotProtected is called before the command runs.
        [string]$ResourceName = ''
    )
    if ($ResourceName -ne '') {
        Assert-NotProtected -Name $ResourceName
    }
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
# Preflight safety check: explicitly confirm protected items are NOT targeted
# ---------------------------------------------------------------------------

Write-Step "Preflight safety checks"

$protected = @('risk_analysis_agent', 'analyze_risk_cases')
Write-Host "  Protected items (will NOT be removed):" -ForegroundColor Green
foreach ($item in $protected) {
    Write-Host "    - $item" -ForegroundColor Green
}

# Confirm venv
$venvActivate = Join-Path $repoRoot 'venv\Scripts\Activate.ps1'
if (-not (Test-Path $venvActivate)) {
    Write-Warning "venv not found at $venvActivate — orchestrate CLI may not be available."
} else {
    Write-Host "  venv present: $venvActivate"
    if (-not $DryRun) {
        & $venvActivate
    }
}

Write-Host ""
Write-Host "Preflight checks passed." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 1 — Remove Orchestrator first
# ---------------------------------------------------------------------------

Write-Step "Step 1 — Remove Orchestrator (must be removed before its collaborators)"

Invoke-Step -ResourceName 'orchestrator_agent' `
    -Cmd @('orchestrate', 'agents', 'remove',
        '--name', 'orchestrator_agent',
        '--kind', 'native')

# ---------------------------------------------------------------------------
# Step 2 — Remove specialist agents (top-down)
# ---------------------------------------------------------------------------

Write-Step "Step 2 — Remove specialist agents"

Invoke-Step -ResourceName 'verification_handoff_agent' `
    -Cmd @('orchestrate', 'agents', 'remove',
        '--name', 'verification_handoff_agent',
        '--kind', 'native')

Invoke-Step -ResourceName 'response_agent' `
    -Cmd @('orchestrate', 'agents', 'remove',
        '--name', 'response_agent',
        '--kind', 'native')

Invoke-Step -ResourceName 'risk_analyst' `
    -Cmd @('orchestrate', 'agents', 'remove',
        '--name', 'risk_analyst',
        '--kind', 'native')

Invoke-Step -ResourceName 'security_investigator' `
    -Cmd @('orchestrate', 'agents', 'remove',
        '--name', 'security_investigator',
        '--kind', 'native')

# ---------------------------------------------------------------------------
# Step 3 — Remove specialist Python tools
# ---------------------------------------------------------------------------

Write-Step "Step 3 — Remove specialist Python tools"

Invoke-Step -ResourceName 'verify_and_handoff' `
    -Cmd @('orchestrate', 'tools', 'remove', '-n', 'verify_and_handoff')

Invoke-Step -ResourceName 'execute_response' `
    -Cmd @('orchestrate', 'tools', 'remove', '-n', 'execute_response')

Invoke-Step -ResourceName 'analyse_impact' `
    -Cmd @('orchestrate', 'tools', 'remove', '-n', 'analyse_impact')

Invoke-Step -ResourceName 'investigate_case' `
    -Cmd @('orchestrate', 'tools', 'remove', '-n', 'investigate_case')

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

Write-Host ""
if ($DryRun) {
    Write-Host "Dry-run complete — no changes were made to the WXO environment." -ForegroundColor Yellow
} else {
    Write-Host "Rollback complete." -ForegroundColor Green
}
Write-Host ""
Write-Host "The following items were NOT removed (preserved):"
foreach ($item in $protected) {
    Write-Host "  - $item"
}
Write-Host ""
Write-Host "Verify with:"
Write-Host "  orchestrate agents list"
Write-Host "  orchestrate tools list"
