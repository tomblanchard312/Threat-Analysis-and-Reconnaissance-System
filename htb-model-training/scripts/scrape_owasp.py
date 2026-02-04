#!/usr/bin/env python3
"""
OWASP Testing Guide Scraper for AI Model Training
Scrapes the OWASP Web Security Testing Guide from GitHub

Usage:
    python scrape_owasp.py --output ../data/owasp
"""

import argparse
import json
import re
import time
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict

import requests

# Constants
GITHUB_API = "https://api.github.com"
OWASP_REPO = "OWASP/wstg"
OWASP_RAW = "https://raw.githubusercontent.com/OWASP/wstg/master"
REQUEST_DELAY = 0.3  # GitHub API rate limiting

# Testing categories in OWASP WSTG
TESTING_CATEGORIES = {
    "WSTG-INFO": "Information Gathering",
    "WSTG-CONF": "Configuration and Deployment Management Testing",
    "WSTG-IDNT": "Identity Management Testing",
    "WSTG-ATHN": "Authentication Testing",
    "WSTG-ATHZ": "Authorization Testing",
    "WSTG-SESS": "Session Management Testing",
    "WSTG-INPV": "Input Validation Testing",
    "WSTG-ERRH": "Testing for Error Handling",
    "WSTG-CRYP": "Testing for Weak Cryptography",
    "WSTG-BUSL": "Business Logic Testing",
    "WSTG-CLNT": "Client-side Testing",
    "WSTG-APIT": "API Testing",
}


@dataclass
class OWASPTestCase:
    """A single OWASP test case."""
    id: str
    title: str
    category: str
    category_name: str
    summary: str
    objectives: List[str]
    how_to_test: str
    tools: List[str]
    remediation: str
    references: List[str]
    raw_content: str


