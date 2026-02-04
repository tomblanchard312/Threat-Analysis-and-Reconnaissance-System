#!/usr/bin/env python3
"""
Training Data Cleaning Script
Removes artifacts, fixes encoding, and improves data quality for model training.

Issues addressed:
1. Concatenated tags without spaces (hacktheboxctfhtb-ouijanmap...)
2. Markdown image tags (![alt](url)) - no actual images in training
3. Badge/external links (hackthebox.com/badge/image/...)
4. Unicode encoding issues (�?T instead of apostrophes)
5. Radar charts, difficulty ratings, first blood metadata
6. Excessive whitespace and newlines

Usage:
    python clean_training_data.py --input ../data/training/htb_pentest_v4.jsonl --output ../data/training/htb_pentest_v4_clean.jsonl
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import unicodedata


class TrainingDataCleaner:
    """Clean training data for improved model quality."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.stats = {
            'total_records': 0,
            'cleaned_records': 0,
            'removed_records': 0,
            'fixes': {
                'unicode': 0,
                'image_tags': 0,
                'badge_links': 0,
                'concatenated_tags': 0,
                'metadata_noise': 0,
                'excessive_whitespace': 0,
                'html_tags': 0,
            }
        }

        # Patterns to remove
        self.patterns = {
            # Markdown image tags - ![alt text](url)
            'image_tags': re.compile(r'!\[[^\]]*\]\([^)]+\)'),

            # Badge links from hackthebox
            'badge_links': re.compile(r'\[.*?\]\(https?://www\.hackthebox\.com/badge/[^)]+\)'),

            # Standalone dates that appear after tag mess
            'trailing_date': re.compile(r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\s*$', re.MULTILINE),

            # Difficulty/radar chart references
            'metadata_noise': re.compile(
                r'(?:Rated difficulty for|Radar chart for|First Blood User|First Blood Root|Box Info)\s*\S*',
                re.IGNORECASE
            ),

            # HTML tags that slipped through
            'html_tags': re.compile(r'<[^>]+>'),

            # Empty markdown headers
            'empty_headers': re.compile(r'^#+\s*$', re.MULTILINE),

            # Orphaned link markers
            'orphaned_links': re.compile(r'\[+\]+|\(+\)+'),

            # Icon references
            'icon_refs': re.compile(r'/icons/[a-zA-Z0-9_-]+\.(png|jpg|svg|gif)', re.IGNORECASE),

            # Image path references
            'img_refs': re.compile(r'/img/[a-zA-Z0-9_-]+\.(png|jpg|svg|gif)', re.IGNORECASE),

            # Multiple consecutive newlines (more than 2)
            'excess_newlines': re.compile(r'\n{3,}'),

            # Multiple consecutive spaces
            'excess_spaces': re.compile(r' {3,}'),
        }

        # Unicode replacements - use explicit unicode escapes for reliability
        self.unicode_fixes = {
            '\u2019': "'",  # RIGHT SINGLE QUOTATION MARK (most common issue)
            '\u2018': "'",  # LEFT SINGLE QUOTATION MARK
            '\u201c': '"',  # LEFT DOUBLE QUOTATION MARK
            '\u201d': '"',  # RIGHT DOUBLE QUOTATION MARK
            '\u2013': '-',  # EN DASH
            '\u2014': '-',  # EM DASH
            '\u2026': '...', # HORIZONTAL ELLIPSIS
            '\u00a0': ' ',  # Non-breaking space
            '\u200b': '',   # Zero-width space
            '\ufffd': '',   # Replacement character
            # Additional problematic sequences
            '�?T': "'",
            '�?t': "'",
            '�??': '"',
            '�?"': '"',
        }

    def fix_unicode(self, text: str) -> str:
        """Fix unicode encoding issues."""
        if not text:
            return text

        original = text

        # Apply direct replacements
        for bad, good in self.unicode_fixes.items():
            if bad in text:
                text = text.replace(bad, good)

        # Normalize unicode
        text = unicodedata.normalize('NFKC', text)

        if text != original:
            self.stats['fixes']['unicode'] += 1

        return text

    def remove_image_tags(self, text: str) -> str:
        """Remove markdown image tags."""
        original = text
        text = self.patterns['image_tags'].sub('', text)
        if text != original:
            self.stats['fixes']['image_tags'] += 1
        return text

    def remove_badge_links(self, text: str) -> str:
        """Remove hackthebox badge links."""
        original = text
        text = self.patterns['badge_links'].sub('', text)
        if text != original:
            self.stats['fixes']['badge_links'] += 1
        return text

    def remove_concatenated_tags(self, text: str) -> str:
        """Remove concatenated tag strings (e.g., hacktheboxctfhtb-ouijanmap...May 18, 2024)."""
        original = text

        # Process line by line for efficiency
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip empty lines (keep them)
            if not stripped:
                cleaned_lines.append(line)
                continue

            # Detect tag-like lines: all lowercase/hyphens/digits, no spaces, 50+ chars
            if len(stripped) > 50 and ' ' not in stripped:
                # Check if it looks like concatenated tags
                if re.match(r'^[a-z0-9-]+$', stripped):
                    self.stats['fixes']['concatenated_tags'] += 1
                    continue  # Skip this line

            # Also remove lines that are just tags followed by a date
            # e.g., "hacktheboxctf...extensionMay 18, 2024"
            if len(stripped) > 30 and re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}$', stripped):
                if ' ' not in stripped[:30]:  # First 30 chars have no spaces = concatenated
                    self.stats['fixes']['concatenated_tags'] += 1
                    continue  # Skip this line

            cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # Remove standalone trailing dates
        text = self.patterns['trailing_date'].sub('', text)

        return text

    def remove_metadata_noise(self, text: str) -> str:
        """Remove difficulty ratings, radar charts, first blood, etc."""
        original = text

        text = self.patterns['metadata_noise'].sub('', text)
        text = self.patterns['icon_refs'].sub('', text)
        text = self.patterns['img_refs'].sub('', text)

        if text != original:
            self.stats['fixes']['metadata_noise'] += 1

        return text

    def remove_html_tags(self, text: str) -> str:
        """Remove any HTML tags that slipped through."""
        original = text
        text = self.patterns['html_tags'].sub('', text)
        if text != original:
            self.stats['fixes']['html_tags'] += 1
        return text

    def clean_whitespace(self, text: str) -> str:
        """Clean up excessive whitespace."""
        original = text

        # Remove empty headers
        text = self.patterns['empty_headers'].sub('', text)

        # Remove orphaned link markers
        text = self.patterns['orphaned_links'].sub('', text)

        # Normalize newlines
        text = self.patterns['excess_newlines'].sub('\n\n', text)

        # Normalize spaces
        text = self.patterns['excess_spaces'].sub(' ', text)

        # Strip lines
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Strip overall
        text = text.strip()

        if text != original:
            self.stats['fixes']['excessive_whitespace'] += 1

        return text

    def clean_text(self, text: str) -> str:
        """Apply all cleaning operations to text."""
        if not text:
            return text

        # Order matters here
        text = self.fix_unicode(text)
        text = self.remove_concatenated_tags(text)
        text = self.remove_image_tags(text)
        text = self.remove_badge_links(text)
        text = self.remove_metadata_noise(text)
        text = self.remove_html_tags(text)
        text = self.clean_whitespace(text)

        return text

    def clean_record(self, record: Dict) -> Optional[Dict]:
        """Clean a single training record."""
        self.stats['total_records'] += 1

        # Clean instruction
        if 'instruction' in record:
            record['instruction'] = self.clean_text(record['instruction'])

        # Clean input
        if 'input' in record:
            record['input'] = self.clean_text(record['input'])

        # Clean output (main content)
        if 'output' in record:
            record['output'] = self.clean_text(record['output'])

            # Skip if output is now too short (less than 50 chars)
            if len(record['output']) < 50:
                self.stats['removed_records'] += 1
                return None

        self.stats['cleaned_records'] += 1
        return record

    def process_file(self, input_path: Path, output_path: Path):
        """Process a JSONL file and write cleaned output."""
        if self.verbose:
            print(f"[*] Processing {input_path}")

        cleaned_records = []

        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    cleaned = self.clean_record(record)
                    if cleaned:
                        cleaned_records.append(cleaned)
                except json.JSONDecodeError as e:
                    if self.verbose:
                        print(f"[!] JSON error on line {line_num}: {e}")

        # Write cleaned output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in cleaned_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')

        if self.verbose:
            print(f"\n[+] Cleaned data saved to {output_path}")
            self.print_stats()

    def print_stats(self):
        """Print cleaning statistics."""
        print("\n=== Cleaning Statistics ===")
        print(f"Total records processed: {self.stats['total_records']}")
        print(f"Records kept: {self.stats['cleaned_records']}")
        print(f"Records removed (too short): {self.stats['removed_records']}")
        print("\nFixes applied:")
        for fix_type, count in self.stats['fixes'].items():
            if count > 0:
                print(f"  - {fix_type}: {count}")


