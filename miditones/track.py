"""Track class representing a single MIDI track."""

from typing import Iterator, List
from .tone import Tone


class Track:
    """Represents a single MIDI track. Iterable - yields lists of Tone objects."""
    
    def __init__(self, name: str, channel: int, midi_track, tempo_map: List[tuple], 
                 ticks_per_beat: int):
        """
        Initialize a Track object.
        
        Args:
            name: Track name
            channel: Primary MIDI channel (0-15)
            midi_track: Raw MIDI track from mido
            tempo_map: List of (tick, tempo_us) tuples
            ticks_per_beat: MIDI ticks per beat
        """
        self._name = name
        self._channel = channel
        self._midi_track = midi_track
        self._tempo_map = tempo_map
        self._ticks_per_beat = ticks_per_beat
        self._duration = None
        self._note_count = None
    
    @property
    def name(self) -> str:
        """The track name (from MIDI metadata or auto-generated)."""
        return self._name
    
    @property
    def channel(self) -> int:
        """Primary MIDI channel used by this track (0-15)."""
        return self._channel
    
    @property
    def duration(self) -> float:
        """Total duration of the track in seconds."""
        if self._duration is None:
            self._calculate_track_info()
        return self._duration
    
    def __iter__(self) -> Iterator[List[Tone]]:
        """
        Iterate through all tone groups in the track sequentially.
        
        Yields lists of Tone objects. When multiple notes are played simultaneously,
        the list contains all those tones. Single notes are also yielded as a list
        with one item.
        """
        from .parser import process_track_events
        
        # Process track events and yield tone groups
        for tone_group in process_track_events(self._midi_track, self._tempo_map, 
                                                 self._ticks_per_beat):
            yield tone_group
    
    def __len__(self) -> int:
        """Returns the total number of tones in the track."""
        if self._note_count is None:
            self._calculate_track_info()
        return self._note_count
    
    def _calculate_track_info(self):
        """Calculate duration and note count by iterating through the track."""
        max_end_time = 0.0
        note_count = 0
        
        for tone_group in self:
            for tone in tone_group:
                note_count += 1
                end_time = tone.start_time + tone.duration
                if end_time > max_end_time:
                    max_end_time = end_time
        
        self._duration = max_end_time
        self._note_count = note_count
