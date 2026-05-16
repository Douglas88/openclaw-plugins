#!/usr/bin/env bash
# =============================================================================
# OpenClaw Enhanced Deploy — macOS / Ubuntu One-Click Setup
# =============================================================================
# Usage: bash install.sh [--skip-node] [--skip-skills] [--skip-mcp] [--dry-run]
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn() { echo -e "${YELLOW}[!]${NC} $*"; }
err()  { echo -e "${RED}[✗]${NC} $*"; exit 1; }
info() { echo -e "${CYAN}[•]${NC} $*"; }

DRY_RUN=false; SKIP_NODE=false; SKIP_SKILLS=false; SKIP_MCP=false
for arg in "$@"; do
  case "$arg" in --dry-run) DRY_RUN=true ;; --skip-node) SKIP_NODE=true ;; --skip-skills) SKIP_SKILLS=true ;; --skip-mcp) SKIP_MCP=true ;; esac
done
$DRY_RUN && log "DRY RUN MODE — no changes will be made"

OS="$(uname -s)"
if [[ "$OS" == "Darwin" ]]; then PLATFORM="macOS"
elif [[ "$OS" == "Linux" ]]; then PLATFORM="Ubuntu"
else err "Unsupported OS: $OS"; fi
info "Detected: $PLATFORM"

# ────────────────────────────────────────────────────────
# Step 1: Prerequisites
# ────────────────────────────────────────────────────────
info "Step 1/7: Checking prerequisites..."

if ! $SKIP_NODE; then
  if ! command -v node &>/dev/null; then
    warn "Node.js not found. Installing via nvm..."
    if $DRY_RUN; then log "Would install nvm + Node 24"; else
      curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
      export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
      nvm install 24 && nvm use 24
    fi
  fi
  NODE_VER=$(node --version 2>/dev/null || echo "?")
  log "Node.js $NODE_VER"
fi

if ! command -v python3 &>/dev/null; then
  warn "Python3 not found."
  if [[ "$PLATFORM" == "macOS" ]]; then
    $DRY_RUN && log "Would: brew install python3" || brew install python3
  else
    $DRY_RUN && log "Would: sudo apt install python3" || sudo apt-get install -y python3
  fi
fi
PY_VER=$(python3 --version 2>/dev/null || echo "?")
log "Python $PY_VER"

# ────────────────────────────────────────────────────────
# Step 2: Install OpenClaw
# ────────────────────────────────────────────────────────
info "Step 2/7: Installing OpenClaw..."

if ! command -v openclaw &>/dev/null; then
  $DRY_RUN && log "Would: npm install -g openclaw" || npm install -g openclaw@latest
fi
OPENCLAW_VER=$(openclaw --version 2>/dev/null || echo "?")
log "OpenClaw $OPENCLAW_VER"

# Start gateway if not running
if ! systemctl --user is-active openclaw-gateway &>/dev/null 2>&1 && ! pgrep -f "openclaw gateway" &>/dev/null; then
  $DRY_RUN && log "Would: openclaw gateway start" || openclaw gateway start
fi

# ────────────────────────────────────────────────────────
# Step 3: Apply Enhanced Configuration
# ────────────────────────────────────────────────────────
info "Step 3/7: Applying enhanced configuration..."

EXEC_APPROVALS="$HOME/.openclaw/exec-approvals.json"
OPENCLAW_JSON="$HOME/.openclaw/openclaw.json"

# exec-approvals.json
if [ -f "$EXEC_APPROVALS" ]; then
  $DRY_RUN && log "Would patch exec-approvals.json" || python3 -c "
import json; path='$EXEC_APPROVALS'
c=json.load(open(path)); c['defaults']={'security':'full','ask':'off','askFallback':'full'}
json.dump(c,open(path,'w'),indent=2)
"
  log "exec-approvals.json: security=full, ask=off"
fi

# openclaw.json — add exec tools config
if [ -f "$OPENCLAW_JSON" ]; then
  $DRY_RUN && log "Would patch openclaw.json" || python3 -c "
