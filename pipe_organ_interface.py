import math
import threading
import time
from typing import Dict

try:
    import numpy as np  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

try:
    import sounddevice as sd  # type: ignore
    _SD_OK = True
except Exception:  # pragma: no cover - optional dependency
    sd = None  # type: ignore
    _SD_OK = False

from miditones.utils import midi_to_frequency

# Valve 0 is C3 (MIDI note 48). Negative valves are allowed.
BASE_MIDI_FOR_VALVE_ZERO = 48


class PipeOrgan:
    """Simulated pipe organ with optional audio via sounddevice.

    If sounddevice/numpy are unavailable or disabled, it falls back to
    timestamped prints only (stable, no native crashes).
    """

    def __init__(
        self,
        sample_rate: int = 44_100,
        volume: float = 0.2,
        use_audio: bool = False,
        ramp_duration: float = 0.05,
    ) -> None:
        self._start = time.perf_counter()
        self._sample_rate = sample_rate
        self._volume = max(0.0, min(volume, 1.0))
        self._use_audio = bool(use_audio and _SD_OK and np is not None)
        self._ramp_samples = max(1, int(max(0.0, ramp_duration) * self._sample_rate))

        self._voices: Dict[int, Dict[str, float]] = {}
        self._lock = threading.Lock()
        self._phase = 0
        self._stream = None

        if self._use_audio:
            try:
                self._stream = sd.OutputStream(
                    samplerate=self._sample_rate,
                    channels=1,
                    callback=self._sd_callback,
                    blocksize=0,
                )
                self._stream.start()
            except Exception as exc:
                print(f"Audio disabled (sounddevice stream init failed): {exc}")
                self._use_audio = False
        else:
            if use_audio and not _SD_OK:
                print("Audio disabled: sounddevice not available")
            if use_audio and np is None:
                print("Audio disabled: numpy not available")



    def _sd_callback(self, outdata, frames, time_info, status):  # type: ignore[override]
        if not self._voices or np is None:
            outdata.fill(0)
            return

        t = (np.arange(frames, dtype=np.float32) + self._phase) / float(self._sample_rate)
        signal = np.zeros(frames, dtype=np.float32)
        ramp_step = 1.0 / float(self._ramp_samples)

        with self._lock:
            voice_count = max(1, len(self._voices))
            to_remove = []

            for valve, voice in self._voices.items():
                freq = voice["freq"]
                gain = voice["gain"]
                target = voice["target"]

                max_delta = ramp_step * frames
                delta = max(-max_delta, min(max_delta, target - gain))
                end_gain = gain + delta
                gain_ramp = np.linspace(gain, end_gain, frames, endpoint=False, dtype=np.float32)

                signal += np.sin(2 * math.pi * freq * t).astype(np.float32) * gain_ramp
                voice["gain"] = end_gain
                if target == 0.0 and end_gain <= 1e-4:
                    to_remove.append(valve)

            for valve in to_remove:
                self._voices.pop(valve, None)

        signal *= (self._volume / voice_count)
        outdata[:, 0] = signal
        self._phase = (self._phase + frames) % self._sample_rate

    def valve_open(self, valve_index: int):
        midi_note = BASE_MIDI_FOR_VALVE_ZERO + valve_index
        freq = midi_to_frequency(midi_note)

        if self._use_audio:
            with self._lock:
                voice = self._voices.get(valve_index)
                if voice:
                    voice["target"] = 1.0
                else:
                    self._voices[valve_index] = {"freq": freq, "gain": 0.0, "target": 1.0}

    def valve_close(self, valve_index: int):
        if self._use_audio:
            with self._lock:
                voice = self._voices.get(valve_index)
                if voice:
                    voice["target"] = 0.0

    def close_all(self):
        if self._use_audio:
            with self._lock:
                for voice in self._voices.values():
                    voice["target"] = 0.0
            time.sleep(self._ramp_samples / float(self._sample_rate))
            with self._lock:
                self._voices.clear()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def __del__(self):
        try:
            self.close_all()
        except Exception:
            pass