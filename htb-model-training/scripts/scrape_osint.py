#!/usr/bin/env python3
"""
OSINT Resources Scraper/Builder for AI Model Training
Builds OSINT knowledge base from curated sources and generates training data

OSINT (Open Source Intelligence) categories:
- Username enumeration
- Email reconnaissance
- Social media intelligence
- Domain/IP research
- People search
- Image/metadata analysis
- Dark web research
- Company/organization intel

Usage:
    python scrape_osint.py --output ../data/osint
"""

import argparse
import json
import re
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

# Constants
REQUEST_DELAY = 0.5

# OSINT Framework categories with tools and techniques
OSINT_CATEGORIES = {
    "username_enumeration": {
        "description": "Finding accounts associated with a username across platforms",
        "tools": [
            {"name": "sherlock", "url": "https://github.com/sherlock-project/sherlock",
             "usage": "sherlock username", "description": "Hunt down social media accounts by username"},
            {"name": "namechk", "url": "https://namechk.com",
             "usage": "Web-based username checker", "description": "Check username availability across platforms"},
            {"name": "knowem", "url": "https://knowem.com",
             "usage": "Web-based username search", "description": "Check 500+ social networks"},
            {"name": "whatsmyname", "url": "https://whatsmyname.app",
             "usage": "Web-based or API", "description": "Username enumeration across websites"},
            {"name": "maigret", "url": "https://github.com/soxoj/maigret",
             "usage": "maigret username", "description": "Collect person info from usernames"},
            {"name": "social-analyzer", "url": "https://github.com/qeeqbox/social-analyzer",
             "usage": "python -m social-analyzer -u username", "description": "API/CLI for analyzing social profiles"},
        ],
        "techniques": [
            "Search for username variations (user123, user_123, user.123)",
            "Check common platforms: Twitter/X, Instagram, GitHub, LinkedIn, Reddit, TikTok",
            "Use Google dorks: site:twitter.com \"username\"",
            "Check archived versions via Wayback Machine",
            "Look for email patterns: username@gmail.com, username@protonmail.com",
        ]
    },
    "email_reconnaissance": {
        "description": "Gathering intelligence from email addresses",
        "tools": [
            {"name": "theHarvester", "url": "https://github.com/laramies/theHarvester",
             "usage": "theHarvester -d domain.com -b all", "description": "E-mails, subdomains and names from public sources"},
            {"name": "hunter.io", "url": "https://hunter.io",
             "usage": "Web API - find email patterns", "description": "Find professional email addresses"},
            {"name": "phonebook.cz", "url": "https://phonebook.cz",
             "usage": "Web-based email search", "description": "Search emails, domains, URLs from breach data"},
            {"name": "haveibeenpwned", "url": "https://haveibeenpwned.com",
             "usage": "Web/API email breach check", "description": "Check if email was in data breaches"},
            {"name": "emailrep.io", "url": "https://emailrep.io",
             "usage": "curl emailrep.io/email@example.com", "description": "Email reputation and activity"},
            {"name": "holehe", "url": "https://github.com/megadose/holehe",
             "usage": "holehe email@example.com", "description": "Check if email is used on different sites"},
        ],
        "techniques": [
            "Extract domain from email, research company",
            "Search email in Google with quotes",
            "Check paste sites for leaked credentials",
            "Verify email validity with SMTP checks",
            "Look up email in breach databases",
            "Find associated accounts with holehe",
        ]
    },
    "domain_reconnaissance": {
        "description": "Gathering information about domains and websites",
        "tools": [
            {"name": "whois", "url": "builtin",
             "usage": "whois domain.com", "description": "Query domain registration info"},
            {"name": "amass", "url": "https://github.com/owasp-amass/amass",
             "usage": "amass enum -d domain.com", "description": "In-depth attack surface mapping"},
            {"name": "subfinder", "url": "https://github.com/projectdiscovery/subfinder",
             "usage": "subfinder -d domain.com", "description": "Fast passive subdomain enumeration"},
            {"name": "dnsrecon", "url": "https://github.com/darkoperator/dnsrecon",
             "usage": "dnsrecon -d domain.com", "description": "DNS enumeration script"},
            {"name": "dig", "url": "builtin",
             "usage": "dig domain.com ANY", "description": "DNS lookup utility"},
            {"name": "crt.sh", "url": "https://crt.sh",
             "usage": "Web search for SSL certificates", "description": "Certificate transparency logs"},
            {"name": "dnsdumpster", "url": "https://dnsdumpster.com",
             "usage": "Web-based DNS recon", "description": "DNS recon and research"},
            {"name": "securitytrails", "url": "https://securitytrails.com",
             "usage": "Web/API for historical DNS", "description": "Historical DNS data"},
            {"name": "builtwith", "url": "https://builtwith.com",
             "usage": "Web-based tech stack detection", "description": "Identify web technologies"},
            {"name": "wappalyzer", "url": "https://www.wappalyzer.com",
             "usage": "Browser extension or API", "description": "Identify technologies on websites"},
        ],
        "techniques": [
            "Enumerate subdomains with multiple tools",
            "Check historical DNS records for old IPs",
            "Search certificate transparency logs",
            "Identify technology stack for attack vectors",
            "Find related domains via reverse WHOIS",
            "Check robots.txt and sitemap.xml",
            "Use Wayback Machine for historical content",
        ]
    },
    "ip_reconnaissance": {
        "description": "Gathering intelligence about IP addresses",
        "tools": [
            {"name": "shodan", "url": "https://shodan.io",
             "usage": "shodan host IP", "description": "Search engine for Internet-connected devices"},
            {"name": "censys", "url": "https://censys.io",
             "usage": "Web/API search", "description": "Search engine for hosts and networks"},
            {"name": "greynoise", "url": "https://greynoise.io",
             "usage": "API/Web IP lookup", "description": "IP behavior and threat intel"},
            {"name": "ipinfo.io", "url": "https://ipinfo.io",
             "usage": "curl ipinfo.io/IP", "description": "IP geolocation and ASN info"},
            {"name": "abuseipdb", "url": "https://abuseipdb.com",
             "usage": "Web/API reputation check", "description": "IP address abuse reports"},
            {"name": "bgpview", "url": "https://bgpview.io",
             "usage": "Web-based BGP/ASN lookup", "description": "BGP routing and ASN info"},
        ],
        "techniques": [
            "Check IP reputation in threat intel feeds",
            "Identify ASN and hosting provider",
            "Scan for open ports and services with Shodan",
            "Look up reverse DNS records",
            "Check if IP is in blacklists",
            "Find other domains hosted on same IP",
        ]
    },
    "social_media_intelligence": {
        "description": "Gathering information from social media platforms",
        "tools": [
            {"name": "twint", "url": "https://github.com/twintproject/twint",
             "usage": "twint -u username", "description": "Twitter/X scraping tool"},
            {"name": "instaloader", "url": "https://github.com/instaloader/instaloader",
             "usage": "instaloader profile username", "description": "Download Instagram photos and metadata"},
            {"name": "osintgram", "url": "https://github.com/Datalux/Osintgram",
             "usage": "Interactive Instagram OSINT", "description": "Instagram OSINT analysis"},
            {"name": "socialscan", "url": "https://github.com/iojw/socialscan",
             "usage": "socialscan -e email", "description": "Check email/username usage on platforms"},
            {"name": "GHunt", "url": "https://github.com/mxrch/GHunt",
             "usage": "ghunt email@gmail.com", "description": "Google account investigation"},
        ],
        "techniques": [
            "Analyze posting patterns and times",
            "Extract location data from posts",
            "Map social connections and followers",
            "Search hashtags and mentions",
            "Archive posts before they're deleted",
            "Cross-reference profiles across platforms",
            "Extract EXIF data from uploaded images",
        ]
    },
    "image_analysis": {
        "description": "Analyzing images for metadata and reverse searching",
        "tools": [
            {"name": "exiftool", "url": "https://exiftool.org",
             "usage": "exiftool image.jpg", "description": "Read/write metadata in files"},
            {"name": "Google Images", "url": "https://images.google.com",
             "usage": "Upload image for reverse search", "description": "Reverse image search"},
            {"name": "TinEye", "url": "https://tineye.com",
             "usage": "Upload image for reverse search", "description": "Reverse image search engine"},
            {"name": "Yandex Images", "url": "https://yandex.com/images",
             "usage": "Upload image for reverse search", "description": "Reverse image search (good for faces)"},
            {"name": "PimEyes", "url": "https://pimeyes.com",
             "usage": "Upload face image", "description": "Face recognition search engine"},
            {"name": "fotoforensics", "url": "https://fotoforensics.com",
             "usage": "Upload image for analysis", "description": "Image forensics (ELA, metadata)"},
        ],
        "techniques": [
            "Extract GPS coordinates from EXIF data",
            "Check image modification with Error Level Analysis",
            "Reverse search to find image origin",
            "Compare lighting and shadows for authenticity",
            "Search for higher resolution versions",
            "Identify camera model from metadata",
        ]
    },
    "people_search": {
        "description": "Finding information about individuals",
        "tools": [
            {"name": "pipl", "url": "https://pipl.com",
             "usage": "Web/API people search", "description": "Identity resolution platform"},
            {"name": "spokeo", "url": "https://spokeo.com",
             "usage": "Web-based people search", "description": "Aggregate public records"},
            {"name": "whitepages", "url": "https://whitepages.com",
             "usage": "Web-based people search", "description": "Phone/address lookup"},
            {"name": "truepeoplesearch", "url": "https://truepeoplesearch.com",
             "usage": "Web-based people search", "description": "Free people search"},
            {"name": "fastpeoplesearch", "url": "https://fastpeoplesearch.com",
             "usage": "Web-based people search", "description": "Free people search"},
        ],
        "techniques": [
            "Combine name with location for better results",
            "Search for relatives and associates",
            "Check property records and court records",
            "Look up voter registration records",
            "Search obituaries for family connections",
            "Use LinkedIn for professional history",
        ]
    },
    "company_reconnaissance": {
        "description": "Researching companies and organizations",
        "tools": [
            {"name": "LinkedIn", "url": "https://linkedin.com",
             "usage": "Search company employees", "description": "Professional network"},
            {"name": "crunchbase", "url": "https://crunchbase.com",
             "usage": "Web-based company search", "description": "Company information database"},
            {"name": "opencorporates", "url": "https://opencorporates.com",
             "usage": "Web-based company search", "description": "Company registration data"},
            {"name": "glassdoor", "url": "https://glassdoor.com",
             "usage": "Web-based company reviews", "description": "Employee reviews and salary data"},
            {"name": "zoominfo", "url": "https://zoominfo.com",
             "usage": "B2B contact database", "description": "Business contact information"},
        ],
        "techniques": [
            "Map organizational structure from LinkedIn",
            "Find employee email patterns",
            "Research acquisitions and subsidiaries",
            "Check SEC filings for public companies",
            "Review job postings for tech stack hints",
            "Search for data breaches affecting company",
        ]
    },
    "phone_osint": {
        "description": "Gathering information from phone numbers",
        "tools": [
            {"name": "phoneinfoga", "url": "https://github.com/sundowndev/phoneinfoga",
             "usage": "phoneinfoga scan -n +1234567890", "description": "Phone number OSINT framework"},
            {"name": "truecaller", "url": "https://truecaller.com",
             "usage": "Web/App lookup", "description": "Caller ID and spam blocking"},
            {"name": "sync.me", "url": "https://sync.me",
             "usage": "Web-based phone lookup", "description": "Reverse phone lookup"},
            {"name": "numverify", "url": "https://numverify.com",
             "usage": "API phone validation", "description": "Phone number validation"},
        ],
        "techniques": [
            "Identify carrier and country from number",
            "Search number in social media",
            "Check messaging apps (WhatsApp, Telegram)",
            "Use Google to search number in quotes",
            "Check if number is in spam databases",
        ]
    },
    "dark_web_research": {
        "description": "Researching dark web and underground forums",
        "tools": [
            {"name": "Tor Browser", "url": "https://torproject.org",
             "usage": "Browse .onion sites", "description": "Anonymous browsing"},
            {"name": "ahmia", "url": "https://ahmia.fi",
             "usage": "Web search for .onion sites", "description": "Search engine for hidden services"},
            {"name": "onionscan", "url": "https://github.com/s-rah/onionscan",
             "usage": "onionscan onionaddress.onion", "description": "Scan hidden services for issues"},
            {"name": "darksearch", "url": "https://darksearch.io",
             "usage": "API/Web dark web search", "description": "Dark web search engine"},
        ],
        "techniques": [
            "Always use Tor for accessing .onion sites",
            "Use VMs for isolation",
            "Monitor paste sites for leaked data",
            "Track threat actor activities",
            "Search for company mentions in leaks",
            "Use throwaway accounts for research",
        ]
    },
    "geolocation_osint": {
        "description": "Determining physical locations from various sources",
        "tools": [
            {"name": "Google Earth", "url": "https://earth.google.com",
             "usage": "Satellite imagery analysis", "description": "3D globe imagery"},
            {"name": "Google Street View", "url": "https://maps.google.com",
             "usage": "Ground-level imagery", "description": "Street-level photos"},
            {"name": "SunCalc", "url": "https://suncalc.org",
             "usage": "Web-based sun position calculator", "description": "Sun position for time/location"},
            {"name": "GeoGuessr", "url": "https://geoguessr.com",
             "usage": "Location guessing game", "description": "Practice geolocation skills"},
            {"name": "overpass-turbo", "url": "https://overpass-turbo.eu",
             "usage": "OpenStreetMap query tool", "description": "Query OSM data"},
        ],
        "techniques": [
            "Analyze shadows to determine time of day",
            "Look for street signs and landmarks",
            "Check vegetation type for region hints",
            "Analyze architecture styles",
            "Look for license plates and language",
            "Cross-reference multiple image sources",
            "Use sun position to verify timing",
        ]
    }
}


