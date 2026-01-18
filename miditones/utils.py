"""Helper functions for MIDI note conversions and time calculations."""

import math
from typing import Tuple


def midi_to_frequency(midi_note: int) -> float:
    """
    Convert MIDI note number to frequency in Hz.
    
    Uses the formula: frequency = 440 × 2^((midi_note - 69) / 12)
    where MIDI note 69 corresponds to A4 (440 Hz).
    
    Args:
        midi_note: MIDI note number (0-127)
    
    Returns:
        Frequency in Hertz
    """
    return 440.0 * math.pow(2, (midi_note - 69) / 12.0)


def midi_to_note_name(midi_note: int) -> Tuple[str, str]:
    """
    Convert MIDI note number to note name.
    
    Args:
        midi_note: MIDI note number (0-127)
    
    Returns:
        Tuple of (note_name, note_full)
        - note_name: Note without octave (e.g., "A#", "C", "F#")
        - note_full: Note with octave (e.g., "A4", "C#5", "F3")
    """
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (midi_note // 12) - 1
    note_index = midi_note % 12
    note_name = note_names[note_index]
    note_full = f"{note_name}{octave}"
    return note_name, note_full


def midi_to_note_int(midi_note: int) -> int:
    """
    Convert MIDI note number to integer representation relative to A.
    
    The note_int property uses A as the reference (A=0):
    A=0, A#=1, B=2, C=3, C#=4, D=5, D#=6, E=7, F=8, F#=9, G=10, G#=11
    
    Calculation: note_int = (midi_note - 21) % 12 where MIDI note 21 is A0.
    
    Args:
        midi_note: MIDI note number (0-127)
    
    Returns:
        Integer representation (0-11)
    """
    return (midi_note - 21) % 12


def ticks_to_seconds(ticks: int, tempo_us: int, ticks_per_beat: int) -> float:
    """
    Convert MIDI ticks to seconds using tempo.
    
    Formula: duration_seconds = (ticks × tempo_microseconds) / (ticks_per_beat × 1,000,000)
    
    Args:
        ticks: Number of MIDI ticks
        tempo_us: Tempo in microseconds per beat
        ticks_per_beat: MIDI ticks per beat (resolution)
    
    Returns:
        Duration in seconds
    """
    return (ticks * tempo_us) / (ticks_per_beat * 1_000_000)
