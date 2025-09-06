# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime, timedelta
import threading
import time
import random
import os
from markupsafe import escape  # Correct import for escape

app = Flask(__name__)

# Global variables to store the fetched data
brainrots_data = []
last_update_time = None
# Get update interval from environment variable or default to 2 seconds
update_interval = int(os.environ.get('UPDATE_INTERVAL', 2))

# Lock for thread-safe access to shared data
data_lock = threading.Lock()

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

# Flag to track if data update thread is running
data_update_thread_started = False
data_update_thread = None

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
        print(f"Fetching data from brainrots API with User-Agent: {headers['User-Agent']}")
        response = requests.get("https://brainrotss.up.railway.app/brainrots", timeout=10, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"Successfully fetched {len(data)} servers from brainrots API")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching brainrots data: {e}")
        # Return sample data if the API is not available
        return get_sample_data()

def get_sample_data():
    """Return sample data when the API is not available"""
    print("Using sample data as fallback")
    return [
        {
            "name": "Sample Server 1",
            "serverId": "123456789",
            "jobId": "job1234567890",
            "players": "5/10",
            "moneyPerSec": "$100",
            "lastSeen": int(time.time() * 1000) - 60000,  # 1 minute ago
            "source": "Sample"
        },
        {
            "name": "Sample Server 2",
            "serverId": "987654321",
            "jobId": "job0987654321",
            "players": "8/12",
            "moneyPerSec": "$150",
            "lastSeen": int(time.time() * 1000) - 120000,  # 2 minutes ago
            "source": "Sample"
        }
    ]

def update_brainrots_data():
    """Update brainrots data periodically"""
    global brainrots_data, last_update_time
    
    print("Starting brainrots data update thread")
    
    # Initial data fetch
    try:
        new_brainrots = fetch_brainrots_data()
        if new_brainrots:
            with data_lock:
                brainrots_data = new_brainrots
                last_update_time = datetime.now()
            print(f"Initial brainrots data updated at {last_update_time}. Servers: {len(brainrots_data)}")
        else:
            print("No data received from initial fetch")
    except Exception as e:
        print(f"Error in initial brainrots data update: {e}")
        # Initialize with sample data if there's an error
        with data_lock:
            brainrots_data = get_sample_data()
            last_update_time = datetime.now()
    
    # Continue with periodic updates
    while True:
        try:
            time.sleep(update_interval)
            
            new_brainrots = fetch_brainrots_data()
            if new_brainrots:
                with data_lock:
                    brainrots_data = new_brainrots
                    last_update_time = datetime.now()
                print(f"Brainrots data updated at {last_update_time}. Servers: {len(brainrots_data)}")
            else:
                print("No data received from periodic fetch")
        except Exception as e:
            print(f"Error in periodic brainrots data update: {e}")

def start_data_update_thread():
    """Start the data update thread if not already running"""
    global data_update_thread_started, data_update_thread
    
    if not data_update_thread_started:
        data_update_thread = threading.Thread(target=update_brainrots_data)
        data_update_thread.daemon = True
        data_update_thread.start()
        data_update_thread_started = True
        print("Data update thread started")

def process_data():
    """Process brainrots data"""
    global brainrots_data
    
    with data_lock:
        current_data = brainrots_data.copy()
        current_last_update = last_update_time
    
    processed_data = []
    
    for brainrot in current_data:
        job_id = brainrot.get("jobId", "unknown")
        server_id = brainrot.get("serverId", "unknown")
        
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
        
        processed_data.append({
            "name": name,
            "serverId": server_id,
            "jobId": job_id,
            "players": players_str,
            "currentPlayers": current_players,
            "maxPlayers": max_players,
            "moneyPerSec": money_per_sec,
            "lastSeen": last_seen,
            "timeAgo": time_ago,
            "source": brainrot.get("source", "Unknown"),
            "joinLink": join_link,
        })
    
    # Sort by money per second (convert to numeric value for sorting)
    def money_to_numeric(money_str):
        try:
            # Remove HTML entities before processing
            clean_str = money_str.replace('$', '').replace(' ', '')
            if 'K' in clean_str:
                return float(clean_str.replace('K', '')) * 1000
            elif 'M' in clean_str:
                return float(clean_str.replace('M', '')) * 1000000
            else:
                return float(clean_str)
        except:
            return 0
    
    processed_data.sort(key=lambda x: money_to_numeric(x["moneyPerSec"]), reverse=True)
    
    return processed_data, current_last_update

@app.route('/')
def dashboard():
    """Main dashboard route"""
    print("Dashboard accessed")
    
    # Start data update thread if not running
    start_data_update_thread()
    
    processed_data, current_last_update = process_data()
    
    # Calculate stats
    total_servers = len(processed_data)
    total_players = sum(item["currentPlayers"] for item in processed_data)
    total_capacity = sum(item["maxPlayers"] for item in processed_data)
    
    # Format last update time
    if current_last_update:
        last_update_str = current_last_update.strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_update_str = "Never"
    
    print(f"Rendering dashboard with {total_servers} servers, {total_players} players")
    
    return render_template('dashboard.html', 
                         data=processed_data,
                         total_servers=total_servers,
                         total_players=total_players,
                         total_capacity=total_capacity,
                         last_update=last_update_str,
                         update_interval=update_interval)

@app.route('/data')
def data_api():
    """API endpoint to get processed data as JSON"""
    print("Data API accessed")
    processed_data, _ = process_data()
    return jsonify(processed_data)

@app.route('/stats')
def stats_api():
    """API endpoint to get stats as JSON"""
    print("Stats API accessed")
    processed_data, current_last_update = process_data()
    
    total_servers = len(processed_data)
    total_players = sum(item["currentPlayers"] for item in processed_data)
    total_capacity = sum(item["maxPlayers"] for item in processed_data)
    
    return jsonify({
        "total_servers": total_servers,
        "total_players": total_players,
        "total_capacity": total_capacity,
        "last_update": current_last_update.strftime('%Y-%m-%d %H:%M:%S') if current_last_update else "Never",
        "update_interval": update_interval
    })

# Start the data update thread when the app starts
print("Initializing Brainrot Server Dashboard")
start_data_update_thread()
print("Brainrot Server Dashboard initialized")
