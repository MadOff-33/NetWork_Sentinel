# Fichier : main.py
# Encodage : utf-8

from src.gui_app import NetworkSentinelApp
import sys

# Désactivation des logs console inutiles pour l'app
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

if __name__ == "__main__":
    try:
        print("Lancement de l'interface graphique...")
        app = NetworkSentinelApp()
        app.mainloop()
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        print(f"Erreur critique au lancement : {e}")
        input("Appuyez sur Entrée pour fermer...")