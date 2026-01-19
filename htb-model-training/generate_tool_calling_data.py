#!/usr/bin/env python3
"""
Generate tool-calling training data for htb-pentest model v3.
This teaches the model when and how to invoke pentest tools.
"""

import json
import random
from pathlib import Path

# Tool call format that AnythingLLM expects
TOOL_CALL_FORMAT = '<tool_call>{{"name": "pentest-tools", "arguments": {{"command": "{cmd}", "args": "{args}"}}}}</tool_call>'

def generate_nmap_examples():
    """Generate nmap tool-calling examples."""
    examples = []

    # Target variations
    targets = [
        "192.168.1.1", "10.10.10.1", "172.16.0.1", "10.0.0.1",
        "192.168.100.1", "10.10.14.5", "target.htb", "10.129.x.x"
    ]

    # Basic scans
    prompts = [
        ("Scan {ip} for open ports", "-sV {ip}"),
        ("Run a quick scan on {ip}", "-F {ip}"),
        ("Do a full port scan of {ip}", "-p- {ip}"),
        ("Check what services are running on {ip}", "-sV -sC {ip}"),
        ("Scan {ip} with default scripts", "-sC {ip}"),
        ("Run an aggressive scan on {ip}", "-A {ip}"),
        ("Scan the top 1000 ports on {ip}", "--top-ports 1000 {ip}"),
        ("Do a UDP scan on {ip}", "-sU {ip}"),
        ("Run a stealth SYN scan on {ip}", "-sS {ip}"),
        ("Scan {ip} for vulnerabilities", "--script vuln {ip}"),
        ("Check if {ip} has any SMB vulnerabilities", "--script smb-vuln* -p 445 {ip}"),
        ("Enumerate SMB shares on {ip}", "--script smb-enum-shares -p 445 {ip}"),
        ("Scan {ip} for web services", "-p 80,443,8080,8443 -sV {ip}"),
        ("Do OS detection on {ip}", "-O {ip}"),
        ("Run a ping scan on {ip}", "-sn {ip}"),
        ("Scan {ip} without ping", "-Pn {ip}"),
        ("Fast scan {ip} with version detection", "-F -sV {ip}"),
        ("Enumerate HTTP methods on {ip}", "--script http-methods -p 80,443 {ip}"),
        ("Check for default credentials on {ip}", "--script http-default-accounts -p 80,443 {ip}"),
        ("Scan {ip} for FTP vulnerabilities", "--script ftp-vuln* -p 21 {ip}"),
    ]

    for target in targets[:5]:  # Use subset of targets
        for prompt_template, args_template in prompts:
            prompt = prompt_template.format(ip=target)
            args = args_template.format(ip=target)

            examples.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd="nmap", args=args)}
                ]
            })

    return examples

def generate_ping_examples():
    """Generate ping tool-calling examples."""
    examples = []

    targets = ["192.168.1.1", "10.10.10.1", "8.8.8.8", "google.com", "target.htb"]

    prompts = [
        ("Ping {ip}", "-c 4 {ip}"),
        ("Check if {ip} is alive", "-c 4 {ip}"),
        ("Is {ip} reachable?", "-c 4 {ip}"),
        ("Test connectivity to {ip}", "-c 4 {ip}"),
        ("Can you ping {ip} for me?", "-c 4 {ip}"),
        ("Send 10 pings to {ip}", "-c 10 {ip}"),
        ("Quick ping check on {ip}", "-c 2 {ip}"),
    ]

    for target in targets:
        for prompt_template, args_template in prompts:
            prompt = prompt_template.format(ip=target)
            args = args_template.format(ip=target)

            examples.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd="ping", args=args)}
                ]
            })

    return examples

