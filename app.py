from flask import Flask, jsonify, render_template_string
import requests
import time
from datetime import datetime

app = Flask(__name__)

BRAINROT_URL = "https://brainrotss.up.railway.app/brainrots"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Cache-Control": "no-cache"
}
MAX_SERVERS = 100
TIMEOUT = 1


def fetch_brainrot_servers():
    """Fetch server list (jobId, placeId, name) from brainrotss API."""
    try:
        resp = requests.get(BRAINROT_URL, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error fetching brainrot list: {e}")
        return []


def fetch_live_servers():
    """Fetch Roblox server info for all brainrot servers."""
    brainrot_servers = fetch_brainrot_servers()
    place_map = {}

    # group jobIds by placeId
    for s in brainrot_servers:
        jobId = s.get("jobId")
        placeId = s.get("serverId")
        name = s.get("name")
        if jobId and placeId:
            place_map.setdefault(placeId, []).append((jobId, name))

    results = []
    for placeId, job_list in place_map.items():
        url = f"https://games.roblox.com/v1/games/{placeId}/servers/Public?sortOrder=Asc&limit={MAX_SERVERS}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            servers = r.json().get("data", [])
        except Exception as e:
            print(f"Error fetching Roblox servers for {placeId}: {e}")
            continue

        for s in servers:
            jobId = s.get("id")
            for target_jobId, name in job_list:
                if jobId == target_jobId:
                    players = s.get("playing", 0)
                    max_players = s.get("maxPlayers", 0)
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    join_link = f"https://www.roblox.com/games/{placeId}?jobId={jobId}"
                    results.append({
                        "timestamp": timestamp,
                        "name": name,
                        "placeId": placeId,
                        "jobId": jobId,
                        "players": f"{players}/{max_players}",
                        "link": join_link,
                        "created": int(time.time() * 1000)
                    })
    return results


@app.route("/")
def dashboard():
    # Embeds your full HTML dashboard (unchanged)
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Brainrot Finder Dashboard</title>
    <style>
        /* full CSS here (same as your HTML) */
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
    let interval = 50;
    let timer;

    function copyToClipboard(link) {
      navigator.clipboard.writeText(link);
    }

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

        let div = document.querySelector(\`.entry[data-jobid="\${s.jobId}"]\`);
        const meta = JSON.stringify({ name: s.name, jobId: s.jobId, placeId: s.placeId }, null, 2);

        if (div) {
          div.querySelector(".server-info").innerHTML =
            \`[\${s.timestamp}] <b>\${s.name}</b> | \${s.players} → <a href="\${s.link}" target="_blank">Join</a>\`;
        } else {
          div = document.createElement("div");
          div.className = "entry";
          div.setAttribute("data-jobid", s.jobId);
          div.setAttribute("data-created", s.created);
          div.innerHTML = \`
            <div class="server-info">[\${s.timestamp}] <b>\${s.name}</b> | \${s.players} → <a href="\${s.link}" target="_blank">Join</a></div>
            <div>
              <button class="copy-btn" onclick="copyToClipboard('\${s.link}')">Copy</button>
              <button class="copy-btn" onclick="toggleMeta('\${s.jobId}')">Details</button>
            </div>
            <pre class="meta-block" id="meta-\${s.jobId}">\${meta}</pre>
          \`;
          out.appendChild(div);
        }
      });

      document.getElementById("statBlock").innerHTML = \`
        <p>Total Brainrot Servers Found: <b>\${document.querySelectorAll(".entry").length}</b></p>
        <p>Last Refresh Rate: <b>\${interval}ms</b></p>
      \`;
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


@app.route("/api/data")
def api_data():
    servers = fetch_live_servers()
    return jsonify(servers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
