#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
from colorama import Fore

class ReportGenerator:
    def __init__(self, scan_results=None):
        self.scan_results = scan_results if scan_results else {'vulns': [], 'info': {}}
        self.timestamp = int(time.time())

    def save(self, format_type='html'):
        if format_type == 'html':
            self.to_html()
        elif format_type == 'json':
            self.to_json()
        else:
            self.to_html()
            self.to_json()

    def to_html(self):
        filename = f"report_{self.timestamp}.html"
        html_content = f"""<!DOCTYPE html>
<html>
<head><title>BlackRecon Report</title><style>body{{font-family:monospace;background:#0a0a0a;color:#00ff00;}} .vuln{{color:#ff4444;}}</style></head>
<body>
<h1>☠️ BlackRecon Overpower Report</h1>
<p>Target: {self.scan_results.get('target', 'unknown')}</p>
<p>Time: {time.ctime(self.timestamp)}</p>
<h2>Vulnerabilities ({len(self.scan_results.get('vulns', []))})</h2>
<ul>
"""
        for v in self.scan_results.get('vulns', []):
            html_content += f"<li class='vuln'>{v.get('type','Generic')} : {v.get('param','')} -> {v.get('payload','')[:80]}</li>\n"
        html_content += """</ul>
</body>
</html>"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(Fore.GREEN + f"[REPORT] HTML saved: {filename}")

    def to_json(self):
        filename = f"report_{self.timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scan_results, f, indent=2)
        print(Fore.GREEN + f"[REPORT] JSON saved: {filename}")

    @staticmethod
    def generate_last_report():
        print(Fore.YELLOW + "[REPORT] Generating from last scan data...")
        try:
            with open('report_last.json', 'r') as f:
                data = json.load(f)
            rep = ReportGenerator(data)
            rep.save()
        except:
            print(Fore.RED + "[REPORT] No previous scan data found.")
