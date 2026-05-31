const grid = document.getElementById("hosts-grid");
const emptyState = document.getElementById("empty-state");
const statusBar = document.getElementById("status-bar");
const refreshBtn = document.getElementById("refresh-btn");
const addHostBtn = document.getElementById("add-host-btn");
const demoBadge = document.getElementById("demo-badge");
const hostDialog = document.getElementById("host-dialog");
const hostForm = document.getElementById("host-form");
const dialogTitle = document.getElementById("dialog-title");
const dialogCancel = document.getElementById("dialog-cancel");
const fieldId = document.getElementById("field-id");

let editingHostId = null;

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(1)} ${units[unit]}`;
}

function statusLabel(status) {
  const labels = { online: "온라인", offline: "오프라인", error: "오류" };
  return labels[status] || status;
}

function renderHistory(history) {
  if (!history?.length) {
    return '<p class="history-empty">히스토리 없음 (메트릭 조회 후 저장됩니다)</p>';
  }
  const items = history
    .slice(0, 8)
    .map((item) => {
      const time = new Date(item.checked_at).toLocaleTimeString();
      const mem = item.memory?.used_percent;
      return `<span class="history-dot ${item.status}" title="${time} · mem ${mem ?? "?"}%"></span>`;
    })
    .join("");
  return `<div class="history-row">${items}</div>`;
}

function renderCard(host, metrics, history) {
  const card = document.createElement("article");
  card.className = "card";

  const mem = metrics?.memory;
  const disk = metrics?.disk;
  const status = metrics?.status || "offline";

  card.innerHTML = `
    <div class="card-header">
      <div>
        <h2>${host.name}</h2>
        <div class="host-meta">${host.username}@${host.hostname}:${host.port}</div>
      </div>
      <span class="status-pill ${status}">${statusLabel(status)}</span>
    </div>
    <div class="metrics">
      <div class="metric-row"><span>업타임</span><span>${metrics?.uptime || "—"}</span></div>
      <div class="metric-row">
        <span>로드 (1/5/15)</span>
        <span>${[metrics?.load_1, metrics?.load_5, metrics?.load_15].map((v) => v ?? "—").join(" / ")}</span>
      </div>
      <div>
        <div class="metric-row">
          <span>메모리</span>
          <span>${mem ? `${mem.used_mb} / ${mem.total_mb} MB (${mem.used_percent}%)` : "—"}</span>
        </div>
        ${mem ? `<div class="bar"><span style="width:${Math.min(mem.used_percent, 100)}%"></span></div>` : ""}
      </div>
      <div>
        <div class="metric-row">
          <span>디스크 (${disk?.mount || "/"})</span>
          <span>${disk ? `${formatBytes(disk.used_bytes)} / ${formatBytes(disk.total_bytes)} (${disk.used_percent}%)` : "—"}</span>
        </div>
        ${disk ? `<div class="bar"><span style="width:${Math.min(disk.used_percent, 100)}%"></span></div>` : ""}
      </div>
      <div class="metric-row"><span>최근 상태</span></div>
      ${renderHistory(history)}
    </div>
    ${metrics?.error ? `<p class="error-text">${metrics.error}</p>` : ""}
    <div class="card-actions">
      <button type="button" data-action="edit" data-id="${host.id}">수정</button>
      <button type="button" data-action="delete" data-id="${host.id}" class="btn-danger">삭제</button>
    </div>
  `;
  return card;
}

async function fetchHistory(hostId) {
  const response = await fetch(`/api/hosts/${hostId}/history?limit=12`);
  if (!response.ok) return [];
  return response.json();
}

function openDialog(host = null) {
  editingHostId = host?.id ?? null;
  dialogTitle.textContent = host ? "호스트 수정" : "호스트 추가";
  fieldId.value = host?.id ?? "";
  fieldId.disabled = Boolean(host);
  document.getElementById("field-name").value = host?.name ?? "";
  document.getElementById("field-hostname").value = host?.hostname ?? "";
  document.getElementById("field-port").value = host?.port ?? 22;
  document.getElementById("field-username").value = host?.username ?? "ubuntu";
  document.getElementById("field-key").value = host?.private_key_path ?? "";
  hostDialog.showModal();
}

async function submitHostForm(event) {
  event.preventDefault();
  const payload = {
    name: document.getElementById("field-name").value.trim(),
    hostname: document.getElementById("field-hostname").value.trim(),
    port: Number(document.getElementById("field-port").value),
    username: document.getElementById("field-username").value.trim(),
    private_key_path: document.getElementById("field-key").value.trim() || null,
  };
  const idValue = fieldId.value.trim();
  if (!editingHostId && idValue) {
    payload.id = idValue;
  }

  const url = editingHostId ? `/api/hosts/${editingHostId}` : "/api/hosts";
  const method = editingHostId ? "PUT" : "POST";
  const response = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    alert(err.detail || "저장에 실패했습니다.");
    return;
  }
  hostDialog.close();
  await loadDashboard();
}

async function deleteHost(hostId) {
  if (!confirm(`호스트 '${hostId}'를 삭제할까요?`)) return;
  const response = await fetch(`/api/hosts/${hostId}`, { method: "DELETE" });
  if (!response.ok) {
    alert("삭제에 실패했습니다.");
    return;
  }
  await loadDashboard();
}

async function loadDashboard() {
  refreshBtn.disabled = true;
  statusBar.textContent = "데이터를 불러오는 중…";

  try {
    const [healthRes, hostsRes, metricsRes] = await Promise.all([
      fetch("/api/health"),
      fetch("/api/hosts"),
      fetch("/api/metrics"),
    ]);

    if (!hostsRes.ok || !metricsRes.ok) {
      throw new Error("API 요청 실패");
    }

    const health = await healthRes.json();
    const hosts = await hostsRes.json();
    const metricsList = await metricsRes.json();
    const metricsById = Object.fromEntries(metricsList.map((m) => [m.host_id, m]));

    demoBadge.classList.toggle("hidden", health.demo_mode !== "true");

    grid.innerHTML = "";
    if (hosts.length === 0) {
      emptyState.classList.remove("hidden");
      statusBar.textContent = "호스트를 추가해 모니터링을 시작하세요.";
      return;
    }

    emptyState.classList.add("hidden");
    const histories = await Promise.all(hosts.map((host) => fetchHistory(host.id)));
    hosts.forEach((host, index) => {
      grid.appendChild(renderCard(host, metricsById[host.id], histories[index]));
    });

    grid.querySelectorAll("[data-action=edit]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const host = hosts.find((item) => item.id === btn.dataset.id);
        openDialog(host);
      });
    });
    grid.querySelectorAll("[data-action=delete]").forEach((btn) => {
      btn.addEventListener("click", () => deleteHost(btn.dataset.id));
    });

    const online = metricsList.filter((m) => m.status === "online").length;
    statusBar.textContent = `${hosts.length}대 중 ${online}대 온라인 · 마지막 갱신 ${new Date().toLocaleTimeString()}`;
  } catch (err) {
    statusBar.textContent = `오류: ${err.message}`;
  } finally {
    refreshBtn.disabled = false;
  }
}

refreshBtn.addEventListener("click", loadDashboard);
addHostBtn.addEventListener("click", () => openDialog());
dialogCancel.addEventListener("click", () => hostDialog.close());
hostForm.addEventListener("submit", submitHostForm);
loadDashboard();
setInterval(loadDashboard, 30000);
