#!/usr/bin/env bash
# Shared paths for ModelRouter scripts.

if [[ -z "${MODELROUTER_ROOT:-}" ]]; then
  MODELROUTER_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

# Project-local venv (fast on local disk; override with MODELROUTER_VENV)
modelrouter_venv() {
  echo "${MODELROUTER_VENV:-$MODELROUTER_ROOT/.venv}"
}

modelrouter_activate() {
  local venv
  venv="$(modelrouter_venv)"
  if [[ ! -x "$venv/bin/python" ]]; then
    echo "[modelrouter] Virtualenv missing at $venv — run: make install" >&2
    return 1
  fi
  # shellcheck disable=SC1091
  source "$venv/bin/activate"
  export PYTHONPATH="${MODELROUTER_ROOT}:${PYTHONPATH:-}"
}

modelrouter_install_python_deps() {
  local venv
  venv="$(modelrouter_venv)"

  mkdir -p "$(dirname "$venv")"

  if command -v uv &>/dev/null; then
    echo "[modelrouter] Installing with uv → $venv"
    uv venv "$venv" --python python3
    uv pip install --python "$venv/bin/python" -r "$MODELROUTER_ROOT/requirements.txt"
    return 0
  fi

  echo "[modelrouter] Installing with pip → $venv"
  if [[ ! -x "$venv/bin/python" ]]; then
    python3 -m venv "$venv"
  fi
  "$venv/bin/pip" install --upgrade pip
  PIP_PROGRESS_BAR=on "$venv/bin/pip" install -r "$MODELROUTER_ROOT/requirements.txt"
}
