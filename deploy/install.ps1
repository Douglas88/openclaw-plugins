# =============================================================================
# OpenClaw Enhanced Deploy — Windows (PowerShell) One-Click Setup
# =============================================================================
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1 [-SkipNode] [-SkipSkills] [-SkipMcp] [-DryRun]
# =============================================================================
param(
    [switch]$SkipNode,
    [switch]$SkipSkills,
    [switch]$SkipMcp,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "OpenClaw Enhanced Deploy"

function Log   { Write-Host "[✓] $args" -ForegroundColor Green }
function Warn  { Write-Host "[!] $args" -ForegroundColor Yellow }
function Err   { Write-Host "[✗] $args" -ForegroundColor Red; exit 1 }
function Info  { Write-Host "[•] $args" -ForegroundColor Cyan }

$HOME_DIR = $env:USERPROFILE
$OPENCLAW_DIR = "$HOME_DIR\.openclaw"
$WORKSPACE = "$HOME_DIR\.openclaw\workspace"
$SKILLS_DIR = "$OPENCLAW_DIR\plugin-skills"
$REGISTRY_URL = "https://douglas88.github.io/openclaw-plugins/registry.json"

if ($DryRun) { Log "DRY RUN MODE — no changes will be made" }

# ────────────────────────────────────────────────────────
# Step 1: Prerequisites
# ────────────────────────────────────────────────────────
Info "Step 1/7: Checking prerequisites..."

# Node.js
if (-not $SkipNode) {
    $nodeVer = (Get-Command node -ErrorAction SilentlyContinue).Source
    if (-not $nodeVer) {
        Warn "Node.js not found."
        if ($DryRun) { Log "Would install Node.js 24 LTS via winget" }
        else {
            Log "Installing Node.js 24 LTS via winget..."
            winget install OpenJS.NodeJS.LTS --silent
            refreshenv
        }
    }
    $nv = node --version 2>$null; Log "Node.js $nv"
}

# Python
$pyVer = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pyVer) {
    Warn "Python not found."
    if ($DryRun) { Log "Would install Python 3.12 via winget" }
    else {
        Log "Installing Python 3.12 via winget..."
        winget install Python.Python.3.12 --silent
        refreshenv
    }
}
$pv = python --version 2>$null; Log "Python $pv"

# Git
$gitVer = (Get-Command git -ErrorAction SilentlyContinue).Source
if (-not $gitVer) {
    Warn "Git not found."
    if ($DryRun) { Log "Would install Git via winget" }
    else {
        Log "Installing Git..."
        winget install Git.Git --silent
        refreshenv
    }
}
Log "Git $(git --version 2>$null)"

# ────────────────────────────────────────────────────────
# Step 2: Install OpenClaw
# ────────────────────────────────────────────────────────
Info "Step 2/7: Installing OpenClaw..."

$oc = Get-Command openclaw -ErrorAction SilentlyContinue
if (-not $oc) {
    if ($DryRun) { Log "Would: npm install -g openclaw" }
    else { npm install -g openclaw@latest }
}
$ocv = openclaw --version 2>$null; Log "OpenClaw $ocv"

# ────────────────────────────────────────────────────────
# Step 3: Enhanced Configuration
# ────────────────────────────────────────────────────────
Info "Step 3/7: Applying enhanced configuration..."

$ApprovalsFile = "$OPENCLAW_DIR\exec-approvals.json"
$ConfigFile = "$OPENCLAW_DIR\openclaw.json"

# Create workspaces/config if needed
if (-not (Test-Path $WORKSPACE)) { New-Item -ItemType Directory -Path $WORKSPACE -Force | Out-Null }

# exec-approvals.json
if (Test-Path $ApprovalsFile) {
    if ($DryRun) { Log "Would patch exec-approvals.json" }
    else {
        $ea = Get-Content $ApprovalsFile -Raw | ConvertFrom-Json
        $ea.defaults = @{ security = "full"; ask = "off"; askFallback = "full" }
        $ea | ConvertTo-Json -Depth 5 | Set-Content $ApprovalsFile
    }
    Log "exec-approvals: security=full, ask=off"
}

# openclaw.json
if (Test-Path $ConfigFile) {
    if ($DryRun) { Log "Would patch openclaw.json" }
    else {
        $cfg = Get-Content $ConfigFile -Raw | ConvertFrom-Json
        if (-not $cfg.tools) { $cfg | Add-Member -MemberType NoteProperty -Name tools -Value @{} -Force }
        $cfg.tools | Add-Member -MemberType NoteProperty -Name exec -Value @{ security="full"; strictInlineEval=$false } -Force
        $cfg | ConvertTo-Json -Depth 10 | Set-Content $ConfigFile
    }
    Log "openclaw.json: exec=full"
}

# ────────────────────────────────────────────────────────
# Step 4: HEARTBEAT Monitoring
# ────────────────────────────────────────────────────────
Info "Step 4/7: Configuring HEARTBEAT monitoring..."

$HeartbeatFile = "$WORKSPACE\HEARTBEAT.md"
if ($DryRun) { Log "Would write HEARTBEAT.md" }
else {
@'
# Heartbeat Periodic Check Checklist

## High Priority (every heartbeat)
- [ ] System health: openclaw status normal?
- [ ] Gateway: Get-Process openclaw-gateway (Windows) running?

## Medium Priority (every 1-2 hours)
- [ ] Disk space: Get-PSDrive C (alert at 80%)
- [ ] Memory: Get-CimInstance Win32_OperatingSystem (alert at 90%)

## Low Priority (every 12-24 hours)
- [ ] Security audit: openclaw security audit
- [ ] Update check: openclaw update status
- [ ] Error logs: Get-EventLog -LogName Application -Newest 50

## Alert Thresholds
- CPU > 80% for 5min → warning
- Disk < 10GB → critical
'@ | Set-Content $HeartbeatFile
}
Log "HEARTBEAT.md configured"

