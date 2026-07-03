# Fichier : src/security.py
# Encodage : utf-8

import json
import os
from datetime import datetime

class SecurityMonitor:
    def __init__(self, data_path="data/known_devices.json"):
        self.data_path = data_path
        self.known_devices = self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    for mac, info in data.items():
                        info['mac'] = mac
                        # Par défaut, les anciens sont considérés comme approuvés
                        if 'trusted' not in info: info['trusted'] = True 
                    return data
            except: return {}
        return {}

    def _save_data(self):
        try:
            with open(self.data_path, 'w') as f:
                json.dump(self.known_devices, f, indent=4)
        except Exception as e:
            print(f"Erreur sauvegarde JSON: {e}")

    def trust_device(self, mac):
        """Valide un appareil comme étant sûr."""
        if mac in self.known_devices:
            self.known_devices[mac]['trusted'] = True
            self._save_data()
            return True
        return False

    def analyze_intrusions(self, current_scan_results):
        new_devices = []
        known_list = []

        for device in current_scan_results:
            mac = device['mac']
            ip = device['ip']
            
            # Cas 1 : Jamais vu -> Création en mode NON APPROUVÉ
            if mac not in self.known_devices:
                device_info = {
                    "ip": ip,
                    "mac": mac,
                    "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "trusted": False, # NOUVEAU ! Il doit être validé manuellement
                    "status": "NEW"
                }
                self.known_devices[mac] = device_info
                new_devices.append(device_info)
            
            # Cas 2 : Déjà vu
            else:
                self.known_devices[mac]['last_seen'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.known_devices[mac]['ip'] = ip
                self.known_devices[mac]['mac'] = mac
                
                # Si l'appareil n'est pas "Trusted", il reste dans les "Nouveaux"
                if not self.known_devices[mac].get('trusted', False):
                    new_devices.append(self.known_devices[mac])
                else:
                    known_list.append(self.known_devices[mac])

        self._save_data()
        return new_devices, known_list