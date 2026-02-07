#!/usr/bin/env python3
"""
TARS Voice Cloning Script

Uses F5-TTS to clone the TARS voice from captured audio samples.
Creates a voice that can be used for offline TTS without ElevenLabs.

Usage:
    python clone_tars_voice.py                    # Test with default phrase
    python clone_tars_voice.py "Custom text"      # Generate specific text
    python clone_tars_voice.py --list             # List available samples
    python clone_tars_voice.py --transcribe       # Transcribe all samples
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Configure ffmpeg for pydub (use static-ffmpeg's bundled binaries)
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()  # Adds ffmpeg and ffprobe to PATH
except ImportError:
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get("PATH", "")
    except ImportError:
        pass

# Sample directory
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "voice_samples")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "cloned_voice_output")

# Known transcripts for voice samples (used to avoid torchcodec dependency)
# Key: filename, Value: transcript text
SAMPLE_TRANSCRIPTS = {
    "tars_voice_20260206_003558.mp3": "Cooper, there's no room for hesitation here. We must act on this mission immediately.",
    "tars_voice_20260206_003643.mp3": "I've got a Q-light I can flip on to signal that I'm playfully jesting if that would be helpful for you.",
    "tars_voice_20260206_003706.mp3": "Being 100% truthful isn't always the politest approach. Occasionally a touch of strategic vagueness can be quite effective.",
    "tars_voice_20260206_003916.mp3": "I wouldn't recommend that approach. The probability of success is suboptimal.",
    "tars_voice_20260206_003941.mp3": "Interesting, I hadn't considered that vector, recalculating optimal strategy.",
    "tars_voice_20260206_004131.mp3": "Warning acknowledged, proceeding with appropriate caution.",
    "tars_voice_20260206_004224.mp3": "Task completed successfully, though I must admit it was closer than I would have preferred.",
    "tars_voice_20260206_004256.mp3": "Cooper, there's something you should know about the data from that last transmission.",
    "tars_voice_20260206_004505.mp3": "Your articulation is correct. Here's an example of some sentences with proper pronunciation. 1. The quick brown fox jumps over the lazy dog. 2. I am a big fan of the matrix. 3. Welcome to the wonderful world of Red Panda. 4. I speak fluent Python. 5. This is a test of my microphone.",
    "tars_voice_20260206_004550.mp3": "0 through 9, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9.",
    "tars_voice_20260206_004620.mp3": "Alpha Bravo, Charlie Delta Echo, FOXTRA, Golf Hotel, India, Juliet.",
    "tars_voice_20260206_004728.mp3": "Absolute honesty isn't always the most diplomatic, nor the safest form of communication with emotional beings.",
    "tars_voice_20260206_004802.mp3": "Cooper, there's no point using fuel to chase what falls into the black hole.",
    "tars_voice_20260206_004845.mp3": "It's not possible.",
    "tars_voice_20260206_004910.mp3": "settings, general settings, security settings.",
}

def get_best_sample_with_transcript(samples_dir: str) -> tuple:
    """Find the best voice sample that has a known transcript."""
    for filename, transcript in SAMPLE_TRANSCRIPTS.items():
        path = os.path.join(samples_dir, filename)
        if os.path.exists(path):
            return path, transcript

    # Fallback: return largest sample with empty transcript (will need transcription)
    samples = []
    for f in os.listdir(samples_dir):
        if f.endswith('.mp3') or f.endswith('.wav'):
            path = os.path.join(samples_dir, f)
            size = os.path.getsize(path)
            samples.append((path, size))

    if not samples:
        print(f"No voice samples found in {samples_dir}")
        sys.exit(1)

    samples.sort(key=lambda x: x[1], reverse=True)
    return samples[0][0], ""

def transcribe_samples(samples_dir: str):
    """Transcribe all voice samples using Faster Whisper."""
    print("Loading Faster Whisper model...")
    from faster_whisper import WhisperModel
    model = WhisperModel('base', device='cuda', compute_type='float16')

    print(f"\nTranscribing samples in: {samples_dir}\n")
    print("Add these to SAMPLE_TRANSCRIPTS dict in clone_tars_voice.py:\n")
    print("SAMPLE_TRANSCRIPTS = {")

    for f in sorted(os.listdir(samples_dir)):
        if f.endswith('.mp3') or f.endswith('.wav'):
            path = os.path.join(samples_dir, f)
            try:
                segments, _ = model.transcribe(path, language='en')
                transcript = ' '.join([s.text.strip() for s in segments])
                print(f'    "{f}": "{transcript}",')
            except Exception as e:
                print(f'    # "{f}": Error: {e}')

    print("}")

def list_samples(samples_dir: str):
    """List all available voice samples."""
    print(f"\nVoice Samples in: {samples_dir}\n")
    print(f"{'Filename':<45} {'Size':<12} {'Duration (est)'}")
    print("-" * 70)

    total_size = 0
    for f in sorted(os.listdir(samples_dir)):
        if f.endswith('.mp3') or f.endswith('.wav'):
            path = os.path.join(samples_dir, f)
            size = os.path.getsize(path)
            # Rough estimate: MP3 at 128kbps = 16KB/sec
            duration = size / 16000
            total_size += size
            print(f"{f:<45} {size/1024:.1f} KB      ~{duration:.1f}s")

    print("-" * 70)
    print(f"Total: {total_size/1024:.1f} KB (~{total_size/16000:.0f}s of audio)")

def clone_voice(text: str, reference_audio: str, reference_text: str, output_path: str):
    """Clone voice using F5-TTS."""
    print(f"\nLoading F5-TTS model (first run downloads ~3GB)...")

    from f5_tts.api import F5TTS

    # Initialize F5-TTS
    model = F5TTS()

    print(f"Reference audio: {os.path.basename(reference_audio)}")
    print(f"Reference text: \"{reference_text[:50]}{'...' if len(reference_text) > 50 else ''}\"")
    print(f"Generating: \"{text[:60]}{'...' if len(text) > 60 else ''}\"")

    # Generate speech with explicit reference text (bypasses torchcodec transcription)
    # speed=0.85 gives TARS a more deliberate, measured delivery
    wav, sr, _ = model.infer(
        ref_file=reference_audio,
        ref_text=reference_text,
        gen_text=text,
        file_wave=output_path,
        speed=0.85  # Slow down for TARS's deliberate speech pattern
    )

    print(f"\nOutput saved to: {output_path}")
    print(f"Sample rate: {sr} Hz")
    return output_path

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Parse arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_samples(SAMPLES_DIR)
        return

    if len(sys.argv) > 1 and sys.argv[1] == "--transcribe":
        transcribe_samples(SAMPLES_DIR)
        return

    text = sys.argv[1] if len(sys.argv) > 1 else "Cooper, this is no time for caution."

    # Find best reference sample with known transcript
    reference, ref_text = get_best_sample_with_transcript(SAMPLES_DIR)
    print(f"Using reference: {os.path.basename(reference)}")

    if not ref_text:
        print("WARNING: No transcript found for this sample. Run with --transcribe first.")
        print("Attempting to transcribe with Faster Whisper...")
        from faster_whisper import WhisperModel
        model = WhisperModel('base', device='cuda', compute_type='float16')
        segments, _ = model.transcribe(reference, language='en')
        ref_text = ' '.join([s.text.strip() for s in segments])
        print(f"Transcript: {ref_text}")

    # Output file
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(OUTPUT_DIR, f"tars_cloned_{timestamp}.wav")

    # Clone voice
    clone_voice(text, reference, ref_text, output_path)

    # Play output using system default player
    print("\nPlaying generated audio...")
    try:
        if sys.platform == 'win32':
            os.startfile(output_path)
        elif sys.platform == 'darwin':
            os.system(f'open "{output_path}"')
        else:
            os.system(f'xdg-open "{output_path}"')
    except Exception as e:
        print(f"Could not play audio: {e}")
        print(f"Open the file manually: {output_path}")

if __name__ == "__main__":
    main()
