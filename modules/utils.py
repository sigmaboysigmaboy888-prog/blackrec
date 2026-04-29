#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import time
import requests

def load_wordlist(name):
    base_path = os.path.join('wordlists', f"{name}.txt")
    fallback = {
        'subdomains': ['www', 'mail', 'admin', 'dev', 'api', 'test'],
        'directories': ['admin', 'backup', 'config', 'api', 'login'],
        'payloads': ["' OR '1'='1", "<script>alert(1)</script>", "../../../etc/passwd"]
    }
    if not os.path.exists(base_path):
        return fallback.get(name, [])
    with open(base_path, 'r', encoding='utf-8', errors='ignore') as f:
        return [line.strip() for line in f if line.strip()]

def random_delay(min_ms=10, max_ms=100):
    time.sleep(random.randint(min_ms, max_ms) / 1000.0)

def update_payloads():
    url = "https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/master/README.md"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open('wordlists/payloads.txt', 'wb') as f:
                f.write(r.content)
            print("[UPDATED] Payloads synced from PayloadsAllTheThings")
        else:
            print("[UPDATED] Using local payloads")
    except:
        print("[UPDATED] Offline mode, no remote update")
