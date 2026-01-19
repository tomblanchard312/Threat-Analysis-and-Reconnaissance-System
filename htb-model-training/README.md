# HTB Pentest Model Training

Train a custom AI model on Hack The Box writeups for educational penetration testing.

## Overview

This project provides a complete pipeline to:
1. **Scrape** HTB writeups from 0xdf's blog
2. **Process** content into instruction-response training pairs
3. **Fine-tune** a 7B parameter model using QLoRA
4. **Export** to GGUF format for Ollama
5. **Deploy** to your Jetson Orin Nano

## Prerequisites

### Local Workstation (for training)
- NVIDIA GPU with 16GB+ VRAM (RTX 3090/4090 recommended)
- Python 3.10+
- CUDA 11.8+
- 50GB+ free disk space

### Jetson Orin Nano (for inference)
- Ollama container running (see main project README)
- 8GB+ free storage for model

## Quick Start

### Step 1: Setup Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Scrape Writeups

```bash
cd scripts

# Scrape all HTB writeups from 0xdf (takes 30-60 minutes)
python scrape_0xdf.py --output ../data/raw_writeups

# Or test with a few writeups first
python scrape_0xdf.py --output ../data/raw_writeups --limit 10
```

### Step 3: Process Training Data

```bash
# Convert writeups to training format
python process_to_training_data.py \
    --input ../data/raw_writeups/processed \
    --output ../data/training

# Check generated data
ls ../data/training/
# htb_alpaca.json    - Alpaca format
# htb_sharegpt.json  - ShareGPT format
# htb_chatml.json    - ChatML format (for Axolotl/Unsloth)
# metadata.json      - Dataset statistics
# train.json         - Training split
# test.json          - Test split
```

### Step 4: Train the Model

**Option A: Unsloth (Recommended - 2x faster)**

```bash
# Install Unsloth
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --no-deps xformers trl peft accelerate bitsandbytes

# Train
cd configs
python unsloth_config.py
```

**Option B: Axolotl (More configurable)**

```bash
# Install Axolotl
pip install axolotl

# Train
accelerate launch -m axolotl.cli.train configs/axolotl_config.yaml
```

Training takes approximately:
- RTX 4090: 2-4 hours
- RTX 3090: 4-6 hours
- A100: 1-2 hours

### Step 5: Convert to GGUF

```bash
cd scripts

# Convert and quantize (q4_k_m recommended for Jetson)
python convert_to_gguf.py \
    --model ../output/htb-mistral-7b-unsloth-merged \
    --output ../output/gguf \
    --quant q4_k_m

# Output files:
# ../output/gguf/model-f16.gguf    - Full precision
# ../output/gguf/model-q4_k_m.gguf - Quantized (recommended)
# ../output/gguf/Modelfile          - Ollama config
```

### Step 6: Deploy to Jetson

```bash
# Automatic deployment
./deploy_to_jetson.sh 192.168.1.100

# Or manual:
scp ../output/gguf/model-q4_k_m.gguf jetson@<IP>:~/models/
scp ../output/gguf/Modelfile jetson@<IP>:~/models/
ssh jetson@<IP>
docker exec ollama-orin ollama create htb-pentest -f ~/models/Modelfile
```

### Step 7: Test

```bash
# Interactive chat
docker exec -it ollama-orin ollama run htb-pentest

# API test
curl http://JETSON_IP:11434/api/generate -d '{
  "model": "htb-pentest",
  "prompt": "How would you enumerate a web application?"
}'
```

## Project Structure

```
htb-model-training/
├── scripts/
│   ├── scrape_0xdf.py           # Web scraper for HTB writeups
│   ├── process_to_training_data.py  # Convert to training format
│   ├── convert_to_gguf.py       # Export for Ollama
│   └── deploy_to_jetson.sh      # Deployment script
├── configs/
│   ├── axolotl_config.yaml      # Axolotl training config
│   └── unsloth_config.py        # Unsloth training script
├── data/
│   ├── raw_writeups/            # Scraped content
│   └── training/                # Processed training data
├── output/
│   ├── htb-mistral-7b-*/        # Trained model checkpoints
│   └── gguf/                    # Exported GGUF files
└── README.md
```

## Configuration Options

### Scraper Options

| Option | Default | Description |
|--------|---------|-------------|
| `--output` | `../data/raw_writeups` | Output directory |
| `--limit` | None | Limit number of writeups |
| `--delay` | 1.0 | Delay between requests (seconds) |

### Training Options (Unsloth)

Edit `configs/unsloth_config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MODEL_NAME` | mistral-7b-v0.3 | Base model |
| `LORA_R` | 32 | LoRA rank |
| `LEARNING_RATE` | 2e-4 | Learning rate |
| `NUM_EPOCHS` | 3 | Training epochs |
| `BATCH_SIZE` | 2 | Batch size |

### Quantization Options

| Method | Size | Quality | Use Case |
|--------|------|---------|----------|
| q2_k | ~2.5GB | Low | Testing only |
| q4_k_m | ~4GB | Good | **Recommended for Jetson** |
| q5_k_m | ~5GB | Better | If you have space |
| q8_0 | ~7GB | Best | Maximum quality |

## Expected Results

After training on ~200 HTB writeups:
- **Dataset**: ~5,000-10,000 instruction-response pairs
- **Model size**: ~4GB (q4_k_m quantized)
- **Inference speed**: 10-20 tokens/sec on Jetson Orin Nano

### Sample Output

```
User: How would you approach the Lame machine on HTB?

Model: Lame is an easy Linux machine that's great for beginners. Here's my approach:

## Reconnaissance
Start with an nmap scan:
```
nmap -sC -sV -oA nmap/lame 10.10.10.3
```

This reveals several services including SMB on ports 139/445.

## Enumeration
The Samba version (3.0.20) is vulnerable to CVE-2007-2447,
which allows remote code execution through the username field.

## Exploitation
Use Metasploit's exploit/multi/samba/usermap_script module:
```
use exploit/multi/samba/usermap_script
set RHOSTS 10.10.10.3
run
```

This gives you a root shell directly - no privilege escalation needed!

Remember: Only use these techniques in authorized environments like HTB.
```

## Troubleshooting

### Out of Memory During Training

- Reduce `BATCH_SIZE` to 1
- Reduce `LORA_R` to 16
- Enable gradient checkpointing (already enabled)

### Slow Inference on Jetson

- Use smaller quantization (q3_k_m or q2_k)
- Reduce `num_ctx` in Modelfile
- Ensure swap is configured (see main project docs)

### Model Gives Generic Responses

- Increase training epochs to 5
- Add more diverse writeups to training data
- Increase LoRA rank to 64

## Legal & Ethical Notice

This project is for **educational purposes only**. The trained model:
- Should only be used in authorized testing environments
- Is based on publicly available writeups
- Does not grant permission to attack any systems

Always obtain proper authorization before security testing.

## Credits

- Training data: [0xdf hacks stuff](https://0xdf.gitlab.io/)
- Base model: [Mistral AI](https://mistral.ai/)
- Training framework: [Unsloth](https://github.com/unslothai/unsloth)
- Inference: [Ollama](https://ollama.ai/)