@dataclass
class OSINTCategory:
    """An OSINT category with tools and techniques."""
    name: str
    description: str
    tools: List[Dict[str, str]]
    techniques: List[str]


class OSINTResourceBuilder:
    """Builder for OSINT training resources."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.categories = []

        # Create output directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "processed").mkdir(exist_ok=True)

    def build_category(self, name: str, data: dict) -> OSINTCategory:
        """Build an OSINT category from data."""
        return OSINTCategory(
            name=name,
            description=data.get('description', ''),
            tools=data.get('tools', []),
            techniques=data.get('techniques', [])
        )

    def save_category(self, category: OSINTCategory):
        """Save category to disk."""
        safe_name = re.sub(r'[^\w\-]', '_', category.name.lower())

        output_path = self.output_dir / "processed" / f"{safe_name}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(category), f, indent=2, ensure_ascii=False)

        self.categories.append(category.name)

    def convert_to_training_format(self, category: OSINTCategory) -> List[dict]:
        """Convert an OSINT category to training QA pairs."""
        training_data = []

        clean_name = category.name.replace('_', ' ')

        # General overview question
        q_overview = f"What tools and techniques can I use for {clean_name}?"
        answer = f"Here's an overview of {clean_name}:\n\n"
        answer += f"{category.description}\n\n"

        answer += "**Recommended Tools:**\n"
        for tool in category.tools[:6]:
            answer += f"- **{tool['name']}**: {tool['description']}\n"
            answer += f"  Usage: `{tool['usage']}`\n"

        answer += "\n**Key Techniques:**\n"
        for tech in category.techniques[:5]:
            answer += f"- {tech}\n"

        training_data.append({
            'instruction': q_overview,
            'output': answer,
            'source': 'osint',
            'category': category.name
        })

        # Tool-specific questions
        for tool in category.tools:
            q_tool = f"How do I use {tool['name']} for OSINT?"
            a_tool = f"**{tool['name']}** - {tool['description']}\n\n"
            a_tool += f"**Usage:** `{tool['usage']}`\n\n"
            if tool.get('url') and tool['url'] != 'builtin':
                a_tool += f"**URL:** {tool['url']}\n\n"
            a_tool += f"This tool is commonly used for {clean_name}. "

            # Add related techniques
            relevant_techs = [t for t in category.techniques if tool['name'].lower() in t.lower()]
            if not relevant_techs:
                relevant_techs = category.techniques[:2]

            a_tool += "Related techniques:\n"
            for tech in relevant_techs[:3]:
                a_tool += f"- {tech}\n"

            training_data.append({
                'instruction': q_tool,
                'output': a_tool,
                'source': 'osint',
                'tool': tool['name'],
                'category': category.name
            })

        # Technique-specific questions
        for tech in category.techniques[:5]:
            q_tech = f"How do I {tech.lower().rstrip('.')}?"
            a_tech = f"To {tech.lower().rstrip('.')}:\n\n"

            # Find relevant tools
            relevant_tools = [t for t in category.tools
                           if any(word in tech.lower() for word in t['name'].lower().split())]
            if not relevant_tools:
                relevant_tools = category.tools[:2]

            a_tech += "**Recommended tools:**\n"
            for tool in relevant_tools[:3]:
                a_tech += f"- {tool['name']}: `{tool['usage']}`\n"

            a_tech += f"\nThis is part of {clean_name} in OSINT investigations."

            training_data.append({
                'instruction': q_tech,
                'output': a_tech,
                'source': 'osint',
                'category': category.name
            })

        return training_data

    def build_all(self):
        """Build all OSINT resources."""
        training_data = []

        for name, data in OSINT_CATEGORIES.items():
            print(f"[*] Building category: {name}")

            category = self.build_category(name, data)
            self.save_category(category)
            training_data.extend(self.convert_to_training_format(category))

        # Add cross-category questions
        training_data.extend(self._build_workflow_questions())

        # Save index
        index_path = self.output_dir / "index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump({
                'total_categories': len(self.categories),
                'categories': self.categories,
            }, f, indent=2)

        # Save training data
        training_path = self.output_dir / "osint_training.jsonl"
        with open(training_path, 'w', encoding='utf-8') as f:
            for entry in training_data:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"\n[+] Building complete!")
        print(f"    - {len(self.categories)} categories built")
        print(f"    - {len(training_data)} training entries generated")

        return self.categories

    def _build_workflow_questions(self) -> List[dict]:
        """Build workflow/methodology questions that span categories."""
        workflows = [
            {
                'question': "How do I perform OSINT on a target email address?",
                'answer': """To perform OSINT on an email address, follow this workflow:

