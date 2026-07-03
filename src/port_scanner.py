# Fichier : src/port_scanner.py
# Encodage : utf-8

import socket

class PortScanner:
    def __init__(self):
        # Dictionnaire COMPLET : Risque + Description Pédagogique
        self.port_info = {
            20: {"name": "FTP Data", "risk": 2, "desc": "Transfert de fichiers (Obsolète)."},
            21: {"name": "FTP Control", "risk": 2, "desc": "Commande transfert fichiers (Mots de passe en clair)."},
            22: {"name": "SSH", "risk": 1, "desc": "Accès distant sécurisé (Admin)."},
            23: {"name": "Telnet", "risk": 2, "desc": "Accès distant NON sécurisé (Dangereux)."},
            25: {"name": "SMTP", "risk": 1, "desc": "Envoi d'emails."},
            53: {"name": "DNS", "risk": 0, "desc": "Serveur de noms (Normal sur une Box)."},
            80: {"name": "HTTP", "risk": 0, "desc": "Serveur Web (Interface Box/Caméra)."},
            110: {"name": "POP3", "risk": 1, "desc": "Emails ancien protocole."},
            139: {"name": "NetBIOS", "risk": 1, "desc": "Partage fichiers Windows (Local)."},
            143: {"name": "IMAP", "risk": 1, "desc": "Emails."},
            443: {"name": "HTTPS", "risk": 0, "desc": "Web Sécurisé (Standard)."},
            445: {"name": "SMB", "risk": 1, "desc": "Partage Windows/Imprimante (Critique si exposé internet)."},
            3306: {"name": "MySQL", "risk": 1, "desc": "Base de données."},
            3389: {"name": "RDP", "risk": 2, "desc": "Bureau à distance Windows (Cible de virus)."},
            8080: {"name": "HTTP-Alt", "risk": 0, "desc": "Web alternatif (Souvent administration)."},
            554: {"name": "RTSP", "risk": 0, "desc": "Flux Vidéo (Caméras IP)."}
        }

    def quick_scan(self, ip):
        """Scan ultra-rapide (juste les numéros) pour l'automatisation."""
        open_ports = []
        for port in self.port_info.keys():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.2) # Timeout très court
                if s.connect_ex((ip, port)) == 0:
                    open_ports.append(port)
                s.close()
            except OSError:
                pass
        return open_ports

    def scan_device(self, ip):
        """Scan détaillé avec explications textuelles (Pour la Popup)."""
        results_text = []
        # On réutilise le quick_scan pour trouver les ports, puis on formate le texte
        open_ports = self.quick_scan(ip)

        if not open_ports:
            return []

        for port in open_ports:
            info = self.port_info.get(port, {"name": "Inconnu", "desc": "Non identifié", "risk": 0})

            # Emoji selon le risque
            if info['risk'] == 2: icon = "⛔ DANGER"
            elif info['risk'] == 1: icon = "⚠️ ATTENTION"
            else: icon = "✅ INFO"

            message = (
                f"🔓 [PORT {port}] : {info['name']}\n"
                f"   📝 {info['desc']}\n"
                f"   🛡️ Niveau : {icon}\n"
                f"   {'-'*30}"
            )
            results_text.append(message)

        return results_text

    def assess_risk(self, open_ports):
        """Calcule la couleur du bouton selon les ports trouvés."""
        max_risk = 0
        details = []

        for p in open_ports:
            info = self.port_info.get(p, {"risk": 0, "name": "Inconnu"})
            if info["risk"] > max_risk:
                max_risk = info["risk"]
            details.append(str(p))

        if not open_ports:
            return "green", "Sécurisé", 0

        if max_risk == 2:
            return "#ff4444", f"DANGER: {','.join(details)}", 2 # Rouge
        elif max_risk == 1:
            return "#ffbb33", f"ATTENTION: {','.join(details)}", 1 # Orange
        else:
            return "#00ff88", f"Ports: {','.join(details)}", 0 # Vert
