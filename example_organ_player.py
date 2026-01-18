"""Example: play the 'Trumpet' track of Imperial March on the pipe organ.

This script translates MIDI notes to pipe-organ valve operations. It compensates
for valve actuation time with configurable turn-on and turn-off delays. Valve 0
is assumed to correspond to MIDI note C3 (note number 48); valve indices may be
negative for notes below C3.
"""

import argparse
import time
from typing import Iterable, List, Sequence, Tuple, Optional

from miditones import Midi
from miditones.tone import Tone
from pipe_organ_interface import PipeOrgan

# MIDI note 48 is C3. Valve 0 maps to this note; other valves are offset from it.
BASE_MIDI_FOR_VALVE_ZERO = 48


Event = Tuple[float, bool, int, Tone, str]


def midi_note_to_valve_index(midi_note: int, base_note: int = BASE_MIDI_FOR_VALVE_ZERO) -> int:
    """Map a MIDI note to a valve index relative to C3 (valve 0)."""
    return midi_note - base_note


def build_valve_events(
    track: Iterable[Sequence[Tone]],
    turn_on_delay: float,
    turn_off_delay: float,
    speed: float,
    start_time_limit: float,
    stop_time_limit: Optional[float],
) -> List[Event]:
    """Translate tones into time-ordered valve events.

    Each tone becomes two events:
    - An open event scheduled `turn_on_delay` before the intended start.
    - A close event scheduled `turn_off_delay` before the intended end.
    """
    events: List[Event] = []

    for tone_group in track:
        for tone in tone_group:
            # Scale timeline by speed; durations rely on integer ticks for consistency.
            tick_seconds = tone.duration / tone.duration_ticks if tone.duration_ticks else tone.duration
            start_time = tone.start_time / speed
            duration = (tone.duration_ticks * tick_seconds) / speed if tone.duration_ticks else tone.duration / speed

            original_end = start_time + duration
            if stop_time_limit is not None and start_time >= stop_time_limit:
                continue
            if original_end <= start_time_limit:
                continue

            clipped_start = max(start_time, start_time_limit)
            clipped_end = original_end if stop_time_limit is None else min(original_end, stop_time_limit)
            if clipped_end <= clipped_start:
                continue

            relative_start = clipped_start - start_time_limit
            relative_end = clipped_end - start_time_limit

            start_cmd_time = max(0.0, relative_start - turn_on_delay)
            end_cmd_time = max(0.0, relative_end - turn_off_delay)
            valve_index = midi_note_to_valve_index(tone.midi_note)
            events.append((start_cmd_time, True, valve_index, tone, track.name if hasattr(track, "name") else ""))
            events.append((end_cmd_time, False, valve_index, tone, track.name if hasattr(track, "name") else ""))

    # Sort by time; open events before close events if simultaneous to avoid spurious closures.
    events.sort(key=lambda e: (e[0], not e[1], e[2]))
    return events


def play_events(events: List[Event], organ: PipeOrgan) -> None:
    """Execute valve events with monotonic timing for accuracy."""
    open_valves = set()
    start = time.monotonic()

    for event_time, is_open, valve_index, tone, track_name in events:
        elapsed = time.monotonic() - start
        sleep_time = event_time - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

        if is_open:
            if valve_index not in open_valves:
                organ.valve_open(valve_index)
                now_s = time.monotonic() - start
                print(
                    f"ON t={now_s:8.3f}s |  tick={tone.start_tick:6d} | "
                    f"valve={valve_index:3d} | duration={tone.duration_ticks:3d} |  note={tone.note_full:>4s} | "
                    f"freq={tone.frequency:8.2f} Hz | track={track_name} "
                )
                open_valves.add(valve_index)
        else:
            if valve_index in open_valves:
                organ.valve_close(valve_index)
                open_valves.discard(valve_index)

    # Make sure everything is closed when done.
    for valve_index in list(open_valves):
        organ.valve_close(valve_index)



def main() -> None:
    parser = argparse.ArgumentParser(description="Play Imperial March 'Trumpet' track on the pipe organ")
    parser.add_argument("--midi", default="imperialmarch.mid", help="Path to the Imperial March MIDI file")
    parser.add_argument("--track", default="Trumpet", help="Track name to play from the MIDI file")
    parser.add_argument("--turn-on-delay", type=float, default=0.0, help="Seconds to pre-open a valve before note start")
    parser.add_argument("--turn-off-delay", type=float, default=0.0, help="Seconds to pre-close a valve before note end")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier (1.0 = original)")
    parser.add_argument("--audio", action="store_true", help="Enable audio output (requires sounddevice + numpy)")
    parser.add_argument("--start-time", type=float, default=0.0, help="Start time in seconds (post speed scaling)")
    parser.add_argument("--stop-time", type=float, default=None, help="Stop time in seconds (post speed scaling, exclusive)")
    args = parser.parse_args()

    midi = Midi(args.midi)

    if args.speed <= 0:
        raise ValueError("Speed must be > 0")

    if args.track.lower() == "all":
        tracks = [midi[name] for name in midi.list_tracks()]
        if not tracks:
            print(f"No tracks found in {midi.filename}.")
            return
    else:
        try:
            tracks = [midi[args.track]]
        except KeyError:
            print(f"Track '{args.track}' not found in {midi.filename}. Available tracks:")
            for name in midi.list_tracks():
                print(f"- {name}")
            return

    events: List[Event] = []
    for track in tracks:
        events.extend(
            build_valve_events(
                track=track,
                turn_on_delay=args.turn_on_delay,
                turn_off_delay=args.turn_off_delay,
                speed=args.speed,
                start_time_limit=args.start_time,
                stop_time_limit=args.stop_time,
            )
        )

    if not events:
        print("No events found for the selected track(s). Available tracks:")
        for name in midi.list_tracks():
            print(f"- {name}")
        return

    # Sort combined events so overlapping tracks stay in chronological order.
    events.sort(key=lambda e: (e[0], not e[1], e[2]))

    track_names = ", ".join(track.name for track in tracks)
    total_tones = sum(len(track) for track in tracks)

    print(f"Playing track(s) '{track_names}' from {midi.filename}")
    print(f"Total tones: {total_tones} | Events queued: {len(events)}")
    print(
        f"turn_on_delay={args.turn_on_delay:.3f}s, "
        f"turn_off_delay={args.turn_off_delay:.3f}s, "
        f"speed={args.speed:.3f}x, "
        f"start={args.start_time:.3f}s, stop={args.stop_time if args.stop_time is not None else 'end'}"
    )

    organ = PipeOrgan(use_audio=args.audio)
    play_events(events, organ)


if __name__ == "__main__":
    main()
