#!/usr/bin/env python3
"""
HackTricks Scraper for AI Model Training
Scrapes technique documentation from book.hacktricks.xyz

Usage:
    python scrape_hacktricks.py --output ../data/hacktricks
"""

import argparse
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Constants - Site moved from .xyz to .wiki in 2024
# New URL structure: /en/{category}/{page}/index.html
BASE_URL = "https://book.hacktricks.wiki"
REQUEST_DELAY = 0.5  # Be respectful

# Categories to scrape - paths need /en/ prefix
CATEGORIES = {
    "linux-hardening": "Linux privilege escalation and hardening",
    "windows-hardening": "Windows privilege escalation and hardening",
    "network-services-pentesting": "Network service exploitation",
    "pentesting-web": "Web application attacks",
    "cloud-security": "Cloud security (AWS, Azure, GCP)",
    "mobile-pentesting": "Mobile application security",
    "forensics-basic-forensic-methodology": "Digital forensics techniques",
    "crypto-and-stego": "Cryptography and steganography",
    "reversing": "Reverse engineering",
    "binary-exploitation": "Binary exploitation",
    "generic-methodologies-and-resources": "General methodology",
}

# Known high-value pages to scrape directly
HIGH_VALUE_PAGES = [
    "/en/linux-hardening/privilege-escalation/index.html",
    "/en/linux-hardening/useful-linux-commands/index.html",
    "/en/windows-hardening/active-directory-methodology/index.html",
    "/en/windows-hardening/basic-powershell-for-pentesters/index.html",
    "/en/windows-hardening/windows-local-privilege-escalation/index.html",
    "/en/network-services-pentesting/pentesting-smb/index.html",
    "/en/network-services-pentesting/pentesting-ssh/index.html",
    "/en/network-services-pentesting/pentesting-web/index.html",
    "/en/network-services-pentesting/pentesting-ldap/index.html",
    "/en/pentesting-web/sql-injection/index.html",
    "/en/pentesting-web/xss-cross-site-scripting/index.html",
    "/en/pentesting-web/xxe-xee-xml-external-entity/index.html",
    "/en/pentesting-web/file-inclusion/index.html",
    "/en/pentesting-web/command-injection/index.html",
    "/en/pentesting-web/ssti-server-side-template-injection/index.html",
    "/en/pentesting-web/ssrf-server-side-request-forgery/index.html",
    "/en/generic-methodologies-and-resources/pentesting-methodology/index.html",
    "/en/generic-methodologies-and-resources/shells/index.html",
]


@dataclass
class TechniquePage:
    """A single technique page from HackTricks."""
    title: str
    url: str
    category: str
    subcategory: Optional[str]
    content: str
    code_blocks: List[str]
    tools_mentioned: List[str]
    commands: List[str]


