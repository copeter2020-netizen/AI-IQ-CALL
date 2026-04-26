from flask import Flask, jsonify, render_template_string
import json
import os

app = Flask(__name__)

STATS_FILE = "stats.json"
TRADES_FILE = "trades.json"

def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r") as f:
        return json.load(f)

@app.route("/")
def dashboard():
    return render_template_string("""
    <html>
    <head>
        <title>Trading Desk</title>
        <script>
        async function loadData(){
            let stats = await fetch('/stats').then(r=>r.json());
            let trades = await fetch('/trades').then(r=>r.json());

            document.getElementById("wins").innerText = stats.wins;
            document.getElementById("losses").innerText = stats.losses;
            document.getElementById("winrate").innerText = stats.winrate + "%";

            let list = "";
            trades.slice(-10).reverse().forEach(t=>{
                list += `<li>${t.pair} ${t.direction} → ${t.result}</li>`;
            });

            document.getElementById("trades").innerHTML = list;
        }

        setInterval(loadData, 2000);
        </script>
    </head>

    <body onload="loadData()" style="font-family:Arial;background:#0f172a;color:white;">
        <h1>🏦 Trading Desk</h1>

        <div>
            <h2>📊 Estadísticas</h2>
            <p>Wins: <span id="wins"></span></p>
            <p>Losses: <span id="losses"></span></p>
            <p>Winrate: <span id="winrate"></span></p>
        </div>

        <div>
            <h2>🔥 Últimos Trades</h2>
            <ul id="trades"></ul>
        </div>

    </body>
    </html>
    """)

@app.route("/stats")
def stats():
    data = load_json(STATS_FILE, {"wins":0,"losses":0})
    total = data["wins"] + data["losses"]

    winrate = 0
    if total > 0:
        winrate = round((data["wins"]/total)*100,2)

    return jsonify({
        "wins": data["wins"],
        "losses": data["losses"],
        "winrate": winrate
    })

@app.route("/trades")
def trades():
    return jsonify(load_json(TRADES_FILE, []))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