class OWASPScraper:
    """Scraper for OWASP Web Security Testing Guide."""

    def __init__(self, output_dir: str, delay: float = REQUEST_DELAY):
        self.output_dir = Path(output_dir)
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HTB-Training-Scraper/1.0 (Educational Purpose)',
            'Accept': 'application/vnd.github.v3+json'
        })
        self.scraped_tests = []

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "raw").mkdir(exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    def get_test_files(self) -> List[Dict]:
        """Get all test case file paths from the repository."""
        print("[*] Fetching OWASP WSTG structure...")

        # The test cases are in document/4-Web_Application_Security_Testing/
        test_dir = "document/4-Web_Application_Security_Testing"
        files = []

        try:
            # Get top-level directories (categories)
            url = f"{GITHUB_API}/repos/{OWASP_REPO}/contents/{test_dir}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            categories = response.json()

            for category in categories:
                if category['type'] == 'dir':
                    # Get files in each category
                    cat_url = category['url']
                    time.sleep(self.delay)

                    cat_response = self.session.get(cat_url, timeout=30)
                    cat_response.raise_for_status()

                    for file_info in cat_response.json():
                        if file_info['name'].endswith('.md') and file_info['name'] != 'README.md':
                            files.append({
                                'name': file_info['name'],
                                'path': file_info['path'],
                                'download_url': file_info.get('download_url'),
                                'category_dir': category['name']
                            })

        except requests.RequestException as e:
            print(f"[!] Failed to fetch file list: {e}")
            # Fallback to known structure
            return self._get_fallback_files()

        print(f"[+] Found {len(files)} test case files")
        return files

    def _get_fallback_files(self) -> List[Dict]:
        """Fallback list of known test files."""
        # Known OWASP WSTG test IDs
        test_ids = [
            # Information Gathering
            "01-Conduct_Search_Engine_Discovery",
            "02-Fingerprint_Web_Server",
            "03-Review_Webserver_Metafiles",
            "04-Enumerate_Applications_on_Webserver",
            "05-Review_Webpage_Content",
            "06-Identify_Application_Entry_Points",
            "07-Map_Execution_Paths",
            "08-Fingerprint_Web_Application_Framework",
            "09-Fingerprint_Web_Application",
            "10-Map_Application_Architecture",
        ]
        # This would need to be expanded with full paths
        return []

    def scrape_test_file(self, file_info: Dict) -> Optional[OWASPTestCase]:
        """Scrape a single test case markdown file."""
        print(f"[*] Scraping: {file_info['name']}")

        try:
            # Get raw content
            if file_info.get('download_url'):
                response = self.session.get(file_info['download_url'], timeout=30)
            else:
                raw_url = f"{OWASP_RAW}/{file_info['path']}"
                response = self.session.get(raw_url, timeout=30)

            response.raise_for_status()
            content = response.text

        except requests.RequestException as e:
            print(f"[!] Failed: {e}")
            return None

        # Parse the markdown content
        return self._parse_test_case(content, file_info)

    def _parse_test_case(self, content: str, file_info: Dict) -> Optional[OWASPTestCase]:
        """Parse markdown content into structured test case."""

        # Extract test ID from filename (e.g., "01-Something.md" -> "WSTG-INFO-01")
        filename = file_info['name']
        category_dir = file_info.get('category_dir', '')

        # Determine category from directory name
        category_code = "WSTG-UNKN"
        category_name = "Unknown"

        for code, name in TESTING_CATEGORIES.items():
            if code.split('-')[1].lower() in category_dir.lower():
                category_code = code
                category_name = name
                break

        # Extract test number
        num_match = re.match(r'^(\d+)', filename)
        test_num = num_match.group(1) if num_match else "00"
        test_id = f"{category_code}-{test_num}"

        # Extract title (usually first H1 or H2)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else filename.replace('.md', '').replace('_', ' ')

        # Extract summary (usually first paragraph after title)
        summary = self._extract_section(content, ['summary', 'overview', 'introduction'])
        if not summary:
            # Get first substantial paragraph
            paragraphs = re.findall(r'\n\n([^#\n].+?)\n\n', content, re.DOTALL)
            summary = paragraphs[0] if paragraphs else ""

        # Extract objectives
        objectives = self._extract_list_section(content, ['objectives', 'goals'])

        # Extract how to test
        how_to_test = self._extract_section(content, ['how to test', 'test', 'testing', 'methodology'])

        # Extract tools
        tools = self._extract_tools(content)

        # Extract remediation
        remediation = self._extract_section(content, ['remediation', 'countermeasures', 'prevention', 'fix'])

        # Extract references
        references = self._extract_references(content)

        return OWASPTestCase(
            id=test_id,
            title=title,
            category=category_code,
            category_name=category_name,
            summary=summary,
            objectives=objectives,
            how_to_test=how_to_test,
            tools=tools,
            remediation=remediation,
            references=references,
            raw_content=content
        )

    def _extract_section(self, content: str, section_names: List[str]) -> str:
        """Extract a section by header name."""
        for name in section_names:
            # Look for header followed by content
            pattern = rf'#+\s*{name}[^\n]*\n(.*?)(?=\n#|\Z)'
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_list_section(self, content: str, section_names: List[str]) -> List[str]:
        """Extract a section that contains a list."""
        section_content = self._extract_section(content, section_names)
        if not section_content:
            return []

        items = []
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* ') or re.match(r'^\d+\.', line):
                # Remove list markers
                item = re.sub(r'^[-*]\s*|\d+\.\s*', '', line)
                if item:
                    items.append(item)

        return items

    def _extract_tools(self, content: str) -> List[str]:
        """Extract tools mentioned in the content."""
        # Common security testing tools
        known_tools = [
            'burp', 'burpsuite', 'zap', 'owasp zap', 'nmap', 'nikto', 'sqlmap',
            'wfuzz', 'ffuf', 'gobuster', 'dirb', 'dirbuster', 'curl', 'wget',
            'hydra', 'john', 'hashcat', 'metasploit', 'nessus', 'openvas',
            'wireshark', 'tcpdump', 'netcat', 'nc', 'socat', 'postman',
            'browser developer tools', 'chrome devtools', 'firefox devtools',
            'feroxbuster', 'nuclei', 'httpx', 'subfinder', 'amass'
        ]

        found_tools = []
        content_lower = content.lower()

        for tool in known_tools:
            if tool in content_lower:
                found_tools.append(tool)

        # Also extract from tool sections
        tool_section = self._extract_section(content, ['tools', 'recommended tools'])
        if tool_section:
            # Look for markdown links or list items
            links = re.findall(r'\[([^\]]+)\]', tool_section)
            found_tools.extend(links)

        return list(set(found_tools))

    def _extract_references(self, content: str) -> List[str]:
        """Extract references and links."""
        refs = []

        # Find reference section
        ref_section = self._extract_section(content, ['references', 'resources', 'further reading'])
        if ref_section:
            # Extract URLs
            urls = re.findall(r'https?://[^\s\)]+', ref_section)
            refs.extend(urls)

            # Extract markdown links
            links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', ref_section)
            for text, url in links:
                refs.append(f"{text}: {url}")

        return refs[:20]  # Limit to 20 references

    def save_test_case(self, test_case: OWASPTestCase):
        """Save test case to disk."""
        safe_name = re.sub(r'[^\w\-]', '_', test_case.id.lower())

        # Save raw markdown
        raw_path = self.output_dir / "raw" / f"{safe_name}.md"
        with open(raw_path, 'w', encoding='utf-8') as f:
            f.write(test_case.raw_content)

        # Save processed JSON
        processed_path = self.output_dir / "processed" / f"{safe_name}.json"
        data = {
            'id': test_case.id,
            'title': test_case.title,
            'category': test_case.category,
            'category_name': test_case.category_name,
            'summary': test_case.summary,
            'objectives': test_case.objectives,
            'how_to_test': test_case.how_to_test,
            'tools': test_case.tools,
            'remediation': test_case.remediation,
            'references': test_case.references
        }

        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.scraped_tests.append(test_case.id)

    def scrape_all(self, limit: int = None):
        """Scrape all OWASP test cases."""
        files = self.get_test_files()

        if limit:
            files = files[:limit]

        for i, file_info in enumerate(files):
            print(f"\n[{i+1}/{len(files)}]")

            test_case = self.scrape_test_file(file_info)
            if test_case:
                self.save_test_case(test_case)

            time.sleep(self.delay)

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_tests': len(self.scraped_tests),
                'tests': self.scraped_tests,
                'categories': TESTING_CATEGORIES
            }, f, indent=2)

        print(f"\n[+] Scraping complete! {len(self.scraped_tests)} test cases saved")
        return self.scraped_tests


def main():
    parser = argparse.ArgumentParser(
        description='Scrape OWASP Web Security Testing Guide'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/owasp',
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
        help='Limit number of test cases to scrape'
    )
    parser.add_argument(
        '--github-token',
        default=None,
        help='GitHub API token for higher rate limits'
    )

    args = parser.parse_args()

    scraper = OWASPScraper(args.output, delay=args.delay)

    if args.github_token:
        scraper.session.headers['Authorization'] = f'token {args.github_token}'

    scraper.scrape_all(limit=args.limit)


if __name__ == '__main__':
    main()