def generate_dns_examples():
    """Generate DNS lookup tool-calling examples."""
    examples = []

    domains = ["example.com", "target.htb", "hackthebox.com", "google.com", "megacorp.local"]

    # nslookup examples
    nslookup_prompts = [
        ("Look up DNS for {domain}", "{domain}"),
        ("What's the IP of {domain}?", "{domain}"),
        ("Resolve {domain}", "{domain}"),
        ("DNS lookup for {domain}", "{domain}"),
        ("Find the IP address of {domain}", "{domain}"),
    ]

    for domain in domains:
        for prompt_template, args_template in nslookup_prompts:
            prompt = prompt_template.format(domain=domain)
            args = args_template.format(domain=domain)

            examples.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd="nslookup", args=args)}
                ]
            })

    # dig examples
    dig_prompts = [
        ("Get all DNS records for {domain}", "ANY {domain}"),
        ("Find MX records for {domain}", "MX {domain}"),
        ("Get TXT records for {domain}", "TXT {domain}"),
        ("Find nameservers for {domain}", "NS {domain}"),
        ("Do a zone transfer on {domain}", "AXFR {domain}"),
        ("Get A records for {domain}", "A {domain}"),
    ]

    for domain in domains[:3]:
        for prompt_template, args_template in dig_prompts:
            prompt = prompt_template.format(domain=domain)
            args = args_template.format(domain=domain)

            examples.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd="dig", args=args)}
                ]
            })

    return examples

def generate_curl_examples():
    """Generate curl/wget tool-calling examples."""
    examples = []

    urls = [
        "http://192.168.1.1", "http://10.10.10.1:8080",
        "https://target.htb", "http://10.10.10.1/robots.txt"
    ]

    curl_prompts = [
        ("Fetch {url}", "{url}"),
        ("Get the contents of {url}", "{url}"),
        ("Check {url}", "-I {url}"),
        ("Get headers from {url}", "-I {url}"),
        ("Download {url}", "-O {url}"),
        ("Make a request to {url}", "-v {url}"),
        ("Check if {url} is up", "-I {url}"),
    ]

    for url in urls:
        for prompt_template, args_template in curl_prompts:
            prompt = prompt_template.format(url=url)
            args = args_template.format(url=url)

            examples.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd="curl", args=args)}
                ]
            })

    return examples

def generate_whois_examples():
    """Generate whois tool-calling examples."""
    examples = []

    domains = ["example.com", "hackthebox.com", "target.com", "megacorp.com"]

    prompts = [
        ("Whois lookup for {domain}", "{domain}"),
        ("Who owns {domain}?", "{domain}"),
        ("Get registration info for {domain}", "{domain}"),
        ("Find whois data for {domain}", "{domain}"),
    ]

    for domain in domains:
        for prompt_template, args_template in prompts:
            prompt = prompt_template.format(domain=domain)
            args = args_template.format(domain=domain)

            examples.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd="whois", args=args)}
                ]
            })

    return examples

def generate_traceroute_examples():
    """Generate traceroute tool-calling examples."""
    examples = []

    targets = ["192.168.1.1", "10.10.10.1", "8.8.8.8", "google.com"]

    prompts = [
        ("Traceroute to {ip}", "{ip}"),
        ("Show the route to {ip}", "{ip}"),
        ("How do packets get to {ip}?", "{ip}"),
        ("Trace the path to {ip}", "{ip}"),
    ]

    for target in targets:
        for prompt_template, args_template in prompts:
            prompt = prompt_template.format(ip=target)
            args = args_template.format(ip=target)

            examples.append({
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd="traceroute", args=args)}
                ]
            })

    return examples

def generate_netstat_examples():
    """Generate netstat tool-calling examples."""
    examples = []

    prompts = [
        ("Show all listening ports", "-tlnp"),
        ("What ports are open on this machine?", "-tlnp"),
        ("Show active connections", "-an"),
        ("List all network connections", "-an"),
        ("Show TCP connections", "-tn"),
        ("Show UDP listeners", "-ulnp"),
    ]

    for prompt, args in prompts:
        examples.append({
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd="netstat", args=args)}
            ]
        })

    return examples

