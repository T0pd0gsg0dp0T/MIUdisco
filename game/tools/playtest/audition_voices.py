#!/usr/bin/env python3
"""Render one line per cast member so the voice picks can actually be judged.

The speakers in content/voices.json were chosen by measuring median F0 across
every candidate in both models — that settles pitch, depth and gender, but not
whether a voice *sounds like the character*. That needs ears. This writes a
numbered WAV per cast member, each speaking their own words, so the whole cast
can be listened through in a couple of minutes.

    python3 tools/playtest/audition_voices.py [outdir]
    # then: for f in outdir/*.wav; do echo "$f"; paplay "$f"; done

To recast anybody, change `speaker` for that entry in content/voices.json and
re-run. Candidate speaker indices with measured pitch are in the profile files
written by the tooling; any index valid for that model will work.
"""
from __future__ import annotations
import json, sys, wave
from pathlib import Path

HERE = Path(__file__).resolve()
GAME = HERE.parent.parent.parent
sys.path.insert(0, str(GAME))

import voice as V  # noqa: E402

# Each character says something that is unmistakably theirs, so the voice is
# judged doing the job it will actually have to do.
LINES = {
 "narrator": "The hallway to the back stretches or does not stretch depending on the hour, and on nothing else you have been able to isolate.",
 "oliver": "Count the exits. Now count them again, and note that the number is the same, which in this town is worth writing down.",
 "furthermore": "You have both been in here talking to yourselves. I have been in here the whole time. Somebody has been listening. That was never the part that was in doubt.",
 "revilo": "Well. Now we have both had a very long day.",
 "asimov": "Ah. The tenant who survives things. Come in, come in — mind the corridor, it is longer today than it was contracted to be.",
 "luigi": "Ey! Careful, careful — is wet, is *blessed*, is not the same thing but today they happen in the same place.",
 "darek": "Well, hey there, Ols. Sorry about your wait. — Ah. You ain't waited yet. Gimme a second, I'm runnin' a touch ahead this evenin'.",
 "ginny": "You came in the front. Nobody comes in the front. That's not a compliment, that's a stance — and yours is wide open.",
 "instagator": "Circling back on your presence in this space. Do you have a moment for a quick alignment.",
 "soliloquy": "A visitor. Vertical. How novel, and how temporary — I say that of everyone, and I have never once been wrong.",
 "barney": "Well now! Look what the trail dragged in. You'll be wanting the dry side — we've got a front coming through the lounge around ten.",
 "bud": "BUT — before you say anything — everything in this establishment is completely normal and I'd thank you to note that I said it first.",
 "dee": "We were hoping you'd come over. We've been having an argument and we can't settle it, which is unusual, because normally we can.",
 "dee_two": "One of us would. That's the trouble.",
 "chef_d": "Mishter Onionsh. Shit down, shit down. I got shomething going and ish nearly at the — shhhk. There. Ish at the shhhk.",
 "t": "Voilà! In view, a humble vessel of a victual, veteran of vinegar and veal, vouchsafing neither vanity nor vulgar— ... Sorry. It's the T. It gets away from me on a T.",
 "wino_t": "Onions in the door / at a quarter to whenever / take a chair, take two / I got nothing but forever.",
 "sir_jerry": "Well met, good sir. Be seated, and let us assess the presenting field. I observe recession at the temporal aspect and I shall speak no further of it, for a knight is not a herald.",
 "albert": "You are looking at me. Not past. At. Do you know how long, monsieur.",
 "ben": "What you been up to, my friend? — No. Don't answer that one. I'll take the other one. What you been up to that you ain't told nobody.",
 "woolbinkle": "Mr Onions! I had a feeling. I had a feeling and I put one on and if I was wrong I'd have eaten it myself, so there's no — there's no obligation, is what I'm saying.",
 "mary": "Hey. Yeah. You're the one who orders in words. That's fine. That's a whole way of doing it.",
 "fatty": "Sit. Sit. Look at this straw. No — look at it. In the shake and above the shake, same straw, one straw. Now: which bit of it is the straw?",
 "landy": "Mr Onions! 2-F! Now — the window. I've been at the window. It's sorted. It's completely sorted and I'd not want you to worry about the weather in it.",
}

# The four facets of Oliver's interior, one per attribute.
ATTR_LINES = {
 "INTELLECT": "Nine by eleven. Every measurement in Silvora Reefs resolves against this room, and this room resolves against nothing.",
 "PSYCHE": "The lamppost has been leaning away from you since you arrived. Not from the wind. It would prefer not to be looked at directly.",
 "FORTITUDE": "It is still hot. Things that are still hot are still happening. Do not put a hand on it.",
 "MOTORICS": "Pace it. Fourteen steps out, fourteen back, and the fourteenth is against the same scuff both times.",
}


def render(spec: dict, text: str, path: Path) -> float:
    from piper import SynthesisConfig
    v = V._get_model(spec["model"])
    cfg = SynthesisConfig(speaker_id=spec.get("speaker"),
                          length_scale=spec.get("length_scale"),
                          noise_scale=spec.get("noise_scale"),
                          noise_w_scale=spec.get("noise_w"))
    with open(path, "wb") as fh, wave.open(fh, "wb") as wf:
        v.synthesize_wav(V.normalise(text), wf, syn_config=cfg)
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/miu-audition")
    out.mkdir(parents=True, exist_ok=True)
    reg = V._load_registry()
    index, n = [], 0

    for who, line in LINES.items():
        spec = V.spec_for(who)
        if not spec:
            print(f"  !! no spec for {who}")
            continue
        n += 1
        path = out / f"{n:02d}_{who}.wav"
        dur = render(spec, line, path)
        note = (reg.get(who) or {}).get("note", "")
        index.append(f"{n:02d}  {who:<12} {spec['model'].split('-')[1]:<10} "
                     f"sid {spec.get('speaker'):<4} {dur:5.1f}s  {note[:70]}")
        print(index[-1], flush=True)

    for attr, line in ATTR_LINES.items():
        spec = V.spec_for("oliver", attribute=attr)
        n += 1
        path = out / f"{n:02d}_skill_{attr.lower()}.wav"
        dur = render(spec, line, path)
        index.append(f"{n:02d}  skill:{attr:<10} sid {spec.get('speaker'):<4} {dur:5.1f}s")
        print(index[-1], flush=True)

    (out / "INDEX.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"\n{n} files -> {out}\nplay all:  for f in {out}/*.wav; do echo \"$f\"; paplay \"$f\"; done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
