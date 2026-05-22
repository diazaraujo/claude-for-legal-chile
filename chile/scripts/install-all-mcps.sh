#!/usr/bin/env bash
# Instala los 6 MCPs de Claude Legal Chile en venvs aislados
# y los registra en Claude Code.
#
# Uso:
#   bash chile/scripts/install-all-mcps.sh [--no-register]
#
# Requisitos: python3.11+

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGISTER=true

if [ "${1:-}" = "--no-register" ]; then
    REGISTER=false
fi

declare -a MCPS=(
    "mcp:bcn-leychile"
    "mcp-diario-oficial:diario-oficial"
    "mcp-sii-juris:sii-juris"
    "mcp-cgr-dictamenes:cgr-dictamenes"
    "mcp-tc-fallos:tc-fallos"
    "mcp-cmf:cmf"
    "mcp-dt-dictamenes:dt-dictamenes"
    "mcp-pjud:pjud"
)

echo "==> Instalando 7 MCPs en venvs aislados..."
for entry in "${MCPS[@]}"; do
    pkg_dir="${entry%%:*}"
    pkg_path="$SCRIPT_DIR/$pkg_dir"
    if [ ! -d "$pkg_path" ]; then
        echo "  [SKIP] $pkg_dir (no existe)"
        continue
    fi
    echo "  -> $pkg_dir"
    if [ ! -d "$pkg_path/.venv" ]; then
        python3.11 -m venv "$pkg_path/.venv"
    fi
    "$pkg_path/.venv/bin/pip" install -e "$pkg_path" --quiet
done

if [ "$REGISTER" = true ]; then
    echo ""
    echo "==> Registrando en Claude Code via 'claude mcp add'..."
    for entry in "${MCPS[@]}"; do
        pkg_dir="${entry%%:*}"
        mcp_name="${entry##*:}"
        bin_name="$(echo "$pkg_dir" | sed 's/^mcp$/mcp-bcn-leychile/')"
        # Para mcp/ (BCN), el binario se llama mcp-bcn-leychile
        if [ "$pkg_dir" = "mcp" ]; then
            bin_path="$SCRIPT_DIR/mcp/.venv/bin/mcp-bcn-leychile"
        else
            bin_path="$SCRIPT_DIR/$pkg_dir/.venv/bin/$pkg_dir"
        fi
        if [ ! -x "$bin_path" ]; then
            echo "  [SKIP] $mcp_name (binario no existe: $bin_path)"
            continue
        fi
        # Remove existing registration first
        claude mcp remove "$mcp_name" 2>/dev/null || true
        claude mcp add "$mcp_name" "$bin_path"
    done
fi

echo ""
echo "==> Done. MCPs registrados:"
claude mcp list 2>/dev/null | grep -E "bcn-leychile|diario-oficial|sii-juris|cgr-dictamenes|tc-fallos|cmf|pjud" || true
