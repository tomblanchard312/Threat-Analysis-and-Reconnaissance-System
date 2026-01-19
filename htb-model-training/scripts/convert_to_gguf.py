#!/usr/bin/env python3
"""
Convert trained model to GGUF format for Ollama deployment.

Usage:
    python convert_to_gguf.py --model ../output/htb-mistral-7b-unsloth-merged --output ../output/gguf

Requirements:
    pip install llama-cpp-python
    # Clone llama.cpp for conversion script:
    git clone https://github.com/ggerganov/llama.cpp
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


# Quantization options (ordered by size/quality tradeoff)
QUANT_METHODS = {
    'q2_k': 'Smallest, lowest quality - for testing only',
    'q3_k_s': 'Very small, reduced quality',
    'q3_k_m': 'Small, acceptable quality',
    'q4_0': 'Small, good quality (legacy)',
    'q4_k_s': 'Small, good quality',
    'q4_k_m': 'Medium, good quality (recommended for Jetson)',
    'q5_0': 'Medium, better quality (legacy)',
    'q5_k_s': 'Medium, better quality',
    'q5_k_m': 'Medium-large, high quality',
    'q6_k': 'Large, very high quality',
    'q8_0': 'Largest, best quality',
    'f16': 'Full precision (no quantization)',
}


def check_llama_cpp():
    """Check if llama.cpp is available."""
    llama_cpp_path = Path("llama.cpp")
    if not llama_cpp_path.exists():
        print("[!] llama.cpp not found. Cloning...")
        subprocess.run([
            "git", "clone", "https://github.com/ggerganov/llama.cpp"
        ], check=True)

    convert_script = llama_cpp_path / "convert_hf_to_gguf.py"
    if not convert_script.exists():
        # Try older naming
        convert_script = llama_cpp_path / "convert.py"

    if not convert_script.exists():
        print("[!] Conversion script not found in llama.cpp")
        print("    Please update llama.cpp: cd llama.cpp && git pull")
        sys.exit(1)

    return convert_script


def check_quantize_binary():
    """Check if llama-quantize is built."""
    quantize_paths = [
        Path("llama.cpp/build/bin/llama-quantize"),
        Path("llama.cpp/llama-quantize"),
        Path("llama.cpp/quantize"),
    ]

    for path in quantize_paths:
        if path.exists():
            return path

    print("[!] llama-quantize not found. Building llama.cpp...")
    build_llama_cpp()

    for path in quantize_paths:
        if path.exists():
            return path

    print("[!] Failed to find llama-quantize after build")
    sys.exit(1)


def build_llama_cpp():
    """Build llama.cpp."""
    llama_dir = Path("llama.cpp")
    build_dir = llama_dir / "build"
    build_dir.mkdir(exist_ok=True)

    print("[*] Building llama.cpp...")
    subprocess.run([
        "cmake", "..", "-DCMAKE_BUILD_TYPE=Release"
    ], cwd=build_dir, check=True)

    subprocess.run([
        "cmake", "--build", ".", "--config", "Release", "-j"
    ], cwd=build_dir, check=True)


def convert_to_gguf(model_path: Path, output_path: Path, outtype: str = "f16"):
    """Convert HuggingFace model to GGUF format."""
    convert_script = check_llama_cpp()

    output_file = output_path / f"model-{outtype}.gguf"

    print(f"[*] Converting {model_path} to GGUF...")
    print(f"    Output: {output_file}")

    cmd = [
        sys.executable,
        str(convert_script),
        str(model_path),
        "--outfile", str(output_file),
        "--outtype", outtype,
    ]

    subprocess.run(cmd, check=True)
    print(f"[+] Created: {output_file}")
    return output_file


def quantize_gguf(input_file: Path, output_path: Path, quant_method: str):
    """Quantize GGUF model."""
    quantize_bin = check_quantize_binary()

    output_file = output_path / f"model-{quant_method}.gguf"

    print(f"[*] Quantizing to {quant_method}...")
    print(f"    Output: {output_file}")

    cmd = [
        str(quantize_bin),
        str(input_file),
        str(output_file),
        quant_method.upper(),
    ]

    subprocess.run(cmd, check=True)
    print(f"[+] Created: {output_file}")
    return output_file


def create_modelfile(gguf_path: Path, output_path: Path, model_name: str = "htb-pentest"):
    """Create Ollama Modelfile."""
    modelfile_content = f'''# HTB Pentest Model - Trained on Hack The Box writeups
# Created for educational penetration testing training

FROM {gguf_path.absolute()}

# Model parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1
PARAMETER num_ctx 4096

# System prompt
SYSTEM """You are a helpful penetration testing assistant trained on Hack The Box writeups. You provide detailed, educational explanations of security concepts, tools, and techniques.

