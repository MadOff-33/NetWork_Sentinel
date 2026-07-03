# Fichier : main_standalone.py
# Network Sentinel — ÉDITION AUTONOME (tout sur le PC, aucun NAS requis).
#
# Principe : on démarre le serveur (scan ARP + API Flask) en local sur
# 127.0.0.1:5050, puis on lance l'interface graphique par-dessus, pointée
# sur localhost. On réutilise ainsi tout le code déjà testé (server + client).
#
# Nécessite Npcap installé et des droits administrateur (scan ARP brut).

import os
import sys
import threading
import time

# --- Données écrites À CÔTÉ de l'exe (pas dans /app/data du conteneur) ---
os.environ.setdefault("DATA_DIR", os.path.join(os.getcwd(), "data"))

# --- Correctif flux standards en mode fenêtré (--noconsole) ---
for _name, _mode in (("stdin", "r"), ("stdout", "w"), ("stderr", "w")):
    if getattr(sys, _name) is None:
        try:
            setattr(sys, _name, open(os.devnull, _mode))
        except OSError:
            pass

from src.logger import get_logger

log = get_logger("standalone")


def start_local_server():
    """Serveur Flask + boucle de scan, en local uniquement (127.0.0.1)."""
    try:
        import server.server as srv
        threading.Thread(target=srv.background_scan_loop, daemon=True).start()
        srv.app.run(host="127.0.0.1", port=5050, threaded=True, use_reloader=False)
    except Exception as e:  # noqa: BLE001 - on ne veut jamais tuer l'appli
        log.error("Serveur local en echec : %s", e)


def ensure_local_config():
    """Config client pointée sur le serveur embarqué (localhost, sans token)."""
    import json
    if not os.path.exists("client_config.json"):
        try:
            with open("client_config.json", "w") as f:
                json.dump({"nas_ip": "127.0.0.1", "api_token": ""}, f, indent=4)
        except OSError as e:
            log.warning("Ecriture client_config.json impossible : %s", e)


def main():
    log.info("Demarrage en mode autonome (serveur embarque)")
    threading.Thread(target=start_local_server, daemon=True).start()
    time.sleep(1.2)  # laisse Flask se lier au port

    ensure_local_config()

    from src.gui_app import NetworkSentinelApp
    app = NetworkSentinelApp()
    app.title("Network Sentinel — Édition Autonome")
    app.mainloop()


if __name__ == "__main__":
    main()
