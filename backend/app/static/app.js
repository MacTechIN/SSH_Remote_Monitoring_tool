const grid = document.getElementById("hosts-grid");
const emptyState = document.getElementById("empty-state");
const statusBar = document.getElementById("status-bar");
const refreshBtn = document.getElementById("refresh-btn");
const demoBadge = document.getElementById("demo-badge");

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

function renderCard(host, metrics) {
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
    </div>
    ${metrics?.error ? `<p class="error-text">${metrics.error}</p>` : ""}
  `;
  return card;
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
      statusBar.textContent = "호스트 설정이 필요합니다.";
      return;
    }

    emptyState.classList.add("hidden");
    hosts.forEach((host) => {
      grid.appendChild(renderCard(host, metricsById[host.id]));
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
loadDashboard();
setInterval(loadDashboard, 30000);
