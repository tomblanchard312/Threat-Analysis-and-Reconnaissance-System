#!/usr/bin/env python3
"""
Master Scraping Pipeline
Orchestrates all scrapers and processes data for model training.

Usage:
    python run_scraping_pipeline.py --all
    python run_scraping_pipeline.py --source hacktricks --source kali
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f" {description}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed: {e}")
        return False
    except FileNotFoundError:
        print(f"[!] Command not found: {cmd[0]}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Run the complete scraping and processing pipeline'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Run all scrapers'
    )
    parser.add_argument(
        '--source', '-s',
        action='append',
        choices=['0xdf', 'hacktricks', 'kali', 'owasp'],
        help='Specific sources to scrape (can be specified multiple times)'
    )
    parser.add_argument(
        '--process-only',
        action='store_true',
        help='Only run the processing step (skip scraping)'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit items per source (for testing)'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=0.5,
        help='Delay between requests'
    )

    args = parser.parse_args()

    scripts_dir = Path(__file__).parent
    data_dir = scripts_dir.parent / 'data'

    sources = args.source if args.source else []
    if args.all:
        sources = ['0xdf', 'hacktricks', 'kali', 'owasp']

    if not sources and not args.process_only:
        print("Please specify --all or --source <name>")
        parser.print_help()
        sys.exit(1)

    results = {}

    if not args.process_only:
        # Run scrapers
        for source in sources:
            if source == '0xdf':
                cmd = [
                    sys.executable, str(scripts_dir / 'scrape_0xdf.py'),
                    '--output', str(data_dir / 'raw_writeups'),
                    '--delay', str(args.delay)
                ]
                if args.limit:
                    cmd.extend(['--limit', str(args.limit)])
                results['0xdf'] = run_command(cmd, 'Scraping 0xdf HTB Writeups')

            elif source == 'hacktricks':
                cmd = [
                    sys.executable, str(scripts_dir / 'scrape_hacktricks.py'),
                    '--output', str(data_dir / 'hacktricks'),
                    '--delay', str(args.delay)
                ]
                if args.limit:
                    cmd.extend(['--limit', str(args.limit)])
                results['hacktricks'] = run_command(cmd, 'Scraping HackTricks')

            elif source == 'kali':
                cmd = [
                    sys.executable, str(scripts_dir / 'scrape_kali_tools.py'),
                    '--output', str(data_dir / 'kali_tools'),
                    '--delay', str(args.delay)
                ]
                if args.limit:
                    cmd.extend(['--limit', str(args.limit)])
                results['kali'] = run_command(cmd, 'Scraping Kali Tools')

            elif source == 'owasp':
                cmd = [
                    sys.executable, str(scripts_dir / 'scrape_owasp.py'),
                    '--output', str(data_dir / 'owasp'),
                    '--delay', str(args.delay)
                ]
                if args.limit:
                    cmd.extend(['--limit', str(args.limit)])
                results['owasp'] = run_command(cmd, 'Scraping OWASP Testing Guide')

    # Process all data
    print(f"\n{'='*60}")
    print(" Processing Training Data")
    print(f"{'='*60}\n")

    cmd = [
        sys.executable, str(scripts_dir / 'process_training_data.py'),
        '--data-dir', str(data_dir),
        '--output', str(data_dir / 'training' / 'htb_pentest_v4.jsonl'),
        '--add-tool-calling'
    ]
    results['processing'] = run_command(cmd, 'Generating Training Data')

    # Summary
    print(f"\n{'='*60}")
    print(" Pipeline Summary")
    print(f"{'='*60}\n")

    for step, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        print(f"  {step}: {status}")

    # Check output
    training_file = data_dir / 'training' / 'htb_pentest_v4.jsonl'
    if training_file.exists():
        line_count = sum(1 for _ in open(training_file, encoding='utf-8'))
        print(f"\n[+] Training data ready: {training_file}")
        print(f"[+] Total examples: {line_count}")
    else:
        print(f"\n[!] Training data not found at {training_file}")

    print(f"\n{'='*60}")
    print(" Next Steps")
    print(f"{'='*60}")
    print("""
1. Review the training data:
   head -20 ../data/training/htb_pentest_v4.jsonl

2. Start fine-tuning with Unsloth:
   python train_model.py --config configs/unsloth_config.py

3. Or use Axolotl:
   accelerate launch -m axolotl.cli.train configs/axolotl_config.yaml

4. After training, convert to GGUF:
   python scripts/convert_to_gguf.py --model output/htb-pentest-v4
""")


if __name__ == '__main__':
    main()
