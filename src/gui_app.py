# Fichier : src/gui_app.py (CLIENT V5 - STABLE)
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import json
import os
import sys
import requests
import pandas as pd
from tkinter import messagebox

try:
    import winshell
except ImportError:
    winshell = None

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class NetworkSentinelApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Network Sentinel Pro - Centre de Contrôle")
        self.geometry("1280x850")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.auto_monitor_active = False
        self.nas_ip = "192.168.1.100"
        self.load_local_config()

        # --- GAUCHE ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="NETWORK\nSENTINEL NAS", font=("Arial", 24, "bold"), text_color="#00aaff").pack(pady=(30, 20))
        
        self.btn_scan = ctk.CTkButton(self.sidebar, text="🔄 ACTUALISER", font=("Arial", 14, "bold"), height=45, fg_color="#0066cc", command=self.run_audit_thread)
        self.btn_scan.pack(pady=15, padx=20, fill="x")

        self.switch_auto = ctk.CTkSwitch(self.sidebar, text="Temps Réel (Auto)", command=self.toggle_monitoring)
        self.switch_auto.pack(pady=10)

        # Widget Perf
        self.monitor_frame = ctk.CTkFrame(self.sidebar, fg_color="#1a1a1a")
        self.monitor_frame.pack(pady=20, padx=15, fill="x")
        ctk.CTkLabel(self.monitor_frame, text="LIVE PERF (NAS)", font=("Arial", 11, "bold"), text_color="gray").pack(pady=10)
        
        self.lbl_ping = ctk.CTkLabel(self.monitor_frame, text="-- ms", font=("Arial", 24, "bold"), text_color="#ffcc00"); self.lbl_ping.pack()
        self.lbl_down = ctk.CTkLabel(self.monitor_frame, text="-- Mb", font=("Arial", 24, "bold"), text_color="#00ff88"); self.lbl_down.pack()
        self.lbl_up = ctk.CTkLabel(self.monitor_frame, text="-- Mb", font=("Arial", 20, "bold"), text_color="#00aaff"); self.lbl_up.pack()

        self.lbl_status = ctk.CTkLabel(self.sidebar, text="Connexion...", text_color="gray")
        self.lbl_status.pack(side="bottom", pady=20)

        # --- DROITE ---
        self.main_view = ctk.CTkTabview(self)
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)

        self.tab_dashboard = self.main_view.add("Tableau de Bord")
        self.tab_history = self.main_view.add("Historique Graphique")
        self.tab_settings = self.main_view.add("Paramètres")

        # Onglets Appareils
        self.device_tabs = ctk.CTkTabview(self.tab_dashboard)
        self.device_tabs.pack(fill="both", expand=True)
        self.tab_known = self.device_tabs.add("APPAREILS CONNUS")
        self.tab_new = self.device_tabs.add("⚠️ INTRUS / NOUVEAUX")
        
        self._setup_list(self.tab_known, "known_list")
        self._setup_list(self.tab_new, "unknown_list")

        # Graphique
        self.history_frame = ctk.CTkFrame(self.tab_history)
        self.history_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.fig = Figure(dpi=100, facecolor='#2b2b2b')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2b2b2b')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.history_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Paramètres
        self._setup_settings()
        
        if self.check_startup(): self.switch_startup.select()
        self.after(1000, self.run_audit_thread)

    def _setup_list(self, parent, attr_name):
        f = ctk.CTkScrollableFrame(parent)
        f.pack(fill="both", expand=True)
        setattr(self, attr_name, f)

    def _setup_settings(self):
        f = ctk.CTkScrollableFrame(self.tab_settings)
        f.pack(fill="both", expand=True, padx=20, pady=20)
        
        # IP NAS
        ctk.CTkLabel(f, text="IP DU NAS", font=("Arial", 16, "bold")).pack(pady=10)
        self.entry_ip = ctk.CTkEntry(f, width=200); self.entry_ip.pack()
        self.entry_ip.insert(0, self.nas_ip)
        
        # Intervalle
        ctk.CTkLabel(f, text="FRÉQUENCE DE SCAN (Secondes)", font=("Arial", 16, "bold")).pack(pady=(20,5))
        self.entry_interval = ctk.CTkEntry(f, width=100); self.entry_interval.pack()
        self.entry_interval.insert(0, "30")
        
        # Email (RESTAURÉ)
        ctk.CTkLabel(f, text="CONFIGURATION EMAIL", font=("Arial", 16, "bold")).pack(pady=(20,5))
        self.entry_smtp = ctk.CTkEntry(f, placeholder_text="Serveur SMTP (ex: smtp.gmail.com)", width=300); self.entry_smtp.pack(pady=5)
        self.entry_port = ctk.CTkEntry(f, placeholder_text="Port (ex: 587)", width=300); self.entry_port.pack(pady=5)
        self.entry_user = ctk.CTkEntry(f, placeholder_text="Email Utilisateur", width=300); self.entry_user.pack(pady=5)
        self.entry_pwd = ctk.CTkEntry(f, placeholder_text="Mot de passe d'application", width=300, show="*"); self.entry_pwd.pack(pady=5)
        self.entry_dest = ctk.CTkEntry(f, placeholder_text="Destinataire(s)", width=300); self.entry_dest.pack(pady=5)

        ctk.CTkButton(f, text="💾 APPLIQUER SUR LE NAS", command=self.push_settings, fg_color="green", height=40).pack(pady=30)
        
        # Démarrage
        ctk.CTkLabel(f, text="SYSTÈME PC", font=("Arial", 16, "bold")).pack(pady=10)
        self.switch_startup = ctk.CTkSwitch(f, text="Lancer au démarrage", command=self.toggle_startup)
        self.switch_startup.pack()

    def run_audit_thread(self):
        threading.Thread(target=self.process_nas_data).start()

    def process_nas_data(self):
        try:
            self.nas_ip = self.entry_ip.get()
            r = requests.get(f"http://{self.nas_ip}:5050/status", timeout=5)
            if r.status_code == 200:
                data = r.json()
                
                # Mise à jour GUI (Thread Safe)
                self.after(0, lambda: self.update_full_ui(data))
                
                # Graphique (Automatique)
                try:
                    h_r = requests.get(f"http://{self.nas_ip}:5050/history", timeout=2)
                    if h_r.status_code == 200:
                        self.after(0, lambda: self.update_graph(h_r.json()))
                except: pass

            else:
                self.lbl_status.configure(text=f"Erreur NAS: {r.status_code}", text_color="orange")

        except Exception as e:
            self.lbl_status.configure(text="NAS Injoignable", text_color="red")
        
        self.after(0, lambda: self.btn_scan.configure(state="normal"))

    def update_full_ui(self, data):
        # 1. Mise à jour PERF (Correction de l'affichage)
        p = data.get("performance", {})
        self.lbl_ping.configure(text=f"{p.get('ping_ms',0)} ms")
        self.lbl_down.configure(text=f"{p.get('download_mbps',0)} Mb")
        self.lbl_up.configure(text=f"{p.get('upload_mbps',0)} Mb")

        # 2. Mise à jour LISTES (Correction du CRASH NameError)
        all_devs = data.get("devices", [])
        alerts = data.get("alerts", [])
        alert_macs = [d['mac'] for d in alerts]
        
        # La variable correcte est 'known_devs'
        known_devs = [d for d in all_devs if d['mac'] not in alert_macs]

        # Status
        if alerts:
            self.lbl_status.configure(text=f"⚠️ {len(alerts)} INTRUS !", text_color="red")
            self.device_tabs._segmented_button.configure(selected_color="#AA0000")
        else:
            self.lbl_status.configure(text=f"✅ Sécurisé (MàJ: {data.get('last_update','?')})", text_color="#00ff88")
            self.device_tabs._segmented_button.configure(selected_color=["#3a7ebf", "#1f538d"])

        # Nettoyage Tableaux
        for w in self.known_list.winfo_children(): w.destroy()
        for w in self.unknown_list.winfo_children(): w.destroy()

        def add_line(parent, dev, is_new):
            row = ctk.CTkFrame(getattr(self, parent))
            row.pack(fill="x", pady=2)
            
            name = dev.get('name', 'Inconnu')
            
            ctk.CTkLabel(row, text=dev.get('ip','?'), width=110, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=dev.get('mac','?'), width=130, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(name)[:25], width=180, anchor="w", font=("Arial", 12, "bold")).pack(side="left")

            if is_new:
                ctk.CTkButton(row, text="BLOQUER", fg_color="#cc0000", width=80,
                              command=lambda: messagebox.showwarning("Bloquer", f"Ajoutez {dev['mac']} à la liste noire de votre Box.")).pack(side="right", padx=5)
                ctk.CTkButton(row, text="VALIDER", fg_color="green", width=80,
                              command=lambda: self.authorize_device(dev['mac'])).pack(side="right", padx=5)

        # Utilisation des bonnes variables
        for d in known_devs: add_line("known_list", d, False)
        for d in alerts: add_line("unknown_list", d, True)

    def update_graph(self, data):
        if not data: return
        df = pd.DataFrame(data)
        self.ax.clear()
        self.ax.grid(True, linestyle='-', color='#555', alpha=0.5)
        if 'download_mbps' in df.columns:
            self.ax.plot(df.index, df['download_mbps'], label='Down', color='#00ff88')
            self.ax.plot(df.index, df['upload_mbps'], label='Up', color='#00aaff')
        self.ax.legend(loc='upper left', fontsize='small')
        self.ax.tick_params(colors='white')
        self.canvas.draw()

    def authorize_device(self, mac):
        try:
            requests.post(f"http://{self.nas_ip}:5050/authorize", json={"mac": mac})
            self.after(500, self.run_audit_thread) 
        except Exception as e: messagebox.showerror("Erreur", str(e))

    def push_settings(self):
        try:
            cfg = {
                "scan_interval": int(self.entry_interval.get()),
                "email_enabled": True,
                "smtp_server": self.entry_smtp.get(),
                "smtp_port": int(self.entry_port.get()),
                "smtp_user": self.entry_user.get(),
                "smtp_password": self.entry_pwd.get(),
                "alert_emails": self.entry_dest.get().split(",")
            }
            requests.post(f"http://{self.nas_ip}:5050/update_settings", json=cfg)
            messagebox.showinfo("Succès", "Réglage appliqué sur le NAS !")
        except Exception as e: messagebox.showerror("Erreur", f"Erreur envoi NAS: {e}")

    def toggle_monitoring(self):
        self.auto_monitor_active = bool(self.switch_auto.get())
        if self.auto_monitor_active: self.monitor_loop()

    def monitor_loop(self):
        if not self.auto_monitor_active: return
        self.run_audit_thread()
        try: sec = int(self.entry_interval.get())
        except: sec = 30
        self.after(sec * 1000, self.monitor_loop)

    def load_local_config(self):
        try:
            with open("client_config.json", "r") as f:
                self.nas_ip = json.load(f).get("nas_ip", "192.168.1.100")
        except: pass

    def check_startup(self):
        return winshell and os.path.exists(os.path.join(winshell.startup(), "NetworkSentinelClient.lnk"))
    def toggle_startup(self):
        if not winshell: return
        link = os.path.join(winshell.startup(), "NetworkSentinelClient.lnk")
        if self.switch_startup.get(): winshell.shortcut(link).path = sys.executable
        elif os.path.exists(link): os.remove(link)

if __name__ == "__main__":
    app = NetworkSentinelApp()
    app.mainloop()