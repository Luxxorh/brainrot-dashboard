import requests, json, time

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json"
}

def fetch_brainrots():
    url = "https://brainrotss.up.railway.app/brainrots"
    res = requests.get(url, headers=headers)
    raw = json.loads(res.text)
    return json.loads(raw['objects'][0]['content'])

def check_servers(servers):
    place_ids = list({s['serverId'] for s in servers})  # Deduplicated
    job_ids = [s['jobId'] for s in servers]

    payload = {
        "placeIds": place_ids,
        "jobIds": job_ids
    }

    res = requests.post("https://presence.roblox.com/v1/presence/places", json=payload, headers=headers)
    return res.json().get("serverPresences", [])

def display_open_servers(presences):
    for s in presences:
        if s["userCount"] < s["maxPlayers"]:
            print(f"[OPEN] {s['jobId']} | {s['userCount']}/{s['maxPlayers']}")

while True:
    try:
        servers = fetch_brainrots()
        presences = check_servers(servers)
        display_open_servers(presences)
        print("— Refreshed —")
        time.sleep(3)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(3)
