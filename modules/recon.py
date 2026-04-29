#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import threading
import time
import socket
import dns.resolver
import urllib.parse
import ssl
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
from colorama import Fore
from .utils import load_wordlist, random_delay

class FullRecon:
    def __init__(self, target):
        self.target = target.rstrip('/')
        self.session = requests.Session()
        self.session.verify = False
        self.results = {'target': target, 'vulns': [], 'info': {}}
        self.lock = threading.Lock()
        self.crawled = set()
        self.subdomains = set()
        self.open_ports = []

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
            self.results['info']['status_code'] = r.status_code
            print(Fore.LIGHTBLACK_EX + f"[FINGER] Server: {self.results['info']['server']}, Powered: {self.results['info']['powered']}")
            if 'wp-content' in r.text:
                self.results['info']['cms'] = 'WordPress'
                print(Fore.LIGHTBLACK_EX + "[CMS] WordPress detected")
            elif 'Joomla' in r.text:
                self.results['info']['cms'] = 'Joomla'
                print(Fore.LIGHTBLACK_EX + "[CMS] Joomla detected")
        except Exception:
            pass

    def waf_bypass(self):
        try:
            test = self.session.get(self.target + "?x=<script>alert(1)</script>", timeout=5)
            if test.status_code in [403, 406, 503] or 'blocked' in test.text.lower():
                self.session.headers.update({'X-Forwarded-For': '127.0.0.1', 'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'})
                print(Fore.RED + "[WAF] Detected - bypass headers active")
                self.results['info']['waf'] = True
            else:
                self.results['info']['waf'] = False
        except Exception:
            pass

    def subdomain_enum(self):
        domain = urllib.parse.urlparse(self.target).netloc.split(':')[0]
        wordlist = load_wordlist('subdomains')
        for sub in wordlist[:100]:
            subdomain = f"{sub}.{domain}"
            try:
                dns.resolver.resolve(subdomain, 'A')
                self.subdomains.add(subdomain)
                print(Fore.GREEN + f"[SUB] {subdomain}")
            except Exception:
                pass
        self.results['info']['subdomains'] = list(self.subdomains)

    def port_scan(self):
        host = urllib.parse.urlparse(self.target).netloc.split(':')[0]
        ports = [21,22,23,25,53,80,81,110,111,135,139,143,443,445,993,995,1723,3306,3389,5900,8080,8443,27017]
        for port in ports:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                if s.connect_ex((host, port)) == 0:
                    self.open_ports.append(port)
                    print(Fore.CYAN + f"[PORT] {host}:{port} OPEN")
                s.close()
            except Exception:
                pass
        self.results['info']['open_ports'] = self.open_ports

    def dir_brute(self):
        wordlist = load_wordlist('directories')
        for d in wordlist[:150]:
            url = urllib.parse.urljoin(self.target, d)
            if not url.endswith('/'):
                url += '/'
            try:
                r = self.session.head(url, timeout=2, allow_redirects=False)
                if r.status_code in [200, 301, 302, 403]:
                    print(Fore.MAGENTA + f"[DIR] {url} [{r.status_code}]")
                    self.results['vulns'].append({'type': 'Directory Listing', 'url': url, 'status': r.status_code})
            except Exception:
                pass

    def crawl_recursive(self, url, depth):
        if depth == 0 or url in self.crawled:
            return
        self.crawled.add(url)
        try:
            r = self.session.get(url, timeout=3)
            soup = BeautifulSoup(r.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                full = urllib.parse.urljoin(url, link['href'])
                if urllib.parse.urlparse(full).netloc == urllib.parse.urlparse(self.target).netloc:
                    threading.Thread(target=self.crawl_recursive, args=(full, depth-1)).start()
        except Exception:
            pass

    def param_injection(self):
        params = ['q','id','page','search','user','file','path','redirect','lang','url', 'cmd', 'exec', 'command', 'do', 'action', 'func', 'method', 'op', 'option', 'view', 'controller', 'module']
        payloads = load_wordlist('payloads')
        if not payloads:
            payloads = ["' OR '1'='1", "<script>alert(1)</script>", "../../../etc/passwd", "; whoami"]
        for param in params:
            for payload in payloads[:50]:
                try:
                    r = self.session.get(self.target, params={param: payload}, timeout=3)
                    if payload in r.text or 'error' in r.text.lower() or 'sql' in r.text.lower():
                        with self.lock:
                            self.results['vulns'].append({'type': 'Injection', 'param': param, 'payload': payload[:80], 'status': r.status_code, 'url': r.url})
                            print(Fore.RED + f"[VULN] Injection on {param}={payload[:30]} | HTTP {r.status_code}")
                except Exception:
                    pass

    def graphql_scan(self):
        endpoints = ['/graphql', '/v1/graphql', '/api/graphql', '/gql', '/query']
        query = '{"query":"{__schema{types{name}}}"}'
        headers = {'Content-Type': 'application/json'}
        for ep in endpoints:
            url = urllib.parse.urljoin(self.target, ep)
            try:
                r = self.session.post(url, data=query, headers=headers, timeout=5)
                if 'schema' in r.text and 'types' in r.text:
                    self.results['vulns'].append({'type': 'GraphQL Introspection', 'endpoint': ep, 'status': r.status_code})
                    print(Fore.RED + f"[VULN] GraphQL introspection at {ep}")
            except Exception:
                pass

    def smuggle_test(self):
        # Simulasi deteksi pasif
        try:
            r = self.session.get(self.target, headers={'Transfer-Encoding': 'chunked', 'Content-Length': '4'})
            if r.status_code == 400 or 'error' in r.text.lower():
                self.results['vulns'].append({'type': 'HTTP Request Smuggling (Possible)', 'details': 'Chunked+CL mismatch'})
                print(Fore.RED + "[VULN] Possible HTTP Request Smuggling")
        except Exception:
            pass

    def file_upload_test(self):
        print(Fore.YELLOW + "[UPLOAD] Scanning for upload forms...")
        try:
            r = self.session.get(self.target, timeout=5)
            if 'enctype="multipart/form-data"' in r.text or 'type="file"' in r.text:
                self.results['vulns'].append({'type': 'File Upload Form Found', 'url': self.target})
                print(Fore.MAGENTA + "[UPLOAD] Upload form detected, manual testing required")
        except Exception:
            pass
