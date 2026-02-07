"""
LiveVoiceEngine - Real-time voice conversation pipeline.

Provides Gemini Live-style streaming voice interaction using ElevenLabs
WebSocket APIs for STT (Scribe v2 Realtime) and TTS (streaming input).

Architecture:
    Mic (sounddevice) -> PCM chunks -> STT WebSocket (Scribe v2)
                                            |
                                    Final transcript
                                            |
                                    LLM streaming (Ollama)
                                            |
                                    SentenceChunker
                                            |
                                    TTS WebSocket (ElevenLabs)
                                            |
                                    PCM audio -> Speaker (sounddevice)

All WebSocket and async operations run in a dedicated asyncio event loop
on a background daemon thread. GUI communication uses callbacks dispatched
via tkinter's .after() for thread safety.
"""

import asyncio
import base64
import concurrent.futures
import json
import logging
import math
import queue
import re
import struct
import threading
import time
from enum import Enum, auto
from typing import Callable, Optional

import numpy as np

logger = logging.getLogger("pentest-agent")  # Use same logger as GUI for consistent logging


class LiveVoiceState(Enum):
    """States for the live voice conversation pipeline."""
    INACTIVE = auto()     # Engine not running
    IDLE = auto()         # Active, waiting between turns
    LISTENING = auto()    # Mic open, streaming to STT
    THINKING = auto()     # LLM generating response
    SPEAKING = auto()     # TTS audio playing
    INTERRUPTED = auto()  # Barge-in detected, transitioning


class SentenceChunker:
    """Buffers LLM tokens and emits complete sentences for TTS.

    Strips markdown formatting and code blocks to produce clean text
    suitable for speech synthesis.
    """

    SENTENCE_ENDINGS = re.compile(r'[.!?]\s|[.!?]$|\n\n')
    ABBREVIATIONS = re.compile(
        r'\b(e\.g|i\.e|etc|vs|mr|mrs|dr|st|ft|vol|no)\.\s*$', re.I
    )

    def __init__(self, on_sentence: Callable[[str], None]):
        self._buffer = ""
        self._on_sentence = on_sentence

    def feed(self, token: str, is_done: bool):
        """Feed a token from the LLM stream."""
        self._buffer += token

        # Don't emit from inside code blocks
        if '```' in self._buffer:
            if self._buffer.count('```') % 2 == 1:
                if not is_done:
                    return  # Inside code block

        # Strip tool_call tags
        self._buffer = re.sub(
            r'<tool_call>.*?</tool_call>', '', self._buffer, flags=re.DOTALL
        )
        # Strip incomplete tool_call at end
        self._buffer = re.sub(r'<tool_call>.*$', '', self._buffer, flags=re.DOTALL)

        # Check for sentence boundary
        match = self.SENTENCE_ENDINGS.search(self._buffer)
        if match and not self.ABBREVIATIONS.search(self._buffer[:match.end()]):
            sentence = self._buffer[:match.end()].strip()
            self._buffer = self._buffer[match.end():]
            if sentence:
                clean = self._clean_for_speech(sentence)
                if clean:
                    self._on_sentence(clean)

        # Flush remaining on completion
        if is_done and self._buffer.strip():
            clean = self._clean_for_speech(self._buffer.strip())
            if clean:
                self._on_sentence(clean)
            self._buffer = ""

    def reset(self):
        """Clear the buffer (e.g., on barge-in)."""
        self._buffer = ""

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """Remove markdown formatting for cleaner TTS output."""
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text)
        # Remove inline code
        text = re.sub(r'`[^`]+`', '', text)
        # Remove markdown emphasis
        text = re.sub(r'[*_#]', '', text)
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        # Remove markdown links, keep text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text


