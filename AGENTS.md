# Agent instructions

## Cursor Cloud specific instructions

### Services

| Service | Local | Production (Firebase) |
|---------|-------|-------------------------|
| API | `make run` / `make demo` :8080 | Cloud Run `ssh-monitor-api` |
| UI | same origin | Firebase Hosting |
| Data | YAML + SQLite | Firestore |

### Commands

```bash
make install-dev
make test
make demo                    # STORAGE_BACKEND=file
make build-hosting           # copy static → hosting/public
bash scripts/firebase-deploy.sh   # needs gcloud + firebase CLI + project
```

### Environment

- Local: `STORAGE_BACKEND=file` (default)
- Production: `STORAGE_BACKEND=firestore`, `FIREBASE_AUTH_REQUIRED=true`
- SSH key on Cloud Run: Secret `ssh-monitor-key` → env `SSH_PRIVATE_KEY`

See `docs/firebase-deploy.md` for full deployment steps.
