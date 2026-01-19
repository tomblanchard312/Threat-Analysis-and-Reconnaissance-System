#!/usr/bin/env python3
"""
HTB Pentest Model Training Script
Fine-tunes Mistral 7B on HTB writeups using QLoRA

Features:
- Real-time progress bars
- GPU memory monitoring
- Checkpoint saving
"""

import json
import os
import sys
from pathlib import Path

# Disable tokenizer parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from datasets import Dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

# ============================================================================
# CONFIGURATION
# ============================================================================

# Model
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.3"
MAX_SEQ_LENGTH = 2048  # Reduced for memory

# LoRA
LORA_R = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.05

# Training
BATCH_SIZE = 1  # Small batch for 24GB VRAM
GRADIENT_ACCUMULATION = 8  # Effective batch = 8
LEARNING_RATE = 2e-4
NUM_EPOCHS = 5  # Increased for smaller conceptual dataset
WARMUP_RATIO = 0.1

# Paths
SCRIPT_DIR = Path(__file__).parent
DATASET_PATH = SCRIPT_DIR / "data" / "training" / "htb_combined_v3.json"
OUTPUT_DIR = Path("C:/htb-model-training/htb-mistral-7b-qlora-v3-tools")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_gpu_stats():
    """Print current GPU memory usage."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        reserved = torch.cuda.memory_reserved() / 1024**3
        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"  GPU Memory: {allocated:.1f}GB allocated, {reserved:.1f}GB reserved / {total:.1f}GB total")


def format_chat(example):
    """Format example into chat template."""
    messages = example.get('messages', [])

    # Build conversation
    text_parts = []

    # Add system message
    text_parts.append("<|im_start|>system")
    text_parts.append("You are a helpful penetration testing assistant trained on Hack The Box writeups. You can execute commands using the pentest-tools skill when asked to scan, ping, or perform network operations. For action requests, respond with a tool call in this format: <tool_call>{\"name\": \"pentest-tools\", \"arguments\": {\"command\": \"cmd\", \"args\": \"args\"}}</tool_call>. For questions and explanations, provide detailed educational responses. Always emphasize authorized use only.<|im_end|>")

    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        text_parts.append(f"<|im_start|>{role}")
        text_parts.append(f"{content}<|im_end|>")

    return {"text": "\n".join(text_parts)}


# ============================================================================
# MAIN TRAINING
# ============================================================================

def main():
    print("=" * 60)
    print("HTB Pentest Model Training")
    print("=" * 60)
    print()

    # Check GPU
    if not torch.cuda.is_available():
        print("[ERROR] CUDA not available!")
        sys.exit(1)

    print(f"[INFO] GPU: {torch.cuda.get_device_name(0)}")
    print_gpu_stats()
    print()

    # ========================================================================
    # LOAD DATASET
    # ========================================================================
    print("[1/5] Loading dataset...")

    if not DATASET_PATH.exists():
        print(f"[ERROR] Dataset not found: {DATASET_PATH}")
        sys.exit(1)

    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f"  Loaded {len(raw_data)} examples")

    # Convert to dataset and format
    dataset = Dataset.from_list(raw_data)
    dataset = dataset.map(format_chat, remove_columns=dataset.column_names)

    # Split into train/eval
    dataset = dataset.train_test_split(test_size=0.05, seed=42)
    train_dataset = dataset['train']
    eval_dataset = dataset['test']

    print(f"  Train: {len(train_dataset)}, Eval: {len(eval_dataset)}")
    print()

    # ========================================================================
    # LOAD MODEL
    # ========================================================================
    print("[2/5] Loading model (this takes a few minutes)...")
    print_gpu_stats()

    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Load model in 4-bit
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )

    model.config.use_cache = False
    model = prepare_model_for_kbit_training(model)

    print("  Model loaded!")
    print_gpu_stats()
    print()

    # ========================================================================
    # ADD LORA
    # ========================================================================
    print("[3/5] Adding LoRA adapters...")

    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )

    model = get_peft_model(model, lora_config)

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"  Trainable: {trainable_params:,} / {total_params:,} ({100 * trainable_params / total_params:.2f}%)")
    print_gpu_stats()
    print()

    # ========================================================================
    # TRAINING CONFIG
    # ========================================================================
    print("[4/5] Configuring training...")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    training_args = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        warmup_ratio=WARMUP_RATIO,
        lr_scheduler_type="cosine",

        # Precision
        bf16=True,

        # Logging
        logging_steps=10,
        logging_first_step=True,

        # Evaluation
        eval_strategy="steps",
        eval_steps=100,

        # Checkpoints
        save_strategy="steps",
        save_steps=100,
        save_total_limit=3,

        # Memory optimization
        gradient_checkpointing=True,
        optim="adamw_8bit",

        # Progress
        report_to="none",
        disable_tqdm=False,

        # SFT-specific config (moved from SFTTrainer)
        dataset_text_field="text",
        max_length=MAX_SEQ_LENGTH,
        packing=False,
    )

    print(f"  Epochs: {NUM_EPOCHS}")
    print(f"  Batch size: {BATCH_SIZE} x {GRADIENT_ACCUMULATION} = {BATCH_SIZE * GRADIENT_ACCUMULATION}")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Output: {OUTPUT_DIR}")
    print()

    # ========================================================================
    # TRAIN
    # ========================================================================
    print("[5/5] Starting training...")
    print("=" * 60)
    print()

    trainer = SFTTrainer(
        model=model,
        processing_class=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        args=training_args,
    )

    # Train!
    trainer.train()

    # ========================================================================
    # SAVE
    # ========================================================================
    print()
    print("=" * 60)
    print("Training complete!")
    print("=" * 60)
    print()

    print("Saving model...")
    trainer.save_model(str(OUTPUT_DIR / "final"))
    tokenizer.save_pretrained(str(OUTPUT_DIR / "final"))

    print(f"  Saved to: {OUTPUT_DIR / 'final'}")
    print_gpu_stats()
    print()

    print("Next steps:")
    print("  1. Merge LoRA weights: python merge_lora.py")
    print("  2. Convert to GGUF: python convert_to_gguf.py")
    print("  3. Deploy to Jetson: ./deploy_to_jetson.sh <ip>")


if __name__ == "__main__":
    main()
