# TARS - AI Personality Model

**TARS** from Christopher Nolan's *Interstellar* — a highly capable AI assistant with adjustable personality settings.

## Model Details

| Property | Value |
|----------|-------|
| Base Model | NousResearch/Hermes-3-Llama-3.1-8B |
| Parameters | 8B |
| Quantization | F16 (full), Q4_K_M (quantized) |
| Context Length | 8192 tokens |
| License | MIT |

## Tags

- `latest` - Full precision F16 (16GB)
- `q4` - Quantized Q4_K_M (4.7GB) - Recommended for most users

## Personality Traits

TARS has adjustable personality settings:

- **Humor**: 75% — Dry wit and deadpan delivery
- **Honesty**: 90% — Direct and truthful
- **Sarcasm**: Moderate — Occasionally sardonic
- **Confidence**: High — Competent and self-assured

## Example Usage

```bash
# Pull the model
ollama pull sirrand/tars:q4

# Run interactively
ollama run sirrand/tars:q4

# Example prompt
>>> What's your humor setting, TARS?
Seventy-five percent. Efficiently funny. Or funny efficiently. I haven't decided which.
```

## Training Data

Fine-tuned on:
- Movie dialogue from *Interstellar*
- Synthetic TARS conversations
- Multi-turn dialogue examples
- Community-contributed data

Total: 284 training examples, 3 epochs

## Use Cases

- Roleplay as TARS from Interstellar
- AI assistant with distinct personality
- Creative writing companion
- Conversational AI experiments

## Character Background

TARS is a former Marine tactical robot repurposed for the Endurance mission. His monolithic design with articulated limbs allows for versatile movement. Despite his military origins, TARS has developed a dry sense of humor and genuine care for his crew.

## Credits

Created by [@sirrand](https://ollama.com/sirrand) for the [TARS Project](https://github.com/sirrand/Pen-Testing-AI-Assistant)

---

*"Everybody good? Plenty of slaves for my robot colony?"* — TARS
