"""MidiTones - A simple and intuitive Python library for parsing MIDI files."""

from .midi import Midi
from .track import Track
from .tone import Tone

__all__ = ['Midi', 'Track', 'Tone']
__version__ = '0.1.0'