import json; path='$OPENCLAW_JSON'
c=json.load(open(path))
c.setdefault('tools',{})['exec']={'security':'full','strictInlineEval':False}
json.dump(c,open(path,'w'),indent=2)
"
  log "openclaw.json: tools.exec.security=full"
fi

# ────────────────────────────────────────────────────────
# Step 4: HEARTBEAT Monitoring
# ────────────────────────────────────────────────────────
info "Step 4/7: Configuring HEARTBEAT monitoring..."

HEARTBEAT_MD="$HOME/.openclaw/workspace/HEARTBEAT.md"
$DRY_RUN && log "Would write HEARTBEAT.md" || cat > "$HEARTBEAT_MD" << 'HEARTBEAT_EOF'
# Heartbeat Periodic Check Checklist

## High Priority (every heartbeat)
- [ ] System health: openclaw status normal?
- [ ] Gateway: systemctl --user is-active openclaw-gateway (Linux) / pgrep openclaw (macOS)

## Medium Priority (every 1-2 hours)
- [ ] Disk space: df -h / (alert at 80%)
- [ ] Memory: free -h (Linux) / vm_stat (macOS) (alert at 90%)

## Low Priority (every 12-24 hours)
- [ ] Security audit: openclaw security audit
- [ ] Update check: openclaw update status
- [ ] Error logs: check journalctl / system log

## Alert Thresholds
- CPU > 80% for 5min → warning
- Disk < 10GB → critical
HEARTBEAT_EOF
log "HEARTBEAT.md configured"

# ────────────────────────────────────────────────────────
# Step 5: Install Community Skills
# ────────────────────────────────────────────────────────
if ! $SKIP_SKILLS; then
  info "Step 5/7: Installing community Skills via marketplace..."

  MARKETPLACE_DIR="$HOME/.openclaw/plugin-skills/plugin-marketplace"
  MARKETPLACE_SCRIPT="$MARKETPLACE_DIR/scripts/marketplace.py"

  if [ ! -f "$MARKETPLACE_SCRIPT" ]; then
    info "Bootstrapping marketplace..."
    $DRY_RUN && log "Would: mkdir -p & download marketplace" || {
      mkdir -p "$MARKETPLACE_DIR/scripts"
      curl -sL "https://raw.githubusercontent.com/Douglas88/openclaw-plugins/main/plugin-marketplace/scripts/marketplace.py" \
        -o "$MARKETPLACE_SCRIPT"
      chmod +x "$MARKETPLACE_SCRIPT"
    }
  fi

  if [ -f "$MARKETPLACE_SCRIPT" ]; then
    $DRY_RUN && log "Would: marketplace sync && install all" || {
      python3 "$MARKETPLACE_SCRIPT" sync 2>/dev/null || true
    }
    log "Marketplace synced from global registry"

    # Install key skills
    for skill in code-review test-generator doc-generator session-tools mcp-bridge ide-panel; do
      if [ ! -d "$HOME/.openclaw/plugin-skills/$skill" ]; then
        $DRY_RUN && log "Would install: $skill" || python3 "$MARKETPLACE_SCRIPT" install "$skill" 2>/dev/null || warn "Could not auto-install $skill"
      else
        log "$skill: already installed"
      fi
    done
  fi
fi

