# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime, timedelta
import time
from markupsafe import escape

app = Flask(__name__)

# Global variables to store the fetched data
brainrots_data = []
last_update_time = None
update_interval = int(os.environ.get('UPDATE_INTERVAL', 5))

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

# User Agents list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/极速加速器17.2 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
]

last_user_agent_index = -1

def get_headers():
    global last_user_agent_index
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

def money_to_numeric(money_str):
    try:
        clean_str = money_str.replace('$', '').replace(' ', '').replace(',', '').replace('/s', '')
        if 'K' in clean_str:
            return float(clean_str.replace('K', '')) * 1000
        elif 'M' in clean_str:
            return float(clean_str.replace('M', '')) * 1000000
        elif 'B' in clean_str:
            return float(clean_str.replace('B', '')) * 1000000000
        else:
            return float(clean_str)
    except:
        return 0

def process_data():
    global brainrots_data
    processed_data = []

    for brainrot in brainrots_data:
        job_id = brainrot.get("jobId")
        server_id = brainrot.get("serverId")
        place_id = server_id
        join_link = f"https://www.roblox.com/games/{place_id}/Steal-a-Brainrot?serverJobId={job_id}"

        last_seen_ts = brainrot.get("lastSeen", 0)
        if last_seen_ts:
            last_seen = datetime.fromtimestamp(last_seen_ts / 1000).strftime('%Y-%m-%d %H:%M:%S')
        else:
            last_seen = "Unknown"

        if last_seen_ts:
            time_since = (datetime.now() - datetime.fromtimestamp(last_seen_ts / 1000)).total_seconds()
            minutes_since = int(time_since // 60)
            seconds_since = int(time_since % 60)
            time_ago = f"{minutes_since}m {seconds_since}s ago"
        else:
            time_ago = "Unknown"

        players_str = brainrot.get("players", "0/0")
        try:
            current_players, max_players = map(int, players_str.split('/'))
        except:
            current_players, max_players = 0, 0

        name = str(escape(brainrot.get("name", "Unknown")))
        money_per_sec = str(escape(brainrot.get("moneyPerSec", "$0")))
        
        if money_per_sec.endswith('/s'):
            money_per_sec = money_per_sec[:-2]
        
        rarity = None
        if name in BRAINROT_GOD_NAMES:
            rarity = "Brainrot God"
        elif name in SECRET_NAMES:
            rarity = "Secret"

        if rarity:
            money_numeric = money_to_numeric(money_per_sec)
            
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
                "rarity": rarity,
                "joinLink": join_link,
                "moneyNumeric": money_numeric
            })

    processed_data.sort(key=lambda x: x["moneyNumeric"], reverse=True)
    
    for item in processed_data:
        item.pop("moneyNumeric", None)

    return processed_data

def fetch_initial_data():
    global brainrots_data, last_update_time
    try:
        new_brainrots = fetch_brainrots_data()
        if new_brainrots:
            brainrots_data = new_brainrots
            last_update_time = datetime.now()
            print(f"Initial brainrots data loaded at {last_update_time}. Servers: {len(brainrots_data)}")
        else:
            print("No initial brainrots data received")
    except Exception as e:
        print(f"Error in initial data fetch: {e}")

fetch_initial_data()

@app.route('/')
def dashboard():
    try:
        global brainrots_data, last_update_time
        new_brainrots = fetch_brainrots_data()
        if new_brainrots:
            brainrots_data = new_brainrots
            last_update_time = datetime.now()
        
        processed_data = process_data()

        total_servers = len(processed_data)
        total_players = sum(item["currentPlayers"] for item in processed_data)
        total_capacity = sum(item["maxPlayers"]极速加速器 for item in processed_data)

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
    try:
        global brainrots_data
        new_brainrots = fetch_brainrots_data()
        if new_brainrots:
            brainrots_data = new_brainrots
        
        processed_data = process_data()
        return jsonify(processed_data)
    except Exception as e:
        print(f"Error in data API: {e}")
        return jsonify([])

@app.route('/stats')
def stats_api():
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
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