**1. Verify the email:**
- Check if email exists with SMTP verification
- Use `holehe` to find accounts: `holehe email@example.com`
- Check HaveIBeenPwned for breaches

**2. Extract information:**
- Domain tells you about organization
- Username might be used elsewhere
- Check phonebook.cz for associated data

**3. Find associated accounts:**
- Use `holehe` or `socialscan` to find platform registrations
- Search the email in quotes on Google
- Check paste sites for leaked data

**4. Research the person:**
- Cross-reference with social media
- Check LinkedIn for professional info
- Look for username patterns

**Tools:** holehe, theHarvester, hunter.io, emailrep.io, haveibeenpwned"""
            },
            {
                'question': "How do I investigate a person using OSINT?",
                'answer': """For investigating a person with OSINT:

**1. Start with known information:**
- Full name, username, email, phone, location
- Any social media profiles

**2. Username enumeration:**
- Use `sherlock` or `maigret`: `sherlock targetusername`
- Check variations: user123, user_123, user.123

**3. Social media analysis:**
- Find all profiles across platforms
- Analyze posts for location/time patterns
- Map connections and followers
- Check tagged photos

**4. Email investigation:**
- Find email from username patterns
- Check for account breaches
- Find associated accounts

**5. Image analysis:**
- Reverse search profile photos
- Extract EXIF metadata from posted images
- Check for face matches with Yandex/PimEyes

