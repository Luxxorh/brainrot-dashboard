from flask import Blueprint, jsonify, render_template_string
from .utils import fetch_servers, poll_live_players

routes = Blueprint("routes", __name__)

@routes.route("/")
def index():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Brainrot Finder Dashboard</title>
    <style>
        /* [CSS styles as provided] */
    </style>
</head>
<body>
    <header>🧠 Brainrot Finder Dashboard</header>
    <div id="dashboard">
        <div class="panel" id="live">
            <h3>🔍 Live Servers</h3>
            <div id="output"></div>
        </div>
        <div class="panel" id="stats">
            <h3>📊 Stats</h3>
            <div id="statBlock">Loading...</div>
        </div>
        <div class="panel" id="settings">
            <h3>⚙️ Settings</h3>
            <label>Refresh Rate:</label>
            <select id="speed">
                <option value="100">100ms</option>
                <option value="1000">1s</option>
                <option value="3000">3s</option>
            </select><br>
            <label><input type="checkbox" id="hideFull"> Hide Full Servers</label>
        </div>
    </div>
    <script>
        // [JavaScript logic as provided]
    </script>
</body>
</html>"""
    return render_template_string(html)

@routes.route("/data")
def data():
    cache = fetch_servers()
    result = poll_live_players(cache)
    return jsonify(result)
