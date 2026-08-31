# Playtest harness

Regression drivers that play the actual game end to end. **These live in the
repo on purpose.** Earlier versions were kept in a scratch directory, got wiped
between sessions, and were rebuilt from scratch four times. Do not move them
back out.

## drive.py

Plain-pipe driver. Runs `main.py` under `subprocess.Popen` with piped stdio and
a background reader thread, feeding it a scripted list of inputs.

```bash
cd /home/t0nt0n/MIUdisco/game
python3 tools/playtest/drive.py [seed] [logfile] [step_delay]
```

It works because the game degrades gracefully when it is not attached to a
terminal: `ui.interactive()` returns False whenever stdin/stdout are not ttys,
and every prompt — character creation, the command loop, object checks,
dialogue — falls back to plain `input()` with numbered menus.

That fallback is also this driver's one real limitation: **it does not exercise
the interactive UI a human actually sees** (scroll regions, raw-mode keys,
arrow-key menus). It proves the content and state machine are sound. It does
not prove the renderer is. A pty-based harness driving the real UI is the
complement to this, not a duplicate of it.

### Gotchas worth not rediscovering

- `cabinet` opens a submenu ("Dwell on one of them?") when a thought is known
  and a slot is free. It accepts a blank line to dismiss. Send one, or the next
  scripted command gets eaten as an answer to that menu and every input after
  it desynchronises. The same applies to any command that can branch into a
  menu conditionally.
- Character-creation keystrokes are position-dependent: the attribute menu
  filters out any attribute already at the ceiling, so the option list shortens
  as you spend. Derive the sequence from `character_creation.py` rather than
  guessing.
- Give the process ~2s to start before the first write, and pace steps ~1.2s
  apart. Reading with a blocking background thread rather than `select()` in
  the writer loop avoids a stall seen under sandboxed execution.

## Checks to run after content edits

```bash
python3 -m pytest tools/test_mechanics.py -q   # 85 tests
python3 tools/validate_content.py              # 0 errors, 2 known warnings
python3 tools/voice_lint.py                    # narration rules
```

The two standing validator warnings are by design: `crash_site -> durry_kwain`
is a one-way exit, and `the_office` deliberately has none.