def add_nas_training_data(output_path: Path):
    """Add NAS/Synology-specific training examples."""

    nas_examples = [
        {
            "instruction": "How do I enumerate a Synology NAS?",
            "input": "Target: 192.168.1.100",
            "output": """To enumerate a Synology NAS, follow these steps:

## 1. Port Scanning
```bash
nmap -sV -sC -p- 192.168.1.100
```

Common Synology ports:
- 5000/5001: DSM Web Interface (HTTP/HTTPS)
- 139/445: SMB/CIFS
- 22: SSH (often disabled or filtered)
- 111/2049: NFS
- 3260/3261: iSCSI
- 80/443: Web Station

## 2. DSM Version Detection
```bash
curl -k https://192.168.1.100:5001/webman/info.cgi
```
This reveals DSM version info (major, minor, build number).

## 3. API Enumeration
```bash
curl -k "https://192.168.1.100:5001/webapi/query.cgi?api=SYNO.API.Info&version=1&method=query"
```
Returns list of available APIs and their paths.

## 4. SMB Enumeration
```bash
enum4linux -a 192.168.1.100
smbclient -L //192.168.1.100 -N
```

## 5. Check for Web Applications
- /wordpress/ - WordPress
- /photo/ - Photo Station
- /video/ - Video Station
- /file/ - File Station

## Key Findings to Document
- DSM version (check for CVEs)
- Exposed services
- Share names and permissions
- User enumeration results
- Custom applications""",
            "category": "nas_enumeration",
            "source": "synthetic_nas",
            "tools": ["nmap", "curl", "enum4linux", "smbclient"]
        },
        {
            "instruction": "What are common Synology DSM vulnerabilities?",
            "input": "",
            "output": """Common Synology DSM vulnerabilities to check:

## Authentication Bypasses
- CVE-2024-29243: Authentication bypass in certain DSM versions
- Check for default credentials (admin/admin or admin/blank)

## Remote Code Execution
- CVE-2022-27620: RCE in Synology VPN Plus Server
- CVE-2021-44142: Samba vfs_fruit module heap overflow

## Information Disclosure
- /webman/info.cgi - Version disclosure without auth
- /webapi/query.cgi - API enumeration
- Serial number exposure via web interface

## Configuration Issues
- SMB guest access enabled
- NFS exports without authentication
- SSH with weak passwords
- Exposed iSCSI targets

## Web Application Vulnerabilities
- Photo Station XSS/SQLi (older versions)
- File Station path traversal (older versions)

## Enumeration Commands
```bash
# Check DSM version
curl -k https://target:5001/webman/info.cgi

# Enumerate APIs
curl -k "https://target:5001/webapi/query.cgi?api=SYNO.API.Info&version=1&method=query"

# Check SMB
smbclient -L //target -N
crackmapexec smb target
```

Always check CVE databases for the specific DSM version found.""",
            "category": "nas_vulnerabilities",
            "source": "synthetic_nas",
            "tools": ["curl", "smbclient", "crackmapexec", "nmap"]
        },
        {
            "instruction": "How do I enumerate NFS shares?",
            "input": "Target has NFS running on port 2049",
            "output": """To enumerate NFS shares:

## 1. Show Available Exports
```bash
showmount -e 192.168.1.100
```

## 2. Check RPC Services
```bash
rpcinfo -p 192.168.1.100
```

## 3. Mount Shares (if accessible)
```bash
mkdir /mnt/nfs_share
mount -t nfs 192.168.1.100:/share /mnt/nfs_share
# Or with options:
mount -t nfs -o nolock,vers=3 192.168.1.100:/share /mnt/nfs_share
```

## 4. Nmap NFS Scripts
```bash
nmap --script nfs-ls,nfs-showmount,nfs-statfs -p 111,2049 192.168.1.100
```

## 5. Check for Sensitive Files
After mounting, look for:
- SSH keys (~/.ssh/)
- Configuration files
- Backup files
- Database dumps
- Credentials in scripts

## Common Issues
- Root squashing disabled (no_root_squash)
- World-readable sensitive files
- Weak export permissions
- Anonymous access to sensitive shares

## Privilege Escalation via NFS
If no_root_squash is set:
1. Create SUID binary on your machine
2. Copy to NFS share
3. Execute from target as unprivileged user""",
            "category": "nfs_enumeration",
            "source": "synthetic_nas",
            "tools": ["showmount", "rpcinfo", "mount", "nmap"]
        },
        {
            "instruction": "How do I test iSCSI targets?",
            "input": "Found iSCSI on port 3260",
            "output": """To enumerate and test iSCSI targets:

## 1. Discover Targets
```bash
iscsiadm -m discovery -t sendtargets -p 192.168.1.100:3260
```

## 2. List Discovered Targets
```bash
iscsiadm -m node
```

## 3. Login to Target
```bash
iscsiadm -m node --targetname iqn.2000-01.com.synology:nas.target1 -p 192.168.1.100:3260 --login
```

## 4. Check New Block Devices
```bash
lsblk
fdisk -l
```

## 5. Mount the LUN
```bash
mount /dev/sdb1 /mnt/iscsi
```

## 6. Nmap iSCSI Enumeration
```bash
nmap --script iscsi-info -p 3260 192.168.1.100
```

## Security Concerns
- No CHAP authentication
- Exposed snapshots/backups
- Full disk access to VMs
- Sensitive data on LUNs

## Logout When Done
```bash
iscsiadm -m node --targetname iqn.xxx -p 192.168.1.100:3260 --logout
```""",
            "category": "iscsi_enumeration",
            "source": "synthetic_nas",
            "tools": ["iscsiadm", "nmap", "lsblk", "fdisk"]
        },
        {
            "instruction": "How do I enumerate a QNAP NAS?",
            "input": "Target appears to be QNAP",
            "output": """QNAP NAS enumeration methodology:

## 1. Port Scanning
```bash
nmap -sV -sC -p- target
```

Common QNAP ports:
- 8080: QTS Web Interface (HTTP)
- 443: QTS Web Interface (HTTPS)
- 139/445: SMB
- 22: SSH
- 111/2049: NFS
- 3260: iSCSI

## 2. Version Detection
```bash
curl -k https://target/cgi-bin/authLogin.cgi
```

Check response for firmware version info.

## 3. Default Credentials
- admin/admin (most common)
- admin/[MAC address last 6 chars]

## 4. Known Vulnerabilities
- CVE-2021-28799: HBS 3 RCE (Qlocker ransomware)
- CVE-2020-36195: SQL Injection in Multimedia Console
- CVE-2019-7192-7195: Multiple RCE vulnerabilities

## 5. Web Application Testing
Check these paths:
- /cgi-bin/authLogin.cgi
- /photo/
- /musicstation/
- /videostation/
- /download/

## 6. SMB Enumeration
```bash
enum4linux -a target
smbmap -H target
crackmapexec smb target
```

## Key Points
- QTS is based on Linux
- Many packages have their own vulnerabilities
- Photo Station is frequently vulnerable
- Check for anonymous share access""",
            "category": "nas_enumeration",
            "source": "synthetic_nas",
            "tools": ["nmap", "curl", "enum4linux", "smbmap", "crackmapexec"]
        },
        {
            "instruction": "What smart home hubs should I look for during reconnaissance?",
            "input": "",
            "output": """Smart home hubs commonly found on networks:

## Homebridge (Port 8581 typically)
- Apple HomeKit bridge for non-native devices
- Web UI usually at http://target:8581
- Check for:
  - Default credentials (check docs for version)
  - Exposed API endpoints
  - Plugin vulnerabilities
  - Config file exposure

## Home Assistant (Port 8123)
- Popular open-source automation
- API at /api/
- Check for:
  - Authentication bypass
  - YAML config exposure
  - Supervisor API access
  - Add-on vulnerabilities

## Hubitat (Port 80/443)
- Local-only automation hub
- Check /hub/advanced for settings
- API documentation at /docs

## OpenHAB (Port 8080)
- Java-based automation
- REST API at /rest/
- Check for unauthenticated access

## Samsung SmartThings
- Cloud-dependent but local API exists
- Check for IDE access

## Security Implications
- IoT device control = physical impact
- Network pivoting opportunities
- Credential harvesting
- Lateral movement via connected devices

## Enumeration
```bash
# Find web interfaces
nmap -sV -p 80,443,8080,8081,8123,8581 target

# Check for common paths
gobuster dir -u http://target:8123 -w /usr/share/wordlists/dirb/common.txt
```""",
            "category": "iot_enumeration",
            "source": "synthetic_nas",
            "tools": ["nmap", "gobuster", "curl"]
        },
        {
            "instruction": "Scan the Synology NAS for vulnerabilities",
            "input": "Target: 192.168.100.15, DSM 7.2",
            "output": """<tool_call>{"name": "pentest-tools", "arguments": {"command": "nmap", "args": "-sV --script vuln,http-vuln*,smb-vuln* -p 22,80,139,443,445,5000,5001 192.168.100.15"}}</tool_call>

After the scan, also check:

1. DSM version disclosure:
<tool_call>{"name": "pentest-tools", "arguments": {"command": "curl", "args": "-k https://192.168.100.15:5001/webman/info.cgi"}}</tool_call>

2. SMB enumeration:
<tool_call>{"name": "pentest-tools", "arguments": {"command": "enum4linux", "args": "-a 192.168.100.15"}}</tool_call>

3. Check CVE database for DSM 7.2 vulnerabilities manually.""",
            "category": "tool_calling",
            "source": "synthetic_nas",
            "tools": ["nmap", "curl", "enum4linux"]
        },
        {
            "instruction": "What is the custom HTTP header 'getthefuckoffmynetwork' telling us?",
            "input": "Found Server: getthefuckoffmynetwork in HTTP response",
            "output": """A custom Server header like 'getthefuckoffmynetwork' indicates:

## What It Tells Us
1. **Custom Configuration**: Admin has modified default server header
2. **Security Awareness**: Attempting to hide server software
3. **Not Effective Security**: Security through obscurity doesn't work

## Why Admins Do This
- Hide web server software (nginx, Apache)
- Discourage casual attackers
- Personal humor/message

## What to Do Next
1. **Fingerprint Anyway**:
```bash
whatweb target
nikto -h target
```

2. **Check Other Headers**: The server might leak info elsewhere:
- X-Powered-By
- Via
- X-AspNet-Version

3. **Behavioral Fingerprinting**: Analyze:
- Error page formatting
- Default file locations
- Response to invalid methods

4. **Continue Enumeration**: The custom header doesn't change:
- Port scan results
- Service versions from banners
- Application vulnerabilities

## Document the Finding
- Shows admin customization
- May indicate other custom security measures
- Worth noting but low severity""",
            "category": "web_analysis",
            "source": "synthetic_nas",
            "tools": ["whatweb", "nikto", "curl"]
        },
    ]

    # Append to existing file
    with open(output_path, 'a', encoding='utf-8') as f:
        for example in nas_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"[+] Added {len(nas_examples)} NAS-specific training examples")


def main():
    parser = argparse.ArgumentParser(
        description='Clean training data to remove artifacts and improve quality'
    )
    parser.add_argument(
        '--input', '-i',
        default='../data/training/htb_pentest_v4.jsonl',
        help='Input JSONL file'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/training/htb_pentest_v4_clean.jsonl',
        help='Output JSONL file'
    )
    parser.add_argument(
        '--add-nas',
        action='store_true',
        default=True,
        help='Add NAS/Synology-specific training examples'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    # Resolve relative paths
    if not input_path.is_absolute():
        script_dir = Path(__file__).parent
        input_path = (script_dir / input_path).resolve()
        output_path = (script_dir / args.output).resolve()

    if not input_path.exists():
        print(f"[!] Input file not found: {input_path}")
        return 1

    cleaner = TrainingDataCleaner(verbose=not args.quiet)
    cleaner.process_file(input_path, output_path)

    if args.add_nas:
        add_nas_training_data(output_path)

    print("\n[+] Cleaning complete!")
    print(f"[+] Clean data: {output_path}")

    return 0


if __name__ == '__main__':
    exit(main())