**6. Aggregate findings:**
- Cross-reference information
- Verify claims and connections
- Document everything

**Tools:** sherlock, holehe, theHarvester, exiftool, TinEye"""
            },
            {
                'question': "How do I perform reconnaissance on a company?",
                'answer': """For company reconnaissance using OSINT:

**1. Basic information:**
- Search company on OpenCorporates, Crunchbase
- Check SEC filings for public companies
- Review LinkedIn company page

**2. Domain reconnaissance:**
- WHOIS lookup: `whois company.com`
- Subdomain enumeration: `subfinder -d company.com`
- Check certificate transparency: crt.sh

**3. Employee enumeration:**
- Search LinkedIn for employees
- Find email patterns with hunter.io
- Use theHarvester: `theHarvester -d company.com -b all`

**4. Technology stack:**
- Use BuiltWith or Wappalyzer
- Check job postings for tech hints
- Review open source contributions

**5. External exposure:**
- Search Shodan: `shodan search org:"Company Name"`
- Check for exposed services
- Look for data breaches

**6. Social presence:**
- Find official social accounts
- Monitor for brand mentions
- Check employee social activity

**Tools:** amass, subfinder, theHarvester, hunter.io, Shodan, LinkedIn"""
            },
            {
                'question': "What is the OSINT investigation methodology?",
                'answer': """The OSINT investigation methodology follows these phases:

