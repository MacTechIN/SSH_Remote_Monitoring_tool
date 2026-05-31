#!/usr/bin/env bash
# Ubuntu 서버에 SSH Remote Monitoring 설치
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

INSTALL_SYSTEMD=false
APP_USER="${SUDO_USER:-$USER}"
APP_HOME="$(eval echo "~${APP_USER}")"
APP_DIR="${APP_DIR:-$ROOT}"

for arg in "$@"; do
  case "$arg" in
    --systemd) INSTALL_SYSTEMD=true ;;
    -h|--help)
      echo "Usage: bash scripts/install-ubuntu-server.sh [--systemd]"
      exit 0
      ;;
  esac
done

echo "==> Install system packages"
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq git python3 python3-venv python3-pip openssh-client
fi

echo "==> Python virtualenv"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

echo "==> Config"
if [[ ! -f "$APP_DIR/config/hosts.yaml" ]]; then
  cp "$APP_DIR/config/hosts.example.yaml" "$APP_DIR/config/hosts.yaml"
fi
mkdir -p "$APP_DIR/data"

if [[ ! -f "$APP_DIR/.env" ]]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "# Ubuntu 서버: DEMO_MODE=false, SSH_PRIVATE_KEY_PATH 설정" >> "$APP_DIR/.env"
fi

echo "==> SSH key hint"
KEY_PATH="$APP_HOME/.ssh/id_ed25519_monitor"
if [[ ! -f "$KEY_PATH" ]]; then
  echo "  키가 없으면: ssh-keygen -t ed25519 -N \"\" -f $KEY_PATH"
fi

if [[ "$INSTALL_SYSTEMD" == "true" ]]; then
  echo "==> Install systemd unit"
  SERVICE_FILE="/etc/systemd/system/ssh-monitor.service"
  sed \
    -e "s|User=ubuntu|User=${APP_USER}|g" \
    -e "s|Group=ubuntu|Group=${APP_USER}|g" \
    -e "s|/home/ubuntu|${APP_HOME}|g" \
    -e "s|SSH_Remote_Monitoring_tool|$(basename "$APP_DIR")|g" \
    -e "s|WorkingDirectory=.*|WorkingDirectory=${APP_DIR}|g" \
    -e "s|Environment=PYTHONPATH=.*|Environment=PYTHONPATH=${APP_DIR}|g" \
    -e "s|Environment=HOSTS_FILE=.*|Environment=HOSTS_FILE=${APP_DIR}/config/hosts.yaml|g" \
    -e "s|ExecStart=.*|ExecStart=${APP_DIR}/.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8080|g" \
    "$ROOT/deploy/systemd/ssh-monitor.service" | sudo tee "$SERVICE_FILE" >/dev/null
  sudo systemctl daemon-reload
  echo "  sudo systemctl enable --now ssh-monitor"
fi

echo ""
echo "Done. Test run:"
echo "  cd $APP_DIR"
echo "  export PYTHONPATH=. DEMO_MODE=false SSH_PRIVATE_KEY_PATH=$KEY_PATH"
echo "  .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8080"
