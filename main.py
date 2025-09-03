from flask import Flask, jsonify
import requests

app = Flask(__name__)

BRAINROT_URL = "https://brainrotss.up.railway.app/brainrots"
ROBLOX_API_TEMPLATE = "https://games.roblox.com/v1/games/{}/servers/Public?sortOrder=Asc&limit=100&excludeFullGames=true"

# ✅ Root route to confirm service is alive
@app.route("/", methods=["GET"])
def index():
    return {
        "status": "🧠 Brainrot Checker is live",
        "usage": "Use GET /brainrots for matched server data"
    }

# ✅ Silence favicon.ico requests
@app.route("/favicon.ico")
def favicon():
    return "", 204

# 🔍 Core logic for matching brainrots
@app.route("/brainrots", methods=["GET"])
def get_matched_brainrots():
    try:
        brainrot_data = requests.get(BRAINROT_URL).json()
        results = []

        for entry in brainrot_data:
            name = entry.get("name")
            place_id = entry.get("serverId")
            job_id = entry.get("jobId")
            players = entry.get("players")
            money_per_sec = entry.get("moneyPerSec")

            roblox_url = ROBLOX_API_TEMPLATE.format(place_id)
            roblox_data = requests.get(roblox_url).json().get("data", [])

            for server in roblox_data:
                if server.get("id") == job_id:
                    result = {
                        "name": name,
                        "serverId": place_id,
                        "jobId": job_id,
                        "players": players,
                        "moneyPerSec": money_per_sec,
                        "joinLink": f"https://roblox.com/games/{place_id}/Steal-a-Brainrot?serverJobId={job_id}"
                    }
                    results.append(result)
                    break  # no need to check other servers for this jobId

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🧪 Optional: Local debug mode
if __name__ == "__main__":
    app.run(debug=True)
