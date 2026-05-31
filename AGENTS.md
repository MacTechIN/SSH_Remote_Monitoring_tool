# Agent instructions

## Cursor Cloud specific instructions

### Services

| Service | Required | Start | Port |
|---------|----------|-------|------|
| FastAPI (uvicorn) | Yes | `make demo` or `make run` | 8080 |
| sshd (integration only) | Optional | `make setup-ssh` | 22 |

`make demo` sets `DEMO_MODE=true` (no SSH required). For real SSH: `config/hosts.yaml` + keys, then `make run`.

### Commands

```bash
make install-dev
make lint
make test                 # unit tests only
make test-integration     # local sshd + real SSH collect
make demo
```

Cloud Agent VMs may need `sudo apt install python3.12-venv` before `make install-dev`.

### Non-obvious notes

- Hosts are persisted to `HOSTS_FILE` (default `config/hosts.yaml`). No automatic merge with `hosts.example.yaml`.
- Metrics history uses SQLite at `data/metrics.db` (`METRICS_DB_PATH`). Created on app startup / first record.
- `config/hosts.yaml` is gitignored; copy from `config/hosts.example.yaml` for local dev.
- Host CRUD: `POST/PUT/DELETE /api/hosts`, history: `GET /api/hosts/{id}/history`.
