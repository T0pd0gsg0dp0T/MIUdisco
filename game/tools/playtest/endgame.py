#!/usr/bin/env python3
"""Endgame regression: cross the seam and drive each ending to its epilogue.

The seam is gated on the `awakening` beat and lucidity >= 70, which a bounded
automated tour does not reliably reach — so no tour has ever exercised the
office, the confrontation, or the four endings. That is the one region of the
game the content passes never regression-tested.

This builds the qualifying state directly (every clue the content can grant,
full lucidity, standing at a seam), saves it, and then plays from that save:
through the seam, through Revilo, to a chosen ending and its epilogue.

The state is constructed rather than played into. That is deliberate and worth
being clear about: this tests the *ending content and its gates*, not the route
a player takes to get there.

    python3 tools/playtest/endgame.py --ending wake|stay|together|nevermind|all
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
if not os.path.isdir(os.path.join(GAME, "content")):
    GAME = os.path.join(GAME, "game")
sys.path.insert(0, GAME)

# Which option text identifies each ending at the final choice.
ENDING_PICK = {
    "wake": ("finish the sentence yourself",),
    "stay": ("let him finish it",),
    "together": ("two chairs",),
    # "say nothing" alone also matches an option at arg_three
    # ("Say nothing at all, for a long time"), which is a different branch.
    "nevermind": ("let the elephant",),
}
CONFIRM = ("do it", "sit down", "push the chair", "recommend company", "wait",
           "finish the sentence")


def build_save(slot: str, where: str = "hang_hi") -> dict:
    """Construct a state that qualifies for the seam, and save it."""
    os.chdir(GAME)
    from game_state import GameState
    from investigation import Clue

    st = GameState()
    st.location_id = where
    st.player.name_known = True
    st.player.lucidity = 100
    for attr in ("INTELLECT", "PSYCHE", "FORTITUDE", "MOTORICS"):
        st.player.set_attribute(attr, 6)

    # Grant every clue the content defines, so every gated ending option and
    # every tag_count threshold is satisfied and can be exercised.
    granted = 0
    for p in glob.glob(os.path.join(GAME, "content", "**", "*.json"), recursive=True):
        data = json.load(open(p, encoding="utf-8"))

        def walk(node):
            nonlocal granted
            if isinstance(node, dict):
                spec = node.get("clue")
                if isinstance(spec, dict) and "id" in spec:
                    if st.investigation.add_clue(Clue(
                        id=spec["id"], title=spec.get("title", ""),
                        text=spec.get("text", ""), beat=spec.get("beat"),
                        tags=spec.get("tags", []), source=spec.get("source", ""),
                    )):
                        granted += 1
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
        walk(data)

    # Thought + relationships that some ending options require.
    st.player.thoughts_internalised.append("and_furthermore")
    # Beats are derived from evidence, not stored: the game recomputes them on
    # entering a location. Do it here too so the reported state is the state
    # the game will actually see.
    st.investigation.check_beats()
    for npc_id in st.npcs.npcs:
        st.npcs.adjust(npc_id, 4)
    st.save(slot)
    return {
        "clues": granted,
        "beats": list(st.investigation.beats_reached),
        "lucidity": st.player.lucidity,
    }


class Session:
    def __init__(self, slot, log_path):
        self.proc = subprocess.Popen(
            [sys.executable, "main.py", "--load", slot, "--seed", "31337"],
            cwd=GAME, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0)
        self.buf, self.lock, self.dead = "", threading.Lock(), False
        self.log = open(log_path, "w", encoding="utf-8")
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        fd = self.proc.stdout.fileno()
        while True:
            try:
                c = os.read(fd, 65536)
            except OSError:
                break
            if not c:
                break
            t = c.decode("utf-8", "replace")
            with self.lock:
                self.buf += t
                self.log.write(t); self.log.flush()
        self.dead = True

    def read(self, quiet=0.3, cap=6.0):
        start = last_change = time.time(); last = -1
        while time.time() - start < cap:
            with self.lock:
                n = len(self.buf)
            if n != last:
                last, last_change = n, time.time()
            elif time.time() - last_change >= quiet:
                break
            time.sleep(0.04)
        with self.lock:
            out, self.buf = self.buf, ""
        return out

    def send(self, line=""):
        if self.dead:
            return ""
        try:
            self.proc.stdin.write((line + "\n").encode())
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError):
            self.dead = True
            return ""
        return self.read()


MENU = re.compile(r"^\s*(\d+)\.\s+(.+)$", re.M)


def menu(screen):
    o = [(int(a), b.strip()) for a, b in MENU.findall(screen)]
    return o if o and [n for n, _ in o] == list(range(1, len(o) + 1)) else []


def pick_matching(opts, needles):
    for n, l in opts:
        if any(w in l.lower() for w in needles):
            return n, l
    return None, None


def play(ending: str, slot: str, log_path: str) -> dict:
    s = Session(slot, log_path)
    s.read(cap=8)
    out = {"ending": ending, "crossed": False, "reached": False,
           "epilogue": False, "traceback": False}

    scr = s.send("look at seam")
    for _ in range(4):                      # yes -> irreversible confirm -> yes
        opts = menu(scr)
        if not opts:
            break
        n, _l = pick_matching(opts, ("yes", "go through"))
        scr = s.send(str(n if n else opts[0][0]))
    out["crossed"] = "nine feet by eleven" in scr.lower() or "the office" in scr.lower()

    scr = s.send("talk to revilo")
    for _ in range(40):
        opts = menu(scr)
        if not opts:
            scr = s.send("talk to revilo")
            if not menu(scr):
                break
            continue
        n, lab = pick_matching(opts, ENDING_PICK[ending])
        if n:
            out["reached"] = True
            scr = s.send(str(n))
            c = menu(scr)
            if c:
                cn, _ = pick_matching(c, CONFIRM)
                scr = s.send(str(cn if cn else c[0][0]))
            break
        # otherwise take the first substantive option to advance the argument
        scr = s.send(str(opts[0][0]))

    for _ in range(8):                      # page through the epilogue
        scr = s.send()
        if "Clues found" in scr or "Beats reached" in scr:
            out["epilogue"] = True
            break
    time.sleep(0.4)
    try:
        s.proc.terminate()
    except Exception:
        pass
    log = open(log_path, encoding="utf-8").read()
    out["traceback"] = "Traceback" in log
    out["log_chars"] = len(log)
    for key, pat in (("coda", r"You went and got the language|You gave the last word|"
                              r"Neither of you got the last word|The sentence never got finished"),):
        out[key] = bool(re.search(pat, log))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ending", default="all")
    ap.add_argument("--where", default="hang_hi")
    a = ap.parse_args()

    info = build_save("endgame_test", a.where)
    print(f"constructed save: {info['clues']} clues, lucidity {info['lucidity']}")
    print(f"beats reached: {', '.join(info['beats']) or '(none)'}\n")

    endings = list(ENDING_PICK) if a.ending == "all" else [a.ending]
    rows = []
    for e in endings:
        build_save("endgame_test", a.where)          # fresh state per ending
        r = play(e, "endgame_test", f"/tmp/ending_{e}.log")
        rows.append(r)
        print(f"{e:<10} crossed={str(r['crossed']):<5} option={str(r['reached']):<5} "
              f"epilogue={str(r['epilogue']):<5} coda={str(r['coda']):<5} "
              f"tb={str(r['traceback']):<5} {r['log_chars']:>7} chars")
    bad = [r for r in rows if r["traceback"] or not r["epilogue"]]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
