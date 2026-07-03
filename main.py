# Fichier : main.py
from src.gui_app import NetworkSentinelApp

if __name__ == "__main__":
    try:
        app = NetworkSentinelApp()
        app.mainloop()
    except Exception as e:
        print("Erreur critique au lancement :", e)
        input("Appuyez sur Entrée pour fermer...")