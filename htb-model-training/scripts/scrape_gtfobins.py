#!/usr/bin/env python3
"""
GTFOBins Scraper for AI Model Training
Scrapes Linux binary abuse techniques from gtfobins.github.io

GTFOBins documents Unix binaries that can be exploited to:
- Escape restricted shells
- Escalate privileges (SUID, sudo, capabilities)
- Transfer files
- Execute arbitrary commands

Usage:
    python scrape_gtfobins.py --output ../data/gtfobins
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
BASE_URL = "https://gtfobins.github.io"
INDEX_URL = f"{BASE_URL}/"
REQUEST_DELAY = 0.3

# GTFOBins function types
FUNCTION_TYPES = [
    "shell",
    "command",
    "reverse-shell",
    "non-interactive-reverse-shell",
    "bind-shell",
    "non-interactive-bind-shell",
    "file-upload",
    "file-download",
    "file-write",
    "file-read",
    "library-load",
    "suid",
    "sudo",
    "capabilities",
    "limited-suid",
]


@dataclass
class GTFOBinary:
    """A GTFOBins binary entry."""
    name: str
    url: str
    description: str
    functions: Dict[str, List[Dict[str, str]]]  # function_type -> list of techniques
    tags: List[str] = field(default_factory=list)


class GTFOBinsScraper:
    """Scraper for GTFOBins documentation."""

    def __init__(self, output_dir: str, delay: float = REQUEST_DELAY):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HTB-Training-Scraper/1.0 (Educational Purpose)'
        })
        self.scraped_binaries = []

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    def get_all_binary_urls(self) -> List[dict]:
        """Get all binary URLs from the index page."""
        print(f"[*] Fetching GTFOBins index from {INDEX_URL}")

        try:
            response = self.session.get(INDEX_URL, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed to fetch index: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        binaries = []

        # Find all binary links in the bin-list
        bin_list = soup.find('ul', id='bin-list') or soup.find('ul', class_='bin-list')

        if bin_list:
            for link in bin_list.find_all('a', href=True):
                href = link.get('href', '')
                if '/gtfobins/' in href:
                    name = link.get_text(strip=True)
                    # Get function tags from data attribute or classes
                    functions = []
                    li = link.find_parent('li')
                    if li:
                        func_data = li.get('data-functions', '')
                        if func_data:
                            functions = func_data.split()
                        # Also check for function-tagged classes
                        for func_type in FUNCTION_TYPES:
                            if li.get(f'data-{func_type}') or func_type in li.get('class', []):
                                functions.append(func_type)

                    binaries.append({
                        'name': name,
                        'url': urljoin(BASE_URL, href),
                        'functions': list(set(functions))
                    })
        else:
            # Fallback: find any links to /gtfobins/
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/gtfobins/' in href and href.endswith('/'):
                    name = href.strip('/').split('/')[-1]
                    if name and name not in ['gtfobins']:
                        binaries.append({
                            'name': name,
                            'url': urljoin(BASE_URL, href),
                            'functions': []
                        })

        # Remove duplicates
        seen = set()
        unique = []
        for b in binaries:
            if b['name'] not in seen:
                seen.add(b['name'])
                unique.append(b)

        print(f"[+] Found {len(unique)} binaries")
        return unique

    def scrape_binary(self, binary_info: dict) -> Optional[GTFOBinary]:
        """Scrape a single binary's documentation."""
        url = binary_info['url']
        name = binary_info['name']

        print(f"[*] Scraping binary: {name}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract description
        description = self._extract_description(soup)

        # Extract functions and techniques
        functions = self._extract_functions(soup)

        if not functions:
            print(f"[!] No functions found for {name}")
            return None

        # Determine tags from available functions
        tags = list(functions.keys())

        return GTFOBinary(
            name=name,
            url=url,
            description=description,
            functions=functions,
            tags=tags
        )

    def _extract_description(self, soup) -> str:
        """Extract binary description."""
        desc = ""

        # Look for description paragraph
        main = soup.find('main') or soup.find('article') or soup.find('div', class_='container')
        if main:
            # First paragraph is usually the description
            first_p = main.find('p')
            if first_p:
                desc = first_p.get_text(strip=True)

        # Also check for specific description element
        desc_elem = soup.find(class_='bin-description') or soup.find(id='description')
        if desc_elem:
            desc = desc_elem.get_text(strip=True)

        return desc

    def _extract_functions(self, soup) -> Dict[str, List[Dict[str, str]]]:
        """Extract all function techniques for this binary."""
        functions = {}

        # Find function sections (h2 headers with function names)
        for header in soup.find_all(['h2', 'h3']):
            header_text = header.get_text(strip=True).lower().replace(' ', '-')

            # Check if this is a known function type
            func_type = None
            for ft in FUNCTION_TYPES:
                if ft in header_text or header_text in ft:
                    func_type = ft
                    break

            if not func_type:
                # Try to match partial names
                if 'shell' in header_text:
                    func_type = 'shell'
                elif 'suid' in header_text:
                    func_type = 'suid'
                elif 'sudo' in header_text:
                    func_type = 'sudo'
                elif 'capabil' in header_text:
                    func_type = 'capabilities'
                elif 'upload' in header_text:
                    func_type = 'file-upload'
                elif 'download' in header_text:
                    func_type = 'file-download'
                elif 'write' in header_text:
                    func_type = 'file-write'
                elif 'read' in header_text:
                    func_type = 'file-read'
                elif 'command' in header_text:
                    func_type = 'command'
                elif 'reverse' in header_text:
                    func_type = 'reverse-shell'
                elif 'bind' in header_text:
                    func_type = 'bind-shell'

            if func_type:
                techniques = self._extract_techniques_after_header(header)
                if techniques:
                    if func_type not in functions:
                        functions[func_type] = []
                    functions[func_type].extend(techniques)

        # Also look for code blocks with technique descriptions
        if not functions:
            functions = self._extract_functions_from_sections(soup)

        return functions

    def _extract_techniques_after_header(self, header) -> List[Dict[str, str]]:
        """Extract technique code blocks following a header."""
        techniques = []

        # Navigate through siblings until next header
        sibling = header.find_next_sibling()
        while sibling and sibling.name not in ['h2', 'h3']:
            # Look for code blocks
            if sibling.name == 'pre' or sibling.find('pre'):
                code_elem = sibling if sibling.name == 'pre' else sibling.find('pre')
                if code_elem:
                    code = code_elem.get_text(strip=True)
                    if code:
                        # Look for preceding explanation
                        explanation = ""
                        prev = sibling.find_previous_sibling('p')
                        if prev:
                            explanation = prev.get_text(strip=True)

                        techniques.append({
                            'code': code,
                            'explanation': explanation
                        })

            # Also handle list items with code
            if sibling.name == 'ul':
                for li in sibling.find_all('li'):
                    code_elem = li.find('code') or li.find('pre')
                    if code_elem:
                        code = code_elem.get_text(strip=True)
                        # Get surrounding text as explanation
                        full_text = li.get_text(strip=True)
                        explanation = full_text.replace(code, '').strip()
                        techniques.append({
                            'code': code,
                            'explanation': explanation
                        })

            sibling = sibling.find_next_sibling()

        return techniques

    def _extract_functions_from_sections(self, soup) -> Dict[str, List[Dict[str, str]]]:
        """Fallback: extract functions from section divs."""
        functions = {}

        # Look for function sections by class or id
        for func_type in FUNCTION_TYPES:
            section = soup.find(id=func_type) or soup.find(class_=func_type)
            if section:
                techniques = []
                for code in section.find_all(['pre', 'code']):
                    code_text = code.get_text(strip=True)
                    if code_text and len(code_text) > 3:
                        techniques.append({
                            'code': code_text,
                            'explanation': ''
                        })
                if techniques:
                    functions[func_type] = techniques

        return functions

    def save_binary(self, binary: GTFOBinary):
        """Save binary documentation to disk."""
        safe_name = re.sub(r'[^\w\-]', '_', binary.name.lower())

        output_path = self.output_dir / "processed" / f"{safe_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(binary), f, indent=2, ensure_ascii=False)

        self.scraped_binaries.append(binary.name)

    def convert_to_training_format(self, binary: GTFOBinary) -> List[dict]:
        """Convert a GTFOBins entry to training QA pairs."""
        training_data = []

        for func_type, techniques in binary.functions.items():
            # Create a question about this function
            func_questions = {
                'shell': f"How can I use {binary.name} to get a shell?",
                'suid': f"How can I exploit {binary.name} with SUID bit for privilege escalation?",
                'sudo': f"How can I abuse sudo permissions for {binary.name}?",
                'capabilities': f"How can I exploit Linux capabilities with {binary.name}?",
                'file-read': f"How can I use {binary.name} to read files?",
                'file-write': f"How can I use {binary.name} to write files?",
                'file-upload': f"How can I use {binary.name} to upload files?",
                'file-download': f"How can I use {binary.name} to download files?",
                'reverse-shell': f"How can I get a reverse shell using {binary.name}?",
                'bind-shell': f"How can I create a bind shell using {binary.name}?",
                'command': f"How can I execute commands using {binary.name}?",
            }

            question = func_questions.get(func_type,
                f"How can I use {binary.name} for {func_type.replace('-', ' ')}?")

            # Build the answer from techniques
            answer_parts = [f"You can use `{binary.name}` for {func_type.replace('-', ' ')}:"]
            if binary.description:
                answer_parts.append(f"\n{binary.description}")

            answer_parts.append("\n\n**Techniques:**")
            for i, tech in enumerate(techniques[:5], 1):  # Limit to 5 techniques
                if tech.get('code'):
                    answer_parts.append(f"\n{i}. ```\n{tech['code']}\n```")
                    if tech.get('explanation'):
                        answer_parts.append(f"   {tech['explanation']}")

            training_data.append({
                'instruction': question,
                'output': '\n'.join(answer_parts),
                'source': 'gtfobins',
                'binary': binary.name,
                'function': func_type
            })

        return training_data

    def scrape_all(self, limit: int = None):
        """Scrape all binaries."""
        all_binaries = self.get_all_binary_urls()

        if limit:
            all_binaries = all_binaries[:limit]

        training_data = []

        for i, binary_info in enumerate(all_binaries):
            print(f"\n[{i+1}/{len(all_binaries)}]")

            binary = self.scrape_binary(binary_info)
            if binary and binary.functions:
                self.save_binary(binary)
                training_data.extend(self.convert_to_training_format(binary))

            time.sleep(self.delay)

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_binaries': len(self.scraped_binaries),
                'binaries': self.scraped_binaries,
                'function_types': FUNCTION_TYPES
            }, f, indent=2)

        # Save training data
        training_path = self.output_dir / "gtfobins_training.jsonl"
        with open(training_path, 'w', encoding='utf-8') as f:
            for entry in training_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"\n[+] Scraping complete!")
        print(f"    - {len(self.scraped_binaries)} binaries saved")
        print(f"    - {len(training_data)} training entries generated")

        return self.scraped_binaries


def main():
    parser = argparse.ArgumentParser(
        description='Scrape GTFOBins binary abuse documentation'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/gtfobins',
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
        help='Limit number of binaries to scrape'
    )

    args = parser.parse_args()

    scraper = GTFOBinsScraper(args.output, delay=args.delay)
    scraper.scrape_all(limit=args.limit)


if __name__ == '__main__':
    main()
