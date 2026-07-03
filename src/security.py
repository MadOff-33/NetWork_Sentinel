# Fichier : src/security.py
# Encodage : utf-8

import json
import os
import re
from datetime import datetime

from src.logger import get_logger

log = get_logger("security")

# Champs calculés à la volée, jamais écrits dans known_devices.json
_TRANSIENT_KEYS = ("suggested_match",)


def _normalize_name(name):
    """Ramene un nom reseau a sa racine comparable :
    'Galaxy-A12-1.home' -> 'galaxy-a12'. Retourne '' si non significatif."""
    if not name:
        return ""
    n = name.strip().lower()
    for suffix in (".home", ".lan", ".local"):
        if n.endswith(suffix):
            n = n[:-len(suffix)]
    n = re.sub(r"-\d+$", "", n)  # suffixe DHCP (-1, -2...)
    if n in ("", "inconnu", "?"):
        return ""
    return n


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
            # On retire les champs transitoires (suggestions) avant sauvegarde
            clean = {
                mac: {k: v for k, v in info.items() if k not in _TRANSIENT_KEYS}
                for mac, info in self.known_devices.items()
            }
            with open(self.data_path, 'w') as f:
                json.dump(clean, f, indent=4)
        except OSError as e:
            log.error("Sauvegarde de %s impossible : %s", self.data_path, e)

    @staticmethod
    def _effective_name(entry):
        """Nom affiché : personnalisé s'il existe, sinon nom résolu par le scan."""
        return entry.get("custom_name") or entry.get("name") or ""

    def _find_trusted_match(self, scanned_name, exclude_mac):
        """Cherche un appareil DE CONFIANCE au même nom (MAC différente).
        Retourne {'mac', 'name'} ou None. Sert à repérer les MAC aléatoires."""
        target = _normalize_name(scanned_name)
        if not target:
            return None
        for mac, entry in self.known_devices.items():
            if mac == exclude_mac or not entry.get("trusted"):
                continue
            # On compare au hostname réseau d'origine ('name') ET au nom
            # personnalisé : le hostname reste stable même après renommage.
            candidates = {_normalize_name(entry.get("name")),
                          _normalize_name(entry.get("custom_name"))}
            if target in candidates and target:
                return {"mac": mac, "name": self._effective_name(entry)}
        return None

    def link_device(self, new_mac, source_mac):
        """Confirme qu'une nouvelle MAC est le même appareil que source_mac :
        la nouvelle MAC devient de confiance et hérite du nom."""
        if new_mac in self.known_devices and source_mac in self.known_devices:
            name = self._effective_name(self.known_devices[source_mac])
            self.known_devices[new_mac]['trusted'] = True
            if name:
                self.known_devices[new_mac]['custom_name'] = name
            self._save_data()
            log.info("Re-identification : %s rattache a %s (%s)", new_mac, source_mac, name)
            return True
        return False

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
                # Suggestion de re-identification (champ transitoire, non sauvegardé)
                match = self._find_trusted_match(device.get("name"), exclude_mac=mac)
                if match:
                    device_info["suggested_match"] = match
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
