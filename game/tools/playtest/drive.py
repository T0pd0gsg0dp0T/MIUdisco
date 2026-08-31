#!/usr/bin/env python3
"""Plain-pipe regression driver for MIUdisco, replacing the lost pty harness.

The game's non-interactive path (ui.interactive() False whenever stdin/stdout
aren't ttys) already routes every prompt -- character creation, the command
loop, object checks, dialogue -- through plain input()/print() with numbered
menus, confirmed against main.py/ui.py directly. A background reader thread
does the blocking os.read() continuously so it can never interact badly with
the writer loop's timing (an earlier select()-based pump_output stalled
inexplicably in this sandbox); the writer just paces itself with a fixed
sleep between scripted lines.
"""
import os
import subprocess
import sys
import threading
import time

GAME_DIR = "/home/t0nt0n/MIUdisco/game"
SEED = sys.argv[1] if len(sys.argv) > 1 else "9042"
LOGFILE = sys.argv[2] if len(sys.argv) > 2 else "custom_run.log"
STEP_DELAY = float(sys.argv[3]) if len(sys.argv) > 3 else 1.2

CREATION = [
    "5",
    "4", "4", "4", "4", "4", "3", "3", "3",
    "4", "2", "4", "3", "4", "4", "4", "1",
    "4", "1",
    "1",
    "",
]

TOUR = [
    "survey",
    "examine hands", "1",
    "examine wreck", "1",
    "examine effects", "1",
    "examine harbour_wall", "1",
    "sheet",
    "go durry_kwain",
    "survey", "who",
    "go dudes_dews",
    "survey", "who",
    "go hang_hi",
    "survey", "who",
    "go gs_spot",
    "survey", "who",
    "go lishush_mush",
    "survey", "who",
    "go cheeses_thrice",
    "survey", "who",
    "go giddyup",
    "survey", "who",
    "go outside_inn",
    "survey", "who",
    "go mobius",
    "survey", "who",
    "go rest_assured",
    "survey", "who",
    "sheet",
    "log",
    "case",
    # `cabinet` opens its own submenu ("Dwell on one of them?") whenever a
    # thought is known and a slot is free. It takes allow_blank, so the blank
    # line below dismisses it; without it the NEXT scripted command is eaten
    # as an answer to that menu and everything after desynchronises.
    "cabinet",
    "",
    "save custom_checkpoint",
]

SCRIPT = CREATION + TOUR

proc = subprocess.Popen(
    ["python3", "main.py", "--seed", SEED],
    cwd=GAME_DIR,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    bufsize=0,
)

log = open(LOGFILE, "w", encoding="utf-8")
log_lock = threading.Lock()
start = time.time()
out_fd = proc.stdout.fileno()
stop_reader = threading.Event()


def reader():
    while not stop_reader.is_set():
        try:
            chunk = os.read(out_fd, 65536)
        except OSError:
            break
        if not chunk:
            break
        with log_lock:
            log.write(chunk.decode("utf-8", "replace"))
            log.flush()


t = threading.Thread(target=reader, daemon=True)
t.start()

time.sleep(2.0)
for i, line in enumerate(SCRIPT):
    print(f"[{time.time()-start:6.1f}s] step {i}/{len(SCRIPT)}: {line!r}", flush=True)
    if proc.poll() is not None:
        with log_lock:
            log.write(f"\n[DRIVER] process exited early at step {i} ({line!r}), code={proc.returncode}\n")
        print(f"EXITED EARLY at step {i}, code={proc.returncode}", flush=True)
        break
    try:
        proc.stdin.write((line + "\n").encode())
        proc.stdin.flush()
    except BrokenPipeError:
        with log_lock:
            log.write(f"\n[DRIVER] broken pipe at step {i} ({line!r})\n")
        print(f"BROKEN PIPE at step {i}", flush=True)
        break
    time.sleep(STEP_DELAY)

try:
    proc.stdin.close()
except Exception:
    pass

try:
    proc.wait(timeout=15)
except subprocess.TimeoutExpired:
    proc.kill()
    with log_lock:
        log.write("\n[DRIVER] killed after timeout waiting for exit\n")

time.sleep(1.0)
stop_reader.set()
t.join(timeout=2)

elapsed = time.time() - start
with log_lock:
    log.write(f"\n[DRIVER] elapsed={elapsed:.1f}s exit_code={proc.returncode}\n")
    log.close()
print(f"done elapsed={elapsed:.1f}s exit_code={proc.returncode}")
