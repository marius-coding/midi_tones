#!/usr/bin/env python3
"""Example usage of MidiTones library as shown in README."""

from miditones import Midi
import time

# Load a MIDI file
song = Midi("imperialmarch.mid")

print(f"Loaded: {song.filename}")
print(f"Tempo: {song.tempo:.2f} BPM")
print(f"Available tracks: {', '.join(song.list_tracks())}")
print()

# Example 1: Simple iteration through a track
print("Example 1: Iterate through tones in 'Piano' track")
print("-" * 60)

for i, tones in enumerate(song["Piano"]):
    # tones is a list - may contain one or multiple simultaneous notes
    if len(tones) == 1:
        tone = tones[0]
        print(f"{i+1:2d}. {str(tone)}")
    else:
        print(f"{i+1:2d}. Chord with {len(tones)} notes:")
        for tone in tones:
            print(f"    - {tone.note_full} ({tone.frequency:.2f} Hz)")

print()
print("Example 2: Extract note data for visualization")
print("-" * 60)

# Get first few notes from Trumpet track
notes_data = []
count = 0
for tones in song["Trumpet"]:
    for tone in tones:
        notes_data.append({
            'note': tone.note_full,
            'frequency': tone.frequency,
            'duration': tone.duration,
            'start': tone.start_time,
            'velocity': tone.velocity
        })
        count += 1
        if count >= 5:
            break
    if count >= 5:
        break

print("First 5 notes from Trumpet:")
for note in notes_data:
    print(f"  {note['note']:4s} at {note['start']:6.2f}s, "
          f"duration {note['duration']:.3f}s, "
          f"freq {note['frequency']:.2f} Hz, "
          f"vel {note['velocity']}")

print()
print("Example 3: Playback simulation (conceptual)")
print("-" * 60)

class SimpleOscillator:
    """Simulated oscillator for demonstration."""
    def output_frequency(self, freq):
        # In a real application, this would output to hardware
        pass

osc = SimpleOscillator()

print("Simulating playback of first 3 tone groups from Strings track:")
for i, tones in enumerate(song["Strings"]):
    if i >= 3:
        break
    
    # Play all simultaneous tones (for chords)
    for tone in tones:
        print(f"  Playing {tone.note_full} at {tone.frequency:.2f} Hz "
              f"for {tone.duration:.3f}s")
        osc.output_frequency(tone.frequency)
    
    # In real playback, we would sleep for the duration
    # time.sleep(tones[0].duration)

print()
print("✓ Examples completed!")
