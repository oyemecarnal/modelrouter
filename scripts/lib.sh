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

# Load MODELROUTER_* and provider keys from .env into the current shell.
modelrouter_load_env() {
  local env_file="${MODELROUTER_ROOT}/.env"
  [[ -f "$env_file" ]] || return 0
  set -a
  # shellcheck disable=SC1091
  source "$env_file"
  set +a
  [[ -z "${DATABASE_URL:-}" ]] && unset DATABASE_URL
  [[ -z "${DIRECT_URL:-}" ]] && unset DIRECT_URL
}

modelrouter_wait_healthy() {
  local tries="${1:-30}"
  local i
  for ((i = 1; i <= tries; i++)); do
    if MODELROUTER_ROOT="$MODELROUTER_ROOT" "$MODELROUTER_ROOT/scripts/healthcheck.sh" &>/dev/null; then
      return 0
    fi
    sleep 1
  done
  return 1
}

# Write pidfile from port listener (litellm), not the start.sh wrapper.
modelrouter_reconcile_pidfile() {
  local port="${MODELROUTER_PORT:-3000}"
  local pidfile="${MODELROUTER_ROOT}/.pids/modelrouter.pid"
  local listen_pid
  listen_pid="$(lsof -ti :"$port" 2>/dev/null | head -1 || true)"
  if [[ -n "$listen_pid" ]]; then
    mkdir -p "$(dirname "$pidfile")"
    echo "$listen_pid" > "$pidfile"
    return 0
  fi
  return 1
}

modelrouter_install_python_deps() {
  local venv
  venv="$(modelrouter_venv)"

  mkdir -p "$(dirname "$venv")"

  if [[ -d "$venv" && ! -x "$venv/bin/pip" ]]; then
    echo "[modelrouter] Removing incomplete venv at $venv (pip missing)"
    rm -rf "$venv"
  fi

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

# Active hosts config — optional gitignored overlay for operator-specific homelab values.
modelrouter_hosts_yaml() {
  local local="${MODELROUTER_ROOT}/config/hosts.local.yaml"
  if [[ -f "$local" ]]; then
    echo "$local"
  else
    echo "${MODELROUTER_ROOT}/config/hosts.yaml"
  fi
}

modelrouter_gateway_url() {
  if [[ -n "${MODELROUTER_MINI_URL:-}" ]]; then
    echo "$MODELROUTER_MINI_URL"
    return 0
  fi
  local url
  url="$(awk '/^gateway:/{f=1} f && /^  url:/{print $2; exit}' "$(modelrouter_hosts_yaml)" 2>/dev/null || true)"
  echo "${url:-http://gateway.local:3000}"
}

modelrouter_gateway_tailscale_url() {
  local url
  url="$(awk '/^gateway:/{f=1} f && /^  url_tailscale:/{print $2; exit}' "$(modelrouter_hosts_yaml)" 2>/dev/null || true)"
  echo "${url:-http://100.64.0.1:3000}"
}

modelrouter_mini_gateway_urls() {
  local port="${MODELROUTER_PORT:-3000}"
  if [[ -n "${MODELROUTER_MINI_URL:-}" ]]; then
    echo "$MODELROUTER_MINI_URL"
    return 0
  fi
  local f url ts alias
  f="$(modelrouter_hosts_yaml)"
  url="$(awk '/^gateway:/{f=1} f && /^  url:/{print $2; exit}' "$f" 2>/dev/null || true)"
  ts="$(awk '/^gateway:/{f=1} f && /^  url_tailscale:/{print $2; exit}' "$f" 2>/dev/null || true)"
  alias="$(awk '/^gateway:/{f=1} f && /^  url_ssh_alias:/{print $2; exit}' "$f" 2>/dev/null || true)"
  local -a candidates=()
  [[ -n "$url" ]] && candidates+=("$url")
  [[ -n "$ts" ]] && candidates+=("$ts")
  [[ -n "$alias" ]] && candidates+=("$alias")
  if [[ ${#candidates[@]} -eq 0 ]]; then
    candidates=("http://gateway.local:${port}")
  fi
  printf '%s\n' "${candidates[@]}"
}

modelrouter_remote_host() {
  if [[ -n "${MODELROUTER_REMOTE_HOST:-}" ]]; then
    echo "$MODELROUTER_REMOTE_HOST"
    return 0
  fi
  local f host
  f="$(modelrouter_hosts_yaml)"
  host="$(awk '
    /^  gateway-mini:$/ { in_host=1; next }
    in_host && /^  [a-zA-Z0-9_-]+:$/ { exit }
    in_host && /^    ssh:/ { print $2; exit }
  ' "$f" 2>/dev/null || true)"
  echo "${host:-gateway-mini}"
}

# PID listening on gateway port (litellm), not the start.sh wrapper.
modelrouter_port_listener_pid() {
  local port="${MODELROUTER_PORT:-3000}"
  lsof -ti :"$port" 2>/dev/null | head -1 || true
}

modelrouter_gateway_listening() {
  [[ -n "$(modelrouter_port_listener_pid)" ]]
}
