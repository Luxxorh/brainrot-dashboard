import asyncio
import aiohttp
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime
import time

# ---------------- Config ----------------
URL = os.environ.get("BACKEND_URL", "https://brainrotss.up.railway.app/brainrots")
MAX_PLAYERS = int(os.environ.get("MAX_PLAYERS", 8))
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Cache-Control": "no-cache"
}

# ---------------- Async Backend & Roblox Logic ----------------
async def fetch_backend(session):
    server_cache = {}
    try:
        async with session.get(URL, headers=HEADERS, timeout=3) as resp:
            data = await resp.json()
            for server in data:
                jobId = server.get("jobId")
                placeId = server.get("serverId")
                name = server.get("name")
                if jobId and placeId:
                    server_cache[jobId] = {"name": name, "placeId": placeId}
    except Exception:
        pass
    return server_cache

async def fetch_roblox(session, placeId):
    url = f"https://games.roblox.com/v1/games/{placeId}/servers/Public?sortOrder=Asc&limit=100"
    try:
        async with session.get(url, headers=HEADERS, timeout=3) as r:
            data = await r.json()
            return data.get("data", [])
    except Exception:
        return []

async def poll_live_players():
    async with aiohttp.ClientSession() as session:
        server_cache = await fetch_backend(session)

        place_map = {}
        for jobId, info in server_cache.items():
            place_map.setdefault(info["placeId"], []).append(jobId)

        tasks = [fetch_roblox(session, placeId) for placeId in place_map.keys()]
        results = await asyncio.gather(*tasks)

        printed_data = []
        for i, placeId in enumerate(place_map.keys()):
            jobIds = place_map[placeId]
            servers = results[i]
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
        return printed_data

# ---------------- HTTP Handler ----------------
class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type="text/html"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def safe_write(self, data: bytes):
        try:
            self.wfile.write(data)
        except BrokenPipeError:
            # Client disconnected early — ignore
            pass

    def do_HEAD(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path in ["/", "/api/data"]:
            content_type = "text/html" if parsed_path.path == "/" else "application/json"
            self._set_headers(content_type)
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/":
            self._set_headers("text/html")
            with open("dashboard.html", "r", encoding="utf-8") as f:
                self.safe_write(f.read().encode())
        elif parsed_path.path == "/api/data":
            self._set_headers("application/json")
            data = asyncio.run(poll_live_players())
            self.safe_write(json.dumps(data).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.safe_write(b"404 Not Found")

# ---------------- Main ----------------
def run(server_class=HTTPServer, handler_class=Handler, port=None):
    # Render requires $PORT
    port = int(port or os.environ.get("PORT", 5000))
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server running at http://0.0.0.0:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
