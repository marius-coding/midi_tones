"""Simulated stepper motor interface that can play a single frequency at a time.

This interface is deliberately simple and safe: it only logs actions with
timestamps. Hook it up to real motor driver code as needed.
"""

import time
from typing import Optional



class StepperInterface:
    """Simulate a stepper motor being driven at a given frequency."""

    def __init__(self) -> None:
        self._start = time.perf_counter()
        self._active_freq: Optional[float] = None

    def _ts(self) -> float:
        return time.perf_counter() - self._start

    def set_frequency(self, frequency_hz: Optional[float]) -> None:
        """Set the motor drive frequency. Pass None to stop."""
        if frequency_hz is None:
            if self._active_freq is not None:
                print(f"{self._ts():8.3f}s STOP (was {self._active_freq:7.2f} Hz)")
            else:
                print(f"{self._ts():8.3f}s STOP (idle)")
            self._active_freq = None
            return

        print(f"{self._ts():8.3f}s RUN  {frequency_hz:7.2f} Hz")
        self._active_freq = frequency_hz


    def stop(self) -> None:
        """Stop driving the motor."""
        self.set_frequency(None)

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass
