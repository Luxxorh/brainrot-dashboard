from flask import Flask, jsonify
import requests, threading, time

app = Flask(__name__)

BRAINROT_URL = "https://brainrotss.up.railway.app/brainrots"
ROBLOX_API_TEMPLATE = "https://games.roblox.com/v1/games/{}/servers/Public?sortOrder=Asc&limit=100&excludeFullGames=true"

IPHONE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 "
        "Mobile/15E148 Safari/604.1"
    )
}

brainrot_cache = []
roblox_cache = {}
matched_results = []

def poll_brainrot():
    while True:
        try:
            brainrot_cache.clear()
            brainrot_cache.extend(requests.get(BRAINROT_URL, headers=IPHONE_HEADERS).json())
        except Exception as e:
            print("Brainrot polling error:", e)
        time.sleep(0.075)

def poll_roblox_and_match():
    while True:
        try:
            temp_roblox = {}
            temp_results = []

            for entry in brainrot_cache:
                place_id = entry.get("serverId")
                job_id = entry.get("jobId")
                if not place_id or not job_id:
                    continue

                if place_id not in temp_roblox:
                    try:
                        roblox_data = requests.get(
                            ROBLOX_API_TEMPLATE.format(place_id),
                            headers=IPHONE_HEADERS
                        ).json().get("data", [])
                        temp_roblox[place_id] = roblox_data
                    except Exception as e:
                        print(f"Roblox fetch error for {place_id}:", e)
                        continue

                for server in temp_roblox[place_id]:
                    if server.get("id") == job_id:
                        temp_results.append({
                            "name": entry.get("name"),
                            "serverId": place_id,
                            "jobId": job_id,
                            "players": entry.get("players"),
                            "moneyPerSec": entry.get("moneyPerSec"),
                            "joinLink": f"https://roblox.com/games/{place_id}/Steal-a-Brainrot?serverJobId={job_id}"
                        })
                        break

            roblox_cache.clear()
            roblox_cache.update(temp_roblox)

            matched_results.clear()
            matched_results.extend(temp_results)

        except Exception as e:
            print("Matching error:", e)
        time.sleep(1.5)

threading.Thread(target=poll_brainrot, daemon=True).start()
threading.Thread(target=poll_roblox_and_match, daemon=True).start()

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "status": "🧠 Brainrot Checker is live",
        "usage": "Use GET /brainrots for matched server data"
    })

@app.route("/favicon.ico")
def favicon():
    return "", 204

@app.route("/brainrots", methods=["GET"])
def get_matched_brainrots():
    return jsonify(matched_results)
