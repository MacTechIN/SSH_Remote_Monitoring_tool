# Agent instructions

## Cursor Cloud specific instructions

This repository is currently a **greenfield stub**: the only tracked file is `README.md` (`# SSH_Remote_Monitoring_tool`). There is no application source, lockfiles, Docker config, tests, or lint configuration yet.

### Services

| Service | Status | Notes |
|---------|--------|--------|
| Application / API / UI | Not in repo | Nothing to start until implementation is committed |
| Database | Not in repo | — |
| SSH targets (external) | Runtime dependency | Future E2E flows will need reachable SSH hosts and credentials supplied via secrets |

When application code lands, re-read `README.md`, any `docker-compose` files, and package manifests, then update this section with real start commands and ports.

### VM toolchain (verified on Cloud Agent VMs)

- **Git**: available; repo root is `/workspace`
- **OpenSSH client**: `ssh` on PATH (use for future monitoring flows)
- **Python**: 3.12.x (`python3`)
- **Node.js**: v22.x via nvm (`node`, `npm`)
- **Docker**: not installed on the default Cloud Agent image; add only if the project later requires it

### Lint / test / build / run

No project scripts exist yet. After dependencies are added:

- Prefer commands documented in `README.md` or `package.json` / `Makefile` / `pyproject.toml` scripts.
- Do **not** assume Docker is available unless installation is documented here.

### Update script behavior

The VM startup update script is a no-op (`true`) because there are no installable project dependencies. Once lockfiles exist, change the update script to the appropriate install command (for example `npm ci`, `pip install -r requirements.txt`, or `uv sync`).
