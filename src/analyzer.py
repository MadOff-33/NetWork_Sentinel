# Fichier : src/analyzer.py
# Encodage : utf-8

import sys
import os

# --- CORRECTIF PYINSTALLER (CRITIQUE) ---
# Redirige les flux standards vers null si manquants (mode --noconsole)
# Cela empêche le crash de speedtest-cli à l'importation.
if sys.stdin is None:
    sys.stdin = open(os.devnull, 'r')
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
# ----------------------------------------

import speedtest
import pandas as pd
import time
import urllib.request
from datetime import datetime
from ping3 import ping

class NetworkAnalyzer:
    def __init__(self, history_file="data/network_history.csv"):
        self.history_file = history_file

    def run_performance_test(self):
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ping_ms": 0, "download_mbps": 0, "upload_mbps": 0
        }

        # 1. Ping
        try:
            latency = ping('8.8.8.8', unit='ms')
            results['ping_ms'] = round(latency, 2) if latency else 0
        except: pass

        # 2. Download (Custom method)
        results['download_mbps'] = self._custom_download_test()
        
        # 3. Upload (Custom method)
        results['upload_mbps'] = self._custom_upload_test()

        self._save_to_history(results)
        return results

    def _custom_download_test(self):
        url = "http://speedtest.tele2.net/10MB.zip"
        file_size_mb = 10
        try:
            start = time.time()
            with urllib.request.urlopen(url, timeout=15) as response:
                _ = response.read()
            duration = time.time() - start
            if duration > 0:
                return round((file_size_mb * 8) / duration, 2)
            return 0
        except: return 0

    def _custom_upload_test(self):
        url = "http://speedtest.tele2.net/upload.php"
        data_size_mb = 5
        data = b'0' * (1024 * 1024 * data_size_mb)
        try:
            start = time.time()
            req = urllib.request.Request(url, data=data, method='POST')
            with urllib.request.urlopen(req, timeout=20) as f:
                _ = f.read()
            duration = time.time() - start
            if duration > 0:
                return round((data_size_mb * 8) / duration, 2)
            return 0
        except: return 0

    def _save_to_history(self, data):
        # Création dossier si inexistant
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        
        df = pd.DataFrame([data])
        mode = 'a' if os.path.exists(self.history_file) else 'w'
        header = not os.path.exists(self.history_file)
        try:
            df.to_csv(self.history_file, mode=mode, header=header, index=False)
        except: pass