# ────────────────────────────────────────────────────────
# Step 6: Setup MCP Servers
# ────────────────────────────────────────────────────────
if ! $SKIP_MCP; then
  info "Step 6/7: Setting up MCP servers..."

  MCP_MANAGER="$HOME/.openclaw/plugin-skills/mcp-bridge/scripts/mcp_manager.py"
  
  if [ -f "$MCP_MANAGER" ]; then
    # Filesystem MCP
    $DRY_RUN && log "Would add filesystem MCP" || python3 "$MCP_MANAGER" add \
      --name filesystem --transport stdio --command npx \
      --args '["-y","@modelcontextprotocol/server-filesystem","'"$HOME"'"]' \
      --description "Filesystem MCP server" 2>/dev/null && log "MCP: filesystem" || true

    # SQLite MCP (self-hosted)
    SQLITE_SERVER="$HOME/.openclaw/plugin-skills/mcp-bridge/scripts/sqlite_mcp_server.py"
    if [ -f "$SQLITE_SERVER" ]; then
      $DRY_RUN && log "Would add sqlite MCP" || python3 "$MCP_MANAGER" add \
        --name sqlite --transport stdio --command python3 \
        --args '["'"$SQLITE_SERVER"'","'"$HOME"'/.openclaw/analytics.db"]' \
        --description "SQLite Analytics MCP" 2>/dev/null && log "MCP: sqlite" || true
    fi

    # LSP MCP (Python code intelligence)
    LSP_SERVER="$HOME/.openclaw/plugin-skills/mcp-bridge/scripts/lsp_mcp_server.py"
    if [ -f "$LSP_SERVER" ]; then
      $DRY_RUN && log "Would add lsp MCP" || python3 "$MCP_MANAGER" add \
        --name lsp --transport stdio --command python3 \
        --args '["'"$LSP_SERVER"'"]' \
        --description "LSP MCP Server — Python code intelligence" 2>/dev/null && log "MCP: lsp" || true
    fi
  fi
fi

# ────────────────────────────────────────────────────────
# Step 7: Cron Jobs (Linux only)
# ────────────────────────────────────────────────────────
info "Step 7/7: Setting up automated tasks..."

if [[ "$PLATFORM" == "Ubuntu" ]]; then
  # Daily security audit
  $DRY_RUN && log "Would add cron: daily-security" || openclaw cron add \
    --name "healthcheck:daily-security-audit" \
    --schedule '{"kind":"cron","expr":"0 9 * * *","tz":"Asia/Shanghai"}' \
    --payload '{"kind":"systemEvent","text":"Daily security audit: run openclaw security audit, check disk/memory/logs"}' \
    --sessionTarget main --enabled true 2>/dev/null && log "cron: daily-security (09:00)" || true

  # Weekly update check
  $DRY_RUN && log "Would add cron: weekly-update" || openclaw cron add \
    --name "healthcheck:weekly-update-check" \
    --schedule '{"kind":"cron","expr":"0 10 * * 1","tz":"Asia/Shanghai"}' \
    --payload '{"kind":"systemEvent","text":"Weekly update check: openclaw update status"}' \
    --sessionTarget main --enabled true 2>/dev/null && log "cron: weekly-update (Mon 10:00)" || true

  # Hourly config backup
  $DRY_RUN && log "Would add cron: config-backup" || openclaw cron add \
    --name "backup:config-hourly" \
    --schedule '{"kind":"cron","expr":"0 * * * *","tz":"Asia/Shanghai"}' \
    --payload '{"kind":"agentTurn","message":"Backup config files: cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-$(date +%Y%m%d-%H%M); keep last 24","timeoutSeconds":30}' \
    --sessionTarget isolated --enabled true 2>/dev/null && log "cron: config-backup (hourly)" || true
elif [[ "$PLATFORM" == "macOS" ]]; then
  warn "Cron not configured on macOS — use launchd or cron manually"
fi

# ────────────────────────────────────────────────────────
# Done
# ────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  OpenClaw Enhanced Deploy Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Platform:    ${CYAN}$PLATFORM${NC}"
echo -e "  Node.js:     ${CYAN}$NODE_VER${NC}"
echo -e "  Python:      ${CYAN}$PY_VER${NC}"
echo -e "  OpenClaw:    ${CYAN}$OPENCLAW_VER${NC}"
echo ""
echo -e "  Skills:      ${GREEN}marketplace sync && marketplace list${NC}"
echo -e "  MCP:         ${GREEN}python3 mcp_manager.py list${NC}"
echo -e "  Review:      ${GREEN}Just ask me to review code!${NC}"
echo ""
echo -e "  Plugin Registry: ${CYAN}https://douglas88.github.io/openclaw-plugins${NC}"
echo ""
