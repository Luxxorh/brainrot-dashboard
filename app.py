from flask import Flask, jsonify, render_template_string
import requests
from datetime import datetime
import time

app = Flask(__name__)

URL = "https://brainrotss.up.railway.app/brainrots"
MAX_PLAYERS = 8
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Cache-Control": "no-cache"
}

def fetch_servers():
    """
    Fetch servers from your external API and return a list of server info dictionaries.
    """
    server_cache = {}
    try:
        resp = requests.get(URL, headers=HEADERS, timeout=1)
        data = resp.json()
        for server in data:
            jobId = server.get("jobId")
            placeId = server.get("serverId")
            name = server.get("name")
            if jobId and placeId:
                server_cache[jobId] = {"name": name, "placeId": placeId}
    except Exception:
        pass
    return server_cache

def poll_live_players():
    """
    Poll Roblox for live players using the servers fetched from fetch_servers.
    Returns a list of dictionaries with timestamp, name, placeId, jobId, players, link, created.
    """
    printed_data = []
    server_cache = fetch_servers()
    try:
        place_map = {}
        for jobId, info in server_cache.items():
            place_map.setdefault(info["placeId"], []).append(jobId)

        for placeId, jobIds in place_map.items():
            url = f"https://games.roblox.com/v1/games/{placeId}/servers/Public?sortOrder=Asc&limit=100"
            r = requests.get(url, headers=HEADERS, timeout=1)
            servers = r.json().get("data", [])

            for s in servers:
                jobId = s.get("id")
                if jobId in jobIds:
                    players = s.get("playing", 0)
                    max_players = s.get("maxPlayers", MAX_PLAYERS)
                    name = server_cache[jobId]["name"]
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    join_link = f"https://www.roblox.com/games/{placeId}/Steal-a-Brainrot?serverJobId={jobId}"
                    printed_data.append({
                        "timestamp": timestamp,
                        "name": name,
                        "placeId": placeId,
                        "jobId": jobId,
                        "players": f"{players}/{max_players}",
                        "link": join_link,
                        "created": int(time.time() * 1000)
                    })
    except Exception:
        pass

    return printed_data

