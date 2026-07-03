# Fichier : src/notifier.py
# Encodage : utf-8

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    content = f.read().strip()
                    if not content: return None
                    f.seek(0)
                    return json.load(f)
            except: return None
        return None

    def send_alert(self, new_devices):
        if not self.config or not self.config.get("email_enabled", False):
            return False

        try:
            # Récupération sécurisée des données
            sender_email = self.config.get("smtp_user")
            password = self.config.get("smtp_password")
            smtp_server = self.config.get("smtp_server")
            smtp_port = self.config.get("smtp_port")
            
            # Gestion destinataires (Liste ou unique)
            recipients = self.config.get("alert_emails")
            if not recipients:
                # Fallback sur l'ancien nom de variable au cas où
                recipients = self.config.get("alert_email")
            
            if isinstance(recipients, str):
                recipients = [recipients]

            if not all([sender_email, recipients, password, smtp_server]):
                print("[ERREUR CONFIG] Paramètres email manquants.")
                return False

            # Construction du mail
            msg = MIMEMultipart()
            msg['From'] = "Network Sentinel <" + sender_email + ">"
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = f"🚨 ALERTE INTRUSION : {len(new_devices)} Appareil(s)"

            body = "Nouveaux appareils détectés sur le réseau :\n\n"
            for dev in new_devices:
                body += f"- IP: {dev.get('ip')} | MAC: {dev.get('mac')} | Nom: {dev.get('name', 'Inconnu')}\n"
            
            msg.attach(MIMEText(body, 'plain'))

            # Envoi SMTP
            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, recipients, msg.as_string())
            server.quit()
            print(f"[EMAIL] Alerte envoyée à {len(recipients)} destinataire(s).")
            return True

        except Exception as e:
            print(f"[EMAIL] Erreur technique : {e}")
            return False