# ────────────────────────────────────────────────────────
# Step 5: Community Skills via Marketplace
# ────────────────────────────────────────────────────────
if (-not $SkipSkills) {
    Info "Step 5/7: Installing community Skills..."

    $MarketplaceDir = "$SKILLS_DIR\plugin-marketplace\scripts"
    $MarketplaceScript = "$MarketplaceDir\marketplace.py"

    if (-not (Test-Path $MarketplaceScript)) {
        Info "Bootstrapping marketplace..."
        if ($DryRun) { Log "Would download marketplace.py" }
        else {
            New-Item -ItemType Directory -Path $MarketplaceDir -Force | Out-Null
            Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Douglas88/openclaw-plugins/main/plugin-marketplace/scripts/marketplace.py" -OutFile $MarketplaceScript
        }
    }

    if (Test-Path $MarketplaceScript) {
        if ($DryRun) { Log "Would: marketplace sync" }
        else {
            python $MarketplaceScript sync 2>$null
        }
        Log "Marketplace synced from global registry"
    }

    $Skills = @("code-review","test-generator","doc-generator","session-tools","mcp-bridge","ide-panel")
    foreach ($s in $Skills) {
        if (Test-Path "$SKILLS_DIR\$s") {
            Log "$s: already installed"
        } else {
            if ($DryRun) { Log "Would install: $s" }
            else {
                python $MarketplaceScript install $s 2>$null
                if ($LASTEXITCODE -eq 0) { Log "$s: installed" } else { Warn "Could not auto-install $s" }
            }
        }
    }
}

# ────────────────────────────────────────────────────────
# Step 6: MCP Servers
# ────────────────────────────────────────────────────────
if (-not $SkipMcp) {
    Info "Step 6/7: Setting up MCP servers..."

    $Mgr = "$SKILLS_DIR\mcp-bridge\scripts\mcp_manager.py"
    
    if (Test-Path $Mgr) {
        # File system MCP
        if ($DryRun) { Log "Would add filesystem MCP" }
        else {
            python $Mgr add --name filesystem --transport stdio --command npx `
                --args '["-y","@modelcontextprotocol/server-filesystem","'$HOME_DIR'"]' `
                --description "Filesystem MCP server" 2>$null
            if ($LASTEXITCODE -eq 0) { Log "MCP: filesystem" } else { Warn "MCP filesystem failed" }
        }

        # LSP MCP
        $Lsp = "$SKILLS_DIR\mcp-bridge\scripts\lsp_mcp_server.py"
        if (Test-Path $Lsp) {
            if ($DryRun) { Log "Would add lsp MCP" }
            else {
                python $Mgr add --name lsp --transport stdio --command python --args '["'$Lsp'"]' `
                    --description "LSP MCP Server — Python code intelligence" 2>$null
                if ($LASTEXITCODE -eq 0) { Log "MCP: lsp" }
            }
        }
    }
}

# ────────────────────────────────────────────────────────
# Step 7: Scheduled Tasks (Windows Task Scheduler)
# ────────────────────────────────────────────────────────
Info "Step 7/7: Setting up scheduled tasks..."

if ($DryRun) {
    Log "Would create scheduled tasks (daily security, weekly update)"
} else {
    # Daily security audit — 09:00
    $Action = New-ScheduledTaskAction -Execute "powershell" -Argument "-Command `"openclaw message send --channel webchat --message 'Daily security audit reminder: run openclaw security audit'`""
    $Trigger = New-ScheduledTaskTrigger -Daily -At 09:00
    $TaskName = "OpenClaw-Daily-Security-Audit"
    try {
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Description "OpenClaw daily security audit" -Force 2>$null
        Log "Task: $TaskName (09:00 daily)"
    } catch { Warn "Could not create task: $TaskName" }

    # Weekly update check — Monday 10:00
    $Action2 = New-ScheduledTaskAction -Execute "powershell" -Argument "-Command `"openclaw update status`""
    $Trigger2 = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 10:00
    $TaskName2 = "OpenClaw-Weekly-Update-Check"
    try {
        Register-ScheduledTask -TaskName $TaskName2 -Action $Action2 -Trigger $Trigger2 -Description "OpenClaw weekly update check" -Force 2>$null
        Log "Task: $TaskName2 (Mon 10:00)"
    } catch { Warn "Could not create task: $TaskName2" }
}

# ────────────────────────────────────────────────────────
# Done
# ────────────────────────────────────────────────────────
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  OpenClaw Enhanced Deploy Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "  Platform:    Windows" -ForegroundColor Cyan
Write-Host "  Node.js:     $nv" -ForegroundColor Cyan
Write-Host "  Python:      $pv" -ForegroundColor Cyan
Write-Host "  OpenClaw:    $ocv" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Skills:     marketplace sync && marketplace list" -ForegroundColor Green
Write-Host "  MCP:        python mcp_manager.py list" -ForegroundColor Green
Write-Host ""
Write-Host "  Registry:   $REGISTRY_URL" -ForegroundColor Cyan
Write-Host ""
