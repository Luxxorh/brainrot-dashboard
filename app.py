# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime, timedelta
import threading
import time
import random
from markupsafe import escape  # Correct import for escape

app = Flask(__name__)

# Global variables to store the fetched data
brainrots_data = []
last_update_time = None
update_interval = int(os.environ.get('UPDATE_INTERVAL', 5))  # Update brainrot data every 5 seconds

# Brainrot God rarity brainrots
BRAINROT_GOD_NAMES = [
    "Cocofanto Elefanto", "Girafa Celestre", "Tralalero Tralala", 
    "Los Crocodillitos", "Tigroligre Frutonni", "Odin Din Din Dun", 
    "Pakrahmatmamat", "Brr es Teh Patipum", "Tartaruga Cisterna", 
    "Orcalero Orcala", "Tralalita Tralala", "Los Orcalitos", 
    "Tukanno Bananno", "Trenostruzzo Turbo 3000", "Trippi Troppi Troppa Trippa", 
    "Ballerino Lololo", "Bulbito Bandito Traktorito", "Los Tungtungtungcitos", 
    "Piccione Macchina", "Crabbo Limonetta", "Cacasito Satalito", 
    "Chihuanini Taconini"
]

# Secret rarity brainrots
SECRET_NAMES = [
    "La Vacca Saturno Saturnita", "Torrtuginni Dragonfrutini", 
    "Agarrini La Palini", "Los Tralaleritos", "Las Tralaleritas", 
    "Job Job Job Sahur", "Las Vaquitas Saturnitas", "Ketupat Kepat", 
    "Graipuss Medussi", "Pot Hotspot", "Chicleteira Bicicleteira", 
    "La Grande Combinasion", "Los Combinasionas", "Nuclearo Dinossauro", 
    "Bisonte Giuppitere", "Los Hotspotsitos", "Esok Sekolah", 
    "Garama and Madundung", "Los Matteos", "Dragon Cannelloni", 
    "Los Spyderinis", "La Supreme Combinasion", "Spaghetti Tualetti", 
    "Guerriro Digitale"
]

# Comprehensive list of User Agents to rotate through
USER_AGENTS = [
    # Windows - Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",

    # Windows - Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",

    # macOS - Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",

    # macOS - Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    # Linux - Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",

    # Mobile - iOS Safari
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",

    # Mobile - Android Chrome
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.210 Mobile Safari/537.36",
]

# Track which User Agent was used last to ensure rotation
last_user_agent_index = -1

def get_headers():
    """Get headers with a rotating User Agent"""
    global last_user_agent_index

    # Rotate through User Agents
    last_user_agent_index = (last_user_agent_index + 1) % len(USER_AGENTS)
    user_agent = USER_AGENTS[last_user_agent_index]

    return {
        'User-Agent': user_agent,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }

