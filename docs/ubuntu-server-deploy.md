# Ubuntu 서버에 SSH로 설치·배포하기

모니터링 **앱 자체**를 Ubuntu 서버에 올리고, 그 서버에서 다른 Linux 호스트를 SSH로 감시하는 방법입니다.  
(Firebase Hosting 배포와 별개의 **자체 호스팅** 방식입니다.)

## 구성 개요

```
[브라우저] ──HTTP:8080──▶ [Ubuntu: 모니터링 앱 (FastAPI)]
                              │
                              └──SSH──▶ [감시 대상 서버 A, B, C ...]
```

| 역할 | 설명 |
|------|------|
| **모니터링 서버** | 이 문서대로 설치하는 Ubuntu (앱 실행) |
| **감시 대상** | SSH로 접속할 원격 Linux 서버들 |

---

## 1. 사전 준비

### 모니터링 서버 (Ubuntu 22.04 / 24.04 권장)

- Python 3.12+
- Git
- 방화벽에서 사용할 포트 개방 (예: `8080` 또는 `80`/`443`)

### 감시 대상 서버

- SSH 서버(`sshd`) 실행 중
- 모니터링 서버의 **공개키**가 `authorized_keys`에 등록되어 있거나, 키 파일 경로 지정 가능

---

## 2. 로컬 PC에서 Ubuntu 서버로 SSH 접속

```bash
ssh ubuntu@YOUR_SERVER_IP
# 또는
ssh -i ~/.ssh/your_key.pem ubuntu@YOUR_SERVER_IP
```

최초 접속 후 패키지 업데이트:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip openssh-client
```

---

## 3. 애플리케이션 설치 (서버에서)

### 3-1. 저장소 클론

```bash
cd ~
git clone https://github.com/MacTechIN/SSH_Remote_Monitoring_tool.git
cd SSH_Remote_Monitoring_tool
```

### 3-2. 자동 설치 스크립트 (권장)

```bash
bash scripts/install-ubuntu-server.sh
```

### 3-3. 수동 설치

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp config/hosts.example.yaml config/hosts.yaml
```

---

## 4. SSH 키 설정 (감시 대상 접속용)

모니터링 서버에서 키 생성:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519_monitor
```

감시 대상 서버에 공개키 등록 (대상 서버에서 또는 `ssh-copy-id`):

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_monitor.pub USER@TARGET_HOST
```

앱에서 사용할 키 경로 지정:

```bash
export SSH_PRIVATE_KEY_PATH=$HOME/.ssh/id_ed25519_monitor
```

또는 `.env` 파일:

```bash
cp .env.example .env
# .env 편집
# SSH_PRIVATE_KEY_PATH=/home/ubuntu/.ssh/id_ed25519_monitor
# DEMO_MODE=false
```

---

## 5. 감시 호스트 설정

`config/hosts.yaml` 예시:

```yaml
hosts:
  - id: web-01
    name: Web Server 1
    hostname: 10.0.1.10
    port: 22
    username: ubuntu
    # private_key_path: /home/ubuntu/.ssh/id_ed25519_monitor

  - id: db-01
    name: DB Server
    hostname: 10.0.1.20
    port: 22
    username: deploy
```

대시보드에서 **호스트 추가**로 등록해도 됩니다 (같은 파일에 저장).

---

## 6. 실행·확인

### 일회 실행 (테스트)

```bash
cd ~/SSH_Remote_Monitoring_tool
export PYTHONPATH=.
export DEMO_MODE=false
export SSH_PRIVATE_KEY_PATH=$HOME/.ssh/id_ed25519_monitor
.venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8080
```

브라우저: `http://YOUR_SERVER_IP:8080`

헬스 체크:

```bash
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/metrics
```

### systemd 서비스 (상시 운영)

```bash
sudo bash scripts/install-ubuntu-server.sh --systemd
sudo systemctl enable --now ssh-monitor
sudo systemctl status ssh-monitor
```

로그:

```bash
journalctl -u ssh-monitor -f
```

---

## 7. 방화벽

```bash
# UFW 예시
sudo ufw allow OpenSSH
sudo ufw allow 8080/tcp
sudo ufw enable
```

---

## 8. (선택) Nginx + HTTPS

80/443으로 서비스할 때:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

`/etc/nginx/sites-available/ssh-monitor` 예시:

```nginx
server {
    listen 80;
    server_name monitor.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ssh-monitor /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d monitor.example.com
```

---

## 9. 환경 변수 요약

| 변수 | Ubuntu 서버 권장값 |
|------|-------------------|
| `STORAGE_BACKEND` | `file` (기본) |
| `DEMO_MODE` | `false` |
| `SSH_PRIVATE_KEY_PATH` | 모니터링용 개인키 경로 |
| `HOSTS_FILE` | `config/hosts.yaml` |
| `HISTORY_ENABLED` | `true` |

---

## 10. 문제 해결

| 증상 | 확인 |
|------|------|
| 메트릭이 전부 오프라인 | `ssh -i 키 USER@HOST` 수동 접속 테스트 |
| 인증 실패 | 키 권한 `chmod 600`, `authorized_keys` |
| 대시보드만 되고 API 오류 | `DEMO_MODE=false` 인지, 방화벽 |
| Site Not Found (Firebase URL) | Firebase 미배포 → 이 문서는 **자체 Ubuntu 배포** |

---

## Firebase vs Ubuntu 자체 호스팅

| 방식 | URL 예 | 용도 |
|------|--------|------|
| Firebase | `https://ssh-analyzer.web.app` | 관리형, Firestore |
| Ubuntu 서버 | `http://서버IP:8080` | 사내/VPS, 파일 DB |

둘 다 사용할 수 있으나, **같은 인스턴스에 중복 설치할 필요는 없습니다.**
