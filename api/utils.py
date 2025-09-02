import requests
from datetime import datetime
import time

URL = "https://brainrotss.up.railway.app/brainrots"
MAX_PLAYERS = 8
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Cache-Control": "no-cache"
}

def fetch_servers():
    cache = {}
    try:
        resp = requests.get(URL, headers=HEADERS)
        data = resp.json()
        for server in data:
            jobId = server.get("jobId")
            placeId = server.get("serverId")
            name = server.get("name")
            if jobId and placeId:
                cache[jobId] = {"name": name, "placeId": placeId}
    except Exception as e:
        print("Error in fetch_servers:", e)
    return cache

def poll_live_players(server_cache):
    updated = []
    try:
        place_map = {}
        for jobId, info in server_cache.items():
            place_map.setdefault(info["placeId"], []).append(jobId)

        for placeId, jobIds in place_map.items():
            url = f"https://games.roblox.com/v1/games/{placeId}/servers/Public?sortOrder=Asc&limit=100"
            r = requests.get(url, headers=HEADERS)
            servers = r.json().get("data", [])

            for s in servers:
                jobId = s.get("id")
                if jobId in jobIds:
                    players = s.get("playing", 0)
                    max_players = s.get("maxPlayers", MAX_PLAYERS)
                    name = server_cache[jobId]["name"]
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
    except Exception as e:
        print("Error in poll_live_players:", e)
    return updated
