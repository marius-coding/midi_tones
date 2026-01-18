#!/usr/bin/env python3
"""Test script for the MidiTones library."""

from miditones import Midi

def main():
    print("Testing MidiTones library with imperialmarch.mid")
    print("=" * 60)
    
    # Load MIDI file
    try:
        song = Midi("imperialmarch.mid")
        print(f"✓ Successfully loaded: {song.filename}")
        print(f"  Tempo: {song.tempo:.2f} BPM")
        print(f"  Ticks per beat: {song.ticks_per_beat}")
        print()
    except Exception as e:
        print(f"✗ Failed to load MIDI file: {e}")
        return
    
    # List all tracks
    print("Available tracks:")
    for track_name in song.list_tracks():
        track = song[track_name]
        print(f"  - {track_name}: Channel {track.channel}")
    print()
    
    # Test iterating through a track
    print("Testing track iteration (first track, first 10 tones):")
    print("-" * 60)
    
    first_track_name = song.list_tracks()[0]
    track = song[first_track_name]
    
    print(f"Track: {track.name}")
    
    tone_count = 0
    for tone_group in track:
        tone_count += len(tone_group)
        
        # Only print first 10 tones
        if tone_count <= 10:
            if len(tone_group) == 1:
                tone = tone_group[0]
                print(f"  {str(tone)}")
                print(f"    - Velocity: {tone.velocity}, Start: {tone.start_time:.3f}s")
            else:
                print(f"  Chord with {len(tone_group)} notes:")
                for tone in tone_group:
                    print(f"    - {tone.note_full} ({tone.frequency:.2f} Hz)")
        
        if tone_count > 10:
            break
    
    print()
    print(f"Track statistics:")
    print(f"  Total tones: {len(track)}")
    print(f"  Duration: {track.duration:.2f}s")
    print()
    
    # Test accessing track by index
    print("Testing track access by index:")
    try:
        track_by_idx = song.get_track_by_index(0)
        print(f"✓ Track 0: {track_by_idx.name}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    print()
    
    # Test properties of a single tone
    print("Testing Tone properties:")
    print("-" * 60)
    track = song[first_track_name]
    for tone_group in track:
        if tone_group:
            tone = tone_group[0]
            print(f"Sample Tone object:")
            print(f"  __str__():  {str(tone)}")
            print(f"  __repr__(): {repr(tone)}")
            print(f"  Properties:")
            print(f"    - midi_note: {tone.midi_note}")
            print(f"    - note_name: {tone.note_name}")
            print(f"    - note_full: {tone.note_full}")
            print(f"    - note_int:  {tone.note_int}")
            print(f"    - frequency: {tone.frequency:.2f} Hz")
            print(f"    - duration:  {tone.duration:.3f}s")
            print(f"    - velocity:  {tone.velocity}")
            print(f"    - start_time: {tone.start_time:.3f}s")
            break
    
    print()
    print("=" * 60)
    print("✓ All tests completed successfully!")

if __name__ == "__main__":
    main()
