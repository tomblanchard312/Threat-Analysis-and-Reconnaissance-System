#!/usr/bin/env python3
"""
Kali Linux Tools Scraper for AI Model Training
Scrapes tool documentation from kali.org/tools

Usage:
    python scrape_kali_tools.py --output ../data/kali_tools
"""

import argparse
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://www.kali.org"
TOOLS_INDEX = f"{BASE_URL}/tools/"
REQUEST_DELAY = 0.5

# Tool categories on Kali
TOOL_CATEGORIES = [
    "information-gathering",
    "vulnerability-analysis",
    "web-applications",
    "database-assessment",
    "password-attacks",
    "wireless-attacks",
    "reverse-engineering",
    "exploitation-tools",
    "sniffing-spoofing",
    "post-exploitation",
    "forensics-tools",
    "reporting-tools",
    "social-engineering",
]


@dataclass
class KaliTool:
    """A Kali Linux tool documentation page."""
    name: str
    url: str
    category: str
    description: str
    usage_examples: List[str]
    options: List[str]
    similar_tools: List[str]
    package_info: Optional[str]


class KaliToolsScraper:
    """Scraper for Kali Linux tools documentation."""

    def __init__(self, output_dir: str, delay: float = REQUEST_DELAY):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HTB-Training-Scraper/1.0 (Educational Purpose)'
        })
        self.scraped_tools = []

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "raw").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    def get_all_tool_urls(self) -> List[dict]:
        """Get all tool URLs from the main tools page."""
        print(f"[*] Fetching tools index from {TOOLS_INDEX}")
        tools = []

        try:
            response = self.session.get(TOOLS_INDEX, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed to fetch index: {e}")
            return tools

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all tool links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/tools/' in href and href != '/tools/':
                # Extract tool name from URL
                parts = href.strip('/').split('/')
                if len(parts) >= 2 and parts[0] == 'tools':
                    tool_name = parts[1]
                    full_url = urljoin(BASE_URL, href)

                    if not any(t['url'] == full_url for t in tools):
                        tools.append({
                            'name': tool_name,
                            'url': full_url,
                            'link_text': link.get_text(strip=True)
                        })

        print(f"[+] Found {len(tools)} tools")
        return tools

    def get_tools_by_category(self, category: str) -> List[dict]:
        """Get tools from a specific category page."""
        category_url = f"{BASE_URL}/tools/{category}/"
        tools = []

        print(f"[*] Fetching category: {category}")

        try:
            response = self.session.get(category_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed to fetch {category_url}: {e}")
            return tools

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find tool cards/links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/tools/' in href and category not in href:
                tool_name = href.strip('/').split('/')[-1]
                if tool_name and tool_name not in ['tools', category]:
                    full_url = urljoin(BASE_URL, href)
                    tools.append({
                        'name': tool_name,
                        'url': full_url,
                        'category': category
                    })

        return tools

    def scrape_tool(self, tool_info: dict) -> Optional[KaliTool]:
        """Scrape a single tool's documentation."""
        url = tool_info['url']
        name = tool_info['name']
        category = tool_info.get('category', 'unknown')

        print(f"[*] Scraping tool: {name}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract description
        description = self._extract_description(soup)

        # Extract usage examples
        usage_examples = self._extract_usage_examples(soup)

        # Extract command options
        options = self._extract_options(soup)

        # Extract similar tools
        similar = self._extract_similar_tools(soup)

        # Extract package info
        package_info = self._extract_package_info(soup)

        # Determine category from page if not provided
        if category == 'unknown':
            category = self._detect_category(soup, description)

        return KaliTool(
            name=name,
            url=url,
            category=category,
            description=description,
            usage_examples=usage_examples,
            options=options,
            similar_tools=similar,
            package_info=package_info
        )

    def _extract_description(self, soup) -> str:
        """Extract tool description."""
        # Try common description locations
        desc = ""

        # Look for lead paragraph or description div
        lead = soup.find('p', class_='lead') or soup.find('div', class_='description')
        if lead:
            desc = lead.get_text(strip=True)

        # If not found, get first substantial paragraph
        if not desc:
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 50:
                    desc = text
                    break

        # Also get any article content
        article = soup.find('article') or soup.find('main')
        if article:
            # Get all text content, preserving structure
            full_text = []
            for elem in article.find_all(['p', 'li']):
                text = elem.get_text(strip=True)
                if text and len(text) > 20:
                    full_text.append(text)

            if full_text:
                desc = desc + "\n\n" + "\n".join(full_text[:10])  # First 10 paragraphs

        return desc

    def _extract_usage_examples(self, soup) -> List[str]:
        """Extract usage examples from code blocks."""
        examples = []

        # Find all code/pre blocks
        for code in soup.find_all(['pre', 'code']):
            text = code.get_text(strip=True)
            if text and len(text) > 5:
                # Clean up the example
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and len(line) > 5:
                        examples.append(line)

        return list(set(examples))[:20]  # Limit to 20 unique examples

    def _extract_options(self, soup) -> List[str]:
        """Extract command-line options."""
        options = []

        # Look for options in lists or tables
        for li in soup.find_all('li'):
            text = li.get_text(strip=True)
            # Look for option patterns like "-a, --all"
            if re.match(r'^-{1,2}\w', text):
                options.append(text[:200])  # Limit length

        # Also check for definition lists
        for dt in soup.find_all('dt'):
            text = dt.get_text(strip=True)
            if re.match(r'^-{1,2}\w', text):
                dd = dt.find_next_sibling('dd')
                desc = dd.get_text(strip=True) if dd else ""
                options.append(f"{text}: {desc[:100]}")

        return options[:30]  # Limit to 30 options

    def _extract_similar_tools(self, soup) -> List[str]:
        """Extract similar/related tools."""
        similar = []

        # Look for "similar", "related", "see also" sections
        for header in soup.find_all(['h2', 'h3', 'h4']):
            text = header.get_text(strip=True).lower()
            if any(word in text for word in ['similar', 'related', 'see also', 'alternatives']):
                # Get links after this header
                next_elem = header.find_next_sibling()
                if next_elem:
                    for link in next_elem.find_all('a'):
                        tool_name = link.get_text(strip=True)
                        if tool_name and len(tool_name) < 50:
                            similar.append(tool_name)

        return similar[:10]

    def _extract_package_info(self, soup) -> Optional[str]:
        """Extract package installation info."""
        # Look for apt/package info
        for code in soup.find_all(['pre', 'code']):
            text = code.get_text(strip=True)
            if 'apt' in text or 'install' in text:
                return text[:200]

        return None

    def _detect_category(self, soup, description: str) -> str:
        """Try to detect tool category from content."""
        text = (description or "").lower()

        category_keywords = {
            "information-gathering": ["reconnaissance", "recon", "discovery", "scan", "enumerate"],
            "vulnerability-analysis": ["vulnerability", "vuln", "audit", "assessment"],
            "web-applications": ["web", "http", "api", "injection", "xss"],
            "password-attacks": ["password", "crack", "brute", "hash", "credential"],
            "wireless-attacks": ["wireless", "wifi", "wpa", "wep", "bluetooth"],
            "exploitation-tools": ["exploit", "payload", "shell", "metasploit"],
            "post-exploitation": ["post-exploit", "pivot", "lateral", "persistence"],
            "forensics-tools": ["forensic", "analysis", "artifact", "memory"],
            "sniffing-spoofing": ["sniff", "capture", "spoof", "mitm", "packet"],
        }

        for category, keywords in category_keywords.items():
            if any(kw in text for kw in keywords):
                return category

        return "unknown"

    def save_tool(self, tool: KaliTool):
        """Save tool documentation to disk."""
        safe_name = re.sub(r'[^\w\-]', '_', tool.name.lower())

        # Save as JSON
        output_path = self.output_dir / "processed" / f"{safe_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(tool), f, indent=2, ensure_ascii=False)

        self.scraped_tools.append(tool.name)

    def scrape_all(self, limit: int = None):
        """Scrape all tools."""
        all_tools = self.get_all_tool_urls()

        if limit:
            all_tools = all_tools[:limit]

        for i, tool_info in enumerate(all_tools):
            print(f"\n[{i+1}/{len(all_tools)}]")

            tool = self.scrape_tool(tool_info)
            if tool and tool.description:
                self.save_tool(tool)

            time.sleep(self.delay)

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_tools': len(self.scraped_tools),
                'tools': self.scraped_tools
            }, f, indent=2)

        print(f"\n[+] Scraping complete! {len(self.scraped_tools)} tools saved")
        return self.scraped_tools

    def scrape_by_categories(self, categories: List[str] = None):
        """Scrape tools organized by category."""
        if categories is None:
            categories = TOOL_CATEGORIES

        all_tools = []
        for category in categories:
            tools = self.get_tools_by_category(category)
            for tool in tools:
                tool['category'] = category
            all_tools.extend(tools)
            time.sleep(self.delay)

        # Remove duplicates
        seen = set()
        unique_tools = []
        for tool in all_tools:
            if tool['name'] not in seen:
                seen.add(tool['name'])
                unique_tools.append(tool)

        print(f"[*] Total unique tools: {len(unique_tools)}")

        for i, tool_info in enumerate(unique_tools):
            print(f"\n[{i+1}/{len(unique_tools)}]")

            tool = self.scrape_tool(tool_info)
            if tool and tool.description:
                self.save_tool(tool)

            time.sleep(self.delay)

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_tools': len(self.scraped_tools),
                'tools': self.scraped_tools,
                'categories': categories
            }, f, indent=2)

        print(f"\n[+] Complete! {len(self.scraped_tools)} tools saved")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape Kali Linux tools documentation'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/kali_tools',
        help='Output directory'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.5,
        help='Delay between requests'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit number of tools to scrape'
    )
    parser.add_argument(
        '--by-category',
        action='store_true',
        help='Scrape by category instead of all at once'
    )

    args = parser.parse_args()

    scraper = KaliToolsScraper(args.output, delay=args.delay)

    if args.by_category:
        scraper.scrape_by_categories()
    else:
        scraper.scrape_all(limit=args.limit)


if __name__ == '__main__':
    main()
