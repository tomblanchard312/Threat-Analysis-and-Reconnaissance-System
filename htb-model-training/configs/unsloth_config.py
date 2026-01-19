#!/usr/bin/env python3
"""
Unsloth Training Configuration for HTB Pentest Model
Faster alternative to Axolotl with 2x speedup and 50% less memory.

Usage:
    python unsloth_config.py

Requirements:
    pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
    pip install --no-deps xformers trl peft accelerate bitsandbytes
"""

import json
import torch
from datasets import load_dataset, Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

# ============================================================================
# CONFIGURATION
# ============================================================================

# Model settings
MODEL_NAME = "unsloth/mistral-7b-v0.3-bnb-4bit"  # Pre-quantized for speed
MAX_SEQ_LENGTH = 4096
LOAD_IN_4BIT = True

# LoRA settings
LORA_R = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.05
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj"
]

# Training settings
BATCH_SIZE = 2
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
WARMUP_RATIO = 0.1
WEIGHT_DECAY = 0.01

# Paths
DATASET_PATH = "../data/training/htb_chatml.json"
OUTPUT_DIR = "../output/htb-mistral-7b-unsloth"

# ============================================================================
# CHAT TEMPLATE
# ============================================================================

CHATML_TEMPLATE = """<|im_start|>system
You are a helpful penetration testing assistant trained on Hack The Box writeups. You provide detailed, educational explanations of security concepts, tools, and techniques. Always emphasize that these techniques should only be used in authorized environments.<|im_end|>
<|im_start|>user
{instruction}<|im_end|>
<|im_start|>assistant
{output}<|im_end|>"""


def format_prompts(examples):
    """Format examples using ChatML template."""
    texts = []
    for messages in examples['messages']:
        # Extract user and assistant messages
        user_msg = ""
        assistant_msg = ""
        for msg in messages:
            if msg['role'] == 'user':
                user_msg = msg['content']
            elif msg['role'] == 'assistant':
                assistant_msg = msg['content']

        text = CHATML_TEMPLATE.format(
            instruction=user_msg,
            output=assistant_msg
        )
        texts.append(text)
    return {"text": texts}


def main():
    print("=" * 60)
    print("HTB Pentest Model Training with Unsloth")
    print("=" * 60)

    # ========================================================================
    # LOAD MODEL
    # ========================================================================
    print("\n[1/5] Loading model...")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,  # Auto-detect
        load_in_4bit=LOAD_IN_4BIT,
    )

    # ========================================================================
    # ADD LORA ADAPTERS
    # ========================================================================
    print("\n[2/5] Adding LoRA adapters...")

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_R,
        target_modules=TARGET_MODULES,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",  # Optimized checkpointing
        random_state=42,
        use_rslora=False,
        loftq_config=None,
    )

    # ========================================================================
    # LOAD DATASET
    # ========================================================================
    print("\n[3/5] Loading dataset...")

    # Load from JSON
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    dataset = Dataset.from_list(data)
    dataset = dataset.map(format_prompts, batched=True)

    print(f"    Dataset size: {len(dataset)} examples")
    print(f"    Sample: {dataset[0]['text'][:200]}...")

    # ========================================================================
    # CONFIGURE TRAINING
    # ========================================================================
    print("\n[4/5] Configuring trainer...")

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        warmup_ratio=WARMUP_RATIO,
        num_train_epochs=NUM_EPOCHS,
        learning_rate=LEARNING_RATE,
        weight_decay=WEIGHT_DECAY,
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        optim="adamw_8bit",
        seed=42,
        report_to="none",  # Set to "wandb" if using Weights & Biases
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        dataset_num_proc=2,
        packing=True,  # Pack short sequences together
        args=training_args,
    )

    # ========================================================================
    # TRAIN
    # ========================================================================
    print("\n[5/5] Starting training...")
    print("-" * 60)

    # Show GPU memory before training
    if torch.cuda.is_available():
        gpu_stats = torch.cuda.get_device_properties(0)
        start_gpu_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
        print(f"    GPU: {gpu_stats.name}")
        print(f"    Memory: {start_gpu_memory} GB / {max_memory} GB")

    trainer_stats = trainer.train()

    # ========================================================================
    # SAVE MODEL
    # ========================================================================
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)

    # Show final stats
    if torch.cuda.is_available():
        used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
        print(f"Peak GPU memory: {used_memory} GB")

    print(f"Training time: {trainer_stats.metrics['train_runtime']:.2f} seconds")
    print(f"Training loss: {trainer_stats.metrics['train_loss']:.4f}")

    # Save LoRA adapters
    print(f"\nSaving LoRA adapters to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    # Save merged model (optional, for easier deployment)
    merged_output = f"{OUTPUT_DIR}-merged"
    print(f"Saving merged model to {merged_output}...")
    model.save_pretrained_merged(merged_output, tokenizer, save_method="merged_16bit")

    print("\n" + "=" * 60)
    print("Done! Next steps:")
    print("  1. Convert to GGUF: python convert_to_gguf.py")
    print("  2. Create Ollama model: ollama create htb-pentest -f Modelfile")
    print("=" * 60)


if __name__ == "__main__":
    main()
