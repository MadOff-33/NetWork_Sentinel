# Fichier : src/gui_app.py — CLIENT (pilote le serveur NAS)
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

from src.logger import get_logger

try:
    import winshell
except ImportError:
    winshell = None

log = get_logger("client")

CLIENT_CONFIG_FILE = "client_config.json"
HTTP_TIMEOUT = 5

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
        self.api_token = ""
        self.notified_macs = set()  # intrus deja notifies (toast) cette session
        self.load_local_config()

        # --- GAUCHE ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="NETWORK\nSENTINEL NAS", font=("Arial", 24, "bold"), text_color="#00aaff").pack(pady=(30, 20))

        self.btn_scan = ctk.CTkButton(self.sidebar, text="🔄 ACTUALISER", font=("Arial", 14, "bold"),
                                      height=45, fg_color="#0066cc", command=self.run_audit_thread)
        self.btn_scan.pack(pady=15, padx=20, fill="x")

        self.btn_scan_now = ctk.CTkButton(self.sidebar, text="🔎 SCAN NAS IMMÉDIAT", height=35, fg_color="#444", command=self.request_nas_scan)
        self.btn_scan_now.pack(pady=(0, 10), padx=20, fill="x")

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

        if self.check_startup():
            self.switch_startup.select()
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

        # Token API (optionnel, doit correspondre a API_TOKEN cote serveur)
        ctk.CTkLabel(f, text="TOKEN API (optionnel)", font=("Arial", 16, "bold")).pack(pady=(20, 5))
        self.entry_token = ctk.CTkEntry(f, width=300, show="*"); self.entry_token.pack()
        self.entry_token.insert(0, self.api_token)

        ctk.CTkButton(f, text="💾 ENREGISTRER CONNEXION (PC)", command=self.save_local_config, height=35).pack(pady=15)

        # Intervalle
        ctk.CTkLabel(f, text="FRÉQUENCE DE SCAN (Secondes)", font=("Arial", 16, "bold")).pack(pady=(20, 5))
        self.entry_interval = ctk.CTkEntry(f, width=100); self.entry_interval.pack()
        self.entry_interval.insert(0, "30")

        # Email
        ctk.CTkLabel(f, text="CONFIGURATION EMAIL", font=("Arial", 16, "bold")).pack(pady=(20, 5))
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

    # ---------- Réseau (helpers avec token + timeout) ----------

    def _headers(self):
        return {"X-Auth-Token": self.api_token} if self.api_token else {}

    def _api_get(self, path, timeout=HTTP_TIMEOUT):
        return requests.get(f"http://{self.nas_ip}:5050{path}", headers=self._headers(), timeout=timeout)

    def _api_post(self, path, payload=None, timeout=HTTP_TIMEOUT):
        return requests.post(f"http://{self.nas_ip}:5050{path}", json=payload or {}, headers=self._headers(), timeout=timeout)

    # ---------- Audit ----------

    def run_audit_thread(self):
        # Lecture des widgets DANS le thread GUI, avant de partir en worker.
        ip = self.entry_ip.get().strip() if hasattr(self, "entry_ip") else self.nas_ip
        if ip:
            self.nas_ip = ip
        self.btn_scan.configure(state="disabled")
        threading.Thread(target=self.process_nas_data, daemon=True).start()

    def process_nas_data(self):
        """Worker : ne touche JAMAIS aux widgets directement (self.after uniquement)."""
        try:
            r = self._api_get("/status")
            if r.status_code == 200:
                data = r.json()
                self.after(0, lambda: self.update_full_ui(data))
                try:
                    h_r = self._api_get("/history", timeout=3)
                    if h_r.status_code == 200:
                        hist = h_r.json()
                        self.after(0, lambda: self.update_graph(hist))
                except requests.RequestException as e:
                    log.warning("Historique indisponible : %s", e)
            elif r.status_code == 401:
                self.after(0, lambda: self.lbl_status.configure(text="⛔ Token API refusé", text_color="orange"))
            else:
                code = r.status_code
                self.after(0, lambda: self.lbl_status.configure(text=f"Erreur NAS: {code}", text_color="orange"))

        except requests.RequestException as e:
            log.warning("NAS injoignable (%s) : %s", self.nas_ip, e)
            self.after(0, lambda: self.lbl_status.configure(text="NAS Injoignable", text_color="red"))

        self.after(0, lambda: self.btn_scan.configure(state="normal"))

    def update_full_ui(self, data):
        # 1. Perf
        p = data.get("performance", {})
        self.lbl_ping.configure(text=f"{p.get('ping_ms', 0)} ms")
        self.lbl_down.configure(text=f"{p.get('download_mbps', 0)} Mb")
        self.lbl_up.configure(text=f"{p.get('upload_mbps', 0)} Mb")

        # 2. Listes
        all_devs = data.get("devices", [])
        alerts = data.get("alerts", [])
        alert_macs = [d['mac'] for d in alerts]
        known_devs = [d for d in all_devs if d['mac'] not in alert_macs]

        # Status
        if alerts:
            self.lbl_status.configure(text=f"⚠️ {len(alerts)} INTRUS !", text_color="red")
            self.device_tabs._segmented_button.configure(selected_color="#AA0000")
            self._notify_new_intruders(alerts)
        else:
            self.lbl_status.configure(text=f"✅ Sécurisé (MàJ: {data.get('last_update', '?')})", text_color="#00ff88")
            self.device_tabs._segmented_button.configure(selected_color=["#3a7ebf", "#1f538d"])

        # Nettoyage Tableaux
        for w in self.known_list.winfo_children():
            w.destroy()
        for w in self.unknown_list.winfo_children():
            w.destroy()

        def add_line(parent, dev, is_new):
            row = ctk.CTkFrame(getattr(self, parent))
            row.pack(fill="x", pady=2)

            name = dev.get('name', 'Inconnu')

            ctk.CTkLabel(row, text=dev.get('ip', '?'), width=110, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=dev.get('mac', '?'), width=130, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=str(name)[:25], width=180, anchor="w", font=("Arial", 12, "bold")).pack(side="left")

            if is_new:
                ctk.CTkButton(row, text="BLOQUER", fg_color="#cc0000", width=80,
                              command=lambda m=dev['mac']: messagebox.showwarning(
                                  "Bloquer", f"Ajoutez {m} à la liste noire de votre Box.")).pack(side="right", padx=5)
                ctk.CTkButton(row, text="VALIDER", fg_color="green", width=80,
                              command=lambda m=dev['mac']: self.authorize_device(m)).pack(side="right", padx=5)

        for d in known_devs:
            add_line("known_list", d, False)
        for d in alerts:
            add_line("unknown_list", d, True)

    def update_graph(self, data):
        if not data:
            return
        df = pd.DataFrame(data)
        self.ax.clear()
        self.ax.grid(True, linestyle='-', color='#555', alpha=0.5)

        # Abscisse : vraies dates si disponibles, sinon index
        x = df.index
        if 'timestamp' in df.columns:
            try:
                x = pd.to_datetime(df['timestamp'])
            except (ValueError, TypeError):
                pass

        if 'download_mbps' in df.columns:
            self.ax.plot(x, df['download_mbps'], label='Down', color='#00ff88')
            self.ax.plot(x, df['upload_mbps'], label='Up', color='#00aaff')
        self.ax.legend(loc='upper left', fontsize='small')
        self.ax.tick_params(colors='white', labelsize=8)
        for label in self.ax.get_xticklabels():
            label.set_rotation(30)
            label.set_horizontalalignment('right')
        self.fig.tight_layout()
        self.canvas.draw()

    def _notify_new_intruders(self, alerts):
        """Notification Windows (balloon) pour les intrus pas encore signalés cette session."""
        fresh = [d for d in alerts if d.get('mac') not in self.notified_macs]
        if not fresh:
            return
        for d in fresh:
            self.notified_macs.add(d.get('mac'))
        try:
            import subprocess
            text = f"{len(fresh)} nouvel(s) appareil(s) inconnu(s) sur le réseau"
            ps = ("Add-Type -AssemblyName System.Windows.Forms;"
                  "Add-Type -AssemblyName System.Drawing;"
                  "$n = New-Object System.Windows.Forms.NotifyIcon;"
                  "$n.Icon = [System.Drawing.SystemIcons]::Warning;"
                  "$n.Visible = $true;"
                  f"$n.ShowBalloonTip(8000, 'Network Sentinel', '{text}',"
                  "[System.Windows.Forms.ToolTipIcon]::Warning);"
                  "Start-Sleep -Seconds 9; $n.Dispose()")
            subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except OSError as e:
            log.warning("Notification Windows impossible : %s", e)

    def request_nas_scan(self):
        """Demande au NAS de scanner immédiatement, puis rafraîchit 3 s plus tard."""
        def worker():
            try:
                self._api_post("/scan_now")
                self.after(3000, self.run_audit_thread)
            except requests.RequestException as e:
                log.warning("Scan immediat impossible : %s", e)
                self.after(0, lambda: self.lbl_status.configure(text="Scan NAS refusé", text_color="orange"))
        threading.Thread(target=worker, daemon=True).start()

    def authorize_device(self, mac):
        try:
            self._api_post("/authorize", {"mac": mac})
            self.after(500, self.run_audit_thread)
        except requests.RequestException as e:
            messagebox.showerror("Erreur", str(e))

    def push_settings(self):
        try:
            cfg = {
                "scan_interval": int(self.entry_interval.get()),
                "email_enabled": True,
                "smtp_server": self.entry_smtp.get(),
                "smtp_port": int(self.entry_port.get()),
                "smtp_user": self.entry_user.get(),
                "smtp_password": self.entry_pwd.get(),
                "alert_emails": [x.strip() for x in self.entry_dest.get().split(",") if x.strip()]
            }
            self._api_post("/update_settings", cfg)
            messagebox.showinfo("Succès", "Réglage appliqué sur le NAS !")
        except (requests.RequestException, ValueError) as e:
            messagebox.showerror("Erreur", f"Erreur envoi NAS: {e}")

    def toggle_monitoring(self):
        self.auto_monitor_active = bool(self.switch_auto.get())
        if self.auto_monitor_active:
            self.monitor_loop()

    def monitor_loop(self):
        if not self.auto_monitor_active:
            return
        self.run_audit_thread()
        try:
            sec = max(5, int(self.entry_interval.get()))
        except ValueError:
            sec = 30
        self.after(sec * 1000, self.monitor_loop)

    # ---------- Config locale (PC) ----------

    def load_local_config(self):
        try:
            with open(CLIENT_CONFIG_FILE, "r") as f:
                cfg = json.load(f)
                self.nas_ip = cfg.get("nas_ip", self.nas_ip)
                self.api_token = cfg.get("api_token", "")
        except FileNotFoundError:
            log.info("Pas de %s : valeurs par defaut.", CLIENT_CONFIG_FILE)
        except (OSError, json.JSONDecodeError) as e:
            log.error("Lecture %s impossible : %s", CLIENT_CONFIG_FILE, e)

    def save_local_config(self):
        self.nas_ip = self.entry_ip.get().strip() or self.nas_ip
        self.api_token = self.entry_token.get().strip()
        try:
            with open(CLIENT_CONFIG_FILE, "w") as f:
                json.dump({"nas_ip": self.nas_ip, "api_token": self.api_token}, f, indent=4)
            messagebox.showinfo("OK", f"Connexion enregistrée ({self.nas_ip}).")
        except OSError as e:
            messagebox.showerror("Erreur", f"Sauvegarde impossible : {e}")

    # ---------- Démarrage Windows ----------

    def check_startup(self):
        return winshell and os.path.exists(os.path.join(winshell.startup(), "NetworkSentinelClient.lnk"))

    def toggle_startup(self):
        if not winshell:
            return
        link = os.path.join(winshell.startup(), "NetworkSentinelClient.lnk")
        try:
            if self.switch_startup.get():
                winshell.shortcut(link).path = sys.executable
            elif os.path.exists(link):
                os.remove(link)
        except OSError as e:
            log.error("Gestion du raccourci de demarrage impossible : %s", e)


if __name__ == "__main__":
    app = NetworkSentinelApp()
    app.mainloop()
