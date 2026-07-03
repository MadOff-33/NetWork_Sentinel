# Fichier : server.py (NAS V5 - FINAL STABLE)
from flask import Flask, jsonify, request
import threading
import time
import os
import json
import socket
import pandas as pd
import requests

# Modules internes (Vérifiez qu'ils sont bien dans le dossier src/)
from src.scanner import NetworkScanner
from src.security import SecurityMonitor
from src.analyzer import NetworkAnalyzer
from src.notifier import EmailNotifier

app = Flask(__name__)

# --- CONFIGURATION ---
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
HISTORY_FILE = os.path.join(DATA_DIR, "network_history.csv")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
VENDOR_CACHE = {}


def detect_ip_range():
    """Determine la plage /24 du reseau local en regardant quelle interface route vers Internet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return ".".join(local_ip.split(".")[:3]) + ".0/24"
    except OSError:
        return "192.168.1.0/24"


def get_ip_range():
    """Plage IP a scanner : config.json (cle 'ip_range') sinon auto-detection."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                configured = json.load(f).get("ip_range", "")
                if configured:
                    return configured
        except (OSError, json.JSONDecodeError):
            pass
    return detect_ip_range()

# État global avec initialisation des clés vitales
current_state = {
    "devices": [],
    "alerts": [],
    "performance": {"ping_ms": 0, "download_mbps": 0, "upload_mbps": 0}, # CLÉ CRITIQUE
    "last_update": "Démarrage...",
    "scan_interval": 30
}

def get_mac_vendor(mac):
    if mac in VENDOR_CACHE: return VENDOR_CACHE[mac]
    try:
        r = requests.get(f"https://api.macvendors.co/{mac}", timeout=1)
        if r.status_code == 200:
            vendor = r.text.strip()
            VENDOR_CACHE[mac] = vendor
            return vendor
    except: pass
    return ""

def resolve_details(dev):
    ip, mac = dev['ip'], dev['mac']
    name = dev.get('name', '?')
    if name in ["?", "Inconnu"]:
        try: name = socket.gethostbyaddr(ip)[0]
        except: name = "?"
    if name == "?":
        vendor = get_mac_vendor(mac)
        name = f"({vendor})" if vendor else "Inconnu"
    dev['name'] = name
    return dev

def background_scan_loop():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
    
    # Chargement config initiale
    interval = 30
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f: 
                cfg = json.load(f)
                interval = cfg.get("scan_interval", 30)
        except: pass
    
    alerted_macs = set()

    while True:
        try:
            print(f"[INFO] Scan... ({interval}s)")
            
            # 1. SCAN
            scanner = NetworkScanner(get_ip_range())
            scan_res = scanner.scan()
            enriched_res = [resolve_details(d) for d in scan_res]
            
            # 2. SECURITÉ
            sec = SecurityMonitor()
            new_devs, known_devs = sec.analyze_intrusions(enriched_res)
            
            # 3. PERF (Ping à chaque tour, Speedtest moins souvent)
            # On initialise les valeurs par défaut
            perf = current_state.get("performance", {"ping_ms": 0, "download_mbps": 0, "upload_mbps": 0})
            
            # Logique : Ping toutes les 30s, Speedtest toutes les 5 minutes (300s)
            now = int(time.time())
            if now % 300 < interval + 5: 
                try:
                    analyzer = NetworkAnalyzer()
                    new_perf = analyzer.run_performance_test()
                    if new_perf: perf = new_perf
                    
                    # Sauvegarde CSV
                    df = pd.DataFrame([perf])
                    df['timestamp'] = time.strftime("%Y-%m-%d %H:%M:%S")
                    hdr = not os.path.exists(HISTORY_FILE)
                    df.to_csv(HISTORY_FILE, mode='a', header=hdr, index=False)
                except Exception as e: print(f"Perf Error: {e}")
            
            # 4. EMAIL
            if new_devs and os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE) as f: conf = json.load(f)
                    if conf.get("email_enabled"):
                        # On filtre : on ne garde que ceux qui ne sont PAS dans la mémoire
                        to_notify = [d for d in new_devs if d['mac'] not in alerted_macs]
                        
                        if to_notify:
                            notifier = EmailNotifier()
                            notifier.config = conf
                            notifier.send_alert(to_notify)
                            
                            # On mémorise les MACs pour ne plus les spammer tant que le serveur tourne
                            for d in to_notify:
                                alerted_macs.add(d['mac'])
                except Exception as e: print(f"Mail Error: {e}")

            # Mise à jour Etat
            current_state["devices"] = new_devs + known_devs
            current_state["alerts"] = new_devs
            current_state["performance"] = perf
            current_state["last_update"] = time.strftime("%H:%M:%S")
            
            # Mise à jour intervalle dynamique
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE) as f: interval = json.load(f).get("scan_interval", 30)
                except: pass

        except Exception as e:
            print(f"[ERREUR] {e}")
        
        time.sleep(interval)

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify(current_state)

@app.route('/authorize', methods=['POST'])
def authorize_device():
    mac = request.json.get('mac')
    if mac:
        try:
            sec = SecurityMonitor()
            sec.trust_device(mac)
            # Mise à jour mémoire immédiate pour réactivité client
            for d in current_state["alerts"]:
                if d['mac'] == mac:
                    current_state["alerts"].remove(d)
                    current_state["devices"].append(d)
                    break
            return jsonify({"status": "ok"})
        except Exception as e: return jsonify({"error": str(e)}), 500
    return jsonify({"error": "No MAC"}), 400

@app.route('/update_settings', methods=['POST'])
def update_settings():
    try:
        with open(CONFIG_FILE, 'w') as f: json.dump(request.json, f)
        return jsonify({"status": "ok"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/history', methods=['GET'])
def get_history():
    if os.path.exists(HISTORY_FILE):
        try: return pd.read_csv(HISTORY_FILE).tail(30).to_json(orient="records")
        except: pass
    return jsonify([])

if __name__ == '__main__':
    threading.Thread(target=background_scan_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5050)