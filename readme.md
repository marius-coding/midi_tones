# MidiTones - Python MIDI Library

A simple and intuitive Python library for parsing MIDI files and extracting musical notes with frequency, duration, and note name information.

## Overview

MidiTones loads MIDI files and provides easy access to individual tracks by name. Each track yields lists of tone objects containing frequency (Hz), note representation, and duration (seconds) - perfect for playback, analysis, or music visualization. When multiple notes are played simultaneously, the list contains all those tones. When only a single note is played, the list contains one item.

tested with:
https://bitmidi.com/imperialmarch-mid
python example_organ_player.py --audio --start-time=11 --track Trumpet

**Dependencies:**
- `mido` >= 1.2.0 (MIDI file parsing)

## Quick Start

```python
from miditones import Midi
import time

# Load a MIDI file
song = Midi("imperialmarch.mid")

# Iterate through tone lists in a specific track
for tones in song["piano"]:
    # tones is a list - may contain one or multiple simultaneous notes
    for tone in tones:
        print(str(tone))  # "A4 (440.00 Hz) - 0.5s"
        playback_device.output_frequency(tone.frequency)
    time.sleep(tones[0].duration)
```

## API Reference

### `Midi` Class

Main class for loading and accessing MIDI file content.

#### Constructor

```python
Midi(filename: str)
```

**Parameters:**
- `filename`: Path to the MIDI file

**Raises:**
- `FileNotFoundError`: If the MIDI file doesn't exist
- `ValueError`: If the file is not a valid MIDI file

#### Methods

```python
__getitem__(track_name: str) -> Track
```

Access a track by its name. Returns a `Track` object.

**Parameters:**
- `track_name`: Name of the track (as specified in MIDI track_name meta message)

**Raises:**
- `KeyError`: If the track name doesn't exist

**Note:** Track names are case-sensitive.

```python
list_tracks() -> List[str]
```

Returns a list of all available track names.

```python
get_track_by_index(index: int) -> Track
```

Access a track by its zero-based index (for MIDI files without track names).

#### Properties

```python
tracks: Dict[str, Track]
```

Dictionary mapping track names to Track objects.

```python
tempo: float
```

Initial tempo in BPM (beats per minute).

```python
ticks_per_beat: int
```

MIDI ticks per beat (resolution).

---

### `Track` Class

Represents a single MIDI track. Iterable - yields lists of `Tone` objects.

#### Methods

```python
__iter__() -> Iterator[List[Tone]]
```

Iterate through all tone groups in the track sequentially. Each iteration yields a list containing one or more Tone objects. When multiple notes are played simultaneously, the list contains all those tones. When only a single note is played, the list contains one item.

```python
__len__() -> int
```

Returns the total number of tones in the track.

#### Properties

```python
name: str
```

The track name (from MIDI metadata or auto-generated).

```python
channel: int
```

Primary MIDI channel used by this track (0-15).

```python
duration: float
```

Total duration of the track in seconds.

---

### `Tone` Class

Represents a single musical note/tone.

#### Properties

```python
frequency: float
```

Frequency in Hertz (Hz). Calculated using A4 = 440 Hz.

```python
midi_note: int
```

MIDI note number (0-127). Middle C (C4) = 60.

```python
note_int: int
```

