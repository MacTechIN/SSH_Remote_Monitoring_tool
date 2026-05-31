# Agent instructions

## Cursor Cloud specific instructions

### Services

| Service | Required | Start | Port |
|---------|----------|-------|------|
| FastAPI (uvicorn) | Yes | `make demo` or `make run` | 8080 |

`make demo` sets `DEMO_MODE=true` and does not require SSH targets. For real SSH checks, configure `config/hosts.yaml` and keys, then `make run`.

### Commands

```bash
make install-dev   # venv + deps (run once per fresh VM)
make lint
make test
make demo          # background-friendly: PYTHONPATH=. DEMO_MODE=true uvicorn ...
```

Uvicorn does not hot-reload dependency installs; after `pip install`, restart the server.

### Non-obvious notes

- `config/hosts.yaml` is gitignored; example is `config/hosts.example.yaml`.
- Committed `config/hosts.yaml` in dev branches may exist for local demo; production should use secrets and real host config.
- No Docker in the default Cloud Agent image unless installed separately.
