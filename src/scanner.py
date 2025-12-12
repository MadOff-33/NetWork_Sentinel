# Fichier : scanner.py
# Encodage : utf-8

import scapy.all as scapy
from src.ui import ConsoleUI

class NetworkScanner:
    def __init__(self, ip_range="192.168.1.1/24"):
        """
        Initialise le scanner.
        :param ip_range: Plage IP à scanner (ex: 192.168.1.1/24)
        """
        self.ip_range = ip_range

    def scan(self):
        """
        Envoie des requêtes ARP pour découvrir les hôtes actifs.
        Retourne une liste de dictionnaires.
        """
        ConsoleUI.log_info(f"Démarrage du scan ARP sur {self.ip_range}...")
        
        try:
            # 1. Création du paquet ARP
            arp_request = scapy.ARP(pdst=self.ip_range)
            # 2. Création de la trame Ethernet de diffusion (Broadcast)
            broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
            # 3. Combinaison des deux
            arp_request_broadcast = broadcast / arp_request
            
            # 4. Envoi et réception (verbose=0 pour éviter le spam scapy)
            # timeout=1 évite de bloquer indéfiniment
            answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=0)[0]
            
            devices_list = []
            
            # 5. Traitement des réponses
            for sent, received in answered_list:
                device = {
                    "ip": received.psrc,
                    "mac": received.hwsrc
                }
                devices_list.append(device)
            
            ConsoleUI.log_success(f"Scan terminé. {len(devices_list)} appareils trouvés.")
            return devices_list

        except Exception as e:
            ConsoleUI.log_error(f"Erreur lors du scan : {str(e)}")
            return []