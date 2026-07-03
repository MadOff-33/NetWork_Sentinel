# Fichier : src/security.py
# Encodage : utf-8

import json
import os
from datetime import datetime

from src.logger import get_logger

log = get_logger("security")


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
                        if 'trusted' not in info:
                            info['trusted'] = True
                    return data
            except (OSError, json.JSONDecodeError) as e:
                log.error("Lecture de %s impossible (%s) : base repartie de zero", self.data_path, e)
                return {}
        return {}

    def _save_data(self):
        try:
            os.makedirs(os.path.dirname(self.data_path) or ".", exist_ok=True)
            with open(self.data_path, 'w') as f:
                json.dump(self.known_devices, f, indent=4)
        except OSError as e:
            log.error("Sauvegarde de %s impossible : %s", self.data_path, e)

    def trust_device(self, mac):
        """Valide un appareil comme étant sûr."""
        if mac in self.known_devices:
            self.known_devices[mac]['trusted'] = True
            self._save_data()
            return True
        return False

    def rename_device(self, mac, custom_name):
        """Attribue un nom personnalisé (ex: iphone17_mike). Jamais écrasé par les scans."""
        if mac in self.known_devices and custom_name and custom_name.strip():
            self.known_devices[mac]['custom_name'] = custom_name.strip()
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
                    "name": device.get("name", "Inconnu"),
                    "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "trusted": False,  # Doit être validé manuellement
                    "status": "NEW"
                }
                self.known_devices[mac] = device_info
                new_devices.append(device_info)
                log.info("Nouvel appareil detecte : %s (%s)", mac, ip)

            # Cas 2 : Déjà vu
            else:
                entry = self.known_devices[mac]
                entry['last_seen'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                entry['ip'] = ip
                entry['mac'] = mac
                # Le nom issu du scan (hostname/fabricant) ne remplace le nom
                # stocké que s'il apporte une vraie information.
                # 'custom_name' (choisi par l'utilisateur) n'est JAMAIS touché.
                scanned_name = device.get('name')
                if scanned_name and scanned_name not in ("Inconnu", "?") \
                        and entry.get('name') in (None, "", "Inconnu", "?"):
                    entry['name'] = scanned_name

                # Si l'appareil n'est pas "Trusted", il reste dans les "Nouveaux"
                if not self.known_devices[mac].get('trusted', False):
                    new_devices.append(self.known_devices[mac])
                else:
                    known_list.append(self.known_devices[mac])

        self._save_data()
        return new_devices, known_list