**1. Planning:**
- Define objectives and scope
- Identify available starting information (selectors)
- Choose appropriate tools and techniques
- Set up secure research environment

**2. Collection:**
- Gather data from open sources
- Use multiple tools for each selector
- Document everything with timestamps
- Archive findings (screenshots, downloads)

**3. Processing:**
- Organize collected data
- Remove duplicates
- Validate information accuracy
- Cross-reference sources

**4. Analysis:**
- Identify patterns and connections
- Map relationships between entities
- Create timelines of events
- Assess confidence levels

**5. Reporting:**
- Document findings clearly
- Include evidence and sources
- Highlight key insights
- Provide recommendations

**Key principles:**
- Always use legal, ethical methods
- Verify information from multiple sources
- Maintain operational security
- Document your methodology
- Respect privacy boundaries"""
            }
        ]

        training_data = []
        for wf in workflows:
            training_data.append({
                'instruction': wf['question'],
                'output': wf['answer'],
                'source': 'osint',
                'category': 'workflow'
            })

        return training_data


def main():
    parser = argparse.ArgumentParser(
        description='Build OSINT training resources'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/osint',
        help='Output directory'
    )

    args = parser.parse_args()

    builder = OSINTResourceBuilder(args.output)
    builder.build_all()


if __name__ == '__main__':
    main()
