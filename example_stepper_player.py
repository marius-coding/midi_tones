"""Example: drive a stepper motor at note frequencies from a MIDI track.

- Only one frequency can play at a time; if multiple notes start together,
  the first in the group is used and the rest are ignored.
- Timing uses monotonic scheduling for accuracy.
"""

import argparse
import time
from typing import Iterable, List, Sequence, Tuple

from miditones import Midi
from miditones.tone import Tone
from stepper_interface import StepperInterface

Event = Tuple[float, bool, float, Tone]
# event_time, is_start, frequency_hz, tone


def build_events(
    track: Iterable[Sequence[Tone]],
    speed: float,
) -> List[Event]:
    events: List[Event] = []
    for tone_group in track:
        if not tone_group:
            continue
        tone = tone_group[0]  # take the first tone; ignore others

        tick_seconds = tone.duration / tone.duration_ticks if tone.duration_ticks else tone.duration
        start_time = tone.start_time / speed
        duration = (tone.duration_ticks * tick_seconds) / speed if tone.duration_ticks else tone.duration / speed

        freq = tone.frequency
        start_evt = (start_time, True, freq, tone)
        stop_evt = (start_time + duration, False, freq, tone)
        events.append(start_evt)
        events.append(stop_evt)

    events.sort(key=lambda e: (e[0], not e[1]))
    return events


def play_events(events: List[Event], motor: StepperInterface) -> None:
    start = time.monotonic()
    for event_time, is_start, freq, tone in events:
        elapsed = time.monotonic() - start
        wait = event_time - elapsed
        if wait > 0:
            time.sleep(wait)

        if is_start:
            motor.set_frequency(freq)
        else:
            motor.stop()

    # ensure stopped at end
    motor.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Drive stepper motor from MIDI track frequencies")
    parser.add_argument("--midi", default="imperialmarch.mid", help="Path to the MIDI file")
    parser.add_argument("--track", default="Trumpet", help="Track name to use")
    parser.add_argument("--speed", type=float, default=1.0, help="Playback speed multiplier")
    args = parser.parse_args()

    if args.speed <= 0:
        raise ValueError("Speed must be > 0")

    midi = Midi(args.midi)
    track = midi[args.track]

    events = build_events(track=track, speed=args.speed)
    if not events:
        print("No events found for this track.")
        return

    print(f"Track '{track.name}' from {midi.filename} -> stepper motor")
    print(f"Events: {len(events)} | speed={args.speed:.3f}x")

    motor = StepperInterface()
    play_events(events, motor)


if __name__ == "__main__":
    main()
