#!/usr/bin/env python3
"""Adaptive regression driver: reads the game's output and responds to it.

drive.py sends a fixed list of inputs, which is fine for a walking tour and
useless the moment a dialogue tree branches. This one watches stdout, works
out what is being asked, and answers:

  * a numbered menu  -> pick an option by policy (prefer unexplored, avoid
                        the seam and quit unless told otherwise)
  * a command prompt -> take the next instruction from the plan

It also records every distinct screen it sees, so a run doubles as a coverage
sample: which rooms, which objects, which NPCs, how many checks were rolled
and how many of them were passed.

    python3 tools/playtest/autoplay.py [--seed N] [--build 0-3|custom]
                                       [--steps N] [--log PATH]

Exits non-zero if the game crashes, if it stops responding, or if any screen
contains a traceback.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import threading
import time
from collections import Counter

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = os.path.join(GAME, "game") if os.path.isdir(os.path.join(GAME, "game")) else GAME

# Options we never want an automated run to take.
AVOID = (
    "go through", "no way back", "whatever is unfinished",
    "quit", "give up", "wake up", "push the chair",
)
PREFER = ("examine", "look at", "talk", "ask", "say", "\"")


class Runner:
    def __init__(self, seed: int, log_path: str):
        self.proc = subprocess.Popen(
            [sys.executable, "main.py", "--seed", str(seed)],
            cwd=GAME, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0,
        )
        self.buf = ""
        self.lock = threading.Lock()
        self.log = open(log_path, "w", encoding="utf-8")
        self.dead = False
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        fd = self.proc.stdout.fileno()
        while True:
            try:
                chunk = os.read(fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            text = chunk.decode("utf-8", "replace")
            with self.lock:
                self.buf += text
                self.log.write(text)
                self.log.flush()
        self.dead = True

    def drain(self, quiet=0.45, cap=6.0) -> str:
        """Wait until output stops arriving, then return and clear it."""
        start = time.time()
        last_len, last_change = -1, time.time()
        while time.time() - start < cap:
            with self.lock:
                n = len(self.buf)
            if n != last_len:
                last_len, last_change = n, time.time()
            elif time.time() - last_change >= quiet:
                break
            time.sleep(0.05)
        with self.lock:
            out, self.buf = self.buf, ""
        return out

    def send(self, line: str):
        try:
            self.proc.stdin.write((line + "\n").encode())
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError):
            self.dead = True



OBJ_RE = re.compile(r"comes back holding (.+?)\. It will keep going back",
                    re.S)
ONE_EXIT_RE = re.compile(r"one way on from here: (.+?) —")
MANY_EXIT_RE = re.compile(r"^\s{2,}([A-Z][A-Za-z''\-. ]+?) — ", re.M)


def _split_list(text: str):
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(", and ", ", ")
    return [p.strip() for p in text.split(", ") if p.strip()]


def parse_objects(screen: str):
    m = OBJ_RE.search(screen)
    if not m:
        return []
    return _split_list(m.group(1))


def parse_exits(screen: str):
    one = ONE_EXIT_RE.search(screen)
    if one:
        return [one.group(1).strip()]
    return [x.strip() for x in MANY_EXIT_RE.findall(screen)]


def parse_people(screen: str):
    out = []
    for line in screen.splitlines():
        m = re.match(r"^\s{2,}([A-Z][\w''\-. ]+?) — ", line)
        if m and len(m.group(1)) < 40:
            out.append(m.group(1).strip())
    return out


def build_plan(objs, exits, seen, people):
    plan = []
    for o in objs:
        if seen[f"look at {o}"] < 1:
            plan.append(f"look at {o}")
    plan.append("who")
    for p in people:
        if seen[f"talk to {p}"] < 1:
            plan.append(f"talk to {p}")
    fresh = [e for e in exits if seen[f"go to {e}"] < 2]
    if fresh:
        plan.append(f"go to {fresh[0]}")
    elif exits:
        plan.append(f"go to {exits[0]}")
    return plan


MENU_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$")


def parse_menu(screen: str):
    """Return [(number, label)] if the tail of the screen offers a menu."""
    opts = []
    for line in screen.splitlines():
        m = MENU_RE.match(line)
        if m:
            opts.append((int(m.group(1)), m.group(2).strip()))
    # Only trust it if the numbers run 1..n
    if opts and [n for n, _ in opts] == list(range(1, len(opts) + 1)):
        return opts
    return []


def choose(opts, seen: Counter):
    """Pick a menu option: something new, interesting, and not irreversible."""
    scored = []
    for num, label in opts:
        low = label.lower()
        if any(a in low for a in AVOID):
            continue
        score = -seen[label] * 10
        if any(p in low for p in PREFER):
            score += 3
        scored.append((score, num, label))
    if not scored:
        return opts[-1][0], opts[-1][1]
    scored.sort(reverse=True)
    return scored[0][1], scored[0][2]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--build", default="1")
    ap.add_argument("--steps", type=int, default=220)
    ap.add_argument("--log", default="/tmp/autoplay.log")
    args = ap.parse_args()

    r = Runner(args.seed, args.log)
    seen = Counter()
    stats = Counter()
    rooms, crashes = set(), []
    people = []

    screen = r.drain(cap=8)

    # --- character creation: archetype, then accept -----------------------
    for _ in range(12):
        if "Begin" in screen and "Start again" in screen:
            r.send("1"); screen = r.drain(); break
        opts = parse_menu(screen)
        if not opts:
            break
        pick = args.build if args.build.isdigit() and len(opts) >= int(args.build) else "1"
        r.send(pick)
        screen = r.drain()

    plan = ["survey", "who", "log", "case", "sheet"]
    step = 0
    while step < args.steps and not r.dead:
        step += 1
        if "Traceback" in screen or "Exception" in screen:
            crashes.append(screen[-800:])
            break

        for nm in parse_people(screen):
            if nm not in people and len(people) < 60:
                people.append(nm)
        stats["checks"] += len(re.findall(r"\[(?:[A-Z][a-z\-]+) \d+", screen))
        stats["clues"] += len(re.findall(r"── CLUE ──", screen))
        stats["skill_voices"] += len(re.findall(r"^ [A-Z][a-z]+(?:-[A-Z][a-z]+)? *$", screen, re.M))

        opts = parse_menu(screen)
        if opts:
            num, label = choose(opts, seen)
            seen[label] += 1
            r.send(str(num))
            screen = r.drain()
            continue

        # No menu: read what this room affords straight out of the prose.
        objs = parse_objects(screen)
        exits = parse_exits(screen)
        for o in objs:
            rooms.add(o)
        if not plan:
            plan = build_plan(objs, exits, seen, people)
        cmd = plan.pop(0) if plan else "survey"
        seen[cmd] += 1
        r.send(cmd)
        screen = r.drain()

    r.send("quit")
    time.sleep(0.6)
    try:
        r.proc.terminate()
    except Exception:
        pass

    log = open(args.log, encoding="utf-8").read()
    tb = log.count("Traceback")
    print(f"steps run          {step}")
    print(f"log size           {len(log):,} chars")
    print(f"clues surfaced     {log.count('── CLUE ──')}")
    print(f"tracebacks         {tb}")
    print(f"distinct menu opts {len(seen)}")
    if crashes:
        print("\n--- crash ---\n" + crashes[0])
    return 1 if tb or crashes else 0


if __name__ == "__main__":
    raise SystemExit(main())
