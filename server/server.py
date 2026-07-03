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

# Token d'authentification optionnel : si API_TOKEN est defini dans
# l'environnement du conteneur, toutes les routes POST exigent le header
# X-Auth-Token. Sans API_TOKEN, comportement historique (API ouverte LAN).
API_TOKEN = os.environ.get("API_TOKEN", "")

# Event permettant au client de declencher un scan immediat (/scan_now)
scan_request = threading.Event()


@app.before_request
def check_token():
    if API_TOKEN and request.method == "POST":
        if request.headers.get("X-Auth-Token") != API_TOKEN:
            return jsonify({"error": "Token invalide ou absent"}), 401

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
    except requests.RequestException:
        pass
    return ""

def resolve_details(dev):
    ip, mac = dev['ip'], dev['mac']
    name = dev.get('name', '?')
    if name in ["?", "Inconnu"]:
        try: name = socket.gethostbyaddr(ip)[0]
        except OSError: name = "?"
    if name == "?":
        vendor = get_mac_vendor(mac)
        name = f"({vendor})" if vendor else "Inconnu"
    dev['name'] = name
    return dev

def trim_history(max_rows=20000, keep_rows=10000):
    """Empeche le CSV d'historique de grossir sans limite."""
    try:
        if not os.path.exists(HISTORY_FILE):
            return
        df = pd.read_csv(HISTORY_FILE)
        if len(df) > max_rows:
            df.tail(keep_rows).to_csv(HISTORY_FILE, index=False)
            print(f"[INFO] Historique tronque : {len(df)} -> {keep_rows} lignes")
    except (OSError, pd.errors.ParserError) as e:
        print(f"[ERREUR] Troncature historique : {e}")


def background_scan_loop():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

    # Chargement config initiale
    interval = 30
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
                interval = cfg.get("scan_interval", 30)
        except (OSError, json.JSONDecodeError) as e:
            print(f"[ERREUR] Config illisible : {e}")

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
                    trim_history()
                except Exception as e: print(f"Perf Error: {e}")

            # 4. EMAIL
            if new_devs and os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE) as f: conf = json.load(f)
                    if conf.get("email_enabled"):
                        # On ne notifie pas les appareils déjà signalés ni les bloqués
                        to_notify = [d for d in new_devs
                                     if d['mac'] not in alerted_macs and not d.get('blocked')]

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
                except (OSError, json.JSONDecodeError):
                    pass

        except Exception as e:
            print(f"[ERREUR] {e}")

        # Attend l'intervalle OU un declenchement manuel via /scan_now
        scan_request.wait(timeout=interval)
        scan_request.clear()

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

@app.route('/block', methods=['POST'])
def block_device():
    """Marque un appareil comme bloqué (statut affiché, sort du décompte d'intrus)."""
    mac = (request.json or {}).get('mac')
    if not mac:
        return jsonify({"error": "No MAC"}), 400
    sec = SecurityMonitor()
    if not sec.block_device(mac):
        return jsonify({"error": "MAC inconnue"}), 404
    for d in current_state["alerts"]:
        if d.get('mac') == mac:
            d['blocked'] = True
            d['trusted'] = False
    return jsonify({"status": "ok"})


@app.route('/unblock', methods=['POST'])
def unblock_device():
    """Lève le blocage : l'appareil redevient un intrus à trier."""
    mac = (request.json or {}).get('mac')
    if not mac:
        return jsonify({"error": "No MAC"}), 400
    sec = SecurityMonitor()
    if not sec.unblock_device(mac):
        return jsonify({"error": "MAC inconnue"}), 404
    for d in current_state["alerts"]:
        if d.get('mac') == mac:
            d['blocked'] = False
    return jsonify({"status": "ok"})


@app.route('/update_settings', methods=['POST'])
def update_settings():
    try:
        with open(CONFIG_FILE, 'w') as f: json.dump(request.json, f)
        return jsonify({"status": "ok"})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/rename', methods=['POST'])
def rename_device():
    """Donne un nom personnalise a un appareil connu ({mac, name})."""
    payload = request.json or {}
    mac = payload.get('mac')
    name = (payload.get('name') or '').strip()
    if not mac or not name:
        return jsonify({"error": "mac et name requis"}), 400
    sec = SecurityMonitor()
    if not sec.rename_device(mac, name):
        return jsonify({"error": "MAC inconnue"}), 404
    # Mise a jour memoire immediate pour reactivite client
    for lst in (current_state["devices"], current_state["alerts"]):
        for d in lst:
            if d.get('mac') == mac:
                d['custom_name'] = name
    return jsonify({"status": "ok"})


@app.route('/link', methods=['POST'])
def link_device():
    """Re-identification : confirme qu'une nouvelle MAC est un appareil connu.
    Corps : {mac (nouvelle), source_mac (appareil de confiance existant)}."""
    payload = request.json or {}
    mac = payload.get('mac')
    source_mac = payload.get('source_mac')
    if not mac or not source_mac:
        return jsonify({"error": "mac et source_mac requis"}), 400
    sec = SecurityMonitor()
    if not sec.link_device(mac, source_mac):
        return jsonify({"error": "MAC inconnue"}), 404
    # Sort l'appareil des alertes en memoire (reactivite client)
    linked_name = sec._effective_name(sec.known_devices[mac])
    for d in list(current_state["alerts"]):
        if d.get('mac') == mac:
            d['trusted'] = True
            d['custom_name'] = linked_name
            current_state["alerts"].remove(d)
            if d not in current_state["devices"]:
                current_state["devices"].append(d)
    return jsonify({"status": "ok"})


@app.route('/scan_now', methods=['POST'])
def scan_now():
    """Declenche immediatement un cycle de scan (sans attendre l'intervalle)."""
    scan_request.set()
    return jsonify({"status": "scan demande"})


@app.route('/history', methods=['GET'])
def get_history():
    if os.path.exists(HISTORY_FILE):
        try: return pd.read_csv(HISTORY_FILE).tail(30).to_json(orient="records")
        except (OSError, pd.errors.ParserError) as e:
            print(f"[ERREUR] Historique illisible : {e}")
    return jsonify([])

if __name__ == '__main__':
    threading.Thread(target=background_scan_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5050)
