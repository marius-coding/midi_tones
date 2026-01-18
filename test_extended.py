#!/usr/bin/env python3
"""Extended test script for the MidiTones library."""

from miditones import Midi

def main():
    print("Testing MidiTones library with imperialmarch.mid")
    print("=" * 60)
    
    # Load MIDI file
    song = Midi("imperialmarch.mid")
    print(f"✓ Successfully loaded: {song.filename}")
    print(f"  Tempo: {song.tempo:.2f} BPM")
    print(f"  Ticks per beat: {song.ticks_per_beat}")
    print()
    
    # List all tracks with their note counts
    print("Available tracks with statistics:")
    for track_name in song.list_tracks():
        track = song[track_name]
        try:
            note_count = len(track)
            duration = track.duration
            print(f"  - {track_name:15s}: {note_count:4d} notes, {duration:6.2f}s, Channel {track.channel}")
        except Exception as e:
            print(f"  - {track_name:15s}: Error - {e}")
    print()
    
    # Find a track with notes
    print("Testing iteration on tracks with notes:")
    print("-" * 60)
    
    for track_name in song.list_tracks():
        track = song[track_name]
        
        # Check if track has notes
        first_few_tones = []
        tone_count = 0
        
        for tone_group in track:
            for tone in tone_group:
                first_few_tones.append(tone)
                tone_count += 1
                if len(first_few_tones) >= 10:
                    break
            if len(first_few_tones) >= 10:
                break
        
        if first_few_tones:
            print(f"\nTrack: {track_name}")
            print(f"First 10 tones:")
            for i, tone in enumerate(first_few_tones, 1):
                print(f"  {i:2d}. {str(tone)}")
            
            # Show detailed properties of first tone
            print(f"\nDetailed properties of first tone:")
            tone = first_few_tones[0]
            print(f"  __str__():    {str(tone)}")
            print(f"  __repr__():   {repr(tone)}")
            print(f"  midi_note:    {tone.midi_note}")
            print(f"  note_name:    {tone.note_name}")
            print(f"  note_full:    {tone.note_full}")
            print(f"  note_int:     {tone.note_int}")
            print(f"  frequency:    {tone.frequency:.2f} Hz")
            print(f"  duration:     {tone.duration:.3f}s")
            print(f"  velocity:     {tone.velocity}")
            print(f"  start_time:   {tone.start_time:.3f}s")
            
            # Only test first track with notes
            break
    
    print()
    print("=" * 60)
    print("✓ All tests completed successfully!")

if __name__ == "__main__":
    main()
