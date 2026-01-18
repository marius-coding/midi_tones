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
    ) -> None:
        self._start = time.perf_counter()
        self._sample_rate = sample_rate
        self._volume = max(0.0, min(volume, 1.0))
        self._use_audio = bool(use_audio and _SD_OK and np is not None)

        self._active_freqs: Dict[int, float] = {}
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
        if not self._active_freqs or np is None:
            outdata.fill(0)
            return

        with self._lock:
            freqs = list(self._active_freqs.values())

        t = (np.arange(frames, dtype=np.float32) + self._phase) / float(self._sample_rate)
        # Mix all active sines; normalize by count to prevent clipping.
        signal = np.zeros(frames, dtype=np.float32)
        for f in freqs:
            signal += np.sin(2 * math.pi * f * t).astype(np.float32)
        if freqs:
            signal *= (self._volume / max(1, len(freqs)))

        outdata[:, 0] = signal
        self._phase = (self._phase + frames) % self._sample_rate

    def valve_open(self, valve_index: int):
        if valve_index in self._active_freqs:
            return

        midi_note = BASE_MIDI_FOR_VALVE_ZERO + valve_index
        freq = midi_to_frequency(midi_note)

        if self._use_audio:
            with self._lock:
                self._active_freqs[valve_index] = freq

    def valve_close(self, valve_index: int):

        if self._use_audio:
            with self._lock:
                self._active_freqs.pop(valve_index, None)

    def close_all(self):
        for valve in list(self._active_freqs.keys()):
            self.valve_close(valve)
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