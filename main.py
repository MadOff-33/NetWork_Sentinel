# Fichier : main.py
# Encodage : utf-8

from src.ui import ConsoleUI
from src.scanner import NetworkScanner
import sys

def main():
    # 1. Nettoyage et Titre
    ConsoleUI.clear_screen()
    ConsoleUI.header("NETWORK SENTINEL 2025")

    # 2. Configuration
    # Pour l'instant on hardcode, plus tard on rendra ça dynamique ou auto-détecté
    target_ip = "192.168.1.1/24" 
    
    # 3. Scan du Réseau
    scanner = NetworkScanner(ip_range=target_ip)
    devices = scanner.scan()

    # 4. Affichage des résultats
    if devices:
        # Préparation des données pour le tableau
        table_data = [[d['ip'], d['mac'], "En ligne"] for d in devices]
        headers = ["Adresse IP", "Adresse MAC", "État"]
        
        ConsoleUI.display_table(table_data, headers)
    else:
        ConsoleUI.log_warning("Aucun appareil trouvé. Vérifiez votre connexion ou vos droits d'administrateur.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nArrêt utilisateur.")
        sys.exit()# Fichier : main.py
