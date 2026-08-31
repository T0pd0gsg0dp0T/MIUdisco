"""Piper text-to-speech: a distinct voice for every character, the narrator,
and Oliver's interior.

Three things make this worth having rather than a gimmick:

  1. Every speaker is a different voice, chosen by *measuring* the candidates
     rather than guessing. See content/voices.json for what was measured.
  2. The text is normalised before it is spoken. The prose is full of things
     that wreck a speech engine — 365 asterisk-emphases, 791 em-dashes, 466
     all-caps tokens, Wino-T's slash-separated bars — and read raw they come
     out as spelled-out letters and swallowed pauses.
  3. It never blocks the game. Synthesis happens on a worker thread, output is
     cached to disk by content hash, and if anything at all is missing —
     piper, a model, an audio player — every call quietly becomes a no-op.

Off by default. `--voice` turns it on.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import threading
from pathlib import Path

CONTENT = Path(__file__).parent / "content" / "voices.json"
VOICE_DIR = Path(os.environ.get("MIU_VOICE_DIR", Path.home() / "piper-voices"))
CACHE_DIR = Path(os.environ.get("MIU_VOICE_CACHE", Path.home() / ".cache" / "miu-tts"))

_enabled = False
_registry: dict = {}
_models: dict = {}          # model name -> loaded PiperVoice
_queue: "queue.Queue | None" = None
_worker: threading.Thread | None = None
_player: list[str] | None = None
_current: "subprocess.Popen | None" = None
_lock = threading.Lock()
_skip = threading.Event()


# --------------------------------------------------------------- normalising

_NUM_WORDS = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
              "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}

# Words that are genuinely shouted signage rather than an acronym. Everything
# in this game's all-caps is prose (BUT, RESOLVED, NOT YET, THANK YOU FOR YOUR
# PATIENCE), and espeak spells unknown caps runs out letter by letter, which
# turns Bud's entire personality into "bee you tee".
def _decaps(match: re.Match) -> str:
    run = match.group(0)
    words = run.split()
    if len(words) == 1:
        w = words[0]
        return w if len(w) <= 2 else w.capitalize()
    first, *rest = words
    return " ".join([first.capitalize()] + [w.lower() for w in rest])


def _spell_decimal(match: re.Match) -> str:
    whole, frac = match.group(1), match.group(2)
    digits = " ".join(_NUM_WORDS.get(d, d) for d in frac)
    return f"{whole} point {digits}"


_UPPER = "A-ZÀ-ÖØ-Þ"


def _tidy(t: str) -> str:
    """Collapse the punctuation churn the substitutions above leave behind."""
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s+([.,!?;:])", r"\1", t)
    t = re.sub(r"(,\s*){2,}", ", ", t)
    # ". ." or "!." from a paragraph break landing after existing punctuation
    t = re.sub(r"([.!?;:])[\s.]*\.", r"\1", t)
    t = re.sub(r",\s*([.!?])", r"\1", t)
    t = re.sub(r"^[,.\s]+", "", t)
    # A sentence break we inserted should start the next word like a sentence.
    t = re.sub(r"([.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), t)
    return t.strip()


def normalise(text: str) -> str:
    """Turn display prose into something a speech engine reads correctly."""
    if not text:
        return ""
    t = text

    # Emphasis markers are for the eye. Keep the word, lose the asterisk.
    t = re.sub(r"\*+", "", t)

    # A trailing em-dash is a line cut off mid-thought. Spoken, the cut is the
    # silence that follows; any punctuation we substitute is read as content.
    t = re.sub(r"\s*—\s*$", "", t.strip())

    # Wino-T's bars are slash-separated. Each slash is a break he performs.
    t = re.sub(r"\s+/\s+", ". ", t)

    # 3.331 -> three point three three one (a price that is really a timestamp)
    t = re.sub(r"\b(\d+)\.(\d+)\b", _spell_decimal, t)
    # 2-F -> 2 F, so it is not read as a subtraction
    t = re.sub(r"\b(\d+)-([A-Z])\b", r"\1 \2", t)

    # All-caps runs -> sentence case, before any other word surgery. Two-letter
    # words must be inside the run or "THANK YOU FOR YOUR PATIENCE" breaks at
    # the short word and leaves a shouted "WE" behind.
    t = re.sub(rf"\b[{_UPPER}][{_UPPER}'’]+(?:\s+[{_UPPER}'’&]+)*\b", _decaps, t)

    t = t.replace("&", " and ")

    # Italian yes: espeak reads the accented form unreliably in an en voice.
    t = re.sub(r"\bS[iì]\b", "See", t)
    t = re.sub(r"\bs[iì]\b", "see", t)

    # Em-dash mid-sentence is a beat, not a word.
    t = re.sub(r"\s*—\s*", ", ", t)

    # Ellipsis: keep a pause, drop the dots espeak may enumerate.
    t = re.sub(r"\.{3,}", ", ", t)

    # Quotes carry nothing audible.
    t = re.sub(r"[\"“”]", " ", t)

    # Blank lines are paragraph breaks: a real pause.
    t = re.sub(r"\n\s*\n", ". ", t)
    t = t.replace("\n", " ")

    return _tidy(t)


# ------------------------------------------------------------------ registry

def _load_registry() -> dict:
    global _registry
    if _registry:
        return _registry
    try:
        _registry = json.loads(CONTENT.read_text(encoding="utf-8"))
    except Exception:
        _registry = {}
    return _registry


def spec_for(who: str, attribute: str | None = None) -> dict | None:
    """Resolve a speaker id to a concrete synthesis spec."""
    reg = _load_registry()
    if not reg:
        return None
    base = dict(reg.get("_defaults", {}))
    if attribute:
        entry = (reg.get("_attributes") or {}).get(attribute)
    else:
        entry = reg.get(who)
    if not isinstance(entry, dict):
        entry = reg.get("narrator") if who != "narrator" else None
        if not isinstance(entry, dict):
            return None
    base.update({k: v for k, v in entry.items() if not k.startswith("_") and k != "note"})
    return base


# ------------------------------------------------------------------ playback

def _find_player() -> list[str] | None:
    for cmd in (["paplay"], ["aplay", "-q"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]):
        if shutil.which(cmd[0]):
            return cmd
    return None


def _cache_path(spec: dict, text: str) -> Path:
    key = json.dumps({"s": spec, "t": text}, sort_keys=True)
    return CACHE_DIR / (hashlib.sha1(key.encode()).hexdigest()[:20] + ".wav")


def _get_model(name: str):
    if name in _models:
        return _models[name]
    from piper import PiperVoice          # imported late: optional dependency
    path = VOICE_DIR / f"{name}.onnx"
    if not path.exists():
        from piper.download_voices import download_voice
        VOICE_DIR.mkdir(parents=True, exist_ok=True)
        download_voice(name, VOICE_DIR)
    _models[name] = PiperVoice.load(path)
    return _models[name]


def _synthesise(spec: dict, text: str, out: Path) -> bool:
    try:
        from piper import SynthesisConfig
        voice = _get_model(spec["model"])
        cfg = SynthesisConfig(
            speaker_id=spec.get("speaker"),
            length_scale=spec.get("length_scale"),
            noise_scale=spec.get("noise_scale"),
            noise_w_scale=spec.get("noise_w"),
        )
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".part")
        with open(tmp, "wb") as fh:
            import wave
            with wave.open(fh, "wb") as wf:
                voice.synthesize_wav(text, wf, syn_config=cfg)
        tmp.replace(out)
        return True
    except Exception:
        return False


def _run() -> None:
    global _current
    while True:
        item = _queue.get()
        if item is None:
            return
        spec, text = item
        try:
            if _skip.is_set():
                continue          # a skip landed while this was still queued
            path = _cache_path(spec, text)
            if not path.exists():
                if not _synthesise(spec, text, path):
                    continue
            if _player and not _skip.is_set():
                # Popen rather than run: the player has to stay killable, or
                # skipping ahead leaves the previous line talking over the next
                # screen for several seconds.
                with _lock:
                    _current = subprocess.Popen(
                        _player + [str(path)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                proc = _current
                proc.wait()
                with _lock:
                    if _current is proc:
                        _current = None
        except Exception:
            pass
        finally:
            _queue.task_done()


def stop() -> None:
    """Cut playback now and drop anything queued behind it.

    Called whenever the player moves on — a keypress, a menu choice, a new
    scene. Audio that describes the previous screen is worse than no audio.
    """
    global _current
    if not _enabled:
        return
    _skip.set()
    try:
        while True:
            try:
                _queue.get_nowait()
                _queue.task_done()
            except queue.Empty:
                break
        with _lock:
            proc, _current = _current, None
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=0.4)
            except Exception:
                proc.kill()
    except Exception:
        pass
    finally:
        _skip.clear()


# -------------------------------------------------------------------- public

def enable(on: bool = True) -> bool:
    """Turn voice on. Returns whether it actually came up."""
    global _enabled, _queue, _worker, _player
    if not on:
        _enabled = False
        return False
    try:
        import piper  # noqa: F401
    except Exception:
        return False
    if not _load_registry():
        return False
    _player = _find_player()
    _queue = queue.Queue(maxsize=64)
    _worker = threading.Thread(target=_run, daemon=True)
    _worker.start()
    _enabled = True
    return True


def enabled() -> bool:
    return _enabled


def say(who: str, text: str, attribute: str | None = None) -> None:
    """Queue a line. Never blocks, never raises, no-op when disabled."""
    if not _enabled or not text:
        return
    spec = spec_for(who, attribute)
    if not spec:
        return
    spoken = normalise(text)
    if not spoken:
        return
    try:
        _queue.put_nowait((spec, spoken))
    except Exception:
        pass          # full queue: drop the line rather than stall the game


def wait(timeout: float | None = None) -> None:
    if _enabled and _queue is not None:
        try:
            _queue.join()
        except Exception:
            pass


def shutdown() -> None:
    global _enabled
    _enabled = False
    if _queue is not None:
        try:
            _queue.put_nowait(None)
        except Exception:
            pass
