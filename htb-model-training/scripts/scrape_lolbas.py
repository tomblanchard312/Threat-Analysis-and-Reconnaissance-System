#!/usr/bin/env python3
"""
LOLBAS (Living Off The Land Binaries and Scripts) Scraper
Scrapes Windows binary abuse techniques from lolbas-project.github.io

LOLBAS documents Windows binaries, scripts, and libraries that can be:
- Used for execution bypass
- Downloaded/uploaded files
- Compiled code
- Credential theft
- UAC bypass
- And more...

Usage:
    python scrape_lolbas.py --output ../data/lolbas
"""

import argparse
import json
import re
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://lolbas-project.github.io"
API_URL = "https://lolbas-project.github.io/api/lolbas.json"
REQUEST_DELAY = 0.3

# LOLBAS categories
CATEGORIES = [
    "Binaries",      # Native Windows executables
    "Scripts",       # Script files (bat, vbs, ps1)
    "Libraries",     # DLLs that can be abused
    "OtherMSBinaries",  # Other Microsoft binaries
]

# LOLBAS function types
FUNCTION_TYPES = [
    "Execute",       # Execute arbitrary code/commands
    "Download",      # Download files from internet
    "Upload",        # Upload/exfiltrate files
    "Copy",          # Copy files
    "Compile",       # Compile code
    "Decode",        # Decode encoded data
    "Encode",        # Encode data
    "Credentials",   # Access/dump credentials
    "AWL Bypass",    # Application Whitelist bypass
    "UAC Bypass",    # User Account Control bypass
    "Reconnaissance",  # Gather system info
    "Persistence",   # Establish persistence
]


@dataclass
class LOLBASEntry:
    """A LOLBAS binary/script/library entry."""
    name: str
    url: str
    description: str
    category: str  # Binaries, Scripts, Libraries
    author: str
    commands: List[Dict[str, str]]  # List of command techniques
    functions: List[str]  # Execute, Download, etc.
    full_path: str
    detection: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    mitre_techniques: List[str] = field(default_factory=list)


