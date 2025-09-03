import requests
import time

# URLs
BRAINROTS_URL = "https://brainrotss.up.railway.app/brainrots"
ROBLOX_API_TEMPLATE = "https://games.roblox.com/v1/games/109983668079237/servers/Public?sortOrder=Asc&limit=100&excludeFullGames=true"

# Polling interval in seconds (750ms)
POLL_INTERVAL = 0.75

# Headers to mimic a browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.roblox.com/",
}

def fetch_brainrots():
    response = requests.get(BRAINROTS_URL, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return [
        {
            "name": entry["name"],
            "serverId": entry["serverId"],
            "jobId": entry["jobId"],
            "players": entry["players"],
            "moneyPerSec": entry["moneyPerSec"]
        }
        for entry in data
    ]

def fetch_all_roblox_servers():
    servers = []
    next_page = None

    while True:
        url = ROBLOX_API_TEMPLATE
        if next_page:
            url += f"&cursor={next_page}"
        
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        servers.extend([{
            "jobId": entry["id"],
            "playing": entry["playing"]
        } for entry in data["data"]])
        
        next_page = data.get("nextPageCursor")
        if not next_page:
            break

    return servers

def monitor():
    seen_jobIds = set()  # Tracks matches already printed

    while True:
        try:
            brainrots_data = fetch_brainrots()
            roblox_data = fetch_all_roblox_servers()
            
            # Create a dictionary of Roblox jobId -> playing for quick lookup
            roblox_dict = {server["jobId"]: server["playing"] for server in roblox_data}

            for entry in brainrots_data:
                jobId = entry["jobId"]
                if jobId in roblox_dict and jobId not in seen_jobIds:
                    # New match found
                    match_info = {
                        "name": entry["name"],
                        "moneyPerSec": entry["moneyPerSec"],
                        "players": entry["players"],
                        "playing": roblox_dict[jobId]
                    }
                    print(match_info)
                    seen_jobIds.add(jobId)  # Mark as seen

        except Exception as e:
            print(f"Error fetching data: {e}")

        time.sleep(POLL_INTERVAL)  # Wait before polling again

if __name__ == "__main__":
    monitor()
