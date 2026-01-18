"""MIDI parsing logic for tempo maps, track names, and event processing."""

import os
from typing import List, Dict, Iterator, Tuple
import mido
from .tone import Tone
from .utils import ticks_to_seconds


def parse_midi_file(filename: str) -> mido.MidiFile:
    """
    Load and validate a MIDI file.
    
    Args:
        filename: Path to the MIDI file
    
    Returns:
        mido.MidiFile object
    
    Raises:
        FileNotFoundError: If the MIDI file doesn't exist
        ValueError: If the file is not a valid MIDI file
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"MIDI file not found: {filename}")
    
    try:
        midi_file = mido.MidiFile(filename)
        return midi_file
    except Exception as e:
        raise ValueError(f"Not a valid MIDI file: {e}")


def build_tempo_map(midi_file: mido.MidiFile) -> List[Tuple[int, int]]:
    """
    Extract tempo changes with absolute timing.
    
    Args:
        midi_file: mido.MidiFile object
    
    Returns:
        List of (absolute_tick, tempo_us) tuples sorted by tick
    """
    tempo_map = []
    current_tick = 0
    
    # Default tempo is 120 BPM = 500000 microseconds per beat
    default_tempo = 500000
    tempo_map.append((0, default_tempo))
    
    # Scan all tracks for tempo changes
    for track in midi_file.tracks:
        current_tick = 0
        for msg in track:
            current_tick += msg.time
            if msg.type == 'set_tempo':
                # Add tempo change with absolute tick position
                tempo_map.append((current_tick, msg.tempo))
    
    # Sort by tick and remove duplicates (keep last tempo at same tick)
    tempo_map.sort(key=lambda x: x[0])
    
    # Remove duplicate ticks, keeping the last tempo value
    unique_tempo_map = []
    last_tick = -1
    for tick, tempo in tempo_map:
        if tick != last_tick:
            unique_tempo_map.append((tick, tempo))
            last_tick = tick
        else:
            # Replace previous entry with same tick
            unique_tempo_map[-1] = (tick, tempo)
    
    return unique_tempo_map


def extract_track_names(midi_file: mido.MidiFile) -> List[str]:
    """
    Get track names with conflict resolution.
    
    Strategy:
    1. Use track_name from MIDI meta messages
    2. Fallback to "Track {index}" if no track name
    3. For tracks with program changes, use instrument name
    4. Append " (2)", " (3)", etc. for duplicate names
    
    Args:
        midi_file: mido.MidiFile object
    
    Returns:
        List of track names (one per track)
    """
    track_names = []
    name_counts = {}
    
    instrument_names = {
        0: "Acoustic Grand Piano", 1: "Bright Acoustic Piano", 
        2: "Electric Grand Piano", 3: "Honky-tonk Piano",
        4: "Electric Piano 1", 5: "Electric Piano 2",
        # Add more as needed - truncated for brevity
    }
    
    for idx, track in enumerate(midi_file.tracks):
        name = None
        program = None
        
        # Look for track name meta message
        for msg in track:
            if msg.type == 'track_name' and msg.name.strip():
                name = msg.name.strip()
                break
            elif msg.type == 'program_change':
                program = msg.program
        
        # Apply naming strategy
        if not name:
            if program is not None and program in instrument_names:
                name = instrument_names[program]
            else:
                name = f"Track {idx}"
        
        # Handle duplicates
        if name in name_counts:
            name_counts[name] += 1
            name = f"{name} ({name_counts[name]})"
        else:
            name_counts[name] = 1
        
        track_names.append(name)
    
    return track_names


def get_tempo_at_tick(tick: int, tempo_map: List[Tuple[int, int]]) -> int:
    """
    Get the tempo (in microseconds per beat) at a specific tick.
    
    Args:
        tick: Absolute tick position
        tempo_map: List of (tick, tempo_us) tuples
    
    Returns:
        Tempo in microseconds per beat
    """
    current_tempo = tempo_map[0][1]  # Default tempo
    
    for map_tick, tempo in tempo_map:
        if map_tick <= tick:
            current_tempo = tempo
        else:
            break
    
    return current_tempo


def calculate_absolute_time(tick: int, tempo_map: List[Tuple[int, int]], 
                           ticks_per_beat: int) -> float:
    """
    Calculate absolute time in seconds for a given tick, considering tempo changes.
    
    Args:
        tick: Absolute tick position
        tempo_map: List of (tick, tempo_us) tuples
        ticks_per_beat: MIDI ticks per beat
    
    Returns:
        Absolute time in seconds
    """
    time_seconds = 0.0
    last_tempo_tick = 0
    current_tempo = tempo_map[0][1]
    
    for tempo_tick, tempo in tempo_map:
        if tempo_tick > tick:
            break
        
        # Add time from last tempo change to this one
        if tempo_tick > last_tempo_tick:
            elapsed_ticks = tempo_tick - last_tempo_tick
            time_seconds += ticks_to_seconds(elapsed_ticks, current_tempo, ticks_per_beat)
        
        last_tempo_tick = tempo_tick
        current_tempo = tempo
    
    # Add remaining time from last tempo change to target tick
    if tick > last_tempo_tick:
        elapsed_ticks = tick - last_tempo_tick
        time_seconds += ticks_to_seconds(elapsed_ticks, current_tempo, ticks_per_beat)
    
    return time_seconds


def process_track_events(midi_track, tempo_map: List[Tuple[int, int]], 
                        ticks_per_beat: int) -> Iterator[List[Tone]]:
    """
    Convert MIDI track events to Tone objects, yielding groups of simultaneous notes.
    
    Args:
        midi_track: Raw MIDI track from mido
        tempo_map: List of (tick, tempo_us) tuples
        ticks_per_beat: MIDI ticks per beat
    
    Yields:
        Lists of Tone objects (grouped by start time)
    """
    # Track active notes: {(note, channel): (start_tick, velocity)}
    active_notes = {}
    
    # Collect all note events with absolute timing
    note_events = []
    current_tick = 0
    
    for msg in midi_track:
        current_tick += msg.time
        
        if msg.type == 'note_on' and msg.velocity > 0:
            # Note starts
            key = (msg.note, msg.channel)
            active_notes[key] = (current_tick, msg.velocity)
        
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            # Note ends
            key = (msg.note, msg.channel)
            if key in active_notes:
                start_tick, velocity = active_notes[key]
                duration_ticks = current_tick - start_tick
                
                # Calculate times
                start_time = calculate_absolute_time(start_tick, tempo_map, ticks_per_beat)
                end_time = calculate_absolute_time(current_tick, tempo_map, ticks_per_beat)
                duration = end_time - start_time
                
                note_events.append({
                    'midi_note': msg.note,
                    'start_time': start_time,
                    'duration': duration,
                    'velocity': velocity,
                    'start_tick': start_tick
                })
                
                del active_notes[key]
    
    # Handle notes without note_off (extend to end of track)
    for (note, channel), (start_tick, velocity) in active_notes.items():
        start_time = calculate_absolute_time(start_tick, tempo_map, ticks_per_beat)
        end_time = calculate_absolute_time(current_tick, tempo_map, ticks_per_beat)
        duration = end_time - start_time
        
        note_events.append({
            'midi_note': note,
            'start_time': start_time,
            'duration': max(duration, 0.1),  # Minimum duration
            'velocity': velocity,
            'start_tick': start_tick
        })
    
    # Sort by start time, then by pitch
    note_events.sort(key=lambda x: (x['start_time'], x['midi_note']))
    
    # Group simultaneous notes (within 0.001 second tolerance)
    if not note_events:
        return
    
    current_group = []
    current_start_time = None
    tolerance = 0.001  # 1ms tolerance for grouping
    
    for event in note_events:
        if current_start_time is None or abs(event['start_time'] - current_start_time) < tolerance:
            # Add to current group
            if current_start_time is None:
                current_start_time = event['start_time']
            
            tone = Tone(
                midi_note=event['midi_note'],
                duration=event['duration'],
                velocity=event['velocity'],
                start_time=event['start_time']
            )
            current_group.append(tone)
        else:
            # Yield current group and start new one
            if current_group:
                # Sort group by pitch (lowest to highest)
                current_group.sort(key=lambda t: t.midi_note)
                yield current_group
            
            current_group = [Tone(
                midi_note=event['midi_note'],
                duration=event['duration'],
                velocity=event['velocity'],
                start_time=event['start_time']
            )]
            current_start_time = event['start_time']
    
    # Yield final group
    if current_group:
        current_group.sort(key=lambda t: t.midi_note)
        yield current_group
