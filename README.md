# SSH Remote Monitoring Tool

Linux 서버를 SSH로 연결해 업타임, 로드, 메모리, 디스크 사용량을 웹 대시보드에서 확인하는 도구입니다.

## 기능

- `config/hosts.yaml`에 여러 호스트 등록
- SSH로 원격 셸 스크립트 실행 후 메트릭 파싱
- REST API + 웹 대시보드 (`/`)
- `DEMO_MODE=true`로 SSH 없이 UI/API 개발·데모 가능

## 요구 사항

- Python 3.12+
- 모니터링 대상: Linux, SSH 접근 가능, `free`/`df`/`/proc/loadavg` 사용 가능

## 빠른 시작

```bash
make install-dev
cp config/hosts.example.yaml config/hosts.yaml   # 이미 있으면 생략
make demo   # DEMO_MODE, http://localhost:8080
```

브라우저에서 http://localhost:8080 을 엽니다.

### 실제 SSH 모니터링

1. `config/hosts.yaml`에 호스트 정보 입력
2. SSH 키 설정 (`~/.ssh/id_ed25519` 또는 `SSH_PRIVATE_KEY_PATH`)
3. 데모 모드 없이 실행:

```bash
make run
```


## 호스트 관리 API

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/hosts` | 호스트 등록 |
| PUT | `/api/hosts/{id}` | 호스트 수정 |
| DELETE | `/api/hosts/{id}` | 호스트 삭제 |
| GET | `/api/hosts/{id}/history` | 메트릭 히스토리 (SQLite) |

대시보드에서 **호스트 추가 / 수정 / 삭제** UI를 제공합니다.

## SSH 통합 테스트

```bash
make test-integration
```

로컬 `sshd`와 키 인증을 `scripts/setup-local-ssh.sh`로 구성한 뒤 실제 SSH 수집을 검증합니다.

## API

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/health` | 헬스 체크 |
| GET | `/api/hosts` | 등록된 호스트 목록 |
| GET | `/api/metrics` | 전체 호스트 메트릭 |
| GET | `/api/hosts/{id}/metrics` | 단일 호스트 메트릭 |

## 환경 변수

| 변수 | 설명 |
|------|------|
| `HOSTS_FILE` | 호스트 YAML 경로 (기본: `config/hosts.yaml`) |
| `SSH_PRIVATE_KEY_PATH` | 기본 SSH 개인키 경로 |
| `SSH_CONNECT_TIMEOUT` | 연결 타임아웃(초), 기본 10 |
| `SSH_COMMAND_TIMEOUT` | 명령 타임아웃(초), 기본 15 |
| `DEMO_MODE` | `true`면 데모 메트릭 반환 |

## 개발

```bash
make lint
make test
make run
```

## 라이선스

MIT (프로젝트 정책에 맞게 조정 가능)


## Firebase 프로덕션

실제 서비스 배포는 **Firebase Hosting + Firestore + Cloud Run** 구성을 사용합니다.

```bash
npm install
cp .firebaserc.example .firebaserc   # 프로젝트 ID 입력
# hosting/public/firebase-config.local.js 작성 (docs 참고)
export FIREBASE_PROJECT_ID=your-project-id
bash scripts/firebase-deploy.sh
```

자세한 절차: [docs/firebase-deploy.md](docs/firebase-deploy.md)

| 환경 변수 | 프로덕션 |
|-----------|----------|
| `STORAGE_BACKEND` | `firestore` |
| `FIREBASE_AUTH_REQUIRED` | `true` |
| `SSH_PRIVATE_KEY` | Secret Manager (권장) |

로컬 개발은 기본값 `STORAGE_BACKEND=file` (YAML + SQLite)을 그대로 사용합니다.


## Ubuntu 서버에 직접 설치 (SSH)

VPS/사내 Ubuntu에 앱을 올려 운영하는 방법:

- [docs/ubuntu-server-deploy.md](docs/ubuntu-server-deploy.md)

```bash
# Ubuntu 서버에서
git clone https://github.com/MacTechIN/SSH_Remote_Monitoring_tool.git
cd SSH_Remote_Monitoring_tool
bash scripts/install-ubuntu-server.sh --systemd
```
