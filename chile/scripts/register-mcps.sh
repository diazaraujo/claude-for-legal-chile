#!/usr/bin/env bash
# Registers all chile-legal MCPs in Claude Code
set -e
SCRIPT_DIR="/Volumes/SSD ADA/claude-for-legal-chile/chile/scripts"

claude mcp remove banco-central 2>/dev/null || true
claude mcp add banco-central -- "$SCRIPT_DIR/mcp-banco-central/.venv/bin/mcp-banco-central"
claude mcp remove bcn-tramitacion 2>/dev/null || true
claude mcp add bcn-tramitacion -- "$SCRIPT_DIR/mcp-bcn-tramitacion/.venv/bin/mcp-bcn-tramitacion"
claude mcp remove cgr-dictamenes 2>/dev/null || true
claude mcp add cgr-dictamenes -- "$SCRIPT_DIR/mcp-cgr-dictamenes/.venv/bin/mcp-cgr-dictamenes"
claude mcp remove cmf 2>/dev/null || true
claude mcp add cmf -- "$SCRIPT_DIR/mcp-cmf/.venv/bin/mcp-cmf"
claude mcp remove corpus-search 2>/dev/null || true
claude mcp add corpus-search -- "$SCRIPT_DIR/mcp-corpus-search/.venv/bin/mcp-corpus-search"
claude mcp remove diario-oficial 2>/dev/null || true
claude mcp add diario-oficial -- "$SCRIPT_DIR/mcp-diario-oficial/.venv/bin/mcp-diario-oficial"
claude mcp remove dt-dictamenes 2>/dev/null || true
claude mcp add dt-dictamenes -- "$SCRIPT_DIR/mcp-dt-dictamenes/.venv/bin/mcp-dt-dictamenes"
claude mcp remove fne 2>/dev/null || true
claude mcp add fne -- "$SCRIPT_DIR/mcp-fne/.venv/bin/mcp-fne"
claude mcp remove pjud 2>/dev/null || true
claude mcp add pjud -- "$SCRIPT_DIR/mcp-pjud/.venv/bin/mcp-pjud"
claude mcp remove sernac 2>/dev/null || true
claude mcp add sernac -- "$SCRIPT_DIR/mcp-sernac/.venv/bin/mcp-sernac"
claude mcp remove sii-juris 2>/dev/null || true
claude mcp add sii-juris -- "$SCRIPT_DIR/mcp-sii-juris/.venv/bin/mcp-sii-juris"
claude mcp remove tc-fallos 2>/dev/null || true
claude mcp add tc-fallos -- "$SCRIPT_DIR/mcp-tc-fallos/.venv/bin/mcp-tc-fallos"
claude mcp remove tdlc 2>/dev/null || true
claude mcp add tdlc -- "$SCRIPT_DIR/mcp-tdlc/.venv/bin/mcp-tdlc"
claude mcp remove bcn-cli 2>/dev/null || true
claude mcp add bcn-cli -- "$SCRIPT_DIR/mcp/.venv/bin/mcp-bcn-cli"
