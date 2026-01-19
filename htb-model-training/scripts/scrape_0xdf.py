#!/usr/bin/env python3
"""
HTB Writeup Scraper for 0xdf.gitlab.io
Scrapes Hack The Box writeups for AI model training.

Usage:
    python scrape_0xdf.py --output ../data/raw_writeups
"""

import argparse
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Constants
BASE_URL = "https://0xdf.gitlab.io"
HTB_INDEX_URL = f"{BASE_URL}/tags/#hackthebox"
REQUEST_DELAY = 1.0  # Be respectful to the server


@dataclass
class WriteupMetadata:
    """Metadata for a single writeup."""
    title: str
    url: str
    machine_name: str
    difficulty: Optional[str] = None
    os_type: Optional[str] = None
    date_published: Optional[str] = None
    tags: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class Writeup:
    """Complete writeup with content."""
    metadata: WriteupMetadata
    raw_html: str
    markdown_content: str
    sections: dict  # Parsed sections like recon, foothold, privesc, etc.


class WriteupScraper:
    """Scraper for 0xdf HTB writeups."""

    def __init__(self, output_dir: str, delay: float = REQUEST_DELAY):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HTB-Training-Scraper/1.0 (Educational Purpose)'
        })

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "raw").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    def get_writeup_urls(self) -> list[WriteupMetadata]:
        """Get list of all HTB writeup URLs from the index page."""
        print(f"[*] Fetching writeup index from {HTB_INDEX_URL}")

        try:
            response = self.session.get(HTB_INDEX_URL, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed to fetch index: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        writeups = []

        # Find all HTB writeup links
        # 0xdf uses a tag-based organization
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # HTB writeups typically follow pattern like /htb-machinename/
            if '/htb-' in href.lower() or 'hackthebox' in href.lower():
                full_url = urljoin(BASE_URL, href)
                title = link.get_text(strip=True)

                # Extract machine name from URL
                machine_match = re.search(r'/htb-(\w+)', href.lower())
                machine_name = machine_match.group(1) if machine_match else title

                if full_url not in [w.url for w in writeups]:
                    writeups.append(WriteupMetadata(
                        title=title,
                        url=full_url,
                        machine_name=machine_name
                    ))

        print(f"[+] Found {len(writeups)} writeup URLs")
        return writeups

    def scrape_writeup(self, metadata: WriteupMetadata) -> Optional[Writeup]:
        """Scrape a single writeup page."""
        print(f"[*] Scraping: {metadata.machine_name} ({metadata.url})")

        try:
            response = self.session.get(metadata.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Failed to fetch {metadata.url}: {e}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract main content
        article = soup.find('article') or soup.find('main') or soup.find('div', class_='post-content')
        if not article:
            article = soup.find('body')

        raw_html = str(article) if article else response.text

        # Convert to markdown-like text
        markdown_content = self._html_to_markdown(article)

        # Parse sections
        sections = self._parse_sections(markdown_content)

        # Extract additional metadata
        metadata.difficulty = self._extract_difficulty(soup)
        metadata.os_type = self._extract_os(soup)
        metadata.date_published = self._extract_date(soup)
        metadata.tags = self._extract_tags(soup)

        return Writeup(
            metadata=metadata,
            raw_html=raw_html,
            markdown_content=markdown_content,
            sections=sections
        )

    def _html_to_markdown(self, soup) -> str:
        """Convert HTML to markdown-like plain text."""
        if soup is None:
            return ""

        # Remove script and style elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer']):
            element.decompose()

        lines = []

        for element in soup.descendants:
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                text = element.get_text(strip=True)
                lines.append(f"\n{'#' * level} {text}\n")

            elif element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    lines.append(f"\n{text}\n")

            elif element.name == 'pre' or element.name == 'code':
                # Preserve code blocks
                code = element.get_text()
                if element.name == 'pre':
                    lines.append(f"\n```\n{code}\n```\n")

            elif element.name == 'li':
                text = element.get_text(strip=True)
                lines.append(f"- {text}")

            elif element.name == 'img':
                alt = element.get('alt', 'image')
                src = element.get('src', '')
                lines.append(f"\n![{alt}]({src})\n")

        return '\n'.join(lines)

    def _parse_sections(self, content: str) -> dict:
        """Parse writeup into logical sections."""
        sections = {
            'recon': '',
            'enumeration': '',
            'foothold': '',
            'user': '',
            'privilege_escalation': '',
            'root': '',
            'beyond_root': '',
            'full_content': content
        }

        # Common section headers in HTB writeups
        section_patterns = {
            'recon': r'(?i)(recon|reconnaissance|nmap|scanning)',
            'enumeration': r'(?i)(enumeration|enum|directory|gobuster|feroxbuster)',
            'foothold': r'(?i)(foothold|initial access|shell|exploit)',
            'user': r'(?i)(user\.txt|user flag|lateral)',
            'privilege_escalation': r'(?i)(priv\s*esc|privilege|escalation|root\.txt)',
            'root': r'(?i)(root|admin|system)',
            'beyond_root': r'(?i)(beyond|extra|bonus)',
        }

        # Split by headers and categorize
        header_pattern = r'^(#{1,4})\s+(.+)$'
        current_section = None
        current_content = []

        for line in content.split('\n'):
            header_match = re.match(header_pattern, line)
            if header_match:
                # Save previous section
                if current_section and current_content:
                    sections[current_section] += '\n'.join(current_content)

                # Determine new section
                header_text = header_match.group(2)
                current_section = None
                for section_name, pattern in section_patterns.items():
                    if re.search(pattern, header_text):
                        current_section = section_name
                        break
                current_content = [line]
            else:
                current_content.append(line)

        # Save last section
        if current_section and current_content:
            sections[current_section] += '\n'.join(current_content)

        return sections

    def _extract_difficulty(self, soup) -> Optional[str]:
        """Extract machine difficulty."""
        text = soup.get_text().lower()
        for diff in ['easy', 'medium', 'hard', 'insane']:
            if diff in text:
                return diff.capitalize()
        return None

    def _extract_os(self, soup) -> Optional[str]:
        """Extract operating system type."""
        text = soup.get_text().lower()
        if 'linux' in text:
            return 'Linux'
        elif 'windows' in text:
            return 'Windows'
        return None

    def _extract_date(self, soup) -> Optional[str]:
        """Extract publication date."""
        time_elem = soup.find('time')
        if time_elem:
            return time_elem.get('datetime') or time_elem.get_text(strip=True)
        return None

    def _extract_tags(self, soup) -> list:
        """Extract tags from the page."""
        tags = []
        for tag_elem in soup.find_all('a', class_=re.compile(r'tag|category')):
            tag = tag_elem.get_text(strip=True).lower()
            if tag:
                tags.append(tag)
        return tags

    def save_writeup(self, writeup: Writeup):
        """Save writeup to disk."""
        machine_name = writeup.metadata.machine_name.lower().replace(' ', '_')

        # Save raw HTML
        raw_path = self.output_dir / "raw" / f"{machine_name}.html"
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(writeup.raw_html)

        # Save processed content as JSON
        processed_path = self.output_dir / "processed" / f"{machine_name}.json"
        data = {
            'metadata': asdict(writeup.metadata),
            'markdown_content': writeup.markdown_content,
            'sections': writeup.sections
        }
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[+] Saved: {machine_name}")

    def scrape_all(self, limit: Optional[int] = None):
        """Scrape all writeups."""
        writeup_list = self.get_writeup_urls()

        if limit:
            writeup_list = writeup_list[:limit]

        scraped = []
        for i, metadata in enumerate(writeup_list):
            print(f"\n[{i+1}/{len(writeup_list)}]")

            writeup = self.scrape_writeup(metadata)
            if writeup:
                self.save_writeup(writeup)
                scraped.append(metadata.machine_name)

            # Rate limiting
            time.sleep(self.delay)

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_scraped': len(scraped),
                'machines': scraped
            }, f, indent=2)

        print(f"\n[+] Scraping complete! {len(scraped)} writeups saved to {self.output_dir}")
        return scraped


def main():
    parser = argparse.ArgumentParser(
        description='Scrape 0xdf HTB writeups for model training'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/raw_writeups',
        help='Output directory for scraped data'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit number of writeups to scrape (for testing)'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=1.0,
        help='Delay between requests in seconds'
    )

    args = parser.parse_args()

    scraper = WriteupScraper(args.output, delay=args.delay)
    scraper.scrape_all(limit=args.limit)


if __name__ == '__main__':
    main()
