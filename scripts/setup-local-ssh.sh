#!/usr/bin/env bash
# Configure local sshd + key auth for integration tests.
set -euo pipefail

if ! command -v sshd >/dev/null 2>&1; then
  sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq openssh-server
fi

mkdir -p "${HOME}/.ssh"
chmod 700 "${HOME}/.ssh"
if [[ ! -f "${HOME}/.ssh/id_ed25519" ]]; then
  ssh-keygen -t ed25519 -N "" -f "${HOME}/.ssh/id_ed25519"
fi
touch "${HOME}/.ssh/authorized_keys"
grep -qF "$(cat "${HOME}/.ssh/id_ed25519.pub")" "${HOME}/.ssh/authorized_keys" \
  || cat "${HOME}/.ssh/id_ed25519.pub" >> "${HOME}/.ssh/authorized_keys"
chmod 600 "${HOME}/.ssh/authorized_keys"

sudo service ssh start 2>/dev/null || sudo service sshd start 2>/dev/null || true

python3 - <<'PY'
import socket
import sys

sock = socket.socket()
sock.settimeout(2)
code = sock.connect_ex(("127.0.0.1", 22))
sock.close()
if code != 0:
    print("SSH is not listening on port 22", file=sys.stderr)
    sys.exit(1)
print("SSH is listening on port 22")
PY

echo "Local SSH ready for $(whoami)@127.0.0.1:22"
