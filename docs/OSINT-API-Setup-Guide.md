# OSINT API Setup Guide for HTB Pentest Agent

This guide helps you configure API keys for enhanced OSINT capabilities in theHarvester and other tools.

## Overview

The HTB Pentest Agent uses several OSINT tools, with **theHarvester** being the most API-dependent. By default, theHarvester can only use ~10 free sources. With API keys, you can unlock 30+ additional data sources for more comprehensive reconnaissance.

---

## Quick Start: Essential Free API Keys

These services offer generous free tiers perfect for penetration testing:

### 1. **Shodan** (Infrastructure/IoT Search)
- **Free Tier:** 100 queries/month
- **Signup:** https://account.shodan.io/register
- **Cost:** FREE (Membership: $59/mo for unlimited)
- **Setup:**
  1. Register at Shodan.io
  2. Navigate to **Account → API Key**
  3. Copy your API key
- **Usage:** `theHarvester -d target.com -b shodan`

### 2. **VirusTotal** (Threat Intelligence)
- **Free Tier:** 500 requests/day, 4 requests/minute
- **Signup:** https://www.virustotal.com/gui/join-us
- **Cost:** FREE (Premium: $120/mo)
- **Setup:**
  1. Register at VirusTotal
  2. Go to **Profile → API Key**
  3. Copy your API key
- **Usage:** Detects malicious domains, analyzes files, passive DNS

### 3. **GitHub** (Code/Repository Search)
- **Free Tier:** 5,000 requests/hour
- **Signup:** https://github.com/settings/tokens
- **Cost:** FREE
- **Setup:**
  1. Go to **Settings → Developer settings → Personal access tokens → Tokens (classic)**
  2. Click **Generate new token**
  3. Name: "theHarvester OSINT"
  4. No special scopes needed (leave all unchecked for public search)
  5. Click **Generate token** and copy it immediately
- **Usage:** Find exposed secrets, emails, API keys in public repos

### 4. **SecurityTrails** (DNS/Historical Data)
- **Free Tier:** 50 queries/month
- **Signup:** https://securitytrails.com/app/signup
- **Cost:** FREE (Pro: $99/mo for 5,000/month)
- **Setup:**
  1. Register at SecurityTrails
  2. Go to **API → Generate API Key**
  3. Copy your API key
- **Usage:** Historical DNS records, subdomains, WHOIS history

### 5. **Hunter.io** (Email Discovery)
- **Free Tier:** 25 requests/month
- **Signup:** https://hunter.io/users/sign_up
- **Cost:** FREE (Starter: $49/mo for 500/month)
- **Setup:**
  1. Register at Hunter.io
  2. Go to **API → Get API Key**
  3. Copy your API key
- **Usage:** Find email addresses associated with a domain

### 6. **Censys** (Internet-Wide Scanning)
- **Free Tier:** 250 queries/month
- **Signup:** https://accounts.censys.io/register
- **Cost:** FREE (Paid: $199+/mo)
- **Setup:**
  1. Register at Censys
  2. Go to **Account → API**
  3. Copy **both** API ID and Secret
- **Usage:** Certificate transparency, exposed services, SSL/TLS data

---

## Worth Considering: Paid Services

### Premium OSINT Sources

| Service | Free Tier | Paid Cost | Value Proposition |
|---------|-----------|-----------|-------------------|
| **Dehashed** | None | $90/year | Breach data, leaked credentials (highly valuable) |
| **IntelX** | 50 queries | $2/month | Dark web, paste sites, breach data |
| **BinaryEdge** | 250/month | $10/month for 10K | Internet-wide asset discovery |
| **Criminal IP** | 5,000/month | FREE tier | Threat intelligence, abuse detection |
| **ZoomEye** | 100/month | $89/year | Cyberspace search engine (Chinese alternative to Shodan) |
| **RocketReach** | 5 lookups | $49/month | Contact info, social profiles (B2B focus) |

---

## Configuring theHarvester API Keys

### Method 1: Docker Kali (Recommended)

1. **Access your Kali container:**
   ```bash
   docker exec -it htb-kali bash
   ```

2. **Edit the API keys file:**
   ```bash
   nano /etc/theHarvester/api-keys.yaml
   ```

3. **Add your API keys:**
   ```yaml
   apikeys:
     # Essential free services
     shodan: YOUR_SHODAN_KEY_HERE
     virustotal: YOUR_VIRUSTOTAL_KEY_HERE
     github: YOUR_GITHUB_TOKEN_HERE
     securitytrail: YOUR_SECURITYTRAILS_KEY_HERE
     hunter: YOUR_HUNTER_KEY_HERE
     censys:
       id: YOUR_CENSYS_ID_HERE
       secret: YOUR_CENSYS_SECRET_HERE

     # Optional paid services
     dehashed:
       key: YOUR_DEHASHED_KEY_HERE
       email: YOUR_EMAIL_HERE
     intelx:
       key: YOUR_INTELX_KEY_HERE
       url: 2.intelx.io
     zoomeye: YOUR_ZOOMEYE_KEY_HERE

     # Other services (configure as needed)
     bevigil: YOUR_KEY_HERE
     binaryedge: YOUR_KEY_HERE
     brave: YOUR_KEY_HERE
     bufferoverun: YOUR_KEY_HERE
     criminalip: YOUR_KEY_HERE
     dnsdumpster: YOUR_KEY_HERE
     fofa:
       username: YOUR_USERNAME
       key: YOUR_KEY_HERE
     fullhunt: YOUR_KEY_HERE
     hunterhow: YOUR_KEY_HERE
     netlas: YOUR_KEY_HERE
     onyphe: YOUR_KEY_HERE
     pentesttools: YOUR_KEY_HERE
     projectdiscovery: YOUR_KEY_HERE
     rocketreach: YOUR_KEY_HERE
     tomba:
       key: YOUR_KEY_HERE
       secret: YOUR_SECRET_HERE
     venacus: YOUR_KEY_HERE
     whoisxmlapi: YOUR_KEY_HERE
   ```

