# Fichier : src/gui_app.py
# Encodage : utf-8

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import socket
import json
import os
import sys
import pandas as pd
from tkinter import messagebox
from concurrent.futures import ThreadPoolExecutor

# Import Modules
from src.scanner import NetworkScanner
from src.security import SecurityMonitor
from src.analyzer import NetworkAnalyzer
from src.port_scanner import PortScanner
from src.notifier import EmailNotifier

# Pour la gestion des raccourcis Windows
try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    winshell = None # Fallback si non installé

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class NetworkSentinelApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CONFIGURATION FENÊTRE ---
        self.title("Network Sentinel Pro 2025")
        self.geometry("1280x850")
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.auto_monitor_active = False
        self.monitor_interval = 3600 
        self.scan_cache = {} 
        self.device_buttons = {} 
        
        self.current_new_devs = []
        self.current_known_devs = []

        # =================================================
        # 1. BARRE LATÉRALE (GAUCHE)
        # =================================================
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="NETWORK\nSENTINEL PRO", font=("Arial", 24, "bold"), text_color="#00aaff").pack(pady=(30, 20))
        
        self.btn_scan = ctk.CTkButton(self.sidebar, text="⚡ LANCER ANALYSE", font=("Arial", 14, "bold"), height=45, fg_color="#0066cc", hover_color="#0055aa", command=self.run_audit_thread)
        self.btn_scan.pack(pady=15, padx=20, fill="x")

        self.switch_auto = ctk.CTkSwitch(self.sidebar, text="Surveillance Auto", command=self.toggle_monitoring, font=("Arial", 12))
        self.switch_auto.pack(pady=10)

        # WIDGET LIVE MONITOR
        self.monitor_frame = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a", corner_radius=15, border_width=1, border_color="#333")
        self.monitor_frame.pack(pady=20, padx=15, fill="x")
        
        ctk.CTkLabel(self.monitor_frame, text="PERFORMANCES LIVE", font=("Arial", 11, "bold"), text_color="gray").pack(pady=(15, 10))
        
        self.lbl_ping_val = ctk.CTkLabel(self.monitor_frame, text="-- ms", font=("Arial", 28, "bold"), text_color="#ffcc00")
        self.lbl_ping_val.pack()
        ctk.CTkLabel(self.monitor_frame, text="Latence", font=("Arial", 10)).pack(pady=(0, 10))
        
        ctk.CTkFrame(self.monitor_frame, height=1, fg_color="#444").pack(fill="x", padx=20, pady=5)

        self.lbl_down_val = ctk.CTkLabel(self.monitor_frame, text="-- Mb", font=("Arial", 28, "bold"), text_color="#00ff88")
        self.lbl_down_val.pack()
        ctk.CTkLabel(self.monitor_frame, text="Download", font=("Arial", 10)).pack(pady=(0, 10))

        # AJOUT : Type de connexion détecté
        self.lbl_conn_type = ctk.CTkLabel(self.monitor_frame, text="Analyse requise...", font=("Arial", 11, "italic"), text_color="gray")
        self.lbl_conn_type.pack(pady=(0, 5))

        self.lbl_up_val = ctk.CTkLabel(self.monitor_frame, text="-- Mb", font=("Arial", 22, "bold"), text_color="#00aaff")
        self.lbl_up_val.pack()
        ctk.CTkLabel(self.monitor_frame, text="Upload", font=("Arial", 10)).pack(pady=(0, 15))

        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Système Prêt", text_color="gray", font=("Arial", 11))
        self.lbl_status.pack(side="bottom", pady=20)

        # =================================================
        # 2. ZONE PRINCIPALE (DROITE)
        # =================================================
        self.main_view = ctk.CTkTabview(self)
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)

        self.tab_dashboard = self.main_view.add("Tableau de Bord")
        self.tab_history = self.main_view.add("Historique & Graphiques")
        self.tab_settings = self.main_view.add("Paramètres")

        # DASHBOARD
        self.device_tabs = ctk.CTkTabview(self.tab_dashboard)
        self.device_tabs.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.name_tab_known = "Appareils Connus"
        self.name_tab_new = "Intrus / Nouveaux"
        
        self.tab_known = self.device_tabs.add(self.name_tab_known)
        self.tab_new = self.device_tabs.add(self.name_tab_new)
        
        self._setup_device_list(self.tab_known, "known_list")
        self._setup_device_list(self.tab_new, "unknown_list")

        # HISTORIQUE
        self.history_frame = ctk.CTkFrame(self.tab_history)
        self.history_frame.pack(fill="both", expand=True, padx=0, pady=0)
        ctk.CTkButton(self.tab_history, text="Actualiser Graphique", command=self.update_full_history).pack(pady=10)

        # PARAMÈTRES
        self._setup_settings_tab()
        
        # Chargement initial
        self.update_full_history()

    # ================= UI HELPERS =================

    def _setup_device_list(self, parent, list_attr):
        frame = ctk.CTkScrollableFrame(parent)
        frame.pack(fill="both", expand=True)
        header = ctk.CTkFrame(frame, height=35, fg_color="#333333")
        header.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(header, text="IP", width=130, anchor="w", font=("Arial", 13, "bold"), text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="MAC", width=150, anchor="w", font=("Arial", 13, "bold"), text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="NOM", width=180, anchor="w", font=("Arial", 13, "bold"), text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(header, text="ACTIONS & ÉTAT", width=200, anchor="w", font=("Arial", 13, "bold"), text_color="white").pack(side="left", padx=5)
        setattr(self, list_attr, frame)

    def _setup_settings_tab(self):
        f = ctk.CTkScrollableFrame(self.tab_settings)
        f.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Section 0 : Démarrage Windows
        ctk.CTkLabel(f, text="Système", font=("Arial", 18, "bold")).pack(pady=(10, 5))
        self.switch_startup = ctk.CTkSwitch(f, text="Lancer automatiquement au démarrage de Windows", command=self.toggle_startup)
        self.switch_startup.pack(pady=10)

        # Section 1 : Surveillance
        ctk.CTkLabel(f, text="Fréquence de Surveillance", font=("Arial", 18, "bold")).pack(pady=(20, 5))
        self.entry_interval = ctk.CTkEntry(f, placeholder_text="Ex: 3600", width=150)
        self.entry_interval.pack(pady=5)
        ctk.CTkLabel(f, text="(Intervalle en Secondes)", text_color="gray", font=("Arial", 11)).pack(pady=(0, 10))

        # Section 2 : Emails
        ctk.CTkLabel(f, text="Configuration Alertes Email", font=("Arial", 18, "bold")).pack(pady=10)
        
        def fill_gmail():
            self.entry_server.delete(0, "end"); self.entry_server.insert(0, "smtp.gmail.com")
            self.entry_port.delete(0, "end"); self.entry_port.insert(0, "587")
            
        ctk.CTkButton(f, text="Pré-remplir pour GMAIL", command=fill_gmail, fg_color="gray").pack(pady=5)
        self.entry_server = ctk.CTkEntry(f, placeholder_text="SMTP", width=350); self.entry_server.pack(pady=5)
        self.entry_port = ctk.CTkEntry(f, placeholder_text="Port", width=350); self.entry_port.pack(pady=5)
        self.entry_email = ctk.CTkEntry(f, placeholder_text="Email", width=350); self.entry_email.pack(pady=5)
        self.entry_pwd = ctk.CTkEntry(f, placeholder_text="Mot de passe d'app", width=350, show="*"); self.entry_pwd.pack(pady=5)
        self.entry_dest = ctk.CTkEntry(f, placeholder_text="Destinataires", width=350); self.entry_dest.pack(pady=5)
        
        ctk.CTkButton(f, text="💾 SAUVEGARDER CONFIGURATION", command=self.save_settings, fg_color="green", height=40).pack(pady=30)

        # Section 3 : Reset
        ctk.CTkLabel(f, text="Zone de Danger", font=("Arial", 18, "bold"), text_color="#ff4444").pack(pady=(20, 10))
        ctk.CTkButton(f, text="⚠️ RÉINITIALISER LA BASE DE DONNÉES", command=self.reset_database, fg_color="#AA0000", hover_color="#880000", height=40).pack(pady=10)

        # Chargement
        try:
            with open("config.json", "r") as f:
                d = json.load(f)
                seconds = d.get("monitor_interval_seconds", 3600)
                self.monitor_interval = seconds
                self.entry_interval.insert(0, str(seconds))
                self.entry_server.insert(0, d.get("smtp_server", ""))
                self.entry_port.insert(0, str(d.get("smtp_port", "")))
                self.entry_email.insert(0, d.get("smtp_user", ""))
                self.entry_pwd.insert(0, d.get("smtp_password", ""))
                recipients = d.get("alert_emails", [])
                if isinstance(recipients, list): recipients = ",".join(recipients)
                self.entry_dest.insert(0, recipients)
                
                # Check startup
                if self.check_startup_status():
                    self.switch_startup.select()
        except: pass

    # ================= AUDIT =================

    def run_audit_thread(self):
        self.btn_scan.configure(state="disabled", text="Analyse...", fg_color="gray")
        self.lbl_status.configure(text="🚀 Démarrage...", text_color="#00aaff")
        self.lbl_ping_val.configure(text="...")
        self.lbl_down_val.configure(text="...")
        self.lbl_conn_type.configure(text="Analyse...")
        self.lbl_up_val.configure(text="...")
        threading.Thread(target=self.process_audit).start()

    def process_audit(self):
        try:
            self.update_status("Scan ARP...")
            scanner = NetworkScanner("192.168.1.1/24") 
            scan_results = scanner.scan()
            
            security = SecurityMonitor()
            new_devs, known_devs = security.analyze_intrusions(scan_results)
            
            all_devs = new_devs + known_devs
            for d in all_devs:
                if 'name' not in d: d['name'] = self.get_hostname(d['ip'])
            
            self.current_new_devs = new_devs
            self.current_known_devs = known_devs
            self.after(0, lambda: self.update_device_ui(self.current_new_devs, self.current_known_devs))
            
            self.update_status("Scan Ports...")
            self.run_parallel_port_scan(all_devs)

            self.update_status("Test Performance...")
            analyzer = NetworkAnalyzer()
            perf = analyzer.run_performance_test()
            
            self.after(0, lambda: self.display_metrics(perf))
            self.after(0, self.update_full_history)
            
            if new_devs:
                notifier = EmailNotifier()
                if notifier.config and notifier.config.get("email_enabled"):
                    notifier.send_alert(new_devs)

            self.after(0, self.finish_audit_ui)

        except Exception as e:
            print(f"Erreur Audit: {e}")
            self.after(0, self.finish_audit_ui)

    def run_parallel_port_scan(self, devices):
        scanner = PortScanner()
        def scan_one(device):
            ip = device['ip']
            ports = scanner.quick_scan(ip)
            color, msg, risk = scanner.assess_risk(ports)
            self.scan_cache[ip] = {'color': color, 'msg': msg}
            self.after(0, lambda: self.refresh_single_button(ip, color, msg))
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(scan_one, devices)

    def refresh_single_button(self, ip, color, msg):
        if ip in self.device_buttons:
            try: self.device_buttons[ip].configure(fg_color=color, text=msg)
            except: pass

    def trust_device(self, mac):
        sec = SecurityMonitor()
        sec.trust_device(mac)
        device_to_move = None
        for dev in self.current_new_devs:
            if dev['mac'] == mac:
                device_to_move = dev
                break
        if device_to_move:
            self.current_new_devs.remove(device_to_move)
            self.current_known_devs.append(device_to_move)
            self.update_device_ui(self.current_new_devs, self.current_known_devs)
            messagebox.showinfo("Autorisé", f"L'appareil {mac} est approuvé.")

    def update_device_ui(self, new_devs, known_devs):
        self.device_buttons = {} 
        for w in self.known_list.winfo_children(): w.destroy()
        for w in self.unknown_list.winfo_children(): w.destroy()

        if len(new_devs) > 0:
            self.device_tabs._segmented_button.configure(selected_color="#AA0000") 
            self.lbl_status.configure(text=f"⚠️ ALERTE : {len(new_devs)} INTRUS !", text_color="red")
        else:
            self.device_tabs._segmented_button.configure(selected_color=["#3a7ebf", "#1f538d"])
            if "ALERTE" in self.lbl_status.cget("text"):
                self.lbl_status.configure(text="Système sécurisé", text_color="gray")

        def add_row(parent, device, is_new):
            ip = device['ip']
            bg_color = self.scan_cache.get(ip, {}).get('color', 'gray')
            status_txt = self.scan_cache.get(ip, {}).get('msg', 'Analyse...')

            row = ctk.CTkFrame(getattr(self, parent))
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=ip, width=130, anchor="w", font=("Consolas", 12)).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=device['mac'], width=150, anchor="w", font=("Consolas", 11)).pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(device.get('name', '?'))[:20], width=180, anchor="w").pack(side="left", padx=5)
            
            if is_new:
                ctk.CTkButton(row, text="BLOQUER", fg_color="red", width=80, height=24, 
                              command=lambda: messagebox.showwarning("Bloquer", "Ajoutez cette MAC en liste noire sur votre Box.")).pack(side="right", padx=5)
                ctk.CTkButton(row, text="AUTORISER", fg_color="green", width=90, height=24, 
                              command=lambda: self.trust_device(device['mac'])).pack(side="right", padx=5)
            else:
                cmd = lambda: self.show_port_details(ip)
                btn = ctk.CTkButton(row, text=status_txt, fg_color=bg_color, width=140, height=24, command=cmd)
                btn.pack(side="right", padx=5)
                self.device_buttons[ip] = btn

        for d in known_devs: add_row("known_list", d, False)
        for d in new_devs: add_row("unknown_list", d, True)

    def display_metrics(self, perf):
        ping = perf.get('ping_ms', 0)
        down = perf.get('download_mbps', 0)
        up = perf.get('upload_mbps', 0)
        
        self.lbl_ping_val.configure(text=f"{ping} ms")
        self.lbl_down_val.configure(text=f"{down} Mb")
        self.lbl_up_val.configure(text=f"{up} Mb")
        
        # LOGIQUE DE COMPARAISON (BENCHMARK)
        conn_type = "Inconnu"
        color = "gray"
        
        if down < 5:
            conn_type = "ADSL (Très lent)"
            color = "#ff4444"
        elif down < 20:
            conn_type = "ADSL2+ / 4G (Moyen)"
            color = "#ffbb33"
        elif down < 100:
            conn_type = "VDSL2 / 4G+ / Starlink"
            color = "#00aaff"
        elif down < 500:
            conn_type = "FIBRE OPTIQUE (Standard)"
            color = "#00ff88"
        else:
            conn_type = "FIBRE OPTIQUE (Max Speed)"
            color = "#cc00ff"
            
        self.lbl_conn_type.configure(text=f"Type: {conn_type}", text_color=color)

    def show_port_details(self, ip):
        scanner = PortScanner()
        msg_list = scanner.scan_device(ip)
        details = "\n".join(msg_list) if msg_list else "Aucun port critique ouvert."
        messagebox.showinfo(f"Scan : {ip}", details)

    def update_full_history(self):
        csv_file = "data/network_history.csv"
        if not os.path.exists(csv_file): return
        try:
            df = pd.read_csv(csv_file)
            for w in self.history_frame.winfo_children(): w.destroy()
            fig = Figure(dpi=100, facecolor='#2b2b2b')
            ax = fig.add_subplot(111)
            ax.set_facecolor('#2b2b2b')
            ax.grid(True, linestyle='-', color='#555', alpha=0.5) 
            ax.plot(df.index, df['download_mbps'], label='Download', color='#00ff88', linewidth=2)
            ax.plot(df.index, df['upload_mbps'], label='Upload', color='#00aaff', linewidth=2)
            ax.plot(df.index, df['ping_ms'], label='Ping', color='#ffcc00', linestyle='--')
            ax.legend(loc='upper left'); ax.tick_params(colors='white')
            canvas = FigureCanvasTkAgg(fig, master=self.history_frame)
            canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)
        except: pass

    def get_hostname(self, ip):
        try: return socket.gethostbyaddr(ip)[0]
        except: return "Inconnu"

    def update_status(self, txt): self.lbl_status.configure(text=txt)

    def finish_audit_ui(self):
        self.btn_scan.configure(state="normal", text="⚡ LANCER ANALYSE", fg_color="#0066cc")
        if "ALERTE" not in self.lbl_status.cget("text"):
            self.lbl_status.configure(text="Prêt - Surveillance active", text_color="gray")

    # --- STARTUP LOGIC ---
    def get_startup_path(self):
        return os.path.join(winshell.startup(), "NetworkSentinel.lnk")

    def check_startup_status(self):
        if not winshell: return False
        return os.path.exists(self.get_startup_path())

    def toggle_startup(self):
        if not winshell:
            messagebox.showerror("Erreur", "Module 'winshell' manquant.\nImpossible de gérer le démarrage.")
            return

        link_path = self.get_startup_path()
        if self.switch_startup.get() == 1:
            # ACTIVER
            target = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath("main.py")
            # Si on est en .py, on lance via python
            if not getattr(sys, 'frozen', False):
                 # Logique complexe pour script py, on simplifie pour l'instant : focus sur EXE
                 target = sys.executable 
                 args = f'"{os.path.abspath("main.py")}"'
                 w_dir = os.getcwd()
            else:
                # Si on est en EXE
                target = sys.executable
                args = ""
                w_dir = os.path.dirname(sys.executable)

            try:
                with winshell.shortcut(link_path) as link:
                    link.path = target
                    link.arguments = args
                    link.working_directory = w_dir
                    link.description = "Network Sentinel Pro 2025"
                messagebox.showinfo("Succès", "Lancement automatique ACTIVÉ.")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec création raccourci : {e}")
        else:
            # DÉSACTIVER
            if os.path.exists(link_path):
                os.remove(link_path)
                messagebox.showinfo("Succès", "Lancement automatique DÉSACTIVÉ.")

    def save_settings(self):
        try: sec = int(self.entry_interval.get())
        except: return
        if sec < 10: return
        self.monitor_interval = sec
        d = {
            "email_enabled": True, "monitor_interval_seconds": sec,
            "smtp_server": self.entry_server.get(), "smtp_port": int(self.entry_port.get()),
            "smtp_user": self.entry_email.get(), "smtp_password": self.entry_pwd.get(),
            "alert_emails": self.entry_dest.get().split(",")
        }
        with open("config.json", "w") as f: json.dump(d, f, indent=4)
        messagebox.showinfo("OK", "Sauvegardé !")

    def toggle_monitoring(self):
        self.auto_monitor_active = bool(self.switch_auto.get())
        if self.auto_monitor_active: self.monitor_loop()

    def monitor_loop(self):
        if not self.auto_monitor_active: return
        self.run_audit_thread()
        self.after(self.monitor_interval * 1000, self.monitor_loop)

    def reset_database(self):
        if not messagebox.askyesno("Confirmation", "Effacer tout ?"): return
        try:
            if os.path.exists("data/known_devices.json"): os.remove("data/known_devices.json")
            if os.path.exists("data/network_history.csv"): os.remove("data/network_history.csv")
            self.scan_cache = {}; self.device_buttons = {}
            self.current_new_devs = []; self.current_known_devs = [] 
            for w in self.known_list.winfo_children(): w.destroy()
            for w in self.unknown_list.winfo_children(): w.destroy()
            for w in self.history_frame.winfo_children(): w.destroy()
            self.lbl_ping_val.configure(text="--"); self.lbl_down_val.configure(text="--"); self.lbl_up_val.configure(text="--")
            messagebox.showinfo("OK", "Base de données réinitialisée !")
        except Exception as e: messagebox.showerror("Erreur", str(e))

if __name__ == "__main__":
    app = NetworkSentinelApp()
    app.mainloop()