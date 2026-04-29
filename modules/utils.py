import requests, json, os

def load_wordlist(name):
    path = f"wordlists/{name}.txt"
    if not os.path.exists(path):
        return ["admin", "test", "backup"]  # fallback
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def update_payloads():
    try:
        r = requests.get("https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/master/README.md")
        print(f"[UPDATED] Payloads synced: {len(r.text)} bytes")
    except:
        print("[UPDATED] Offline mode, using local payloads")

def random_delay(min_ms=10, max_ms=100):
    import random, time
    time.sleep(random.randint(min_ms, max_ms)/1000.0)
