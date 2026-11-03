# dynamics_pedal.py

from music21 import converter, dynamics, expressions
import pretty_midi

DYNAMIC_VELOCITY = {
    'pppp': 20, 'ppp': 25, 'pp': 30, 'p': 50,
    'mp': 60, 'mf': 70, 'f': 90, 'ff': 110,
    'fff': 120, 'ffff': 127,
}
DEFAULT_VELOCITY = 70


def get_dynamics_events(score):
    """
    Returns a sorted list of (offset, velocity) with ONE entry per unique
    offset. Discrete Dynamic markings (p, f, mf...) are authoritative;
    wedge (crescendo/diminuendo) endpoints only fill in offsets that have
    no discrete marking, since explicit markings are more reliable than
    our p/f assumption for wedges.
    """
    discrete = {}   # offset -> velocity, from explicit Dynamic marks
    wedge_pts = {}  # offset -> list of velocities, from wedge endpoints

    for d in score.flatten().getElementsByClass(dynamics.Dynamic):
        discrete[float(d.offset)] = DYNAMIC_VELOCITY.get(d.value, DEFAULT_VELOCITY)

    for wedge in score.flatten().getElementsByClass(dynamics.DynamicWedge):
        spanned = wedge.getSpannedElements()
        if not spanned:
            continue
        start_offset = float(spanned[0].offset)
        end_offset = float(spanned[-1].offset + spanned[-1].duration.quarterLength)

        if isinstance(wedge, dynamics.Crescendo):
            start_v, end_v = DYNAMIC_VELOCITY['p'], DYNAMIC_VELOCITY['f']
        elif isinstance(wedge, dynamics.Diminuendo):
            start_v, end_v = DYNAMIC_VELOCITY['f'], DYNAMIC_VELOCITY['p']
        else:
            continue

        wedge_pts.setdefault(start_offset, []).append(start_v)
        wedge_pts.setdefault(end_offset, []).append(end_v)

    # Merge: discrete wins if present at that offset; else average wedge points at that offset
    merged = dict(discrete)
    for offset, vels in wedge_pts.items():
        if offset not in merged:
            merged[offset] = int(round(sum(vels) / len(vels)))

    events = sorted(merged.items(), key=lambda x: x[0])
    return events


def velocity_at(offset, events):
    """
    Finds the velocity at a given offset, interpolating linearly between
    two events if it falls inside a crescendo/diminuendo ramp, else
    holding the last known value.
    """
    if not events:
        return DEFAULT_VELOCITY
    if offset <= events[0][0]:
        return events[0][1]
    if offset >= events[-1][0]:
        return events[-1][1]

    for i in range(len(events) - 1):
        o1, v1 = events[i]
        o2, v2 = events[i + 1]
        if o1 <= offset <= o2:
            if o2 == o1:
                return v1
            frac = (offset - o1) / (o2 - o1)
            return int(round(v1 + frac * (v2 - v1)))
    return events[-1][1]


def get_pedal_events(score):
    """
    Returns a list of (press_time, release_time) tuples in quarter-length
    offsets, one per PedalMark spanner found in the score.
    """
    pedal_events = []
    for pm in score.flatten().getElementsByClass(expressions.PedalMark):
        spanned = pm.getSpannedElements()
        if not spanned:
            continue
        press = float(spanned[0].offset)
        release = float(spanned[-1].offset + spanned[-1].duration.quarterLength)
        pedal_events.append((press, release))
    return pedal_events


def score_to_expressive_midi(score, midi_path, bpm=120):
    """
    Renders a music21 Score to a MIDI file using pretty_midi, applying
    per-note velocity from dynamics markings/wedges and CC64 sustain
    pedal events from PedalMark spanners.
    """
    seconds_per_quarter = 60.0 / bpm
    dyn_events = get_dynamics_events(score)
    pedal_events = get_pedal_events(score)

    pm = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    piano = pretty_midi.Instrument(program=0, name="Piano")

    for n in score.flatten().notes:
        offset_ql = float(n.offset)
        dur_ql = float(n.duration.quarterLength)
        vel = velocity_at(offset_ql, dyn_events)

        pitches = n.pitches if hasattr(n, 'pitches') else [n.pitch]
        for p in pitches:
            piano.notes.append(pretty_midi.Note(
                velocity=vel,
                pitch=p.midi,
                start=offset_ql * seconds_per_quarter,
                end=(offset_ql + dur_ql) * seconds_per_quarter,
            ))

    for press_ql, release_ql in pedal_events:
        piano.control_changes.append(pretty_midi.ControlChange(
            number=64, value=127, time=press_ql * seconds_per_quarter))
        piano.control_changes.append(pretty_midi.ControlChange(
            number=64, value=0, time=release_ql * seconds_per_quarter))

    pm.instruments.append(piano)
    pm.write(midi_path)
    return len(piano.notes), len(pedal_events)


if __name__ == "__main__":
    score = converter.parse("test_dynamics_pedal.musicxml")
    n_notes, n_pedals = score_to_expressive_midi(score, "test_dynamics_pedal_output.mid")
    print(f"Wrote MIDI with {n_notes} notes, {n_pedals} pedal event pair(s)")