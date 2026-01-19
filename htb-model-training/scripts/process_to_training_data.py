#!/usr/bin/env python3
"""
Process scraped HTB writeups into training data format.
Generates instruction-response pairs for fine-tuning.

Usage:
    python process_to_training_data.py --input ../data/raw_writeups/processed --output ../data/training
"""

import argparse
import json
import random
import re
from pathlib import Path
from typing import Optional


# Instruction templates for generating Q&A pairs
INSTRUCTION_TEMPLATES = {
    'general_approach': [
        "How would you approach hacking the {machine} box on Hack The Box?",
        "Walk me through the methodology for compromising {machine}.",
        "Explain the attack path for the HTB machine {machine}.",
        "What's the strategy for pwning {machine} on Hack The Box?",
    ],
    'recon': [
        "What reconnaissance steps would you take for {machine}?",
        "How would you start enumerating the {machine} machine?",
        "Describe the initial scanning approach for {machine}.",
        "What nmap scan would you run against {machine} and why?",
    ],
    'enumeration': [
        "What enumeration techniques are useful for {machine}?",
        "How would you enumerate services on {machine}?",
        "Describe the enumeration phase for the {machine} box.",
    ],
    'foothold': [
        "How do you get initial access to {machine}?",
        "What vulnerability allows foothold on {machine}?",
        "Explain the exploitation technique for gaining a shell on {machine}.",
        "How would you exploit {machine} to get initial access?",
    ],
    'privesc': [
        "How do you escalate privileges on {machine}?",
        "What privilege escalation technique works on {machine}?",
        "Explain the path from user to root on {machine}.",
        "How do you get root on {machine}?",
    ],
    'technique_specific': [
        "Explain how {technique} works in the context of {machine}.",
        "Demonstrate {technique} as used in the {machine} writeup.",
    ],
    'tool_usage': [
        "How would you use {tool} when attacking {machine}?",
        "Show an example of {tool} usage from the {machine} box.",
    ],
}

# Common techniques to extract and create specific Q&A for
TECHNIQUES = [
    'SQL injection', 'command injection', 'file upload', 'LFI', 'RFI',
    'XXE', 'SSRF', 'deserialization', 'path traversal', 'SSTI',
    'buffer overflow', 'format string', 'race condition',
    'password cracking', 'hash cracking', 'brute force',
    'port forwarding', 'tunneling', 'pivoting',
    'SUID exploitation', 'sudo exploitation', 'cron exploitation',
    'kernel exploit', 'docker escape', 'capability abuse',
    'kerberoasting', 'AS-REP roasting', 'pass the hash',
    'bloodhound', 'Active Directory', 'LDAP injection',
]

# Common tools mentioned in writeups
TOOLS = [
    'nmap', 'gobuster', 'feroxbuster', 'ffuf', 'dirbuster',
    'burp suite', 'sqlmap', 'hydra', 'john', 'hashcat',
    'metasploit', 'msfvenom', 'netcat', 'socat', 'chisel',
    'linpeas', 'winpeas', 'pspy', 'bloodhound', 'mimikatz',
    'crackmapexec', 'evil-winrm', 'impacket', 'responder',
]