4. **Save and exit:** Press `Ctrl+O`, `Enter`, `Ctrl+X`

5. **Test your configuration:**
   ```bash
   theHarvester -d example.com -b shodan
   theHarvester -d example.com -b virustotal
   ```

### Method 2: Helper Script

Run the automated setup script (coming soon):
```bash
./agent/docker/setup-theharvester-api.sh
```

---

## Optimized theHarvester Usage

### ❌ Don't Use This (Fails on 28+ Sources)
```bash
theHarvester -d target.com -b all
```

### ✅ Use Targeted Searches Instead

**For Subdomain Discovery (No API Keys Required):**
```bash
theHarvester -d target.com -b crtsh,hackertarget,certspotter,rapiddns,subdomaincenter,otx
```

**For Email/People Discovery (Requires API Keys):**
```bash
theHarvester -d target.com -b hunter,dehashed,intelx,leaklookup
```

**For Infrastructure Discovery (Requires API Keys):**
```bash
theHarvester -d target.com -b shodan,censys,zoomeye
```

**For Comprehensive Scan (All Configured APIs):**
```bash
theHarvester -d target.com -b shodan,censys,securitytrails,virustotal,github,hunter,crtsh,hackertarget
```

---

## Cost Comparison: OSINT Tool Suites

### Budget-Friendly Setup (FREE)
- Shodan (100/month)
- VirusTotal (500/day)
- GitHub (5,000/hour)
- SecurityTrails (50/month)
- Hunter.io (25/month)
- Censys (250/month)
- **Total Cost:** $0/month

### Enthusiast Setup ($8/month)
- All free services above
- IntelX Micro Plan ($2/month)
- Criminal IP (5,000/month FREE)
- BinaryEdge Hobbyist ($10/month) - **or** ZoomEye ($7.42/month)
- **Total Cost:** ~$8-12/month

### Professional Setup ($28/month)
- All above
- Dehashed ($7.50/month annual)
- SecurityTrails Pro ($99/month) - Optional upgrade for heavy use
- **Total Cost:** ~$28/month (or ~$107/month with SecurityTrails Pro)

---

## Testing Your Setup

After configuring API keys, test each service:

```bash
# Test Shodan
theHarvester -d github.com -b shodan

# Test VirusTotal
theHarvester -d github.com -b virustotal

# Test GitHub
theHarvester -d github.com -b github-code

# Test SecurityTrails
theHarvester -d github.com -b securitytrails

# Test comprehensive scan
theHarvester -d github.com -b shodan,virustotal,github,securitytrails,hunter,censys
```

---

## Troubleshooting

### "Missing API key" errors
- Check that your `api-keys.yaml` syntax is correct (proper indentation)
- Ensure no extra spaces or quotes around keys
- Verify the key is active on the service's website

### "Rate limit exceeded"
- Free tiers have strict rate limits
- Wait a few minutes before retrying
- Consider upgrading to paid tier for that service

### "Invalid API key"
- Regenerate the key on the service's website
- Check for typos in the key
- Ensure you copied the entire key (no truncation)

### Docker container doesn't persist API keys
- API keys are stored in `/etc/theHarvester/api-keys.yaml` inside the container
- To persist across container restarts, mount a volume:
  ```bash
  docker run -v ./api-keys.yaml:/etc/theHarvester/api-keys.yaml ...
  ```

---

## Security Best Practices

1. **Never commit API keys to Git repositories**
2. **Use environment variables for sensitive keys**
3. **Rotate keys periodically (every 90 days)**
4. **Use separate keys for different projects/teams**
5. **Monitor API usage for anomalies**
6. **Revoke keys immediately if compromised**

---

## Updates and Maintenance

**Check for API key expiration:**
```bash
# Most services don't expire keys, but some do
# Check your account dashboards monthly
```

**Update theHarvester:**
```bash
docker exec -it htb-kali bash
cd /opt/theHarvester
git pull
pip3 install -r requirements.txt
```

---

## Additional Resources

- [theHarvester Wiki](https://github.com/laramies/theHarvester/wiki)
- [Shodan API Documentation](https://developer.shodan.io/)
- [VirusTotal API Documentation](https://developers.virustotal.com/reference/overview)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [SecurityTrails API Documentation](https://docs.securitytrails.com/)

---

*Last Updated: 2026-01-22*
*Compatible with: HTB Pentest Agent v4, theHarvester 4.9.2+*
