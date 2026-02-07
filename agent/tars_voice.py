"""
TARS Voice Module
Threat Analysis and Reconnaissance System
ElevenLabs TTS Integration - Movie-accurate voice aesthetic

Usage:
    from tars_voice import tars_speak
    tars_speak("Initiating reconnaissance scan.")
"""

import os
import requests
from pathlib import Path

try:
    from dotenv import load_dotenv
    _dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(_dotenv_path)
except ImportError:
    pass  # python-dotenv not installed, relying on system env vars

# Configuration
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
# TARS voice ID - hardcoded for consistent personality
TARS_VOICE_ID = "NCKTc2m4SgOQ7jPgxf0Y"
DEFAULT_VOICE_ID = TARS_VOICE_ID

# TARS-optimized voice settings
TARS_VOICE_SETTINGS = {
    "stability": 0.85,           # High = controlled, flat delivery
    "similarity_boost": 0.60,    # Lower = slightly more synthetic
    "style": 0.05,               # Minimal = deadpan, no drama
    "use_speaker_boost": True    # Clarity enhancement
}


def tars_speak(
    text: str,
    output_path: str = "tars_output.mp3",
    apply_filter: bool = False
) -> str | None:
    """
    Generate TARS-style speech using ElevenLabs API.

    Args:
        text: The text for TARS to speak
        output_path: Where to save the audio file
        apply_filter: Apply post-processing for comms/radio effect

    Returns:
        Path to the generated audio file, or None on failure
    """
    
    if not ELEVENLABS_API_KEY:
        print("[TARS] ERROR: ELEVENLABS_API_KEY not found in environment variables.")
        print("[TARS] Set it in your .env file or system environment.")
        return None
    
    voice_id = DEFAULT_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": TARS_VOICE_SETTINGS
    }
    
    print(f"[TARS] Generating speech: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "wb") as f:
                f.write(response.content)
            
            print(f"[TARS] Audio saved: {output_path}")
            
            if apply_filter:
                filtered_path = _apply_tars_filter(output_path)
                return filtered_path if filtered_path else output_path
            
            return str(output_path)
        else:
            print(f"[TARS] API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"[TARS] Connection error: {e}")
        return None


def _apply_tars_filter(input_path: str) -> str | None:
    """
    Apply subtle radio/comms effect for authentic TARS aesthetic.
    Requires: pip install pydub
    """
    try:
        from pydub import AudioSegment
        from pydub.effects import high_pass_filter, compress_dynamic_range
    except ImportError:
        print("[TARS] WARNING: pydub not installed. Skipping audio filter.")
        print("[TARS] Install with: pip install pydub")
        return None
    
    output_path = input_path.replace(".mp3", "_processed.mp3")
    
    try:
        audio = AudioSegment.from_mp3(input_path)
        
        # High-pass filter - removes low rumble, adds "comms" feel
        audio = high_pass_filter(audio, cutoff=300)
        
        # Compression - evens out delivery, more robotic
        audio = compress_dynamic_range(audio, threshold=-20.0, ratio=4.0)
        
        # Normalize volume
        audio = audio.normalize()
        
        audio.export(output_path, format="mp3")
        print(f"[TARS] Filtered audio saved: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"[TARS] Filter error: {e}")
        return None


def list_voices() -> None:
    """Display TARS voice configuration."""
    print("\n[TARS] Voice Configuration:")
    print("-" * 40)
    print(f"  TARS Voice ID: {TARS_VOICE_ID}")
    print("-" * 40)


def test_connection() -> bool:
    """Test ElevenLabs API connectivity."""
    if not ELEVENLABS_API_KEY:
        print("[TARS] ERROR: No API key configured.")
        return False
    
    url = "https://api.elevenlabs.io/v1/user"
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            user_data = response.json()
            print(f"[TARS] Connection verified.")
            print(f"[TARS] Account: {user_data.get('subscription', {}).get('tier', 'Unknown')}")
            return True
        else:
            print(f"[TARS] Connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"[TARS] Connection error: {e}")
        return False


# =============================================================================
# CLI Interface
# =============================================================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="TARS Voice - Threat Analysis and Reconnaissance System TTS"
    )
    parser.add_argument("text", nargs="?", help="Text to speak")
    parser.add_argument("-o", "--output", default="tars_output.mp3", help="Output file path")
    parser.add_argument("-f", "--filter", action="store_true", help="Apply comms filter")
    parser.add_argument("--test", action="store_true", help="Test API connection")
    parser.add_argument("--info", action="store_true", help="Show voice configuration")

    args = parser.parse_args()

    if args.test:
        test_connection()
    elif args.info:
        list_voices()
    elif args.text:
        tars_speak(args.text, args.output, args.filter)
    else:
        # Demo mode
        print("[TARS] No text provided. Running demo...")
        test_connection()
        list_voices()
        tars_speak(
            "Cooper, this is no time for caution. Initiating reconnaissance scan.",
            "tars_demo.mp3"
        )
