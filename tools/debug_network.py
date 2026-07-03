import scapy.all as scapy
import socket

print("=== DIAGNOSTIC RÉSEAU ===")

# 1. Ce que Scapy voit par défaut
try:
    iface = scapy.conf.iface
    ip_scapy = scapy.get_if_addr(iface)
    print(f"[SCAPY] Interface utilisée : {iface}")
    print(f"[SCAPY] IP sur cette interface : {ip_scapy}")
except Exception as e:
    print(f"[SCAPY] Erreur : {e}")

# 2. La vraie route vers Internet (La méthode la plus fiable)
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # On fait semblant de se connecter à Google (8.8.8.8) pour voir quelle carte réseau répond
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    print(f"[SYSTÈME] IP Locale réelle (vers Internet) : {local_ip}")
except Exception as e:
    print(f"[SYSTÈME] Impossible de déterminer l'IP locale : {e}")

print("=========================")
