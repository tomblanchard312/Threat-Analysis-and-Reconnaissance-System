#!/usr/bin/env python3
"""
PayloadsAllTheThings Scraper for AI Model Training
Scrapes payload collections and bypass techniques from the GitHub repository

This focuses on unique content not covered by HackTricks:
- Specific payload one-liners
- WAF bypass techniques
- Encoding/obfuscation methods
- CVE-specific payloads

Usage:
    python scrape_payloads.py --output ../data/payloads
"""

import argparse
import json
import re
import time
import base64
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests

# Constants
GITHUB_API = "https://api.github.com/repos/swisskyrepo/PayloadsAllTheThings"
RAW_BASE = "https://raw.githubusercontent.com/swisskyrepo/PayloadsAllTheThings/master"
REQUEST_DELAY = 0.5

# Topics to scrape (focusing on payload collections, not methodology)
PAYLOAD_TOPICS = [
    # Shell/Command payloads
    "Command Injection",
    "Reverse Shell Cheatsheet",
    "File Inclusion",
    # Web payloads
    "SQL Injection",
    "XSS Injection",
    "XXE Injection",
    "SSTI Injection",
    "SSRF Injection",
    "CRLF Injection",
    "LDAP Injection",
    "NoSQL Injection",
    "OS Command Injection",
    # Bypass techniques (unique content)
    "WAF Bypass",
    "403 Bypass",
    "Rate Limit Bypass",
    "Upload Insecure Files",
    # Authentication
    "JWT Security",
    "OAuth Misconfiguration",
    "SAML Injection",
    # Serialization
    "Insecure Deserialization",
    "PHP Serialization",
    "Java Deserialization",
    "Python Pickle",
    # Cloud/Modern
    "AWS Amazon Bucket S3",
    "GraphQL Injection",
    "WebSocket Attacks",
    "Prototype Pollution",
    "Mass Assignment",
    # Windows specific
    "Windows - Mimikatz",
    "Windows - Privilege Escalation",
    "Windows - Using credentials",
    # Linux specific
    "Linux - Privilege Escalation",
    "Linux - Persistence",
]


@dataclass
class PayloadCollection:
    """A payload collection from PayloadsAllTheThings."""
    name: str
    path: str
    url: str
    description: str
    payloads: List[Dict[str, str]]  # List of payloads with context
    categories: List[str] = field(default_factory=list)
    bypass_techniques: List[str] = field(default_factory=list)


