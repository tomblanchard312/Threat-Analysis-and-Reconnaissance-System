# Kali Linux container for HTB Pentest Agent
# Provides full pentest toolkit behind the AI agent

FROM kalilinux/kali-rolling:latest

LABEL maintainer="HTB Pentest Agent"
LABEL description="Kali Linux with common pentesting tools for AI-driven security testing"

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Use direct Kali mirror (more reliable than CDN)
RUN echo "deb http://kali.download/kali kali-rolling main contrib non-free non-free-firmware" > /etc/apt/sources.list

# Update and install core pentest tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Network reconnaissance
    nmap \
    masscan \
    netcat-openbsd \
    dnsutils \
    whois \
    traceroute \
    tcpdump \
    net-tools \
    iputils-ping \
    # Web tools
    gobuster \
    dirb \
    nikto \
    whatweb \
    wfuzz \
    ffuf \
    curl \
    wget \
    httpie \
    # Exploitation framework
    metasploit-framework \
    exploitdb \
    # Password attacks
    john \
    hashcat \
    hydra \
    wordlists \
    seclists \
    # SMB/Windows enumeration
    smbclient \
    enum4linux \
    crackmapexec \
    impacket-scripts \
    # LDAP tools
    ldap-utils \
    # SQL tools
    sqlmap \
    # Scripting
    python3 \
    python3-pip \
    python3-venv \
    # Utilities
    vim \
    less \
    jq \
    tree \
    tmux \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install OSINT tools via apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    theharvester \
    amass \
    sublist3r \
    recon-ng \
    fierce \
    dnsrecon \
    dnsenum \
    exiftool \
    metagoofil \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python pentest packages and OSINT tools
RUN pip3 install --no-cache-dir --break-system-packages \
    pwntools \
    requests \
    beautifulsoup4 \
    impacket \
    ldap3 \
    sherlock-project \
    holehe \
    h8mail \
    socialscan

# Install Photon manually (no pip package available)
RUN git clone https://github.com/s0md3v/Photon.git /opt/photon && \
    cd /opt/photon && \
    pip3 install --no-cache-dir --break-system-packages -r requirements.txt && \
    ln -s /opt/photon/photon.py /usr/local/bin/photon

# Create working directory for pentest operations
WORKDIR /pentest

# Create directories for loot and notes
RUN mkdir -p /pentest/loot /pentest/notes /pentest/scans

# Set up Metasploit database (optional, runs on first use)
RUN mkdir -p /root/.msf4

# Default to bash shell
CMD ["/bin/bash"]