def fetch_brainrots_data():
    """Fetch data from the brainrots endpoint"""
    try:
        headers = get_headers()
        response = requests.get("https://brainrotss.up.railway.app/brainrots", timeout=10, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching brainrots data: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error fetching data: {e}")
        return []

def update_brainrots_data():
    """Update brainrots data periodically"""
    global brainrots_data, last_update_time

    while True:
        try:
            new_brainrots = fetch_brainrots_data()
            if new_brainrots:
                brainrots_data = new_brainrots
                last_update_time = datetime.now()
                print(f"Brainrots data updated at {last_update_time}. Servers: {len(brainrots_data)}")
            else:
                print("No brainrots data received from API")
        except Exception as e:
            print(f"Error updating brainrots data: {e}")

        time.sleep(update_interval)

def money_to_numeric(money_str):
    """Convert money string to numeric value for sorting"""
    try:
        # Remove HTML entities and symbols before processing
        clean_str = money_str.replace('$', '').replace(' ', '').replace(',', '').replace('/s', '')
        
        # Handle cases where the value might have extra text like "/s"
        if 'K' in clean_str:
            return float(clean_str.replace('K', '')) * 1000
        elif 'M' in clean_str:
            return float(clean_str.replace('M', '')) * 1000000
        elif 'B' in clean_str:
            return float(clean_str.replace('B', '')) * 1000000000
        else:
            # Try to parse as a regular number
            return float(clean_str)
    except:
        return 0

def process_data():
    """Process brainrots data"""
    global brainrots_data

    processed_data = []

    for brainrot in brainrots_data:
        job_id = brainrot.get("jobId")
        server_id = brainrot.get("serverId")

        # Create join link
        place_id = server_id  # Using serverId as placeId
        join_link = f"https://www.roblox.com/games/{place_id}/Steal-a-Brainrot?serverJobId={job_id}"

        # Convert lastSeen timestamp to readable format
        last_seen_ts = brainrot.get("lastSeen", 0)
        if last_seen_ts:
            last_seen = datetime.fromtimestamp(last_seen_ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            last_seen = "Unknown"

        # Calculate time since last seen
        if last_seen_ts:
            time_since = (datetime.now() - datetime.fromtimestamp(last_seen_ts / 1000)).total_seconds()
            minutes_since = int(time_since // 60)
            seconds_since = int(time_since % 60)
            time_ago = f"{minutes_since}m {seconds_since}s ago"
        else:
            time_ago = "Unknown"

        # Parse players count
        players_str = brainrot.get("players", "0/0")
        try:
            current_players, max_players = map(int, players_str.split('/'))
        except:
            current_players, max_players = 0, 0

        # Escape HTML in the name to prevent XSS and rendering issues
        name = str(escape(brainrot.get("name", "Unknown")))
        money_per_sec = str(escape(brainrot.get("moneyPerSec", "$0")))
        
        # Clean up moneyPerSec - remove any existing "/s" suffix to prevent double "/s"
        if money_per_sec.endswith('/s'):
            money_per_sec = money_per_sec[:-2]
        
        # Determine rarity based on name - only show Brainrot God or Secret
        rarity = None
        if name in BRAINROT_GOD_NAMES:
            rarity = "Brainrot God"
        elif name in SECRET_NAMES:
            rarity = "Secret"

        # Only include brainrots with special rarity
        if rarity:
            # Calculate numeric value for sorting
            money_numeric = money_to_numeric(money_per_sec)
            
            processed_data.append({
                "name": name,
                "serverId": server_id,
                "jobId": job_id,
                "players": players_str,
                "currentPlayers": current_players,
                "maxPlayers": max_players,
                "moneyPerSec": money_per_sec,  # This is now cleaned (no "/s")
                "lastSeen": last_seen,
                "timeAgo": time_ago,
                "rarity": rarity,
                "joinLink": join_link,
                "moneyNumeric": money_numeric  # Add numeric value for sorting
            })

    # Sort by money per second (highest first) using the pre-calculated numeric value
    processed_data.sort(key=lambda x: x["moneyNumeric"], reverse=True)
    
    # Remove the temporary numeric field before returning
    for item in processed_data:
        item.pop("moneyNumeric", None)

    return processed_data

@app.route('/')
def dashboard():
    """Main dashboard route"""
    try:
        processed_data = process_data()

        # Calculate stats
        total_servers = len(processed_data)
        total_players = sum(item["currentPlayers"] for item in processed_data)
        total_capacity = sum(item["maxPlayers"] for item in processed_data)

        # Format last update time
        if last_update_time:
            last_update_str = last_update_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            last_update_str = "Never"

        return render_template('dashboard.html', 
                             data=processed_data,
                             total_servers=total_servers,
                             total_players=total_players,
                             total_capacity=total_capacity,
                             last_update=last_update_str,
                             update_interval=update_interval)
    except Exception as e:
        print(f"Error in dashboard route: {e}")
        return render_template('dashboard.html', 
                             data=[],
                             total_servers=0,
                             total_players=0,
                             total_capacity=0,
                             last_update="Never",
                             update_interval=update_interval)

@app.route('/data')
def data_api():
    """API endpoint to get processed data as JSON"""
    try:
        processed_data = process_data()
        return jsonify(processed_data)
    except Exception as e:
        print(f"Error in data API: {e}")
        return jsonify([])

@app.route('/stats')
def stats_api():
    """API endpoint to get stats as JSON"""
    try:
        processed_data = process_data()

        total_servers = len(processed_data)
        total_players = sum(item["currentPlayers"] for item in processed_data)
        total_capacity = sum(item["maxPlayers"] for item in processed_data)

        return jsonify({
            "total_servers": total_servers,
            "total_players": total_players,
            "total_capacity": total_capacity,
            "last_update": last_update_time.strftime('%Y-%m-%d %H:%M:%S') if last_update_time else "Never",
            "update_interval": update_interval
        })
    except Exception as e:
        print(f"Error in stats API: {e}")
        return jsonify({
            "total_servers": 0,
            "total_players": 0,
            "total_capacity": 0,
            "last_update": "Never",
            "update_interval": update_interval
        })

@app.route('/health')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# Start the data update thread
def start_update_thread():
    """Start the background update thread"""
    brainrot_thread = threading.Thread(target=update_brainrots_data)
    brainrot_thread.daemon = True
    brainrot_thread.start()
    print("Background update thread started")

# Start the update thread when the app starts
start_update_thread()

if __name__ == '__main__':
    # Use PORT environment variable if available, otherwise default to 5000
    port = int(os.environ.get('PORT', 5000))
    # Only run in debug mode if explicitly set
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