class LiveVoiceEngine:
    """Manages the real-time voice conversation pipeline.

    Runs an asyncio event loop in a background thread. Communicates with
    the GUI via callbacks dispatched through gui_after_fn (tkinter .after()).

    Usage:
        engine = LiveVoiceEngine(api_key=..., voice_id=..., callbacks...)
        engine.start()          # Start background event loop
        engine.activate()       # Enter live conversation mode
        engine.deactivate()     # Exit live conversation mode
        engine.stop()           # Shut down completely
    """

    # Audio parameters (must match sounddevice and ElevenLabs)
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'
    BYTES_PER_SAMPLE = 2  # int16

    # Barge-in defaults
    DEFAULT_BARGEIN_THRESHOLD = 800
    DEFAULT_BARGEIN_FRAMES = 3  # ~60ms of consecutive speech to trigger
    HEADPHONE_BARGEIN_THRESHOLD = 500

    def __init__(
        self,
        api_key: str,
        voice_id: str,
        on_state_change: Callable[[LiveVoiceState], None],
        on_transcript: Callable[[str, bool], None],
        on_audio_level: Callable[[str, float], None],
        on_error: Callable[[str], None],
        gui_after_fn: Callable,
        process_message_fn: Callable,
        settings: Optional[dict] = None,
        on_log: Optional[Callable[[str], None]] = None,
    ):
        """
        Args:
            api_key: ElevenLabs API key
            voice_id: ElevenLabs voice ID for TTS
            on_state_change: Called with new LiveVoiceState on state transitions
            on_transcript: Called with (text, is_final) for STT results
            on_audio_level: Called with ("input"|"output", rms_level) for avatar
            on_error: Called with error message string
            gui_after_fn: tkinter's .after() for thread-safe GUI callbacks
            process_message_fn: Function to process a user message with LLM.
                Signature: process_message_fn(text, on_token_callback)
                where on_token_callback(chunk, full_text, is_done)
            settings: Optional settings dict for configuration
            on_log: Optional callback for GUI terminal logging
        """
        self._api_key = api_key
        # TARS voice ID - hardcoded for consistent personality
        self._voice_id = "NCKTc2m4SgOQ7jPgxf0Y"
        logger.info("[LIVE] TTS voice ID: TARS")
        self._on_state_change = on_state_change
        self._on_transcript = on_transcript
        self._on_audio_level = on_audio_level
        self._on_error = on_error
        self._gui_after = gui_after_fn
        self._process_message_fn = process_message_fn
        self._settings = settings or {}
        self._on_log = on_log

        self.state = LiveVoiceState.INACTIVE
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

        # WebSocket connections
        self._stt_ws = None
        self._tts_ws = None
        self._stt_connected = False  # Thread-safe flag for STT connection status

        # Audio streams
        self._mic_stream = None
        self._speaker_stream = None
        self._speaker_buffer = bytearray()
        self._speaker_buffer_lock = threading.Lock()
        self._speaker_started = False

        # Barge-in state
        # Mic isolated mode: barge-in works normally (no echo from speakers)
        # Non-isolated mode: disable barge-in during playback (echo causes false triggers)
        self._mic_isolated = self._settings.get("live_voice_mic_isolated", False)
        bargein_threshold = self._settings.get("live_voice_bargein_threshold", self.DEFAULT_BARGEIN_THRESHOLD)
        if self._mic_isolated:
            bargein_threshold = self.HEADPHONE_BARGEIN_THRESHOLD
        self._bargein_threshold = bargein_threshold
        self._bargein_frames = 0
        self._bargein_enabled = self._settings.get("live_voice_bargein_enabled", True)

        # Pipeline control
        self._sentence_chunker: Optional[SentenceChunker] = None
        self._tts_buffer_ms = self._settings.get("live_voice_buffer_ms", 250)
        self._stt_tasks: list = []
        self._active = False
        self._paused_from_state = None  # State before pause() was called
        self._speaking_done_event: Optional[asyncio.Event] = None

        # STT configuration
        self._stt_language = self._settings.get("live_voice_stt_language", "eng")
        self._stt_endpointing = self._settings.get("live_voice_stt_endpointing_ms", 300)

        # Dynamic speaker drain tracking
        self._last_tts_chunk_time = 0.0  # Timestamp of last received TTS audio chunk
        self._tts_stream_complete = False  # TTS finished sending audio
        self._last_buffer_size = 0  # For detecting buffer activity

        # Event loop synchronization
        self._loop_ready = None  # threading.Event to signal loop is running

        # Voice capture for cloning (saves TTS output to WAV files)
        self._voice_capture_enabled = self._settings.get("voice_capture_enabled", False)
        self._voice_capture_dir = self._settings.get("voice_capture_dir", "voice_samples")
        self._voice_capture_buffer = bytearray()  # Accumulate audio during TTS
        self._voice_capture_count = 0  # Counter for filenames

        # Local STT (Faster-Whisper) support
        self._stt_provider = self._settings.get("live_voice_stt_provider", "elevenlabs")
        self._local_audio_buffer = bytearray()  # Buffer for local transcription
        self._local_audio_lock = threading.Lock()
        self._whisper_model = None  # Lazy-loaded Faster-Whisper model
        self._whisper_model_size = self._settings.get("whisper_model_size", "base")

    def _save_voice_sample(self):
        """Save captured TTS audio to a WAV file for voice cloning."""
        import wave
        import os
        from datetime import datetime

        # Create output directory
        os.makedirs(self._voice_capture_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._voice_capture_count += 1
        filename = f"tars_voice_{timestamp}_{self._voice_capture_count:03d}.wav"
        filepath = os.path.join(self._voice_capture_dir, filename)

        # Write WAV file (16-bit PCM mono)
        with wave.open(filepath, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # 16-bit = 2 bytes
            wav.setframerate(self.SAMPLE_RATE)
            wav.writeframes(bytes(self._voice_capture_buffer))

        duration_sec = len(self._voice_capture_buffer) / (self.SAMPLE_RATE * 2)
        self._log_gui(f"[VOICE CAPTURE] Saved: {filename} ({duration_sec:.1f}s)")
        logger.info(f"[LIVE] Voice sample saved: {filepath} ({duration_sec:.1f}s, {len(self._voice_capture_buffer)} bytes)")

    def _log_gui(self, message: str):
        """Log to both logger and GUI terminal (thread-safe)."""
        logger.info(message)
        if self._on_log:
            self._gui_after(0, lambda m=message: self._on_log(m))

    # ─── Lifecycle ───────────────────────────────────────────────

    def start(self):
        """Start the asyncio event loop in a background thread."""
        if self._loop and self._loop.is_running():
            logger.debug("[LIVE] Event loop already running, skipping start")
            return

        logger.info("[LIVE] Starting async event loop...")
        self._loop = asyncio.new_event_loop()
        self._loop_ready = threading.Event()  # Synchronization event

        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="LiveVoiceLoop"
        )
        self._thread.start()

        # Wait for event loop to actually start (max 5 seconds)
        if not self._loop_ready.wait(timeout=5.0):
            logger.error("[LIVE] Event loop failed to start within 5 seconds!")
        else:
            logger.info("[LIVE] Event loop thread started and running")

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        # Signal that loop is about to run
        self._loop.call_soon(lambda: self._loop_ready.set())
        self._loop.run_forever()

    def stop(self):
        """Shut down everything."""
        self.deactivate()
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=3)
        self._loop = None
        self._thread = None
        logger.info("[LIVE] Engine stopped")

    def _submit(self, coro):
        """Submit a coroutine to the async event loop from any thread."""
        if self._loop and self._loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, self._loop)
        logger.warning(f"[LIVE] _submit failed: loop={self._loop}, running={self._loop.is_running() if self._loop else 'N/A'}")
        return None

    # ─── Activate / Deactivate ───────────────────────────────────

    def activate(self):
        """Enter live conversation mode."""
        logger.info("[LIVE] activate() called")
        if self.state != LiveVoiceState.INACTIVE:
            logger.debug(f"[LIVE] Already active (state={self.state}), skipping")
            return

        if not self._api_key:
            logger.error("[LIVE] No API key provided!")
            self._gui_after(0, lambda: self._on_error(
                "ElevenLabs API key required for live voice mode"
            ))
            return

        self._active = True
        self._set_state(LiveVoiceState.IDLE)

        # Start mic and connect STT
        logger.info("[LIVE] Submitting startup sequence...")
        future = self._submit(self._startup_sequence())
        if future:
            logger.info("[LIVE] Startup sequence submitted to event loop")
            # Add callback to catch any unhandled exceptions
            def _on_startup_done(f):
                try:
                    exc = f.exception()
                    if exc:
                        logger.error(f"[LIVE] Startup sequence exception: {exc}")
                        self._gui_after(0, lambda e=str(exc): self._on_error(f"STT connection failed: {e}"))
                except Exception as e:
                    logger.error(f"[LIVE] Error checking startup result: {e}")
            future.add_done_callback(_on_startup_done)
        else:
            logger.error("[LIVE] Failed to submit startup - event loop not running!")
            self._gui_after(0, lambda: self._on_error("Event loop not running - restart TARS"))

    def deactivate(self):
        """Exit live conversation mode."""
        self._active = False

        # Stop mic
        self._stop_mic()

        # Stop speaker
        self._stop_speaker()

        # Close WebSockets
        self._submit(self._close_connections())

        self._set_state(LiveVoiceState.INACTIVE)

    def pause(self):
        """Temporarily pause live voice (e.g., during tool execution).

        Stops the mic and speaker to prevent state changes during tool execution.
        Closes TTS WebSocket to prevent 20-second timeout during long tool runs.
        Call resume() to continue listening after the operation completes.
        """
        if self.state == LiveVoiceState.INACTIVE:
            return

        logger.info("[LIVE] Pausing live voice engine")
        self._stop_mic()
        self._stop_speaker()  # Stop any ongoing TTS playback
        # Clear speaker buffer to prevent timeout issues
        with self._speaker_buffer_lock:
            self._speaker_buffer = bytearray()

        # Close TTS WebSocket to prevent ElevenLabs 20-second timeout
        # A new connection will be created when speaking resumes
        if self._tts_ws:
            self._submit(self._close_tts_websocket())

        self._paused_from_state = self.state
        self._set_state(LiveVoiceState.IDLE)

    async def _close_tts_websocket(self):
        """Close the TTS WebSocket connection."""
        if self._tts_ws:
            try:
                await self._tts_ws.close()
            except Exception:
                pass
            self._tts_ws = None
            logger.debug("[LIVE] TTS WebSocket closed")

    def resume(self):
        """Resume live voice after pause().

        Respects PTT mode: goes to IDLE (not LISTENING) if PTT is enabled.
        """
        if self.state == LiveVoiceState.INACTIVE:
            return
        if not self._active:
            return

        logger.info("[LIVE] Resuming live voice engine")
        self._paused_from_state = None  # Clear paused flag

        ptt_mode = self._settings.get("live_voice_ptt_mode", True)
        if ptt_mode:
            # PTT mode: go to IDLE, user must press button to speak
            logger.debug("[LIVE] Resumed in PTT mode - waiting for button press")
            self._set_state(LiveVoiceState.IDLE)
        else:
            # Continuous mode: start mic and listen
            self._start_mic()
            self._set_state(LiveVoiceState.LISTENING)

    async def _startup_sequence(self):
        """Connect STT WebSocket and start microphone."""
        try:
            logger.info("[LIVE] Connecting to STT WebSocket...")
            await self._connect_stt()
            self._log_gui("[LIVE] STT WebSocket connected!")
            # Check PTT mode - don't auto-start mic if PTT enabled
            ptt_mode = self._settings.get("live_voice_ptt_mode", True)
            if ptt_mode:
                # In PTT mode, stay in IDLE until user presses mic button
                self._set_state(LiveVoiceState.IDLE)
                logger.debug("[LIVE] PTT mode enabled - waiting for button press")
            else:
                # Continuous listening mode
                self._start_mic()
                self._set_state(LiveVoiceState.LISTENING)
        except Exception as e:
            logger.error(f"[LIVE] Startup failed: {e}")
            self._gui_after(0, lambda msg=str(e): self._on_error(f"Live voice startup failed: {msg}"))
            self._active = False
            self._set_state(LiveVoiceState.INACTIVE)

    async def _close_connections(self):
        """Close all WebSocket connections."""
        # Cancel STT tasks
        for task in self._stt_tasks:
            task.cancel()
        self._stt_tasks.clear()

        self._stt_connected = False  # Mark as disconnected
        if self._stt_ws:
            try:
                await self._stt_ws.close()
            except Exception:
                pass
            self._stt_ws = None

        if self._tts_ws:
            try:
                await self._tts_ws.close()
            except Exception:
                pass
            self._tts_ws = None

    # ─── State Management ────────────────────────────────────────

    def _set_state(self, new_state: LiveVoiceState):
        """Transition to a new state and notify GUI."""
        old_state = self.state
        self.state = new_state
        logger.debug(f"[LIVE] State: {old_state.name} -> {new_state.name}")

        ptt_mode = self._settings.get("live_voice_ptt_mode", True)

        # Ensure mic and STT are running when entering LISTENING state
        # BUT skip mic auto-start in PTT mode (user controls mic with button)
        if new_state == LiveVoiceState.LISTENING and self._active:
            # Reconnect STT if disconnected (always needed)
            if not self._stt_ws or getattr(self._stt_ws, 'closed', True):
                logger.info("[LIVE] Reconnecting STT for LISTENING state")
                self._submit(self._connect_stt())

            # Only auto-start mic if NOT in PTT mode
            if not ptt_mode:
                if not self._mic_stream or not self._mic_stream.active:
                    logger.info("[LIVE] Restarting mic for LISTENING state")
                    self._start_mic()

        self._gui_after(0, lambda s=new_state: self._on_state_change(s))

    # ─── Microphone (sounddevice InputStream) ────────────────────

    def _start_mic(self):
        """Open the microphone input stream."""
        try:
            import sounddevice as sd
        except ImportError:
            self._gui_after(0, lambda: self._on_error("sounddevice not installed"))
            return

        if self._mic_stream and self._mic_stream.active:
            return

        self._mic_stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            callback=self._mic_callback,
            blocksize=1600,  # 100ms chunks
        )
        self._mic_stream.start()
        logger.debug("[LIVE] Microphone started")

    def _stop_mic(self):
        """Close the microphone input stream."""
        if self._mic_stream:
            try:
                self._mic_stream.stop()
                self._mic_stream.close()
            except Exception:
                pass
            self._mic_stream = None

    def _mic_callback(self, indata, frames, time_info, status):
        """Sounddevice input callback - runs in audio thread."""
        if not self._active:
            return

        rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))

        # Report audio level for avatar animation
        self._gui_after(0, lambda l=rms: self._on_audio_level("input", l))

        # ── Barge-in detection during SPEAKING ──
        # Only allow barge-in when mic is isolated (non-isolated setups have echo that causes false triggers)
        if self.state == LiveVoiceState.SPEAKING:
            if self._bargein_enabled and self._mic_isolated:
                if rms > self._bargein_threshold:
                    self._bargein_frames += 1
                    if self._bargein_frames >= self.DEFAULT_BARGEIN_FRAMES:
                        logger.info(f"[LIVE] Barge-in detected (RMS={rms:.0f})")
                        self._submit(self._handle_bargein())
                        self._bargein_frames = 0
                else:
                    self._bargein_frames = 0
            return  # Don't send to STT while speaking (avoid echo)

        # ── Send audio to STT ──
        if self.state in (LiveVoiceState.LISTENING, LiveVoiceState.IDLE):
            audio_bytes = indata.tobytes()

            if self._stt_provider == "faster-whisper":
                # Buffer audio locally for Faster-Whisper transcription on PTT release
                with self._local_audio_lock:
                    self._local_audio_buffer.extend(audio_bytes)
            else:
                # Send to ElevenLabs WebSocket
                audio_b64 = base64.b64encode(audio_bytes).decode('ascii')
                msg = json.dumps({
                    "message_type": "input_audio_chunk",
                    "audio_base_64": audio_b64,  # Correct field name per ElevenLabs API
                    "sample_rate": self.SAMPLE_RATE,
                    "commit": False,
                })
                self._submit(self._send_stt(msg))

    async def _send_stt(self, msg: str):
        """Send a message to the STT WebSocket."""
        if self._stt_ws:
            try:
                await self._stt_ws.send(msg)
            except Exception as e:
                logger.debug(f"[LIVE] STT send error: {e}")

    def _load_whisper_model(self):
        """Load Faster-Whisper model for local transcription."""
        try:
            from faster_whisper import WhisperModel
            logger.info(f"[LIVE] Loading Faster-Whisper model: {self._whisper_model_size}")
            self._log_gui(f"[LIVE] Loading Whisper model ({self._whisper_model_size})...")
            # Use CUDA if available, else CPU
            try:
                self._whisper_model = WhisperModel(
                    self._whisper_model_size, device="cuda", compute_type="float16"
                )
                logger.info("[LIVE] Faster-Whisper loaded on CUDA")
            except Exception:
                self._whisper_model = WhisperModel(
                    self._whisper_model_size, device="cpu", compute_type="int8"
                )
                logger.info("[LIVE] Faster-Whisper loaded on CPU")
            self._log_gui("[LIVE] Whisper model ready")
        except ImportError:
            logger.error("[LIVE] faster-whisper not installed")
            self._gui_after(0, lambda: self._on_error("faster-whisper not installed"))
            self._whisper_model = None

    def _transcribe_local(self) -> str:
        """Transcribe buffered audio using Faster-Whisper."""
        if not self._whisper_model:
            logger.error("[LIVE] Whisper model not loaded")
            return ""

        with self._local_audio_lock:
            if len(self._local_audio_buffer) < 3200:  # Less than 100ms of audio
                logger.debug("[LIVE] Audio buffer too short for transcription")
                return ""
            audio_bytes = bytes(self._local_audio_buffer)
            self._local_audio_buffer.clear()

        try:
            import numpy as np
            import tempfile
            import wave
            import os

            # Convert PCM bytes to numpy array
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            # Write to temp WAV file (Faster-Whisper needs a file)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
                with wave.open(tmp_path, 'wb') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(self.SAMPLE_RATE)
                    wav.writeframes(audio_bytes)

            # Transcribe
            segments, _ = self._whisper_model.transcribe(
                tmp_path, language="en", beam_size=5
            )
            transcript = " ".join([s.text.strip() for s in segments]).strip()

            # Cleanup temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

            logger.info(f"[LIVE] Local transcription: '{transcript[:80]}...' " if len(transcript) > 80 else f"[LIVE] Local transcription: '{transcript}'")
            return transcript

        except Exception as e:
            logger.error(f"[LIVE] Local transcription error: {e}")
            return ""

    def commit_local_audio(self):
        """Called on PTT release to transcribe buffered audio locally."""
        if self._stt_provider != "faster-whisper":
            return  # Not using local STT

        def _transcribe_worker():
            transcript = self._transcribe_local()
            if transcript:
                # Notify GUI of final transcript
                self._gui_after(0, lambda t=transcript: self._on_transcript(t, True))
                # Process with LLM
                self._set_state(LiveVoiceState.THINKING)
                self._process_utterance(transcript)
            else:
                # No transcript - go back to IDLE
                logger.debug("[LIVE] No transcript from local STT")
                ptt_mode = self._settings.get("live_voice_ptt_mode", True)
                if ptt_mode:
                    self._set_state(LiveVoiceState.IDLE)
                else:
                    self._set_state(LiveVoiceState.LISTENING)

        threading.Thread(target=_transcribe_worker, daemon=True, name="LocalSTT").start()

    # ─── STT (ElevenLabs WebSocket or Local Faster-Whisper) ───────

    async def _connect_stt(self):
        """Connect to STT service (ElevenLabs WebSocket or local Faster-Whisper)."""
        # Check if using local Faster-Whisper
        if self._stt_provider == "faster-whisper":
            logger.info("[LIVE] Using local Faster-Whisper for STT (no WebSocket needed)")
            self._stt_connected = True  # Mark as "connected" for PTT logic
            # Pre-load the Whisper model
            if not self._whisper_model:
                self._load_whisper_model()
            return

        # ElevenLabs WebSocket mode
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets not installed - run: pip install websockets")

        # Verify API key is present
        if not self._api_key:
            raise ValueError("No ElevenLabs API key provided")

        # Clean up old connection if exists
        self._stt_connected = False  # Mark as disconnected during reconnect
        if self._stt_ws:
            logger.debug("[LIVE] Closing old STT WebSocket before reconnecting")
            try:
                await self._stt_ws.close()
            except Exception as e:
                logger.debug(f"[LIVE] Old STT close error (expected): {e}")
            self._stt_ws = None

        # Cancel old receive tasks
        for task in self._stt_tasks:
            if not task.done():
                task.cancel()
        self._stt_tasks.clear()

        # Log key info (masked for security)
        key_preview = f"{self._api_key[:8]}...{self._api_key[-4:]}" if len(self._api_key) > 12 else "***"
        logger.info(f"[LIVE] Connecting STT with API key: {key_preview} ({len(self._api_key)} chars)")

        # Build URL with query parameters
        # Use manual commit for PTT mode (instant on release), VAD for continuous
        ptt_mode = self._settings.get("live_voice_ptt_mode", True)
        if ptt_mode:
            # Manual: only commits when we send commit:true (instant PTT release)
            params = (
                f"?audio_format=pcm_{self.SAMPLE_RATE}"
                f"&language_code={self._stt_language}"
                f"&commit_strategy=manual"
            )
        else:
            # VAD: commits on silence detection (continuous mode)
            params = (
                f"?audio_format=pcm_{self.SAMPLE_RATE}"
                f"&language_code={self._stt_language}"
                f"&commit_strategy=vad"
                f"&vad_silence_threshold_secs={self._stt_endpointing / 1000.0:.1f}"
            )
        uri = f"wss://api.elevenlabs.io/v1/speech-to-text/realtime{params}"
        logger.info(f"[LIVE] STT URI: {uri}")
        logger.debug(f"[LIVE] STT connect with {'manual' if ptt_mode else 'VAD'} commit strategy")

        headers = {"xi-api-key": self._api_key}
        logger.info("[LIVE] Attempting WebSocket connection...")
        self._stt_ws = await websockets.connect(
            uri, additional_headers=headers, ping_interval=20, ping_timeout=10
        )
        self._stt_connected = True  # Mark as connected
        logger.info("[LIVE] STT WebSocket connected successfully!")

        # Start receive loop as async task
        task = self._loop.create_task(self._stt_receive_loop())
        self._stt_tasks.append(task)

    async def _stt_receive_loop(self):
        """Receive and process messages from the STT WebSocket."""
        try:
            async for message in self._stt_ws:
                if not self._active:
                    break

                data = json.loads(message)
                msg_type = data.get("message_type", "")

                # Log ALL messages for debugging
                if msg_type != "partial_transcript":  # Don't spam partials
                    logger.info(f"[LIVE] STT message: {msg_type} -> {str(data)[:200]}")

                if msg_type == "session_started":
                    logger.info(f"[LIVE] STT session started: {data.get('session_id', '')}")

                elif msg_type == "partial_transcript":
                    text = data.get("text", "").strip()
                    if text:
                        self._gui_after(0, lambda t=text: self._on_transcript(t, False))
                        # Transition to LISTENING if we were IDLE (only in continuous mode)
                        # In PTT mode, stay in IDLE - user controls when to listen
                        ptt_mode = self._settings.get("live_voice_ptt_mode", True)
                        if self.state == LiveVoiceState.IDLE and not ptt_mode:
                            self._set_state(LiveVoiceState.LISTENING)

                elif msg_type in ("committed_transcript", "committed_transcript_with_timestamps"):
                    text = data.get("text", "").strip()
                    logger.info(f"[LIVE] Received {msg_type}: '{text[:80] if text else '(empty)'}'")
                    if text:
                        logger.info(f"[LIVE] Final transcript: {text[:80]}")
                        self._gui_after(0, lambda t=text: self._on_transcript(t, True))
                        # Process with LLM
                        self._set_state(LiveVoiceState.THINKING)
                        self._process_utterance(text)
                    else:
                        logger.warning("[LIVE] Committed transcript was empty - nothing to process")

                elif msg_type in ("error", "auth_error", "quota_exceeded", "rate_limited"):
                    error = data.get("error", msg_type)
                    logger.error(f"[LIVE] STT error: {error}")
                    self._gui_after(0, lambda e=error: self._on_error(f"STT: {e}"))

                else:
                    # Log any unhandled message types
                    logger.warning(f"[LIVE] Unhandled STT message type: {msg_type}")

        except Exception as e:
            if self._active:
                logger.error(f"[LIVE] STT receive loop error: {e}")
        finally:
            # WebSocket closed (normally or via exception) - reconnect if still active
            self._stt_connected = False
            if self._active:
                self._log_gui("[LIVE] STT reconnecting...")
                await asyncio.sleep(0.5)
                if self._active:
                    try:
                        await self._connect_stt()
                        self._log_gui("[LIVE] STT reconnected!")
                    except Exception as re_e:
                        logger.error(f"[LIVE] STT reconnect failed: {re_e}")
                        self._gui_after(0, lambda msg=str(re_e): self._on_error(f"STT reconnect failed: {msg}"))

    # ─── TTS WebSocket (ElevenLabs Streaming Input) ──────────────

    async def _connect_tts(self):
        """Connect to ElevenLabs streaming TTS WebSocket."""
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets not installed - run: pip install websockets")

        params = (
            f"?model_id=eleven_turbo_v2_5"
            f"&output_format=pcm_{self.SAMPLE_RATE}"
        )
        uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}/stream-input{params}"
        logger.info(f"[LIVE] Connecting TTS with voice: {self._voice_id}")

        headers = {"xi-api-key": self._api_key}
        self._tts_ws = await websockets.connect(
            uri, additional_headers=headers, ping_interval=20, ping_timeout=10
        )

        # Send BOS (Beginning of Stream) message with TARS voice settings
        try:
            from tars_voice import TARS_VOICE_SETTINGS
            voice_settings = dict(TARS_VOICE_SETTINGS)
        except ImportError:
            voice_settings = {
                "stability": 0.85, "similarity_boost": 0.60,
                "style": 0.05, "use_speaker_boost": True,
            }
        bos = {
            "text": " ",
            "voice_settings": voice_settings,
            "generation_config": {
                "chunk_length_schedule": [50, 120, 200, 260],
            },
        }
        await self._tts_ws.send(json.dumps(bos))
        logger.info("[LIVE] TTS WebSocket connected")

        # Start receive loop
        self._speaking_done_event = asyncio.Event()
        task = self._loop.create_task(self._tts_receive_loop())
        self._stt_tasks.append(task)

    async def _tts_receive_loop(self):
        """Receive audio chunks from TTS WebSocket and buffer for playback."""
        buffer_bytes = 0
        started_playback = False
        self._tts_stream_complete = False  # Reset at start

        try:
            async for message in self._tts_ws:
                if not self._active:
                    break

                data = json.loads(message)

                # Check for final marker
                if data.get("isFinal", False):
                    logger.debug("[LIVE] TTS stream complete")
                    break

                # Extract audio
                audio_b64 = data.get("audio")
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    if len(audio_bytes) > 0:
                        # Track when we received audio for dynamic drain detection
                        self._last_tts_chunk_time = time.time()

                        with self._speaker_buffer_lock:
                            self._speaker_buffer.extend(audio_bytes)
                            buffer_bytes += len(audio_bytes)

                        # Capture audio for voice cloning if enabled
                        if self._voice_capture_enabled:
                            self._voice_capture_buffer.extend(audio_bytes)

                        # Start playback after buffer threshold
                        buffer_ms = (buffer_bytes / (self.SAMPLE_RATE * self.BYTES_PER_SAMPLE)) * 1000
                        if not started_playback and buffer_ms >= self._tts_buffer_ms:
                            self._start_speaker()
                            started_playback = True
                            self._set_state(LiveVoiceState.SPEAKING)

        except Exception as e:
            if self._active:
                logger.error(f"[LIVE] TTS receive error: {e}")

        # Mark TTS stream as complete for dynamic drain detection
        self._tts_stream_complete = True

        # Save captured audio for voice cloning
        if self._voice_capture_enabled and len(self._voice_capture_buffer) > 0:
            self._save_voice_sample()
            self._voice_capture_buffer.clear()

        # Wait for speaker to drain buffer using dynamic activity detection
        # The drain method uses intelligent activity tracking with its own safety timeout
        if started_playback:
            await self._wait_speaker_drain()

        # Done speaking - transition back
        self._stop_speaker()
        # Transition back if we're in any "busy" state (SPEAKING or THINKING)
        # THINKING can happen if TTS produced no audio (empty/short response)
        if self._active and self.state in (LiveVoiceState.SPEAKING, LiveVoiceState.THINKING):
            ptt_mode = self._settings.get("live_voice_ptt_mode", True)
            if ptt_mode:
                # PTT mode: go to IDLE, user must press button to speak again
                logger.debug(f"[LIVE] TTS complete (PTT mode), transitioning to IDLE")
                self._set_state(LiveVoiceState.IDLE)
            else:
                # Continuous mode: resume listening automatically
                logger.debug(f"[LIVE] TTS complete, transitioning to LISTENING")
                self._set_state(LiveVoiceState.LISTENING)

        # Close TTS WebSocket (important: prevents "no close frame" error on next connect)
        if self._tts_ws:
            try:
                await self._tts_ws.close()
            except Exception:
                pass
            self._tts_ws = None

        # Ensure STT is still connected after TTS completes (reconnect if needed)
        # Use _stt_connected flag (websockets lib doesn't have .closed attribute)
        if self._active and not self._stt_connected:
            logger.info("[LIVE] STT WebSocket disconnected - reconnecting")
            try:
                await self._connect_stt()
            except Exception as e:
                logger.error(f"[LIVE] STT reconnect failed: {e}")

        # Always set the event to unblock any waiting threads
        if self._speaking_done_event:
            self._speaking_done_event.set()

    async def _wait_speaker_drain(self):
        """Wait until the speaker buffer is drained, using dynamic activity detection.

        This method uses activity-based detection rather than fixed timeouts:
        - While TTS is streaming: wait indefinitely (audio keeps arriving)
        - Once TTS is done: detect when buffer empties OR audio stops playing
        - Absolute safety timeout of 5 minutes as failsafe

        Returns when:
        - Buffer is empty, OR
        - Buffer hasn't changed for 500ms (audio stopped/underrun), OR
        - Safety timeout exceeded
        """
        SILENCE_THRESHOLD_MS = 500  # Time with no buffer change to consider "done"
        SAFETY_TIMEOUT_S = 300  # 5 minute absolute failsafe
        CHECK_INTERVAL_MS = 50

        start_time = time.time()
        last_change_time = time.time()
        last_size = 0

        while self._active and self.state == LiveVoiceState.SPEAKING:
            # Safety timeout check
            elapsed = time.time() - start_time
            if elapsed > SAFETY_TIMEOUT_S:
                logger.warning(f"[LIVE] Speaker drain safety timeout after {SAFETY_TIMEOUT_S}s")
                with self._speaker_buffer_lock:
                    self._speaker_buffer = bytearray()
                break

            # Check current buffer state
            with self._speaker_buffer_lock:
                current_size = len(self._speaker_buffer)

            # Buffer empty check - only exit if TTS is also done streaming
            if current_size == 0:
                if self._tts_stream_complete:
                    # TTS done and buffer empty - we're truly finished
                    await asyncio.sleep(0.15)
                    break
                else:
                    # Buffer underrun while TTS still streaming - wait for more audio
                    await asyncio.sleep(CHECK_INTERVAL_MS / 1000)
                    continue

            # Track buffer activity
            if current_size != last_size:
                last_change_time = time.time()
                last_size = current_size

            # Check for silence (no buffer activity)
            silence_duration = (time.time() - last_change_time) * 1000  # ms

            # Only use silence detection after TTS stream is complete
            # This prevents premature exit while TTS is still streaming
            if self._tts_stream_complete and silence_duration > SILENCE_THRESHOLD_MS:
                logger.debug(f"[LIVE] Speaker drain: no activity for {silence_duration:.0f}ms, completing")
                # Don't force-clear the buffer - let remaining audio play
                # Just exit the wait loop
                break

            await asyncio.sleep(CHECK_INTERVAL_MS / 1000)

    async def _send_tts_text(self, text: str):
        """Send a text chunk to the TTS WebSocket."""
        if self._tts_ws:
            try:
                msg = json.dumps({
                    "text": text + " ",
                    "try_trigger_generation": True,
                })
                await self._tts_ws.send(msg)
            except Exception as e:
                logger.debug(f"[LIVE] TTS send error: {e}")

    async def _flush_tts(self):
        """Signal end of text to TTS WebSocket."""
        if self._tts_ws:
            try:
                await self._tts_ws.send(json.dumps({"text": ""}))
            except Exception as e:
                logger.debug(f"[LIVE] TTS flush error: {e}")

    # ─── Speaker (sounddevice OutputStream) ──────────────────────

    def _start_speaker(self):
        """Open the speaker output stream for streaming TTS playback."""
        try:
            import sounddevice as sd
        except ImportError:
            return

        if self._speaker_stream and self._speaker_stream.active:
            return

        self._speaker_started = True
        self._speaker_stream = sd.OutputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            callback=self._speaker_callback,
            blocksize=1600,  # 100ms blocks
        )
        self._speaker_stream.start()
        logger.debug("[LIVE] Speaker started")

    def _stop_speaker(self):
        """Close the speaker output stream."""
        if self._speaker_stream:
            try:
                self._speaker_stream.stop()
                self._speaker_stream.close()
            except Exception:
                pass
            self._speaker_stream = None
        self._speaker_started = False
        with self._speaker_buffer_lock:
            self._speaker_buffer.clear()

    def _speaker_callback(self, outdata, frames, time_info, status):
        """Sounddevice output callback - feeds buffered TTS audio."""
        bytes_needed = frames * self.BYTES_PER_SAMPLE * self.CHANNELS

        with self._speaker_buffer_lock:
            available = len(self._speaker_buffer)
            if available >= bytes_needed:
                chunk = bytes(self._speaker_buffer[:bytes_needed])
                del self._speaker_buffer[:bytes_needed]
                outdata[:] = np.frombuffer(chunk, dtype=np.int16).reshape(-1, 1)

                # Report output audio level for avatar
                rms = float(np.sqrt(np.mean(outdata.astype(np.float32) ** 2)))
                self._gui_after(0, lambda l=rms: self._on_audio_level("output", l))
            else:
                # Underrun - fill with silence
                outdata.fill(0)

    # ─── Barge-in Handling ───────────────────────────────────────

    async def _handle_bargein(self):
        """User interrupted AI speech. Stop TTS, switch to listening."""
        if self.state != LiveVoiceState.SPEAKING:
            return

        logger.info("[LIVE] Handling barge-in")

        # Stop speaker immediately
        self._stop_speaker()

        # Reset sentence chunker
        if self._sentence_chunker:
            self._sentence_chunker.reset()

        # Close TTS WebSocket
        if self._tts_ws:
            try:
                await self._tts_ws.close()
            except Exception:
                pass
            self._tts_ws = None

        # Signal speaking done
        if self._speaking_done_event:
            self._speaking_done_event.set()

        # Transition based on mode
        ptt_mode = self._settings.get("live_voice_ptt_mode", True)
        if ptt_mode:
            # PTT mode: go to IDLE, user must press button to continue
            self._set_state(LiveVoiceState.IDLE)
        else:
            # Continuous mode: resume listening
            self._set_state(LiveVoiceState.LISTENING)

    # ─── LLM Processing Pipeline ────────────────────────────────

    def _process_utterance(self, text: str):
        """Process a committed transcript through the LLM and TTS pipeline.

        Called from STT receive loop when a final transcript arrives.
        Runs LLM processing in a separate thread (via process_message_fn).
        """
        # Skip processing if engine is paused (e.g., during tool execution)
        if self._paused_from_state is not None:
            logger.info(f"[LIVE] Skipping utterance processing - engine paused: {text[:50]}")
            return

        def _worker():
            try:
                # Reset speaking done event BEFORE connecting TTS
                self._speaking_done_event = None

                # Connect TTS WebSocket for this response
                future = self._submit(self._connect_tts())
                if future:
                    future.result(timeout=10)

                # Verify TTS connected and event was created
                if not self._speaking_done_event:
                    raise RuntimeError("TTS connection failed to initialize")

                # Set up sentence chunker to feed TTS
                self._sentence_chunker = SentenceChunker(
                    on_sentence=lambda s: self._submit(self._send_tts_text(s))
                )

                # Process message through LLM with token callback
                def on_token(chunk: str, full_text: str, is_done: bool):
                    if self.state == LiveVoiceState.INTERRUPTED:
                        return  # Barge-in happened, stop feeding TTS
                    self._sentence_chunker.feed(chunk, is_done)
                    if is_done:
                        # Flush TTS
                        self._submit(self._flush_tts())

                self._process_message_fn(text, on_token)

                # Wait for speaking to complete
                if self._speaking_done_event:
                    # Block this thread until TTS playback finishes
                    future = self._submit(self._speaking_done_event.wait())
                    if future:
                        future.result(timeout=120)

            except concurrent.futures.TimeoutError:
                # Timeout waiting for TTS - likely paused for tool execution
                logger.debug("[LIVE] TTS wait timeout - likely paused for action request")
            except Exception as e:
                error_msg = str(e) if str(e) else type(e).__name__
                logger.error(f"[LIVE] Process utterance error: {error_msg}")
                self._gui_after(0, lambda msg=error_msg: self._on_error(f"Processing error: {msg}"))

                # Cleanup TTS WebSocket on error
                if self._tts_ws:
                    try:
                        future = self._submit(self._tts_ws.close())
                        if future:
                            future.result(timeout=2)
                    except Exception:
                        pass
                    self._tts_ws = None

                # Ensure speaking_done_event is set (in case anything is waiting)
                if self._speaking_done_event:
                    self._speaking_done_event.set()

                # Stop speaker if it was started
                self._stop_speaker()

            finally:
                # Always ensure we return to ready state after processing completes
                # (unless engine was paused during tool execution or deactivated)
                if self._active and self._paused_from_state is None:
                    if self.state in (LiveVoiceState.THINKING, LiveVoiceState.SPEAKING):
                        ptt_mode = self._settings.get("live_voice_ptt_mode", True)
                        if ptt_mode:
                            logger.debug(f"[LIVE] Worker complete (PTT), transitioning to IDLE")
                            self._set_state(LiveVoiceState.IDLE)
                        else:
                            logger.debug(f"[LIVE] Worker complete, transitioning to LISTENING")
                            self._set_state(LiveVoiceState.LISTENING)

        threading.Thread(target=_worker, daemon=True, name="LiveVoiceProcess").start()