class PayloadsAllTheThingsScraper:
    """Scraper for PayloadsAllTheThings repository."""

    def __init__(self, output_dir: str, delay: float = REQUEST_DELAY):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HTB-Training-Scraper/1.0 (Educational Purpose)',
            'Accept': 'application/vnd.github.v3+json'
        })
        self.scraped_collections = []

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    def get_repo_contents(self, path: str = "") -> List[dict]:
        """Get contents of repository directory."""
        url = f"{GITHUB_API}/contents/{path}"
        print(f"[*] Fetching: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[!] Failed to fetch {path}: {e}")
            return []

    def get_file_content(self, path: str) -> str:
        """Get raw content of a file."""
        url = f"{RAW_BASE}/{path}"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[!] Failed to fetch {path}: {e}")
            return ""

    def find_readme_files(self) -> List[dict]:
        """Find all README.md files in payload directories."""
        readme_files = []

        # Get top-level directories
        contents = self.get_repo_contents()
        time.sleep(self.delay)

        for item in contents:
            if item['type'] == 'dir' and not item['name'].startswith('.'):
                dir_name = item['name']

                # Check if this is a topic we want
                if any(topic.replace(' ', '%20').lower() in dir_name.lower() or
                       topic.lower().replace(' ', '-') in dir_name.lower() or
                       dir_name.lower().replace('%20', ' ') in topic.lower()
                       for topic in PAYLOAD_TOPICS):

                    # Look for README.md in this directory
                    dir_contents = self.get_repo_contents(dir_name)
                    time.sleep(self.delay)

                    for file_item in dir_contents:
                        if file_item['name'].lower() == 'readme.md':
                            readme_files.append({
                                'name': dir_name.replace('%20', ' '),
                                'path': f"{dir_name}/{file_item['name']}",
                                'url': file_item.get('html_url', ''),
                                'download_url': file_item.get('download_url', '')
                            })
                            break

        print(f"[+] Found {len(readme_files)} payload collections")
        return readme_files

    def parse_markdown_payloads(self, content: str) -> tuple:
        """Parse payloads and techniques from markdown content."""
        payloads = []
        bypass_techniques = []
        categories = []
        description = ""

        lines = content.split('\n')
        current_section = ""
        current_context = ""
        in_code_block = False
        code_block_content = []
        code_block_lang = ""

        for i, line in enumerate(lines):
            # Track code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    # End of code block
                    code = '\n'.join(code_block_content)
                    if code.strip():
                        payloads.append({
                            'payload': code.strip(),
                            'language': code_block_lang,
                            'context': current_context,
                            'section': current_section
                        })
                    code_block_content = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                    code_block_lang = line.strip()[3:].strip()
                continue

            if in_code_block:
                code_block_content.append(line)
                continue

            # Track sections
            if line.startswith('#'):
                header_match = re.match(r'^#+\s+(.+)$', line)
                if header_match:
                    current_section = header_match.group(1).strip()
                    current_context = ""

                    # Categorize sections
                    section_lower = current_section.lower()
                    if 'bypass' in section_lower:
                        categories.append('bypass')
                        bypass_techniques.append(current_section)
                    elif 'payload' in section_lower or 'injection' in section_lower:
                        categories.append('payload')
                    elif 'exploit' in section_lower:
                        categories.append('exploit')

                    # First section after title is usually description
                    if not description and i > 0:
                        # Get text between this header and next
                        for j in range(i+1, min(i+10, len(lines))):
                            if lines[j].startswith('#'):
                                break
                            if lines[j].strip() and not lines[j].startswith('```'):
                                description += lines[j].strip() + " "
                continue

            # Track context (paragraphs before code blocks)
            if line.strip() and not line.startswith('-') and not line.startswith('*'):
                current_context = line.strip()

            # Also capture inline code as payloads
            inline_codes = re.findall(r'`([^`]+)`', line)
            for code in inline_codes:
                # Filter out short/common words
                if len(code) > 10 and not code.startswith('http'):
                    payloads.append({
                        'payload': code,
                        'language': 'inline',
                        'context': current_context or line.strip(),
                        'section': current_section
                    })

        return payloads, bypass_techniques, list(set(categories)), description.strip()

    def scrape_collection(self, readme_info: dict) -> Optional[PayloadCollection]:
        """Scrape a single payload collection."""
        name = readme_info['name']
        path = readme_info['path']

        print(f"[*] Scraping collection: {name}")

        content = self.get_file_content(path)
        if not content:
            return None

        payloads, bypass_techniques, categories, description = self.parse_markdown_payloads(content)

        if not payloads:
            print(f"[!] No payloads found in {name}")
            return None

        return PayloadCollection(
            name=name,
            path=path,
            url=readme_info.get('url', ''),
            description=description,
            payloads=payloads,
            categories=categories,
            bypass_techniques=bypass_techniques
        )

    def save_collection(self, collection: PayloadCollection):
        """Save collection to disk."""
        safe_name = re.sub(r'[^\w\-]', '_', collection.name.lower())

        output_path = self.output_dir / "processed" / f"{safe_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(collection), f, indent=2, ensure_ascii=False)

        self.scraped_collections.append(collection.name)

    def convert_to_training_format(self, collection: PayloadCollection) -> List[dict]:
        """Convert a payload collection to training QA pairs."""
        training_data = []

        # Group payloads by section
        sections = {}
        for payload in collection.payloads:
            section = payload.get('section', 'General')
            if section not in sections:
                sections[section] = []
            sections[section].append(payload)

        # Create training entries for each meaningful section
        for section, payloads in sections.items():
            if len(payloads) < 2:
                continue

            # Create question
            clean_name = collection.name.replace('-', ' ').replace('_', ' ')
            if 'bypass' in section.lower():
                question = f"How can I bypass {clean_name} protections using {section}?"
            elif 'payload' in section.lower():
                question = f"What are some {clean_name} payloads for {section}?"
            else:
                question = f"What are some {section} techniques for {clean_name}?"

            # Build answer
            answer_parts = [f"Here are {section} techniques for {clean_name}:"]

            if collection.description:
                answer_parts.append(f"\n{collection.description[:200]}")

            answer_parts.append("\n\n**Payloads:**")
            for i, p in enumerate(payloads[:10], 1):  # Limit to 10 payloads
                payload_text = p['payload']
                if len(payload_text) > 200:
                    payload_text = payload_text[:200] + "..."

                if p.get('language') and p['language'] != 'inline':
                    answer_parts.append(f"\n{i}. ```{p['language']}\n{payload_text}\n```")
                else:
                    answer_parts.append(f"\n{i}. `{payload_text}`")

                if p.get('context'):
                    context = p['context'][:100]
                    answer_parts.append(f"   ({context})")

            training_data.append({
                'instruction': question,
                'output': '\n'.join(answer_parts),
                'source': 'payloadsallthethings',
                'collection': collection.name,
                'section': section
            })

        # Also create a general entry for the collection
        q_general = f"What {collection.name.replace('-', ' ')} payloads and techniques are available?"
        answer = f"Here's an overview of {collection.name} techniques:\n\n"

        if collection.description:
            answer += f"{collection.description}\n\n"

        if collection.bypass_techniques:
            answer += "**Bypass Techniques:**\n"
            for tech in collection.bypass_techniques[:5]:
                answer += f"- {tech}\n"
            answer += "\n"

        answer += f"**Sample Payloads ({len(collection.payloads)} total):**\n"
        for i, p in enumerate(collection.payloads[:5], 1):
            payload_preview = p['payload'][:100] + "..." if len(p['payload']) > 100 else p['payload']
            answer += f"{i}. `{payload_preview}`\n"

        training_data.append({
            'instruction': q_general,
            'output': answer,
            'source': 'payloadsallthethings',
            'collection': collection.name
        })

        return training_data

    def scrape_all(self, limit: int = None):
        """Scrape all payload collections."""
        readme_files = self.find_readme_files()

        if limit:
            readme_files = readme_files[:limit]

        training_data = []

        for i, readme_info in enumerate(readme_files):
            print(f"\n[{i+1}/{len(readme_files)}]")

            collection = self.scrape_collection(readme_info)
            if collection and collection.payloads:
                self.save_collection(collection)
                training_data.extend(self.convert_to_training_format(collection))

            time.sleep(self.delay)

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_collections': len(self.scraped_collections),
                'collections': self.scraped_collections,
                'topics': PAYLOAD_TOPICS
            }, f, indent=2)

        # Save training data
        training_path = self.output_dir / "payloads_training.jsonl"
        with open(training_path, 'w', encoding='utf-8') as f:
            for entry in training_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"\n[+] Scraping complete!")
        print(f"    - {len(self.scraped_collections)} collections saved")
        print(f"    - {len(training_data)} training entries generated")

        return self.scraped_collections


def main():
    parser = argparse.ArgumentParser(
        description='Scrape PayloadsAllTheThings payload collections'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/payloads',
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
        help='Limit number of collections to scrape'
    )

    args = parser.parse_args()

    scraper = PayloadsAllTheThingsScraper(args.output, delay=args.delay)
    scraper.scrape_all(limit=args.limit)


if __name__ == '__main__':
    main()
