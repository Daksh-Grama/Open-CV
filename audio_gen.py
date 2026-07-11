"""Procedurally generates a short looping synthwave-style backing track for
each level, using only the standard library (wave/array/math/random) so the
game needs no external, potentially copyrighted music files.

Run this once before playing:

    python audio_gen.py
"""

import math
import os
import random
import wave
from array import array

from levels import LEVELS, TUTORIAL

SAMPLE_RATE = 22050
LOOP_BEATS = 8
SCALE_STEPS = [0, 3, 5, 7, 10]          # minor pentatonic, semitones from root
ARPEGGIO = [0, 2, 4, 2, 1, 3, 4, 2]     # scale-degree pattern, one note per beat

# Hand-picked roots for the original three levels; every other level (the
# tutorial and the 10 generated ones) derives a root deterministically from
# its key so audio_gen.py never needs updating when a new level is added.
ROOT_HZ = {
    "orbit_drop": 220.00,      # A3 - calm intro
    "asteroid_belt": 196.00,   # G3 - grittier mid tempo
    "solar_flare": 277.18,     # C#4 - bright and urgent
}
ROOT_CHOICES = [174.61, 185.00, 196.00, 207.65, 220.00, 233.08, 246.94, 261.63, 277.18]


def root_hz_for(key):
    if key in ROOT_HZ:
        return ROOT_HZ[key]
    return ROOT_CHOICES[hash(key) % len(ROOT_CHOICES)]


OUT_DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")


def note_freq(root_hz, degree):
    semitone = SCALE_STEPS[degree % len(SCALE_STEPS)]
    octave = degree // len(SCALE_STEPS)
    return root_hz * (2 ** ((semitone + 12 * octave) / 12))


def render_track(bpm, root_hz):
    seconds_per_beat = 60.0 / bpm
    beat_samples = int(SAMPLE_RATE * seconds_per_beat)
    samples = array("h")

    for beat_i in range(LOOP_BEATS):
        freq = note_freq(root_hz, ARPEGGIO[beat_i % len(ARPEGGIO)])
        for n in range(beat_samples):
            t = n / SAMPLE_RATE
            progress = n / beat_samples

            # melodic voice: a soft square wave with a quick attack, gentle decay
            square = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
            envelope = min(1.0, progress * 12) * max(0.0, 1.0 - progress) ** 0.6
            melody = square * envelope * 0.18

            # kick thump right on the downbeat - this is the audible "beat"
            # that the level's obstacle spacing is authored against
            kick = math.sin(2 * math.pi * 90 * t) * math.exp(-progress * 18) * 0.5

            # soft hi-hat tick on the off-beat for a little texture
            hat = random.uniform(-1, 1) * 0.06 if 0.5 <= progress < 0.56 else 0.0

            value = max(-1.0, min(1.0, melody + kick + hat))
            samples.append(int(value * 32000))

    return samples


def write_wav(path, samples):
    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(samples.tobytes())


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for module in [TUTORIAL] + LEVELS:
        path = os.path.join(OUT_DIR, f"{module.KEY}.wav")
        samples = render_track(module.BPM, root_hz_for(module.KEY))
        write_wav(path, samples)
        print(f"generated {path} ({module.BPM} BPM)")


if __name__ == "__main__":
    main()
