#!/usr/bin/env python3
"""
Merge LoRA adapters with base model.
This is required before converting to GGUF format.
"""

import os
import sys
from pathlib import Path

# Disable tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Paths
SCRIPT_DIR = Path(__file__).parent
LORA_PATH = Path("C:/htb-model-training/htb-pentest-v5-qlora/final")
OUTPUT_PATH = Path("C:/htb-model-training/htb-pentest-v5-merged")
BASE_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"


def main():
    print("=" * 60)
    print("Merging LoRA Adapters with Base Model")
    print("=" * 60)
    print()

    if not LORA_PATH.exists():
        print(f"[ERROR] LoRA adapter not found: {LORA_PATH}")
        sys.exit(1)

    print(f"[INFO] LoRA adapter: {LORA_PATH}")
    print(f"[INFO] Base model: {BASE_MODEL}")
    print(f"[INFO] Output: {OUTPUT_PATH}")
    print()

    # Check GPU
    if torch.cuda.is_available():
        print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")
        device = "cuda"
    else:
        print("[INFO] Running on CPU (this will be slower)")
        device = "cpu"
    print()

    # Load tokenizer
    print("[1/4] Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(str(LORA_PATH))
    print(f"  Vocab size: {tokenizer.vocab_size}")

    # Load base model
    print("[2/4] Loading base model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    print("  Base model loaded!")

    # Load and merge LoRA
    print("[3/4] Loading and merging LoRA adapters...")
    model = PeftModel.from_pretrained(base_model, str(LORA_PATH))
    model = model.merge_and_unload()
    print("  LoRA merged!")

    # Save merged model
    print("[4/4] Saving merged model...")
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(OUTPUT_PATH), safe_serialization=True)
    tokenizer.save_pretrained(str(OUTPUT_PATH))

    print()
    print("=" * 60)
    print("Merge complete!")
    print("=" * 60)
    print()
    print(f"Merged model saved to: {OUTPUT_PATH}")
    print()
    print("Next step: Convert to GGUF format")
    print(f"  cd scripts && python convert_to_gguf.py --model {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
