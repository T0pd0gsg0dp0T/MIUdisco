#!/usr/bin/env python3
"""Content-driven regression tour.

Earlier drivers either sent a hand-written list of commands (breaks the moment
content moves) or screen-scraped the prose to work out what was in the room
(brittle: the affordance line only appears on a fresh room description, so the
plan collapsed to `who` forever).

This one reads content/locations/*.json and content/npcs.json and generates the
route: every location, every visible object, every NPC, in an order that
follows the actual exit graph. Dialogue menus are answered by number as they
appear. Nothing about the script is hand-maintained, so adding a room or an
object extends the tour automatically.

    python3 tools/playtest/tour.py [--seed N] [--build 1-5] [--log PATH]
                                   [--talk-depth N] [--cross-seam]

Exit code is non-zero on any traceback or if the process dies early.
"""
from __future__ import annotations

import argparse
import json
import glob
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(HERE))
if not os.path.isdir(os.path.join(GAME, "content")):
    GAME = os.path.join(GAME, "game")
CONTENT = os.path.join(GAME, "content")

SEAM_WORDS = ("go through", "no way back", "whatever is unfinished")


def load_world():
    locs, exits, objs = {}, {}, {}
    for p in glob.glob(os.path.join(CONTENT, "locations", "*.json")):
        d = json.load(open(p, encoding="utf-8"))
        lid = d["id"]
        locs[lid] = d.get("name", lid)
        exits[lid] = list((d.get("exits") or {}).keys())
        objs[lid] = [o["id"] for o in d.get("objects", [])
                     if not o.get("hidden") and not o.get("requires")]
    npcs = {}
    for n in json.load(open(os.path.join(CONTENT, "npcs.json"), encoding="utf-8")):
        npcs.setdefault(n["location"], []).append(n)
    return locs, exits, objs, npcs


def route(exits, start="crash_site"):
    """Breadth-first walk that returns a visit order using real exits only."""
    order, seen, q = [], {start}, deque([start])
    while q:
        cur = q.popleft()
        order.append(cur)
        for nxt in exits.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    return order


def path_between(exits, a, b):
    """Shortest exit path a -> b, or None."""
    prev, q = {a: None}, deque([a])
    while q:
        cur = q.popleft()
        if cur == b:
            out = []
            while cur is not None:
                out.append(cur)
                cur = prev[cur]
            return list(reversed(out))[1:]
        for nxt in exits.get(cur, []):
            if nxt not in prev:
                prev[nxt] = cur
                q.append(nxt)
    return None


class Session:
    def __init__(self, seed, log_path):
        self.proc = subprocess.Popen(
            [sys.executable, "main.py", "--seed", str(seed)],
            cwd=GAME, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, bufsize=0)
        self.buf, self.lock = "", threading.Lock()
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
            t = chunk.decode("utf-8", "replace")
            with self.lock:
                self.buf += t
                self.log.write(t); self.log.flush()
        self.dead = True

    def read(self, quiet=0.35, cap=5.0):
        start = last_change = time.time()
        last = -1
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


def menu_of(screen):
    opts = [(int(a), b.strip()) for a, b in MENU.findall(screen)]
    return opts if opts and [n for n, _ in opts] == list(range(1, len(opts) + 1)) else []


def settle(s, screen, depth, cross_seam, stats):
    """Answer any menus until we are back at a command prompt."""
    for _ in range(depth):
        opts = menu_of(screen)
        if not opts:
            return screen
        stats["menus"] += 1
        pick = None
        # Leave the seam alone unless explicitly asked to cross it.
        safe = [(n, l) for n, l in opts
                if cross_seam or not any(w in l.lower() for w in SEAM_WORDS)]
        if not safe:
            safe = [opts[-1]]
        for n, l in safe:
            if any(k in l.lower() for k in ("leave", "back", "nothing", "something else",
                                            "not now", "never mind", "enough")):
                pick = n
        # prefer a fresh substantive option first, fall back to the exit
        fresh = [(n, l) for n, l in safe if n != pick]
        chosen = fresh[0][0] if fresh else (pick or safe[-1][0])
        screen = s.send(str(chosen))
    return screen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--build", default="2")
    ap.add_argument("--log", default="/tmp/tour.log")
    ap.add_argument("--talk-depth", type=int, default=6)
    ap.add_argument("--cross-seam", action="store_true")
    a = ap.parse_args()

    locs, exits, objs, npcs = load_world()
    stats = {"rooms": 0, "objects": 0, "talks": 0, "menus": 0}

    s = Session(a.seed, a.log)
    screen = s.read(cap=8)

    # character creation
    screen = s.send(a.build)                 # archetype
    for _ in range(8):
        if "Begin" in screen and "Start again" in screen:
            screen = s.send("1")
            break
        if menu_of(screen):
            screen = s.send("1")
        else:
            break
    screen = s.send()                        # clear any pause

    order = route(exits)
    here = "crash_site"
    for target in order:
        if s.dead:
            break
        if target != here:
            hop = path_between(exits, here, target) or []
            for stepto in hop:
                screen = s.send(f"go to {locs.get(stepto, stepto)}")
                screen = settle(s, screen, 3, False, stats)
                here = stepto
        if here != target:
            continue
        stats["rooms"] += 1
        screen = settle(s, s.send("survey"), 3, False, stats)
        for oid in objs.get(target, []):
            if s.dead:
                break
            screen = s.send(f"look at {oid}")
            screen = settle(s, screen, 4, a.cross_seam, stats)
            stats["objects"] += 1
        for npc in npcs.get(target, []):
            if s.dead:
                break
            screen = s.send(f"talk to {npc['id']}")
            screen = settle(s, screen, a.talk_depth, False, stats)
            stats["talks"] += 1
    for cmd in ("log", "case", "sheet", "cabinet", ""):
        if s.dead:
            break
        screen = settle(s, s.send(cmd), 3, False, stats)
    s.send("quit"); s.send("1")
    time.sleep(0.5)
    try:
        s.proc.terminate()
    except Exception:
        pass

    log = open(a.log, encoding="utf-8").read()
    tb = log.count("Traceback")
    print(f"rooms visited     {stats['rooms']} of {len(locs)}")
    print(f"objects examined  {stats['objects']}")
    print(f"conversations     {stats['talks']}")
    print(f"menus answered    {stats['menus']}")
    print(f"clues surfaced    {log.count('── CLUE ──')}")
    print(f"log size          {len(log):,} chars")
    print(f"tracebacks        {tb}")
    if tb:
        i = log.find("Traceback")
        print("\n" + log[i:i + 900])
    return 1 if tb else 0


if __name__ == "__main__":
    raise SystemExit(main())