class HackTricksScraper:
    """Scraper for HackTricks GitBook."""

    def __init__(self, output_dir: str, delay: float = REQUEST_DELAY):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HTB-Training-Scraper/1.0 (Educational Purpose)'
        })
        self.scraped_urls = set()

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "raw").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    def get_category_pages(self, category: str) -> List[str]:
        """Get all page URLs from a category using new wiki structure."""
        urls = []
        # Try the new URL structure: /en/{category}/index.html
        category_url = f"{BASE_URL}/en/{category}/index.html"

        print(f"[*] Fetching category: {category}")
        print(f"[*] URL: {category_url}")

        try:
            response = self.session.get(category_url, timeout=30, allow_redirects=True)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed to fetch {category_url}: {e}")
            # Try without index.html
            try:
                alt_url = f"{BASE_URL}/en/{category}/"
                response = self.session.get(alt_url, timeout=30, allow_redirects=True)
                response.raise_for_status()
            except requests.RequestException:
                return urls

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all internal links in the sidebar/content
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')

            # Skip external links, anchors, and already scraped
            if href.startswith('http') and BASE_URL not in href:
                continue
            if href.startswith('#'):
                continue
            if 'twitter' in href or 'linkedin' in href:
                continue

            # Build full URL
            if href.startswith('/'):
                full_url = BASE_URL + href
            elif not href.startswith('http'):
                full_url = urljoin(category_url, href)
            else:
                full_url = href

            # Check if it's a valid content page in our category
            if category in full_url and full_url not in urls:
                # Ensure it ends with .html for the new structure
                if '.html' in full_url or full_url.endswith('/'):
                    urls.append(full_url)

        print(f"[+] Found {len(urls)} pages in {category}")
        return urls

    def get_high_value_pages(self) -> List[str]:
        """Get pre-defined high-value technique pages."""
        urls = []
        for path in HIGH_VALUE_PAGES:
            urls.append(BASE_URL + path)
        return urls

    def scrape_page(self, url: str, category: str) -> Optional[TechniquePage]:
        """Scrape a single technique page."""
        if url in self.scraped_urls:
            return None

        print(f"[*] Scraping: {url}")
        self.scraped_urls.add(url)

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title = ""
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        else:
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else url.split('/')[-1]

        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
        if not main_content:
            main_content = soup.find('body')

        # Convert to clean text
        content = self._extract_content(main_content)

        # Extract code blocks
        code_blocks = self._extract_code_blocks(main_content)

        # Extract tools mentioned
        tools = self._extract_tools(content)

        # Extract commands
        commands = self._extract_commands(code_blocks)

        # Get subcategory from URL
        parts = urlparse(url).path.strip('/').split('/')
        subcategory = parts[1] if len(parts) > 1 else None

        return TechniquePage(
            title=title,
            url=url,
            category=category,
            subcategory=subcategory,
            content=content,
            code_blocks=code_blocks,
            tools_mentioned=tools,
            commands=commands
        )

    def _extract_content(self, soup) -> str:
        """Extract clean text content."""
        if not soup:
            return ""

        # Remove unwanted elements
        for elem in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            elem.decompose()

        lines = []
        for element in soup.descendants:
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"\n{'#' * level} {text}\n")

            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"\n{text}\n")

            elif element.name == 'pre':
                code = element.get_text()
                lines.append(f"\n```\n{code}\n```\n")

            elif element.name == 'li':
                text = element.get_text(strip=True)
                if text and len(text) < 500:  # Avoid nested content
                    lines.append(f"- {text}")

        return '\n'.join(lines)

    def _extract_code_blocks(self, soup) -> List[str]:
        """Extract all code blocks."""
        blocks = []
        if not soup:
            return blocks

        for pre in soup.find_all(['pre', 'code']):
            code = pre.get_text(strip=True)
            if code and len(code) > 10:  # Skip trivial blocks
                blocks.append(code)

        return blocks

    def _extract_tools(self, content: str) -> List[str]:
        """Extract tool names mentioned in content."""
        # Common pentest tools
        tools = [
            'nmap', 'gobuster', 'dirb', 'nikto', 'sqlmap', 'burp', 'hydra',
            'john', 'hashcat', 'metasploit', 'msfconsole', 'msfvenom',
            'nc', 'netcat', 'curl', 'wget', 'ffuf', 'wfuzz', 'feroxbuster',
            'crackmapexec', 'impacket', 'mimikatz', 'bloodhound', 'ldapsearch',
            'smbclient', 'rpcclient', 'enum4linux', 'responder', 'ntlmrelayx',
            'chisel', 'ligolo', 'socat', 'ssh', 'winrm', 'evil-winrm',
            'linpeas', 'winpeas', 'pspy', 'linenum', 'powerup',
            'sherlock', 'theHarvester', 'amass', 'sublist3r', 'recon-ng'
        ]

        found = []
        content_lower = content.lower()
        for tool in tools:
            if tool.lower() in content_lower:
                found.append(tool)

        return list(set(found))

    def _extract_commands(self, code_blocks: List[str]) -> List[str]:
        """Extract command examples from code blocks."""
        commands = []

        # Patterns for command lines
        cmd_patterns = [
            r'^\$\s+(.+)$',  # $ command
            r'^>\s+(.+)$',   # > command
            r'^#\s+(.+)$',   # # command (root)
            r'^C:\\.*>(.+)$', # Windows prompt
        ]

        for block in code_blocks:
            for line in block.split('\n'):
                line = line.strip()
                for pattern in cmd_patterns:
                    match = re.match(pattern, line)
                    if match:
                        cmd = match.group(1).strip()
                        if cmd and len(cmd) > 5:
                            commands.append(cmd)
                            break

                # Also capture lines that look like commands
                if line and not line.startswith('#') and not line.startswith('//'):
                    # Check if it starts with a known command
                    first_word = line.split()[0] if line.split() else ''
                    known_cmds = ['nmap', 'curl', 'wget', 'python', 'bash', 'sh',
                                  'cat', 'grep', 'find', 'ls', 'cd', 'echo',
                                  'sqlmap', 'gobuster', 'nikto', 'hydra']
                    if first_word.lower() in known_cmds:
                        commands.append(line)

        return list(set(commands))[:50]  # Limit to 50 unique commands

    def save_page(self, page: TechniquePage):
        """Save scraped page to disk."""
        # Create safe filename
        safe_name = re.sub(r'[^\w\-]', '_', page.title.lower())[:50]
        safe_name = f"{page.category}_{safe_name}"

        # Save processed JSON
        output_path = self.output_dir / "processed" / f"{safe_name}.json"
        data = {
            'title': page.title,
            'url': page.url,
            'category': page.category,
            'subcategory': page.subcategory,
            'content': page.content,
            'code_blocks': page.code_blocks,
            'tools_mentioned': page.tools_mentioned,
            'commands': page.commands
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def scrape_category(self, category: str) -> int:
        """Scrape all pages in a category."""
        urls = self.get_category_pages(category)
        count = 0

        for url in urls:
            page = self.scrape_page(url, category)
            if page and page.content:
                self.save_page(page)
                count += 1

            time.sleep(self.delay)

        return count

    def scrape_all(self, categories: List[str] = None, limit_per_category: int = None):
        """Scrape all categories plus high-value pages."""
        if categories is None:
            categories = list(CATEGORIES.keys())

        total = 0
        stats = {}

        # First, scrape the high-value pages directly
        print("\n[*] Scraping high-value technique pages...")
        high_value_urls = self.get_high_value_pages()
        hv_count = 0
        for url in high_value_urls:
            # Determine category from URL
            for cat in categories:
                if cat in url:
                    page = self.scrape_page(url, cat)
                    if page and page.content:
                        self.save_page(page)
                        hv_count += 1
                    break
            time.sleep(self.delay)

        stats['high_value_pages'] = hv_count
        total += hv_count
        print(f"[+] Scraped {hv_count} high-value pages")

        # Then scrape categories
        for category in categories:
            print(f"\n[*] Processing category: {category}")
            print(f"    Description: {CATEGORIES.get(category, 'Unknown')}")

            count = self.scrape_category(category)
            stats[category] = count
            total += count

            if limit_per_category and count >= limit_per_category:
                break

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_pages': total,
                'categories': stats,
                'scraped_urls': list(self.scraped_urls)
            }, f, indent=2)

        print(f"\n[+] Scraping complete! {total} pages saved to {self.output_dir}")
        return total


def main():
    parser = argparse.ArgumentParser(
        description='Scrape HackTricks for model training'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/hacktricks',
        help='Output directory for scraped data'
    )
    parser.add_argument(
        '--categories', '-c',
        nargs='+',
        default=None,
        help='Specific categories to scrape'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.5,
        help='Delay between requests in seconds'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit pages per category'
    )

    args = parser.parse_args()

    scraper = HackTricksScraper(args.output, delay=args.delay)
    scraper.scrape_all(categories=args.categories, limit_per_category=args.limit)


if __name__ == '__main__':
    main()
