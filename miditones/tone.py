"""Tone class representing a single musical note."""

from .utils import midi_to_frequency, midi_to_note_name, midi_to_note_int


class Tone:
    """Represents a single musical note/tone."""
    
    def __init__(self, midi_note: int, duration: float, velocity: int, start_time: float):
        """
        Initialize a Tone object.
        
        Args:
            midi_note: MIDI note number (0-127)
            duration: Duration in seconds
            velocity: MIDI velocity (0-127)
            start_time: Absolute start time in seconds
        """
        self._midi_note = midi_note
        self._duration = duration
        self._velocity = velocity
        self._start_time = start_time
        
        # Pre-calculate derived properties
        self._frequency = midi_to_frequency(midi_note)
        self._note_name, self._note_full = midi_to_note_name(midi_note)
        self._note_int = midi_to_note_int(midi_note)
    
    @property
    def frequency(self) -> float:
        """Frequency in Hertz (Hz). Calculated using A4 = 440 Hz."""
        return self._frequency
    
    @property
    def midi_note(self) -> int:
        """MIDI note number (0-127). Middle C (C4) = 60."""
        return self._midi_note
    
    @property
    def note_int(self) -> int:
        """Integer representation of the semitone relative to A (A=0, A#=1, ..., G#=11)."""
        return self._note_int
    
    @property
    def note_name(self) -> str:
        """String representation of the note (e.g., "A#", "C", "F#")."""
        return self._note_name
    
    @property
    def note_full(self) -> str:
        """Full note name with octave (e.g., "A4", "C#5", "F3")."""
        return self._note_full
    
    @property
    def duration(self) -> float:
        """Duration of the note in seconds."""
        return self._duration
    
    @property
    def velocity(self) -> int:
        """MIDI velocity (0-127). Represents how hard the note was played."""
        return self._velocity
    
    @property
    def start_time(self) -> float:
        """Absolute start time of the note in seconds from the beginning of the track."""
        return self._start_time
    
    def __str__(self) -> str:
        """Returns human-readable representation: 'A4 (440.00 Hz) - 0.5s'"""
        return f"{self.note_full} ({self.frequency:.2f} Hz) - {self.duration:.1f}s"
    
    def __repr__(self) -> str:
        """Returns detailed representation: 'Tone(note='A4', frequency=440.0, duration=0.5)'"""
        return f"Tone(note='{self.note_full}', frequency={self.frequency}, duration={self.duration})"