Integer representation of the semitone relative to A (A=0, A#=1, B=2, C=3, ..., G#=11).

```python
note_name: str
```

String representation of the note (e.g., "A#", "C", "F#").

```python
note_full: str
```

Full note name with octave (e.g., "A4", "C#5", "F3").

```python
duration: float
```

Duration of the note in seconds.

```python
velocity: int
```

MIDI velocity (0-127). Represents how hard the note was played.

```python
start_time: float
```

Absolute start time of the note in seconds from the beginning of the track.

#### Methods

```python
__str__() -> str
```

Returns human-readable representation: "A4 (440.00 Hz) - 0.5s"

```python
__repr__() -> str
```

Returns detailed representation: "Tone(note='A4', frequency=440.0, duration=0.5)"

---

## Implementation Details

### MIDI Note to Frequency Conversion

The library uses the standard formula for converting MIDI note numbers to frequencies:

```
frequency = 440 × 2^((midi_note - 69) / 12)
```

Where MIDI note 69 corresponds to A4 (440 Hz).

### Note Integer Representation

The `note_int` property uses A as the reference (A=0):

| Note | A | A# | B | C | C# | D | D# | E | F | F# | G | G# |
|------|---|----|----|---|----|----|----|----|---|----|----|-----|
| Int  | 0 | 1  | 2  | 3 | 4  | 5  | 6  | 7  | 8 | 9  | 10 | 11  |

Calculation: `note_int = (midi_note - 21) % 12` where MIDI note 21 is A0.

### Duration Calculation

Durations are calculated from MIDI ticks using the tempo:

```
duration_seconds = (ticks × tempo_microseconds) / (ticks_per_beat × 1,000,000)
```

The library handles:
- Tempo changes mid-song (via tempo meta messages)
- Multiple note_on/note_off event pairs
- Overlapping notes (returns as separate Tone objects)

### Track Naming Strategy

1. **Primary:** Use track_name from MIDI meta messages
2. **Fallback 1:** If no track name, use "Track {index}" (e.g., "Track 0")
3. **Fallback 2:** For tracks with program changes, use instrument name (e.g., "Acoustic Grand Piano")
4. **Conflict resolution:** If multiple tracks share a name, append " (2)", " (3)", etc.

### Handling MIDI Complexity

**Polyphonic Tracks:**
When multiple notes play simultaneously (chords), the iterator yields them as a list. Notes starting at the same time are grouped together in a single list, ordered by pitch (lowest to highest). Single notes are also yielded as a list with one item.

**Percussion Tracks:**
MIDI channel 10 (drum channel) notes are converted to frequencies using the same formula, though these frequencies don't correspond to musical pitches. Consider filtering by channel if needed.

**Tempo Changes:**
The library automatically tracks tempo changes throughout the MIDI file and applies them to duration calculations.

**Missing note_off Events:**
If a note_on event lacks a matching note_off, the note duration extends to the next note_on or end of track.

---

## Architecture

### Class Hierarchy

```
miditones/
├── __init__.py          # Package exports (Midi, Track, Tone)
├── midi.py              # Midi class implementation
├── track.py             # Track class implementation
├── tone.py              # Tone class implementation
├── parser.py            # MIDI parsing logic (tempo map, event processing)
└── utils.py             # Helper functions (note conversions, naming)
```

### Key Modules

**parser.py:**
- `parse_midi_file(filename)`: Load and validate MIDI file using mido
- `build_tempo_map(tracks)`: Extract tempo changes with absolute timing
- `extract_track_names(tracks)`: Get track names with conflict resolution
- `process_track_events(track, tempo_map, ticks_per_beat)`: Convert events to note data

**utils.py:**
- `midi_to_frequency(midi_note)`: MIDI note number → frequency (Hz)
- `midi_to_note_name(midi_note)`: MIDI note → note name (e.g., "C#4")
- `midi_to_note_int(midi_note)`: MIDI note → integer representation (A=0)
- `ticks_to_seconds(ticks, tempo_us, ticks_per_beat)`: Time conversion

### Data Flow

1. **Load:** `Midi.__init__()` loads file via `mido.MidiFile`
2. **Parse:** Extract tempo map, track names, and create Track objects
3. **Access:** User accesses track via `song["piano"]`
4. **Iterate:** `Track.__iter__()` processes MIDI events on-demand
5. **Generate:** Create Tone objects with calculated properties
6. **Yield:** Return Tone to user for playback/analysis

### Performance Considerations

**Lazy Evaluation:**
Track iteration processes MIDI events on-demand rather than parsing all notes upfront. This improves memory efficiency for large MIDI files.

**Caching:**
- Tempo map is calculated once during initialization
- Track name mapping is built once
- Tone objects are generated during iteration (not cached)

**Memory Usage:**
For a typical MIDI file (5 MB, 10 tracks, 50,000 notes), expect ~50-100 MB memory usage during full iteration.

---

## Usage Examples

### Example 1: List All Tracks

```python
from miditones import Midi

song = Midi("song.mid")
print(f"Tracks in {song.filename}:")
for track_name in song.list_tracks():
    track = song[track_name]
    print(f"  - {track_name}: {len(track)} notes, {track.duration:.2f}s")
```

### Example 2: Extract Melody

```python
from miditones import Midi

song = Midi("melody.mid")
melody_track = song["Lead"]

notes = []
for tones in melody_track:
    for tone in tones:
        notes.append({
            'note': tone.note_full,
            'frequency': tone.frequency,
            'duration': tone.duration,
            'start': tone.start_time
        })

print(f"Extracted {len(notes)} notes from melody")
```

### Example 3: Transposition Analysis

```python
from miditones import Midi
from collections import Counter

song = Midi("piece.mid")
track = song["Piano"]

# Count note occurrences
note_counts = Counter(tone.note_name for tones in track for tone in tones)

print("Most common notes:")
for note, count in note_counts.most_common(5):
    print(f"  {note}: {count} times")
```

### Example 4: Export to JSON

```python
import json
from miditones import Midi

song = Midi("data.mid")

output = {
    'tempo': song.tempo,
    'tracks': {}
}

for track_name in song.list_tracks():
    tones_data = []
    for tone_list in song[track_name]:
        # Each iteration is a list of simultaneous tones
        group = [{
            'note': tone.note_full,
            'freq': tone.frequency,
            'duration': tone.duration,
            'velocity': tone.velocity,
            'start': tone.start_time
        } for tone in tone_list]
        tones_data.append(group)
    output['tracks'][track_name] = tones_data

with open('output.json', 'w') as f:
    json.dump(output, f, indent=2)
```

### Example 5: Simple Playback (Conceptual)

```python
from miditones import Midi
import time

class SimpleOscillator:
    def output_frequency(self, freq):
        # Hardware-specific implementation
        pass

song = Midi("imperialmarch.mid")
osc = SimpleOscillator()

for tones in song["piano"]:
    # Play all simultaneous tones (for chords)
    for tone in tones:
        print(f"Playing {tone.note_full} at {tone.frequency:.2f} Hz for {tone.duration:.3f}s")
        osc.output_frequency(tone.frequency)
    time.sleep(tones[0].duration)
```

---

## License

MIT License - See LICENSE file for details

---

## References

- MIDI Specification: https://www.midi.org/specifications
- MIDI Note to Frequency: https://newt.phys.unsw.edu.au/jw/notes.html
- Mido Documentation: https://mido.readthedocs.io/
