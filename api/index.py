from flask import Flask, jsonify
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

def fetch_live_servers():
    try:
        # Fetch server list from Railway
        resp = requests.get(URL, headers=HEADERS, timeout=1)
        data = resp.json() if resp.status_code == 200 else []
        if not data:
            return []

        place_map = {}
        name_map = {}
        for server in data:
            jobId = server.get("jobId")
            placeId = server.get("serverId")
            name = server.get("name")
            if jobId and placeId:
                place_map.setdefault(placeId, []).append(jobId)
                name_map[jobId] = name

        updated = []
        for placeId, jobIds in place_map.items():
            try:
                r = requests.get(
                    f"https://games.roblox.com/v1/games/{placeId}/servers/Public?sortOrder=Asc&limit=100",
                    headers=HEADERS,
                    timeout=1
                )
                servers = r.json().get("data", [])
                for s in servers:
                    jobId = s.get("id")
                    if jobId in jobIds:
                        players = s.get("playing", 0)
                        max_players = s.get("maxPlayers", MAX_PLAYERS)
                        name = name_map.get(jobId, "Unknown")
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        join_link = f"https://www.roblox.com/games/{placeId}/Steal-a-Brainrot?serverJobId={jobId}"
                        updated.append({
                            "timestamp": timestamp,
                            "name": name,
                            "placeId": placeId,
                            "jobId": jobId,
                            "players": f"{players}/{max_players}",
                            "link": join_link,
                            "created": int(time.time() * 1000)
                        })
            except Exception:
                continue

        return updated[:100]  # limit to 100 servers

    except Exception:
        return []

@app.route("/data")
def data():
    return jsonify(fetch_live_servers())