class TrainingDataGenerator:
    """Generate training data from processed writeups."""

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_writeups(self) -> list[dict]:
        """Load all processed writeups."""
        writeups = []
        failed_files = []
        for json_file in self.input_dir.glob("*.json"):
            try:
                # Use absolute path and handle Windows encoding issues
                abs_path = json_file.resolve()
                with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    # Remove any null bytes that might cause issues
                    content = content.replace('\x00', '')
                    data = json.loads(content)
                    data['source_file'] = json_file.name
                    writeups.append(data)
            except json.JSONDecodeError as e:
                failed_files.append((json_file.name, f"JSON decode error: {e}"))
            except Exception as e:
                failed_files.append((json_file.name, str(e)))

        print(f"[+] Loaded {len(writeups)} writeups")
        if failed_files:
            print(f"[!] Failed to load {len(failed_files)} files:")
            for name, error in failed_files[:10]:  # Show first 10 errors
                print(f"    - {name}: {error}")
            if len(failed_files) > 10:
                print(f"    ... and {len(failed_files) - 10} more")
        return writeups

    def extract_code_blocks(self, content: str) -> list[str]:
        """Extract code blocks from markdown content."""
        pattern = r'```[\w]*\n(.*?)```'
        return re.findall(pattern, content, re.DOTALL)

    def extract_commands(self, content: str) -> list[str]:
        """Extract shell commands from content."""
        commands = []
        # Match common command patterns
        patterns = [
            r'\$\s*(.+?)(?:\n|$)',  # $ command
            r'#\s*(.+?)(?:\n|$)',   # # command (root)
            r'>\s*(.+?)(?:\n|$)',   # > command (Windows)
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content)
            commands.extend(matches)
        return commands

    def detect_techniques(self, content: str) -> list[str]:
        """Detect security techniques mentioned in content."""
        found = []
        content_lower = content.lower()
        for technique in TECHNIQUES:
            if technique.lower() in content_lower:
                found.append(technique)
        return found

    def detect_tools(self, content: str) -> list[str]:
        """Detect tools mentioned in content."""
        found = []
        content_lower = content.lower()
        for tool in TOOLS:
            if tool.lower() in content_lower:
                found.append(tool)
        return found

    def generate_qa_pairs(self, writeup: dict) -> list[dict]:
        """Generate Q&A pairs from a single writeup."""
        pairs = []
        metadata = writeup.get('metadata', {})
        machine = metadata.get('machine_name', 'Unknown')
        sections = writeup.get('sections', {})
        full_content = writeup.get('markdown_content', '')

        # 1. General approach question
        if full_content:
            template = random.choice(INSTRUCTION_TEMPLATES['general_approach'])
            pairs.append({
                'instruction': template.format(machine=machine),
                'input': '',
                'output': self._summarize_approach(writeup),
                'machine': machine,
                'category': 'general_approach'
            })

        # 2. Section-specific questions
        section_mapping = {
            'recon': 'recon',
            'enumeration': 'enumeration',
            'foothold': 'foothold',
            'privilege_escalation': 'privesc',
            'user': 'foothold',
            'root': 'privesc',
        }

        for section_name, template_key in section_mapping.items():
            section_content = sections.get(section_name, '')
            if section_content and len(section_content) > 100:
                template = random.choice(INSTRUCTION_TEMPLATES[template_key])
                pairs.append({
                    'instruction': template.format(machine=machine),
                    'input': '',
                    'output': self._clean_section(section_content),
                    'machine': machine,
                    'category': template_key
                })

        # 3. Technique-specific questions
        techniques = self.detect_techniques(full_content)
        for technique in techniques[:3]:  # Limit to top 3
            template = random.choice(INSTRUCTION_TEMPLATES['technique_specific'])
            # Find relevant content about this technique
            technique_context = self._extract_technique_context(full_content, technique)
            if technique_context:
                pairs.append({
                    'instruction': template.format(technique=technique, machine=machine),
                    'input': '',
                    'output': technique_context,
                    'machine': machine,
                    'category': 'technique',
                    'technique': technique
                })

        # 4. Tool usage questions
        tools = self.detect_tools(full_content)
        for tool in tools[:3]:  # Limit to top 3
            template = random.choice(INSTRUCTION_TEMPLATES['tool_usage'])
            tool_context = self._extract_tool_context(full_content, tool)
            if tool_context:
                pairs.append({
                    'instruction': template.format(tool=tool, machine=machine),
                    'input': '',
                    'output': tool_context,
                    'machine': machine,
                    'category': 'tool_usage',
                    'tool': tool
                })

        # 5. Command explanation pairs
        code_blocks = self.extract_code_blocks(full_content)
        for block in code_blocks[:5]:  # Limit code blocks
            if len(block) > 20 and len(block) < 500:
                pairs.append({
                    'instruction': f"Explain this command/code used in the {machine} machine:",
                    'input': block.strip(),
                    'output': self._generate_command_explanation(block, full_content),
                    'machine': machine,
                    'category': 'command_explanation'
                })

        return pairs

    def _summarize_approach(self, writeup: dict) -> str:
        """Create a summary of the overall approach."""
        sections = writeup.get('sections', {})
        metadata = writeup.get('metadata', {})

        summary_parts = []

        # Add metadata context
        if metadata.get('os_type'):
            summary_parts.append(f"This is a {metadata.get('difficulty', 'medium')} {metadata['os_type']} machine.")

        # Add section summaries
        if sections.get('recon'):
            summary_parts.append(f"\n## Reconnaissance\n{self._truncate(sections['recon'], 500)}")
        if sections.get('foothold'):
            summary_parts.append(f"\n## Initial Foothold\n{self._truncate(sections['foothold'], 500)}")
        if sections.get('privilege_escalation') or sections.get('root'):
            privesc = sections.get('privilege_escalation') or sections.get('root', '')
            summary_parts.append(f"\n## Privilege Escalation\n{self._truncate(privesc, 500)}")

        if not summary_parts:
            return self._truncate(writeup.get('markdown_content', ''), 1500)

        return '\n'.join(summary_parts)

    def _clean_section(self, content: str) -> str:
        """Clean and format a section for training."""
        # Remove excessive whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        # Truncate if too long
        return self._truncate(content, 1500)

    def _extract_technique_context(self, content: str, technique: str) -> Optional[str]:
        """Extract content related to a specific technique."""
        # Find paragraphs mentioning the technique
        paragraphs = content.split('\n\n')
        relevant = []
        technique_lower = technique.lower()

        for i, para in enumerate(paragraphs):
            if technique_lower in para.lower():
                # Include surrounding context
                start = max(0, i - 1)
                end = min(len(paragraphs), i + 2)
                relevant.extend(paragraphs[start:end])

        if relevant:
            return self._truncate('\n\n'.join(relevant), 1000)
        return None

    def _extract_tool_context(self, content: str, tool: str) -> Optional[str]:
        """Extract content related to a specific tool."""
        return self._extract_technique_context(content, tool)

    def _generate_command_explanation(self, command: str, context: str) -> str:
        """Generate explanation for a command based on context."""
        # This is a placeholder - ideally would use an LLM to generate
        # For now, return contextual information
        return f"This command is used in the penetration testing process. Here's the command:\n\n```\n{command}\n```\n\nThis is typically used during the enumeration or exploitation phase."

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."

    def generate_all(self) -> list[dict]:
        """Generate training data from all writeups."""
        writeups = self.load_writeups()
        all_pairs = []

        for writeup in writeups:
            pairs = self.generate_qa_pairs(writeup)
            all_pairs.extend(pairs)
            print(f"[+] Generated {len(pairs)} pairs from {writeup.get('source_file', 'unknown')}")

        print(f"\n[+] Total training pairs generated: {len(all_pairs)}")
        return all_pairs

    def save_training_data(self, pairs: list[dict], format: str = 'all'):
        """Save training data in various formats."""

        # Alpaca format
        if format in ['all', 'alpaca']:
            alpaca_data = [
                {
                    'instruction': p['instruction'],
                    'input': p.get('input', ''),
                    'output': p['output']
                }
                for p in pairs
            ]
            alpaca_path = self.output_dir / "htb_alpaca.json"
            with open(alpaca_path, 'w', encoding='utf-8') as f:
                json.dump(alpaca_data, f, indent=2, ensure_ascii=False)
            print(f"[+] Saved Alpaca format: {alpaca_path}")

        # ShareGPT format
        if format in ['all', 'sharegpt']:
            sharegpt_data = []
            for p in pairs:
                conversation = {
                    'conversations': [
                        {'from': 'human', 'value': p['instruction'] + ('\n' + p['input'] if p.get('input') else '')},
                        {'from': 'gpt', 'value': p['output']}
                    ]
                }
                sharegpt_data.append(conversation)

            sharegpt_path = self.output_dir / "htb_sharegpt.json"
            with open(sharegpt_path, 'w', encoding='utf-8') as f:
                json.dump(sharegpt_data, f, indent=2, ensure_ascii=False)
            print(f"[+] Saved ShareGPT format: {sharegpt_path}")

        # ChatML format (for Axolotl)
        if format in ['all', 'chatml']:
            chatml_data = []
            for p in pairs:
                chatml_data.append({
                    'messages': [
                        {'role': 'user', 'content': p['instruction'] + ('\n' + p['input'] if p.get('input') else '')},
                        {'role': 'assistant', 'content': p['output']}
                    ]
                })

            chatml_path = self.output_dir / "htb_chatml.json"
            with open(chatml_path, 'w', encoding='utf-8') as f:
                json.dump(chatml_data, f, indent=2, ensure_ascii=False)
            print(f"[+] Saved ChatML format: {chatml_path}")

        # Save metadata
        metadata = {
            'total_pairs': len(pairs),
            'categories': {},
            'machines': list(set(p.get('machine', 'unknown') for p in pairs)),
            'techniques': list(set(p.get('technique', '') for p in pairs if p.get('technique'))),
            'tools': list(set(p.get('tool', '') for p in pairs if p.get('tool'))),
        }
        for p in pairs:
            cat = p.get('category', 'unknown')
            metadata['categories'][cat] = metadata['categories'].get(cat, 0) + 1

        meta_path = self.output_dir / "metadata.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"[+] Saved metadata: {meta_path}")

    def create_train_test_split(self, pairs: list[dict], test_ratio: float = 0.1):
        """Split data into training and test sets."""
        random.shuffle(pairs)
        split_idx = int(len(pairs) * (1 - test_ratio))

        train_data = pairs[:split_idx]
        test_data = pairs[split_idx:]

        # Save splits
        train_path = self.output_dir / "train.json"
        test_path = self.output_dir / "test.json"

        with open(train_path, 'w', encoding='utf-8') as f:
            json.dump(train_data, f, indent=2, ensure_ascii=False)

        with open(test_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

        print(f"[+] Train set: {len(train_data)} pairs -> {train_path}")
        print(f"[+] Test set: {len(test_data)} pairs -> {test_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Process HTB writeups into training data'
    )
    parser.add_argument(
        '--input', '-i',
        default='../data/raw_writeups/processed',
        help='Input directory with processed writeups'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/training',
        help='Output directory for training data'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['all', 'alpaca', 'sharegpt', 'chatml'],
        default='all',
        help='Output format(s)'
    )
    parser.add_argument(
        '--test-ratio',
        type=float,
        default=0.1,
        help='Ratio of data to use for test set'
    )

    args = parser.parse_args()

    generator = TrainingDataGenerator(args.input, args.output)
    pairs = generator.generate_all()

    if pairs:
        generator.save_training_data(pairs, format=args.format)
        generator.create_train_test_split(pairs, test_ratio=args.test_ratio)
    else:
        print("[!] No training pairs generated. Check input data.")


if __name__ == '__main__':
    main()
