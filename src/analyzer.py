# Fichier : src/analyzer.py
# Encodage : utf-8

import sys
import os

# --- CORRECTIF PYINSTALLER (CRITIQUE) ---
# Redirige les flux standards vers null si manquants (mode --noconsole)
if sys.stdin is None:
    sys.stdin = open(os.devnull, 'r')
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
# ----------------------------------------

import time
import urllib.request
from datetime import datetime

import pandas as pd
from ping3 import ping

from src.logger import get_logger

log = get_logger("analyzer")


class NetworkAnalyzer:
    def __init__(self, history_file="data/network_history.csv", download_size_mb=10, upload_size_mb=5):
        self.history_file = history_file
        self.download_size_mb = download_size_mb
        self.upload_size_mb = upload_size_mb

    def run_performance_test(self):
        results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ping_ms": 0, "download_mbps": 0, "upload_mbps": 0
        }

        # 1. Ping
        try:
            latency = ping('8.8.8.8', unit='ms')
            results['ping_ms'] = round(latency, 2) if latency else 0
        except OSError as e:
            log.warning("Ping impossible : %s", e)

        # 2. Download
        results['download_mbps'] = self._custom_download_test()

        # 3. Upload
        results['upload_mbps'] = self._custom_upload_test()

        self._save_to_history(results)
        return results

    def _custom_download_test(self):
        url = f"http://speedtest.tele2.net/{self.download_size_mb}MB.zip"
        try:
            start = time.time()
            with urllib.request.urlopen(url, timeout=15) as response:
                _ = response.read()
            duration = time.time() - start
            if duration > 0:
                return round((self.download_size_mb * 8) / duration, 2)
            return 0
        except (OSError, urllib.error.URLError) as e:
            log.warning("Test download echoue : %s", e)
            return 0

    def _custom_upload_test(self):
        url = "http://speedtest.tele2.net/upload.php"
        data = b'0' * (1024 * 1024 * self.upload_size_mb)
        try:
            start = time.time()
            req = urllib.request.Request(url, data=data, method='POST')
            with urllib.request.urlopen(req, timeout=20) as f:
                _ = f.read()
            duration = time.time() - start
            if duration > 0:
                return round((self.upload_size_mb * 8) / duration, 2)
            return 0
        except (OSError, urllib.error.URLError) as e:
            log.warning("Test upload echoue : %s", e)
            return 0

    def _save_to_history(self, data):
        try:
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            df = pd.DataFrame([data])
            header = not os.path.exists(self.history_file)
            mode = 'w' if header else 'a'
            df.to_csv(self.history_file, mode=mode, header=header, index=False)
        except OSError as e:
            log.error("Sauvegarde historique impossible : %s", e)