class LOLBASScraper:
    """Scraper for LOLBAS documentation."""

    def __init__(self, output_dir: str, delay: float = REQUEST_DELAY):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HTB-Training-Scraper/1.0 (Educational Purpose)'
        })
        self.scraped_entries = []

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    def get_all_entries_from_api(self) -> List[dict]:
        """Try to get all entries from the JSON API."""
        print(f"[*] Trying to fetch LOLBAS API from {API_URL}")

        try:
            response = self.session.get(API_URL, timeout=30)
            response.raise_for_status()
            data = response.json()
            print(f"[+] Got {len(data)} entries from API")
            return data
        except Exception as e:
            print(f"[!] API fetch failed: {e}")
            return []

    def get_all_entry_urls(self) -> List[dict]:
        """Get all entry URLs from the website."""
        print(f"[*] Fetching LOLBAS index from {BASE_URL}")

        entries = []

        # Try each category page
        for category in CATEGORIES:
            category_url = f"{BASE_URL}/{category.lower()}/"
            print(f"[*] Fetching category: {category}")

            try:
                response = self.session.get(category_url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find entry links
                    for link in soup.find_all('a', href=True):
                        href = link.get('href', '')
                        if f'/{category.lower()}/' in href.lower():
                            name = link.get_text(strip=True)
                            if name and len(name) < 50:
                                entries.append({
                                    'name': name,
                                    'url': urljoin(BASE_URL, href),
                                    'category': category
                                })
            except requests.RequestException as e:
                print(f"[!] Failed to fetch {category}: {e}")

            time.sleep(self.delay)

        # Remove duplicates
        seen = set()
        unique = []
        for e in entries:
            key = e['url']
            if key not in seen:
                seen.add(key)
                unique.append(e)

        print(f"[+] Found {len(unique)} entries")
        return unique

    def parse_api_entry(self, entry: dict) -> Optional[LOLBASEntry]:
        """Parse an entry from the API JSON format."""
        try:
            name = entry.get('Name', '')
            if not name:
                return None

            # Extract commands
            commands = []
            for cmd in entry.get('Commands', []):
                commands.append({
                    'command': cmd.get('Command', ''),
                    'description': cmd.get('Description', ''),
                    'usecase': cmd.get('Usecase', ''),
                    'category': cmd.get('Category', ''),
                    'mitre': cmd.get('MitreID', ''),
                    'privileges': cmd.get('Privileges', ''),
                    'os': cmd.get('OperatingSystem', '')
                })

            # Extract functions from commands
            functions = list(set(cmd.get('category', '') for cmd in commands if cmd.get('category')))

            # Extract detection methods
            detection = []
            for det in entry.get('Detection', []):
                if isinstance(det, dict):
                    detection.append(det.get('IOC', det.get('Detection', str(det))))
                else:
                    detection.append(str(det))

            # Extract resources
            resources = []
            for res in entry.get('Resources', []):
                if isinstance(res, dict):
                    resources.append(res.get('Link', res.get('Resource', str(res))))
                else:
                    resources.append(str(res))

            # Extract MITRE techniques
            mitre = list(set(cmd.get('mitre', '') for cmd in commands if cmd.get('mitre')))

            return LOLBASEntry(
                name=name,
                url=f"{BASE_URL}/{entry.get('Type', 'binaries').lower()}/{name.lower()}/",
                description=entry.get('Description', ''),
                category=entry.get('Type', 'Binaries'),
                author=entry.get('Author', ''),
                commands=commands,
                functions=functions,
                full_path=entry.get('Full_Path', [{}])[0].get('Path', '') if entry.get('Full_Path') else '',
                detection=detection,
                resources=resources,
                mitre_techniques=mitre
            )
        except Exception as e:
            print(f"[!] Error parsing entry: {e}")
            return None

    def scrape_entry_page(self, entry_info: dict) -> Optional[LOLBASEntry]:
        """Scrape a single entry's page."""
        url = entry_info['url']
        name = entry_info['name']

        print(f"[*] Scraping entry: {name}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract description
        description = ""
        desc_elem = soup.find(class_='description') or soup.find('p')
        if desc_elem:
            description = desc_elem.get_text(strip=True)

        # Extract commands
        commands = []
        for code in soup.find_all(['pre', 'code']):
            cmd_text = code.get_text(strip=True)
            if cmd_text and len(cmd_text) > 5:
                # Look for preceding context
                context = ""
                prev = code.find_previous(['p', 'h3', 'h4'])
                if prev:
                    context = prev.get_text(strip=True)

                commands.append({
                    'command': cmd_text,
                    'description': context,
                    'usecase': '',
                    'category': '',
                    'mitre': '',
                    'privileges': '',
                    'os': ''
                })

        # Try to extract functions from page content
        functions = []
        page_text = soup.get_text().lower()
        for func in FUNCTION_TYPES:
            if func.lower() in page_text:
                functions.append(func)

        if not commands:
            return None

        return LOLBASEntry(
            name=name,
            url=url,
            description=description,
            category=entry_info.get('category', 'Binaries'),
            author='',
            commands=commands,
            functions=functions,
            full_path='',
            detection=[],
            resources=[],
            mitre_techniques=[]
        )

    def save_entry(self, entry: LOLBASEntry):
        """Save entry documentation to disk."""
        safe_name = re.sub(r'[^\w\-]', '_', entry.name.lower())

        output_path = self.output_dir / "processed" / f"{safe_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(entry), f, indent=2, ensure_ascii=False)

        self.scraped_entries.append(entry.name)

    def convert_to_training_format(self, entry: LOLBASEntry) -> List[dict]:
        """Convert a LOLBAS entry to training QA pairs."""
        training_data = []

        # Create general question about this binary
        q_general = f"How can I use {entry.name} for living off the land attacks on Windows?"
        answer_parts = [f"`{entry.name}` is a Windows {entry.category.lower().rstrip('s')} that can be abused for:"]

        if entry.functions:
            answer_parts.append("\n**Functions:** " + ", ".join(entry.functions))

        if entry.description:
            answer_parts.append(f"\n\n{entry.description}")

        if entry.full_path:
            answer_parts.append(f"\n**Path:** `{entry.full_path}`")

        answer_parts.append("\n\n**Techniques:**")
        for i, cmd in enumerate(entry.commands[:5], 1):
            if cmd.get('command'):
                answer_parts.append(f"\n{i}. ```\n{cmd['command']}\n```")
                if cmd.get('description'):
                    answer_parts.append(f"   {cmd['description']}")
                if cmd.get('usecase'):
                    answer_parts.append(f"   Use case: {cmd['usecase']}")

        if entry.detection:
            answer_parts.append("\n\n**Detection:**")
            for det in entry.detection[:3]:
                answer_parts.append(f"\n- {det}")

        training_data.append({
            'instruction': q_general,
            'output': '\n'.join(answer_parts),
            'source': 'lolbas',
            'binary': entry.name,
            'category': entry.category
        })

        # Create specific questions for each function
        for func in entry.functions:
            func_cmds = [c for c in entry.commands if func.lower() in c.get('category', '').lower()
                        or func.lower() in c.get('description', '').lower()]

            if func_cmds:
                q_func = f"How can I use {entry.name} to {func.lower()} on Windows?"
                answer = f"You can use `{entry.name}` for {func.lower()}:\n\n"
                for i, cmd in enumerate(func_cmds[:3], 1):
                    answer += f"{i}. ```\n{cmd['command']}\n```\n"
                    if cmd.get('description'):
                        answer += f"   {cmd['description']}\n"

                training_data.append({
                    'instruction': q_func,
                    'output': answer,
                    'source': 'lolbas',
                    'binary': entry.name,
                    'function': func
                })

        return training_data

    def scrape_all(self, limit: int = None):
        """Scrape all entries."""
        training_data = []

        # First try the API
        api_entries = self.get_all_entries_from_api()

        if api_entries:
            if limit:
                api_entries = api_entries[:limit]

            for i, entry_data in enumerate(api_entries):
                print(f"\n[{i+1}/{len(api_entries)}]")

                entry = self.parse_api_entry(entry_data)
                if entry and entry.commands:
                    self.save_entry(entry)
                    training_data.extend(self.convert_to_training_format(entry))

                time.sleep(self.delay / 2)  # Faster since we're not making HTTP requests
        else:
            # Fall back to scraping pages
            all_entries = self.get_all_entry_urls()

            if limit:
                all_entries = all_entries[:limit]

            for i, entry_info in enumerate(all_entries):
                print(f"\n[{i+1}/{len(all_entries)}]")

                entry = self.scrape_entry_page(entry_info)
                if entry and entry.commands:
                    self.save_entry(entry)
                    training_data.extend(self.convert_to_training_format(entry))

                time.sleep(self.delay)

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_entries': len(self.scraped_entries),
                'entries': self.scraped_entries,
                'categories': CATEGORIES,
                'function_types': FUNCTION_TYPES
            }, f, indent=2)

        # Save training data
        training_path = self.output_dir / "lolbas_training.jsonl"
        with open(training_path, 'w', encoding='utf-8') as f:
            for entry in training_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"\n[+] Scraping complete!")
        print(f"    - {len(self.scraped_entries)} entries saved")
        print(f"    - {len(training_data)} training entries generated")

        return self.scraped_entries


def main():
    parser = argparse.ArgumentParser(
        description='Scrape LOLBAS Windows binary abuse documentation'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/lolbas',
        help='Output directory'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.3,
        help='Delay between requests'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit number of entries to scrape'
    )

    args = parser.parse_args()

    scraper = LOLBASScraper(args.output, delay=args.delay)
    scraper.scrape_all(limit=args.limit)


if __name__ == '__main__':
    main()
