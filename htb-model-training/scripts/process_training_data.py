#!/usr/bin/env python3
"""
Training Data Processing Pipeline
Converts scraped data from multiple sources into training format for fine-tuning.

Usage:
    python process_training_data.py --output ../data/training/combined.jsonl
"""

import argparse
import json
import random
import re
from pathlib import Path
from typing import List, Dict, Generator
from dataclasses import dataclass

# Training data format
@dataclass
class TrainingExample:
    """A single training example in instruction-tuning format."""
    instruction: str
    input: str  # Optional context
    output: str
    category: str
    source: str
    tools: List[str]


class TrainingDataProcessor:
    """Process scraped data into training format."""

    def __init__(self, data_dir: str, output_file: str):
        self.data_dir = Path(data_dir)
        self.output_file = Path(output_file)
        self.examples = []

        # Question templates for generating instruction-tuning pairs
        self.question_templates = {
            'how_to': [
                "How do I {action}?",
                "What's the best way to {action}?",
                "Explain how to {action}",
                "Walk me through {action}",
                "Show me how to {action}",
            ],
            'what_is': [
                "What is {topic}?",
                "Explain {topic}",
                "What does {topic} do?",
                "Tell me about {topic}",
            ],
            'tool_usage': [
                "How do I use {tool}?",
                "What are the common {tool} commands?",
                "Show me {tool} examples",
                "Give me a {tool} cheat sheet",
                "What flags should I use with {tool}?",
            ],
            'scenario': [
                "I found {finding}, what should I do next?",
                "The scan shows {finding}, how do I exploit this?",
                "I have {access}, how do I escalate privileges?",
                "There's a {service} service running, how do I enumerate it?",
            ],
            'methodology': [
                "What's the methodology for {task}?",
                "What are the steps for {task}?",
                "How should I approach {task}?",
                "What's the pentesting workflow for {task}?",
            ]
        }

    def load_0xdf_writeups(self) -> Generator[Dict, None, None]:
        """Load 0xdf HTB writeups."""
        writeups_dir = self.data_dir / "raw_writeups" / "processed"
        if not writeups_dir.exists():
            print(f"[!] 0xdf writeups not found at {writeups_dir}")
            return

        print(f"[*] Loading 0xdf writeups from {writeups_dir}")

        for json_file in writeups_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_source'] = '0xdf'
                    data['_file'] = json_file.name
                    yield data
            except Exception as e:
                print(f"[!] Failed to load {json_file}: {e}")

    def load_hacktricks(self) -> Generator[Dict, None, None]:
        """Load HackTricks technique pages."""
        hacktricks_dir = self.data_dir / "hacktricks" / "processed"
        if not hacktricks_dir.exists():
            print(f"[!] HackTricks data not found at {hacktricks_dir}")
            return

        print(f"[*] Loading HackTricks from {hacktricks_dir}")

        for json_file in hacktricks_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_source'] = 'hacktricks'
                    data['_file'] = json_file.name
                    yield data
            except Exception as e:
                print(f"[!] Failed to load {json_file}: {e}")

    def load_kali_tools(self) -> Generator[Dict, None, None]:
        """Load Kali tools documentation."""
        kali_dir = self.data_dir / "kali_tools" / "processed"
        if not kali_dir.exists():
            print(f"[!] Kali tools data not found at {kali_dir}")
            return

        print(f"[*] Loading Kali tools from {kali_dir}")

        for json_file in kali_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_source'] = 'kali_tools'
                    data['_file'] = json_file.name
                    yield data
            except Exception as e:
                print(f"[!] Failed to load {json_file}: {e}")

    def load_owasp(self) -> Generator[Dict, None, None]:
        """Load OWASP test cases."""
        owasp_dir = self.data_dir / "owasp" / "processed"
        if not owasp_dir.exists():
            print(f"[!] OWASP data not found at {owasp_dir}")
            return

        print(f"[*] Loading OWASP from {owasp_dir}")

        for json_file in owasp_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_source'] = 'owasp'
                    data['_file'] = json_file.name
                    yield data
            except Exception as e:
                print(f"[!] Failed to load {json_file}: {e}")

    def load_pregenerated_training(self, source_name: str, training_file: str) -> List[Dict]:
        """Load pre-generated training data from JSONL file."""
        training_path = self.data_dir / source_name / training_file
        if not training_path.exists():
            print(f"[!] {source_name} training data not found at {training_path}")
            return []

        print(f"[*] Loading {source_name} training from {training_path}")
        examples = []

        with open(training_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        examples.append(data)
                    except json.JSONDecodeError as e:
                        print(f"[!] JSON decode error in {source_name}: {e}")

        print(f"[+] Loaded {len(examples)} {source_name} examples")
        return examples

    def load_gtfobins_training(self) -> List[Dict]:
        """Load GTFOBins pre-generated training data."""
        return self.load_pregenerated_training('gtfobins', 'gtfobins_training.jsonl')

    def load_lolbas_training(self) -> List[Dict]:
        """Load LOLBAS pre-generated training data."""
        return self.load_pregenerated_training('lolbas', 'lolbas_training.jsonl')

    def load_payloads_training(self) -> List[Dict]:
        """Load PayloadsAllTheThings pre-generated training data."""
        return self.load_pregenerated_training('payloads', 'payloads_training.jsonl')

    def load_osint_training(self) -> List[Dict]:
        """Load OSINT pre-generated training data."""
        return self.load_pregenerated_training('osint', 'osint_training.jsonl')

    def load_cleaned_v4_training(self) -> List[Dict]:
        """Load cleaned v4 training data."""
        training_path = self.data_dir / "training" / "htb_pentest_v4_clean.jsonl"
        if not training_path.exists():
            print(f"[!] Cleaned v4 training data not found at {training_path}")
            return []

        print(f"[*] Loading cleaned v4 training from {training_path}")
        examples = []

        with open(training_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        examples.append(data)
                    except json.JSONDecodeError as e:
                        print(f"[!] JSON decode error: {e}")

        print(f"[+] Loaded {len(examples)} cleaned v4 examples")
        return examples

    def generate_writeup_examples(self, writeup: Dict) -> List[TrainingExample]:
        """Generate training examples from a writeup."""
        examples = []
        metadata = writeup.get('metadata', {})
        sections = writeup.get('sections', {})
        machine_name = metadata.get('machine_name', 'Unknown')

        # Full walkthrough question
        if writeup.get('markdown_content'):
            content = writeup['markdown_content'][:8000]  # Limit length
            examples.append(TrainingExample(
                instruction=f"Walk me through the {machine_name} HTB machine",
                input=f"Machine: {machine_name}, Difficulty: {metadata.get('difficulty', 'Unknown')}, OS: {metadata.get('os_type', 'Unknown')}",
                output=content,
                category="htb_walkthrough",
                source="0xdf",
                tools=metadata.get('tags', [])
            ))

        # Section-specific questions
        if sections.get('recon'):
            examples.append(TrainingExample(
                instruction=f"How should I start reconnaissance on {machine_name}?",
                input="",
                output=sections['recon'][:3000],
                category="reconnaissance",
                source="0xdf",
                tools=[]
            ))

        if sections.get('foothold'):
            examples.append(TrainingExample(
                instruction=f"How do I get initial access on {machine_name}?",
                input="",
                output=sections['foothold'][:3000],
                category="exploitation",
                source="0xdf",
                tools=[]
            ))

        if sections.get('privilege_escalation'):
            examples.append(TrainingExample(
                instruction=f"How do I escalate privileges on {machine_name}?",
                input="",
                output=sections['privilege_escalation'][:3000],
                category="privesc",
                source="0xdf",
                tools=[]
            ))

        return examples

    def generate_hacktricks_examples(self, page: Dict) -> List[TrainingExample]:
        """Generate training examples from HackTricks page."""
        examples = []
        title = page.get('title', '')
        content = page.get('content', '')[:5000]
        category = page.get('category', 'general')
        tools = page.get('tools_mentioned', [])
        commands = page.get('commands', [])

        if not content:
            return examples

        # Main explanation
        template = random.choice(self.question_templates['what_is'])
        examples.append(TrainingExample(
            instruction=template.format(topic=title),
            input="",
            output=content,
            category=category,
            source="hacktricks",
            tools=tools
        ))

        # How-to question
        if 'how' in title.lower() or 'exploit' in title.lower() or 'attack' in title.lower():
            action = title.lower().replace('how to', '').strip()
            template = random.choice(self.question_templates['how_to'])
            examples.append(TrainingExample(
                instruction=template.format(action=action),
                input="",
                output=content,
                category=category,
                source="hacktricks",
                tools=tools
            ))

        # Command examples
        if commands:
            cmd_text = "\n".join([f"- `{cmd}`" for cmd in commands[:10]])
            examples.append(TrainingExample(
                instruction=f"What commands are used for {title}?",
                input="",
                output=f"Here are common commands for {title}:\n\n{cmd_text}",
                category=category,
                source="hacktricks",
                tools=tools
            ))

        return examples

    def generate_kali_tool_examples(self, tool: Dict) -> List[TrainingExample]:
        """Generate training examples from Kali tool documentation."""
        examples = []
        name = tool.get('name', '')
        description = tool.get('description', '')
        usage = tool.get('usage_examples', [])
        options = tool.get('options', [])
        category = tool.get('category', 'general')

        if not description:
            return examples

        # Basic tool question
        template = random.choice(self.question_templates['tool_usage'])
        examples.append(TrainingExample(
            instruction=template.format(tool=name),
            input="",
            output=description,
            category=category,
            source="kali_tools",
            tools=[name]
        ))

        # Usage examples
        if usage:
            usage_text = "\n".join([f"```\n{ex}\n```" for ex in usage[:5]])
            examples.append(TrainingExample(
                instruction=f"Show me {name} usage examples",
                input="",
                output=f"Here are {name} usage examples:\n\n{usage_text}",
                category=category,
                source="kali_tools",
                tools=[name]
            ))

        # Options/flags
        if options:
            opts_text = "\n".join([f"- {opt}" for opt in options[:15]])
            examples.append(TrainingExample(
                instruction=f"What are the {name} command options?",
                input="",
                output=f"{name} options:\n\n{opts_text}",
                category=category,
                source="kali_tools",
                tools=[name]
            ))

        return examples

    def generate_owasp_examples(self, test_case: Dict) -> List[TrainingExample]:
        """Generate training examples from OWASP test case."""
        examples = []
        title = test_case.get('title', '')
        test_id = test_case.get('id', '')
        category = test_case.get('category_name', '')
        summary = test_case.get('summary', '')
        how_to_test = test_case.get('how_to_test', '')
        objectives = test_case.get('objectives', [])
        tools = test_case.get('tools', [])
        remediation = test_case.get('remediation', '')

        # Main testing methodology
        if how_to_test:
            template = random.choice(self.question_templates['methodology'])
            task = title.lower().replace('testing', '').replace('test', '').strip()
            examples.append(TrainingExample(
                instruction=template.format(task=task or title),
                input=f"OWASP Test: {test_id}",
                output=how_to_test[:4000],
                category="web_security",
                source="owasp",
                tools=tools
            ))

        # Summary/explanation
        if summary:
            template = random.choice(self.question_templates['what_is'])
            examples.append(TrainingExample(
                instruction=template.format(topic=title),
                input="",
                output=summary[:2000],
                category="web_security",
                source="owasp",
                tools=tools
            ))

        # Remediation
        if remediation:
            examples.append(TrainingExample(
                instruction=f"How do I fix or prevent {title}?",
                input="",
                output=remediation[:2000],
                category="remediation",
                source="owasp",
                tools=[]
            ))

        return examples

    def process_all_sources(self):
        """Process all data sources."""
        print("\n[*] Processing all data sources...")

        # First, load cleaned v4 base training data
        print("\n--- Loading Cleaned V4 Base Training ---")
        cleaned_examples = self.load_cleaned_v4_training()
        for ex in cleaned_examples:
            self.examples.append(TrainingExample(
                instruction=ex.get('instruction', ''),
                input=ex.get('input', ''),
                output=ex.get('output', ''),
                category=ex.get('category', 'general'),
                source=ex.get('source', 'cleaned_v4'),
                tools=ex.get('tools', [])
            ))
        print(f"[+] Loaded {len(cleaned_examples)} cleaned v4 examples")

        # Load new pre-generated training data sources
        print("\n--- Loading GTFOBins Training ---")
        gtfo_examples = self.load_gtfobins_training()
        for ex in gtfo_examples:
            self.examples.append(TrainingExample(
                instruction=ex.get('instruction', ''),
                input=ex.get('input', ''),
                output=ex.get('output', ''),
                category=ex.get('category', 'privesc'),
                source='gtfobins',
                tools=[ex.get('binary', '')] if ex.get('binary') else []
            ))

        print("\n--- Loading LOLBAS Training ---")
        lolbas_examples = self.load_lolbas_training()
        for ex in lolbas_examples:
            self.examples.append(TrainingExample(
                instruction=ex.get('instruction', ''),
                input=ex.get('input', ''),
                output=ex.get('output', ''),
                category=ex.get('category', 'windows'),
                source='lolbas',
                tools=[ex.get('binary', '')] if ex.get('binary') else []
            ))

        print("\n--- Loading PayloadsAllTheThings Training ---")
        payloads_examples = self.load_payloads_training()
        for ex in payloads_examples:
            self.examples.append(TrainingExample(
                instruction=ex.get('instruction', ''),
                input=ex.get('input', ''),
                output=ex.get('output', ''),
                category=ex.get('category', 'payloads'),
                source='payloadsallthethings',
                tools=[]
            ))

        print("\n--- Loading OSINT Training ---")
        osint_examples = self.load_osint_training()
        for ex in osint_examples:
            self.examples.append(TrainingExample(
                instruction=ex.get('instruction', ''),
                input=ex.get('input', ''),
                output=ex.get('output', ''),
                category=ex.get('category', 'osint'),
                source='osint',
                tools=[ex.get('tool', '')] if ex.get('tool') else []
            ))

        # Process 0xdf writeups (if not already in cleaned data)
        print("\n--- Processing 0xdf writeups ---")
        initial_count = len(self.examples)
        for writeup in self.load_0xdf_writeups():
            examples = self.generate_writeup_examples(writeup)
            self.examples.extend(examples)
        print(f"[+] Added {len(self.examples) - initial_count} writeup examples")

        # Process HackTricks
        print("\n--- Processing HackTricks ---")
        hacktricks_count = len(self.examples)
        for page in self.load_hacktricks():
            examples = self.generate_hacktricks_examples(page)
            self.examples.extend(examples)
        print(f"[+] Added {len(self.examples) - hacktricks_count} HackTricks examples")

        # Process Kali tools
        print("\n--- Processing Kali Tools ---")
        kali_count = len(self.examples)
        for tool in self.load_kali_tools():
            examples = self.generate_kali_tool_examples(tool)
            self.examples.extend(examples)
        print(f"[+] Added {len(self.examples) - kali_count} Kali tool examples")

        # Process OWASP
        print("\n--- Processing OWASP ---")
        owasp_count = len(self.examples)
        for test_case in self.load_owasp():
            examples = self.generate_owasp_examples(test_case)
            self.examples.extend(examples)
        print(f"[+] Added {len(self.examples) - owasp_count} OWASP examples")

        print(f"\n[+] Total examples generated: {len(self.examples)}")

    def add_tool_calling_examples(self):
        """Add examples specifically for tool calling behavior."""
        tool_examples = [
            TrainingExample(
                instruction="Scan the target for open ports",
                input="Target: 10.10.10.100",
                output='<tool_call>{"name": "pentest-tools", "arguments": {"command": "nmap", "args": "-sV -sC 10.10.10.100"}}</tool_call>',
                category="tool_calling",
                source="synthetic",
                tools=["nmap"]
            ),
            TrainingExample(
                instruction="Check for SMB vulnerabilities",
                input="Target: 10.10.10.100",
                output='<tool_call>{"name": "pentest-tools", "arguments": {"command": "nmap", "args": "--script smb-vuln-* -p 445 10.10.10.100"}}</tool_call>',
                category="tool_calling",
                source="synthetic",
                tools=["nmap"]
            ),
            TrainingExample(
                instruction="Search for the username john_doe across social platforms",
                input="",
                output='<tool_call>{"name": "pentest-tools", "arguments": {"command": "sherlock", "args": "john_doe --print-found"}}</tool_call>',
                category="tool_calling",
                source="synthetic",
                tools=["sherlock"]
            ),
            TrainingExample(
                instruction="Enumerate directories on the web server",
                input="Target: http://10.10.10.100",
                output='<tool_call>{"name": "pentest-tools", "arguments": {"command": "gobuster", "args": "dir -u http://10.10.10.100 -w /usr/share/wordlists/dirb/common.txt"}}</tool_call>',
                category="tool_calling",
                source="synthetic",
                tools=["gobuster"]
            ),
            TrainingExample(
                instruction="Run a SQL injection test",
                input="URL: http://10.10.10.100/page.php?id=1",
                output='<tool_call>{"name": "pentest-tools", "arguments": {"command": "sqlmap", "args": "-u \'http://10.10.10.100/page.php?id=1\' --batch"}}</tool_call>',
                category="tool_calling",
                source="synthetic",
                tools=["sqlmap"]
            ),
            TrainingExample(
                instruction="Check what services the email is registered on",
                input="Email: test@example.com",
                output='<tool_call>{"name": "pentest-tools", "arguments": {"command": "holehe", "args": "test@example.com"}}</tool_call>',
                category="tool_calling",
                source="synthetic",
                tools=["holehe"]
            ),
            TrainingExample(
                instruction="Enumerate SMB shares",
                input="Target: 10.10.10.100",
                output='<tool_call>{"name": "pentest-tools", "arguments": {"command": "enum4linux", "args": "-a 10.10.10.100"}}</tool_call>',
                category="tool_calling",
                source="synthetic",
                tools=["enum4linux"]
            ),
            TrainingExample(
                instruction="Perform subdomain enumeration",
                input="Domain: example.com",
                output='<tool_call>{"name": "pentest-tools", "arguments": {"command": "amass", "args": "enum -passive -d example.com"}}</tool_call>',
                category="tool_calling",
                source="synthetic",
                tools=["amass"]
            ),
        ]

        self.examples.extend(tool_examples)
        print(f"[+] Added {len(tool_examples)} tool-calling examples")

    def save_training_data(self, format: str = 'jsonl'):
        """Save processed data to training format."""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        # Shuffle examples
        random.shuffle(self.examples)

        if format == 'jsonl':
            with open(self.output_file, 'w', encoding='utf-8') as f:
                for example in self.examples:
                    record = {
                        'instruction': example.instruction,
                        'input': example.input,
                        'output': example.output,
                        'category': example.category,
                        'source': example.source,
                        'tools': example.tools
                    }
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')

        elif format == 'alpaca':
            # Alpaca format for common training frameworks
            records = []
            for example in self.examples:
                records.append({
                    'instruction': example.instruction,
                    'input': example.input,
                    'output': example.output
                })

            output_path = self.output_file.with_suffix('.json')
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)

        # Save statistics
        stats = {
            'total_examples': len(self.examples),
            'by_source': {},
            'by_category': {}
        }

        for example in self.examples:
            stats['by_source'][example.source] = stats['by_source'].get(example.source, 0) + 1
            stats['by_category'][example.category] = stats['by_category'].get(example.category, 0) + 1

        stats_path = self.output_file.with_name('training_stats.json')
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        print(f"\n[+] Saved {len(self.examples)} examples to {self.output_file}")
        print(f"[+] Statistics saved to {stats_path}")
        print(f"\nBreakdown by source:")
        for source, count in sorted(stats['by_source'].items()):
            print(f"  - {source}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description='Process scraped data into training format'
    )
    parser.add_argument(
        '--data-dir', '-d',
        default='../data',
        help='Directory containing scraped data'
    )
    parser.add_argument(
        '--output', '-o',
        default='../data/training/htb_pentest_v4.jsonl',
        help='Output file for training data'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['jsonl', 'alpaca'],
        default='jsonl',
        help='Output format'
    )
    parser.add_argument(
        '--add-tool-calling',
        action='store_true',
        default=True,
        help='Add synthetic tool-calling examples'
    )

    args = parser.parse_args()

    processor = TrainingDataProcessor(args.data_dir, args.output)
    processor.process_all_sources()

    if args.add_tool_calling:
        processor.add_tool_calling_examples()

    processor.save_training_data(format=args.format)


if __name__ == '__main__':
    main()
