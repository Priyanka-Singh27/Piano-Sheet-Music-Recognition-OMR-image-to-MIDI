from music21 import converter


def measure_duration_check(score):
    """
    Checks whether each measure's total note duration matches
    what its time signature says it should be.
    Returns a list of flag dicts for any mismatches.
    """
    flags = []
    for part in score.parts:
        for measure in part.getElementsByClass('Measure'):
            notes = list(measure.notesAndRests)
            if len(notes) == 0:
                continue  # nothing to check — likely a structural artifact, not real music

            ts = measure.timeSignature or measure.getContextByClass('TimeSignature')
            if ts is None:
                continue  # no time signature in scope, skip

            expected = ts.barDuration.quarterLength
            actual = sum(n.duration.quarterLength for n in notes)

            if abs(actual - expected) > 1e-3:  # allow tiny float rounding
                flags.append({
                    "measure_number": measure.number,
                    "expected_quarterLength": float(expected), #converted fraction to float as json can not serialize fraction
                    "actual_quarterLength": float(actual),
                    "issue": "duration_mismatch"
                })
    return flags


def key_signature_check(score):
    """
    Checks whether each note's pitch is plausible given the
    piece's key signature (i.e. not requiring an accidental
    that the key signature doesn't already account for, unless
    explicitly marked).
    Returns a list of flag dicts for any notes that look inconsistent.
    """
    flags = []
    for part in score.parts:
        key = part.flatten().getElementsByClass('KeySignature').first()
        if key is None:
            continue

        allowed_pitches = set(key.alteredPitches)  # pitches the key sig already alters
        allowed_names = {p.name for p in allowed_pitches}

        for note in part.flatten().notes:
            for pitch in note.pitches:
                # if the note has an accidental not implied by the key signature, flag it
                if pitch.accidental is not None and pitch.name not in allowed_names:
                    flags.append({
                        "note": pitch.nameWithOctave,
                        "offset": float(note.offset),
                        "issue": "accidental_outside_key_signature"
                    })
    return flags


if __name__ == "__main__":
    #for monophonic clean file
    score = converter.parse("test_sample.krn")

    duration_flags = measure_duration_check(score)
    key_flags = key_signature_check(score)

    print("Duration check flags:", duration_flags)
    print("Key signature check flags:", key_flags)

    #for broken test file
    score = converter.parse("test_broken.krn")
    
    duration_flags = measure_duration_check(score)
    key_flags = key_signature_check(score)

    print("Duration check flags:", duration_flags)
    print("Key signature check flags:", key_flags)

    #for bad key test file
    score = converter.parse("test_bad_key.krn")
    
    duration_flags = measure_duration_check(score)
    key_flags = key_signature_check(score)

    print("Duration check flags:", duration_flags)
    print("Key signature check flags:", key_flags)