def generate_mixed_qa_tool_examples():
    """Generate examples where the model should answer vs use a tool."""
    examples = []

    # Questions that should be ANSWERED, not trigger a tool
    qa_examples = [
        {
            "messages": [
                {"role": "user", "content": "What is nmap?"},
                {"role": "assistant", "content": "Nmap (Network Mapper) is an open-source tool for network discovery and security auditing. It's used to discover hosts and services on a network by sending packets and analyzing responses. Key features include port scanning, service/version detection, OS detection, and scriptable interaction with targets using NSE (Nmap Scripting Engine)."}
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "Explain how port scanning works"},
                {"role": "assistant", "content": "Port scanning works by sending network packets to target ports and analyzing the responses:\n\n1. **TCP Connect Scan**: Completes the 3-way handshake (SYN, SYN-ACK, ACK). Open ports complete the handshake.\n\n2. **SYN Scan (Stealth)**: Sends SYN, waits for SYN-ACK (open) or RST (closed). Doesn't complete handshake.\n\n3. **UDP Scan**: Sends UDP packets. No response usually means open/filtered, ICMP unreachable means closed.\n\nOpen ports accept connections, closed ports reject them, and filtered ports don't respond (usually due to firewall)."}
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "What's the difference between -sS and -sT in nmap?"},
                {"role": "assistant", "content": "-sS (SYN scan) and -sT (TCP connect scan) differ in how they detect open ports:\n\n**-sS (SYN/Stealth Scan)**:\n- Sends SYN, waits for SYN-ACK\n- Never completes the handshake\n- Faster and less likely to be logged\n- Requires root/admin privileges\n\n**-sT (TCP Connect Scan)**:\n- Completes full TCP handshake\n- Uses OS's connect() call\n- Slower, more likely to be logged\n- Works without root privileges\n\nUse -sS when you have privileges and want stealth; use -sT when you don't have root access."}
            ]
        },
        {
            "messages": [
                {"role": "user", "content": "How do I interpret nmap results?"},
                {"role": "assistant", "content": "Nmap results show port states and service information:\n\n**Port States**:\n- **open**: Service accepting connections\n- **closed**: No service listening, but reachable\n- **filtered**: Firewall blocking, can't determine state\n- **open|filtered**: Can't determine if open or filtered\n\n**Key Information**:\n- PORT: Port number and protocol (22/tcp)\n- STATE: Port status\n- SERVICE: Detected service name (ssh, http)\n- VERSION: Software version (with -sV)\n\nLook for:\n1. Unusual open ports\n2. Outdated service versions\n3. Services that shouldn't be exposed\n4. Default ports for interesting services (445-SMB, 3389-RDP)"}
            ]
        },
    ]

    examples.extend(qa_examples)

    # Examples that SHOULD trigger tools (action-oriented)
    tool_trigger_examples = [
        ("Scan this target: 10.10.10.50", "nmap", "-sV -sC 10.10.10.50"),
        ("Run nmap on 192.168.1.100", "nmap", "-sV 192.168.1.100"),
        ("Execute a port scan against 10.10.10.1", "nmap", "-sV 10.10.10.1"),
        ("I need to scan 172.16.0.5 for services", "nmap", "-sV -sC 172.16.0.5"),
        ("Please ping 10.10.10.1 to check if it's up", "ping", "-c 4 10.10.10.1"),
        ("Do a DNS lookup on megacorp.local", "nslookup", "megacorp.local"),
    ]

    for prompt, cmd, args in tool_trigger_examples:
        examples.append({
            "messages": [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": TOOL_CALL_FORMAT.format(cmd=cmd, args=args)}
            ]
        })

    return examples

def main():
    """Generate and save tool-calling training data."""
    print("Generating tool-calling training data...")

    all_examples = []

    # Generate examples for each tool
    print("  - Generating nmap examples...")
    all_examples.extend(generate_nmap_examples())

    print("  - Generating ping examples...")
    all_examples.extend(generate_ping_examples())

    print("  - Generating DNS examples...")
    all_examples.extend(generate_dns_examples())

    print("  - Generating curl examples...")
    all_examples.extend(generate_curl_examples())

    print("  - Generating whois examples...")
    all_examples.extend(generate_whois_examples())

    print("  - Generating traceroute examples...")
    all_examples.extend(generate_traceroute_examples())

    print("  - Generating netstat examples...")
    all_examples.extend(generate_netstat_examples())

    print("  - Generating mixed Q&A/tool examples...")
    all_examples.extend(generate_mixed_qa_tool_examples())

    # Shuffle examples
    random.shuffle(all_examples)

    # Save to file
    output_dir = Path(__file__).parent / "data" / "training"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "htb_tool_calling.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_examples, f, indent=2, ensure_ascii=False)

    print(f"\nGenerated {len(all_examples)} tool-calling examples")
    print(f"Saved to: {output_file}")

    return all_examples

if __name__ == "__main__":
    main()