Your expertise includes:
- Reconnaissance and enumeration techniques
- Web application security testing
- Network exploitation
- Privilege escalation (Linux and Windows)
- Post-exploitation techniques
- Common security tools (nmap, burp suite, metasploit, etc.)

Important guidelines:
- Always emphasize that techniques should only be used in authorized environments
- Provide educational context for security concepts
- Explain the "why" behind techniques, not just the "how"
- Reference real-world scenarios from HTB machines when relevant
"""

# Template for chat format
TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
{{ .Response }}<|im_end|>"""

# License notice
LICENSE """
This model is trained on publicly available Hack The Box writeups for educational purposes.
Use only in authorized testing environments. The creator is not responsible for misuse.
"""
'''

    modelfile_path = output_path / "Modelfile"
    with open(modelfile_path, 'w') as f:
        f.write(modelfile_content)

    print(f"[+] Created Modelfile: {modelfile_path}")
    print(f"\n    To create Ollama model:")
    print(f"    ollama create {model_name} -f {modelfile_path}")

    return modelfile_path


def main():
    parser = argparse.ArgumentParser(
        description='Convert trained model to GGUF for Ollama',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quantization methods (smallest to largest):
  q2_k   - Smallest, lowest quality (testing only)
  q3_k_m - Small, acceptable quality
  q4_k_m - Medium, good quality (recommended for Jetson)
  q5_k_m - Medium-large, high quality
  q6_k   - Large, very high quality
  q8_0   - Largest, best quality

Example:
  python convert_to_gguf.py --model ../output/htb-mistral-7b-unsloth-merged --quant q4_k_m
        """
    )
    parser.add_argument(
        '--model', '-m',
        default='../output/htb-mistral-7b-unsloth-merged',
        help='Path to trained HuggingFace model'
    )
    parser.add_argument(
        '--output', '-o',
        default='../output/gguf',
        help='Output directory for GGUF files'
    )
    parser.add_argument(
        '--quant', '-q',
        default='q4_k_m',
        choices=list(QUANT_METHODS.keys()),
        help='Quantization method (default: q4_k_m)'
    )
    parser.add_argument(
        '--name', '-n',
        default='htb-pentest',
        help='Model name for Ollama'
    )
    parser.add_argument(
        '--skip-f16',
        action='store_true',
        help='Skip F16 conversion (use existing F16 GGUF)'
    )

    args = parser.parse_args()

    model_path = Path(args.model)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    if not model_path.exists():
        print(f"[!] Model not found: {model_path}")
        print("    Train the model first using unsloth_config.py or axolotl")
        sys.exit(1)

    print("=" * 60)
    print("GGUF Conversion for Ollama Deployment")
    print("=" * 60)
    print(f"Model: {model_path}")
    print(f"Output: {output_path}")
    print(f"Quantization: {args.quant}")
    print("=" * 60)

    # Step 1: Convert to F16 GGUF
    f16_file = output_path / "model-f16.gguf"
    if args.skip_f16 and f16_file.exists():
        print(f"[*] Using existing F16: {f16_file}")
    else:
        f16_file = convert_to_gguf(model_path, output_path, "f16")

    # Step 2: Quantize
    if args.quant != 'f16':
        quant_file = quantize_gguf(f16_file, output_path, args.quant)
    else:
        quant_file = f16_file

    # Step 3: Create Modelfile
    create_modelfile(quant_file, output_path, args.name)

    print("\n" + "=" * 60)
    print("Conversion complete!")
    print("=" * 60)
    print(f"\nFiles created in {output_path}:")
    for f in output_path.glob("*"):
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  - {f.name} ({size_mb:.1f} MB)")

    print(f"\nNext steps:")
    print(f"  1. Copy GGUF to Jetson: scp {quant_file} jetson@<IP>:~/models/")
    print(f"  2. Copy Modelfile: scp {output_path}/Modelfile jetson@<IP>:~/models/")
    print(f"  3. On Jetson, create model: ollama create {args.name} -f ~/models/Modelfile")
    print(f"  4. Test: ollama run {args.name}")


if __name__ == "__main__":
    main()