# ---------------- Dashboard Route ----------------
@app.route("/")
def index():
    html = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Brainrot Finder Dashboard</title>
    <style>
    body {
        margin: 0;
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(-45deg, #0f2027, #203a43, #2c5364, #1c1c1c);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        color: #fff;
        display: flex;
        flex-direction: column;
        height: 100vh;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeOut {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(10px); }
    }
    header {
        background: rgba(255,255,255,0.05);
        padding: 20px;
        text-align: center;
        font-size: 26px;
        color: #00ffe0;
        box-shadow: 0 0 12px #00ffe0;
        backdrop-filter: blur(10px);
    }
    #dashboard {
        display: flex;
        flex: 1;
        overflow: hidden;
    }
    .panel {
        flex: 1;
        padding: 20px;
        overflow-y: auto;
        border-right: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(8px);
    }
    .panel:last-child { border-right: none; }
    h3 { color: #00ffe0; margin-bottom: 12px; }
    .entry {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        padding: 12px 16px;
        margin-bottom: 12px;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        animation: fadeIn 0.3s ease-in;
        transition: transform 0.2s ease;
    }
    .entry:hover { transform: scale(1.02); box-shadow: 0 0 10px #00ffe0; }
    .fade-out { animation: fadeOut 0.5s ease forwards; }
    .copy-btn {
        background: #00ffe0;
        color: #000;
        border: none;
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-weight: bold;
        transition: background 0.3s ease;
        margin-right: 6px;
    }
    .copy-btn:hover { background: #00ccaa; color: #fff; }
    .meta-block {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transition: max-height 0.4s ease, opacity 0.4s ease;
        margin-top: 8px;
        background: rgba(0,0,0,0.3);
        padding: 8px;
        border-radius: 6px;
        white-space: pre-wrap;
        font-size: 12px;
    }
    .meta-block.show { max-height: 500px; opacity: 1; }
    select, input[type="checkbox"] { margin: 6px 0; }
    #statBlock {
        background: rgba(255,255,255,0.1);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.2);
        animation: fadeIn 0.6s ease-in-out;
    }
    </style>
</head>
<body>
  <header>🧠 Brainrot Finder Dashboard</header>
  <div id="dashboard">
    <div class="panel" id="live">
      <h3>🔍 Live Servers</h3>
      <div id="output"></div>
    </div>
    <div class="panel" id="stats">
      <h3>📊 Stats</h3>
      <div id="statBlock">Loading...</div>
    </div>
    <div class="panel" id="settings">
      <h3>⚙️ Settings</h3>
      <label>Refresh Rate:</label>
      <select id="speed">
        <option value="100">100ms</option>
        <option value="1000">1s</option>
        <option value="3000">3s</option>
      </select><br>
      <label><input type="checkbox" id="hideFull"> Hide Full Servers</label>
    </div>
  </div>

<script>
let interval = 100;
let timer;

function copyToClipboard(link) { navigator.clipboard.writeText(link); }
function toggleMeta(jobId) {
  const block = document.getElementById(`meta-${jobId}`);
  block.classList.toggle("show");
}

function render(data) {
  const out = document.getElementById("output");
  const hideFull = document.getElementById("hideFull").checked;

  data.forEach(s => {
    const [p, max] = s.players.split("/").map(Number);
    if (hideFull && p === max) return;

    let div = document.querySelector(`.entry[data-jobid="${s.jobId}"]`);
    const meta = JSON.stringify({ name: s.name, jobId: s.jobId, placeId: s.placeId }, null, 2);

    if (div) {
      div.querySelector(".server-info").innerHTML =
        `[${s.timestamp}] <b>${s.name}</b> | ${s.players} → <a href="${s.link}" target="_blank">Join</a>`;
    } else {
      div = document.createElement("div");
      div.className = "entry";
      div.setAttribute("data-jobid", s.jobId);
      div.setAttribute("data-created", s.created);
      div.innerHTML = `
        <div class="server-info">[${s.timestamp}] <b>${s.name}</b> | ${s.players} → <a href="${s.link}" target="_blank">Join</a></div>
        <div>
          <button class="copy-btn" onclick="copyToClipboard('${s.link}')">Copy</button>
          <button class="copy-btn" onclick="toggleMeta('${s.jobId}')">Details</button>
        </div>
        <pre class="meta-block" id="meta-${s.jobId}">${meta}</pre>
      `;
      out.appendChild(div);
    }
  });

  document.getElementById("statBlock").innerHTML = `
    <p>Total Brainrot Servers Found: <b>${document.querySelectorAll(".entry").length}</b></p>
    <p>Last Refresh Rate: <b>${interval}ms</b></p>
  `;
}

function cleanupOldEntries() {
  const entries = document.querySelectorAll(".entry");
  const now = Date.now();
  entries.forEach(entry => {
    const created = parseInt(entry.getAttribute("data-created"), 10);
    if (now - created > 180000 && !entry.classList.contains("fade-out")) {
      entry.classList.add("fade-out");
      setTimeout(() => entry.remove(), 300);
    }
  });
}

async function fetchData() {
  const res = await fetch("/api/data");
  const data = await res.json();
  render(data);
  cleanupOldEntries();
}

function updateInterval() {
  clearInterval(timer);
  interval = parseInt(document.getElementById("speed").value, 10);
  timer = setInterval(fetchData, interval);
}

document.getElementById("speed").addEventListener("change", updateInterval);
document.getElementById("hideFull").addEventListener("change", fetchData);

updateInterval();
fetchData();
</script>
</body>
</html>
"""
    return render_template_string(html)

# ---------------- JSON API Route ----------------
@app.route("/api/data")
def data():
    return jsonify(poll_live_players())

# ---------------- Main ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
