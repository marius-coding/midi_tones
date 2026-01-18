"""Midi class for loading and accessing MIDI file content."""

from typing import Dict, List
from .parser import parse_midi_file, build_tempo_map, extract_track_names
from .track import Track


class Midi:
    """Main class for loading and accessing MIDI file content."""
    
    def __init__(self, filename: str):
        """
        Load a MIDI file.
        
        Args:
            filename: Path to the MIDI file
        
        Raises:
            FileNotFoundError: If the MIDI file doesn't exist
            ValueError: If the file is not a valid MIDI file
        """
        self._filename = filename
        self._midi_file = parse_midi_file(filename)
        self._tempo_map = build_tempo_map(self._midi_file)
        self._track_names = extract_track_names(self._midi_file)
        
        # Create Track objects
        self._tracks = {}
        for idx, (track_name, midi_track) in enumerate(zip(self._track_names, 
                                                            self._midi_file.tracks)):
            # Determine primary channel for this track
            channel = self._get_primary_channel(midi_track)
            
            track_obj = Track(
                name=track_name,
                channel=channel,
                midi_track=midi_track,
                tempo_map=self._tempo_map,
                ticks_per_beat=self._midi_file.ticks_per_beat
            )
            self._tracks[track_name] = track_obj
    
    def _get_primary_channel(self, midi_track) -> int:
        """
        Get the primary MIDI channel used by a track.
        
        Args:
            midi_track: Raw MIDI track
        
        Returns:
            Primary channel (0-15), defaults to 0
        """
        channel_counts = {}
        
        for msg in midi_track:
            if hasattr(msg, 'channel'):
                channel = msg.channel
                channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        if channel_counts:
            # Return the most frequently used channel
            return max(channel_counts.items(), key=lambda x: x[1])[0]
        else:
            return 0
    
    def __getitem__(self, track_name: str) -> Track:
        """
        Access a track by its name.
        
        Args:
            track_name: Name of the track (case-sensitive)
        
        Returns:
            Track object
        
        Raises:
            KeyError: If the track name doesn't exist
        """
        if track_name not in self._tracks:
            available = ', '.join(self._tracks.keys())
            raise KeyError(f"Track '{track_name}' not found. Available tracks: {available}")
        return self._tracks[track_name]
    
    def list_tracks(self) -> List[str]:
        """
        Returns a list of all available track names.
        
        Returns:
            List of track names
        """
        return list(self._tracks.keys())
    
    def get_track_by_index(self, index: int) -> Track:
        """
        Access a track by its zero-based index.
        
        Useful for MIDI files without track names.
        
        Args:
            index: Zero-based track index
        
        Returns:
            Track object
        
        Raises:
            IndexError: If index is out of range
        """
        track_names = self.list_tracks()
        if index < 0 or index >= len(track_names):
            raise IndexError(f"Track index {index} out of range (0-{len(track_names)-1})")
        return self._tracks[track_names[index]]
    
    @property
    def tracks(self) -> Dict[str, Track]:
        """Dictionary mapping track names to Track objects."""
        return self._tracks.copy()
    
    @property
    def tempo(self) -> float:
        """
        Initial tempo in BPM (beats per minute).
        
        Returns:
            Tempo in BPM
        """
        # First tempo in tempo_map is in microseconds per beat
        initial_tempo_us = self._tempo_map[0][1]
        # Convert to BPM: BPM = 60,000,000 / tempo_us
        return 60_000_000 / initial_tempo_us
    
    @property
    def ticks_per_beat(self) -> int:
        """MIDI ticks per beat (resolution)."""
        return self._midi_file.ticks_per_beat
    
    @property
    def filename(self) -> str:
        """Path to the MIDI file."""
        return self._filename
