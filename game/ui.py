"""Terminal presentation layer.

Design note: this uses plain ANSI escapes on stdout rather than curses.
Curses gives a fixed-size viewport with no native scrollback, which is
actively hostile to a game whose primary content is long prose the player
wants to scroll back through. A wrapped, colourised stdout stream costs
less CPU than a curses refresh loop and lets the terminal do the scrolling
it is already good at.

Every visual element in the game is a "channel" - narration, a skill voice,
Furthermore, an NPC line - and each channel has one consistent look so the
player can parse a dense screen at a glance.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import textwrap
import time

from config import CONFIG
import voice

# --- colour ----------------------------------------------------------------

RESET = "\033[0m"

# 256-colour codes chosen for the palette the source material insists on:
# perpetual twilight in deep purples and crimsons, green flame, gold.
PALETTE = {
    "narration": "\033[38;5;253m",   # bone white, the default voice
    "dim": "\033[38;5;244m",         # stage directions, mechanical asides
    "purple": "\033[38;5;141m",      # Furthermore, and Oliver's tux
    "gold": "\033[38;5;179m",        # the monocle, clues, discoveries
    "green": "\033[38;5;108m",       # lamppost flame, the vest, success
    "crimson": "\033[38;5;131m",     # failure, the sky, C.C.C.C.
    "cyan": "\033[38;5;109m",        # NPC speech
    "white": "\033[38;5;231m",       # emphasis
    "invert": "\033[38;5;114m",      # Revilo: green with purple accents
}

STYLE_BOLD = "\033[1m"
STYLE_ITALIC = "\033[3m"


def _color_enabled() -> bool:
    """Respect NO_COLOR, dumb terminals, pipes, and the config override."""
    setting = CONFIG["display"]["color"]
    if setting == "never":
        return False
    if setting == "always":
        return True
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM", "") in ("", "dumb"):
        return False
    return sys.stdout.isatty()


COLOR = _color_enabled()


def paint(text: str, *codes: str) -> str:
    """Wrap `text` in the given escape codes, or return it bare."""
    if not COLOR or not codes:
        return text
    return "".join(codes) + text + RESET


def width() -> int:
    """Wrap width: the configured value, clamped to the real terminal."""
    configured = CONFIG["display"]["wrap_width"]
    try:
        actual = shutil.get_terminal_size().columns
    except OSError:
        actual = 80
    return max(40, min(configured, actual - 2))


# --- low-level emission ----------------------------------------------------

def _emit(text: str) -> None:
    """Write text, optionally as a typewriter crawl.

    The crawl is off by default. When enabled it is deliberately implemented
    with a per-character sleep rather than a timer thread: this game is
    strictly turn-based and must not spin a CPU on a laptop.
    """
    speed = CONFIG["display"]["crawl_speed"]
    if speed <= 0:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
        return
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(speed)
    sys.stdout.write("\n")


def blank(count: int = 1) -> None:
    for _ in range(count):
        sys.stdout.write("\n")
    sys.stdout.flush()


def _wrap(text: str, indent: str = "", subsequent: str | None = None) -> list[str]:
    """Wrap a paragraph, preserving deliberate blank-line breaks."""
    if subsequent is None:
        subsequent = indent
    lines: list[str] = []
    for para in text.split("\n\n"):
        para = " ".join(para.split())
        if not para:
            continue
        lines.extend(
            textwrap.wrap(
                para,
                width=width(),
                initial_indent=indent,
                subsequent_indent=subsequent,
            )
            or [indent]
        )
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


# --- channels --------------------------------------------------------------

def narrate(text: str) -> None:
    """Second-person narration. The game's default voice.

    Callers are responsible for the perspective; tools/voice_lint.py enforces
    it across the content files.
    """
    voice.say("narrator", text)
    for line in _wrap(text):
        _emit(paint(line, PALETTE["narration"]))
    blank(CONFIG["display"]["paragraph_gap"])


def aside(text: str) -> None:
    """Mechanical or parenthetical information, visually recessed."""
    for line in _wrap(text, indent="  "):
        _emit(paint(line, PALETTE["dim"], STYLE_ITALIC))
    blank()


def block(text: str, colour_key: str = "dim") -> None:
    """Emit pre-formatted lines verbatim, without re-wrapping.

    `aside` and `narrate` reflow their input, which is right for prose and
    destroys anything column-aligned. Sheets, logs and status bars go here.
    """
    for line in text.split("\n"):
        _emit(paint("  " + line, PALETTE[colour_key]))
    blank()


def skill_voice(skill_name: str, text: str, success: bool = True) -> None:
    """A skill speaking in its own right - the load-bearing Disco Elysium idiom.

    The skill name is a labelled speaker, not a die-roll report. A failed
    passive check still speaks; it simply says something wrong or partial,
    which is what makes an unreliable narrator out of the player's own mind.
    """
    from skill_checks import SKILL_ATTRIBUTE
    voice.say("oliver", text, attribute=SKILL_ATTRIBUTE.get(skill_name))
    colour = PALETTE["green"] if success else PALETTE["crimson"]
    label = skill_name.replace("_", "-").title()
    header = paint(f"{label}", colour, STYLE_BOLD)
    body = _wrap(text, indent="   ", subsequent="   ")
    _emit(f" {header}")
    for line in body:
        _emit(paint(line, PALETTE["narration"]))
    blank()


#: What the elephant is called before the player learns his name. Set by
#: game_state once the thought that names him has been picked up - until
#: then he is exactly what he looks like, which is the point.
ELEPHANT_LABEL = ["the elephant"]


def name_the_elephant(name: str = "Furthermore") -> None:
    ELEPHANT_LABEL[0] = name


def furthermore(text: str) -> None:
    """The purple elephant. Telepathy renders as an indented purple intrusion."""
    voice.say("furthermore", text)
    header = paint(ELEPHANT_LABEL[0], PALETTE["purple"], STYLE_BOLD)
    _emit(f" {header}")
    for line in _wrap(text, indent="   ", subsequent="   "):
        _emit(paint(line, PALETTE["purple"], STYLE_ITALIC))
    blank()


def speech(speaker: str, text: str, colour_key: str = "cyan",
           voice_id: str | None = None) -> None:
    """An NPC talking out loud.

    `voice_id` is the npc id rather than the shown name: under amnesia the
    displayed name is an alias ("the friendly Russian"), and the voice must
    not change when the player learns who somebody is.
    """
    voice.say(voice_id or "narrator", text)
    header = paint(speaker.upper(), PALETTE[colour_key], STYLE_BOLD)
    _emit(f" {header}")
    for line in _wrap(text, indent="   ", subsequent="   "):
        _emit(paint(line, PALETTE[colour_key]))
    blank()


def monocle(text: str) -> None:
    """What the gold monocle reveals. Always gold, always set apart."""
    header = paint("THROUGH THE MONOCLE", PALETTE["gold"], STYLE_BOLD)
    _emit(f" {header}")
    for line in _wrap(text, indent="   ", subsequent="   "):
        _emit(paint(line, PALETTE["gold"]))
    blank()


def discovery(title: str, text: str = "") -> None:
    """A clue entering the investigation log."""
    _emit(paint(f" ── CLUE ── {title}", PALETTE["gold"], STYLE_BOLD))
    if text:
        for line in _wrap(text, indent="   ", subsequent="   "):
            _emit(paint(line, PALETTE["dim"]))
    blank()


def heading(text: str) -> None:
    """Location and section titles."""
    bar = "─" * min(width(), len(text) + 4)
    blank()
    _emit(paint(bar, PALETTE["dim"]))
    _emit(paint(f"  {text}", PALETTE["white"], STYLE_BOLD))
    _emit(paint(bar, PALETTE["dim"]))
    blank()


def warn(text: str) -> None:
    for line in _wrap(text):
        _emit(paint(line, PALETTE["crimson"]))
    blank()


def rule() -> None:
    _emit(paint("─" * width(), PALETTE["dim"]))


# --- input -----------------------------------------------------------------

def menu(options: list[str], prompt: str = "> ", allow_blank: bool = False) -> int:
    """Present a list and return the chosen zero-based index.

    On a terminal this is the vertical arrow-key selector. Piped in, it falls
    back to a numbered list read from stdin, which is what the test suite and
    the fuzzer drive - the selector is an input method, not a requirement.

    Returns -1 when the player declines and `allow_blank` is set. Dialogue
    options are never auto-selected: even a single remaining option must be
    chosen deliberately, because the act of choosing is the game.
    """
    if interactive():
        return vertical_choose(options, allow_blank=allow_blank)
    for index, option in enumerate(options, start=1):
        number = paint(f"{index:>2}.", PALETTE["dim"])
        for offset, line in enumerate(
            _wrap(option, indent="", subsequent="    ")
        ):
            if offset == 0:
                _emit(f"{number} {paint(line, PALETTE['narration'])}")
            else:
                _emit(paint(line, PALETTE["narration"]))
    blank()

    while True:
        try:
            raw = input(paint(prompt, PALETTE["purple"])).strip()
        except (EOFError, KeyboardInterrupt):
            blank()
            raise
        if not raw and allow_blank:
            return -1
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        warn("That is not among the available courses of action.")


def ask(prompt: str = "> ") -> str:
    """Free-text command entry."""
    try:
        return input(paint(prompt, PALETTE["purple"])).strip()
    except (EOFError, KeyboardInterrupt):
        blank()
        raise


def pause(message: str = "any key") -> None:
    """Wait for acknowledgement. On a terminal, any key will do."""
    if interactive():
        sys.stdout.write(paint(f"  {message}", PALETTE["dim"]))
        sys.stdout.flush()
        try:
            read_key()
        finally:
            sys.stdout.write("\r\033[2K")
            sys.stdout.flush()
        return
    try:
        input(paint(f"  {message}", PALETTE["dim"]))
    except (EOFError, KeyboardInterrupt):
        blank()
        raise


def clear() -> None:
    if COLOR:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def strip_ansi(text: str) -> str:
    """Remove escape codes - used by the test suite and the voice linter."""
    return re.sub(r"\033\[[0-9;]*m", "", text)


# ---------------------------------------------------------------------------
# Interactive selector: a persistent command bar pinned to the bottom of the
# screen, driven by the arrow keys.
#
# The prose log still scrolls normally. That is achieved with a DECSTBM
# scroll region which reserves the bottom rows, so output above never touches
# the bar and the bar never has to be redrawn on every print. This keeps the
# scrollback that made ANSI the right choice over curses in the first place.
#
# Everything here degrades to nothing when stdin is not a terminal: the game
# then uses its typed verb parser, which is what the test suite and the
# fuzzer drive. The bar is an input method, never a requirement.
# ---------------------------------------------------------------------------

try:
    import termios
    import tty
    import select as _select
    _RAW_AVAILABLE = True
except ImportError:                                  # pragma: no cover
    _RAW_AVAILABLE = False

# Frame geometry adapts to the terminal instead of assuming it is big.
# Below these the panels are dropped one at a time rather than clipped.
MIN_FRAME_COLS = 46   # narrower than this and the box is not worth the rows
MIN_BOX_ROWS = 14     # below this, keep the command bar but drop the box
MIN_BAR_ROWS = 8      # below this, no frame at all


def frame_geometry() -> tuple[int, int]:
    """(header_rows, bar_rows) for the current terminal.

    The command bar is the only way to play, so it is never dropped while the
    interface is interactive - at worst it narrows to a few verbs with scroll
    markers. Only the status box is optional, and it goes first.
    """
    if not interactive():
        return 0, 0
    cols, rows = _term_size()
    if rows < MIN_BAR_ROWS:
        return 0, 0
    bar = 3 if rows >= 12 else 2          # drop the hint row when short
    header = 4 if (rows >= MIN_BOX_ROWS and cols >= MIN_FRAME_COLS) else 0
    return header, bar


def framed() -> bool:
    return frame_geometry() != (0, 0)


MAX_GAP = 6           # beyond this, spreading reads as a layout accident


def justify(segments: list[str], width_avail: int, lead: int = 1,
            fixed_gap: int | None = None) -> str:
    """Spread segments across the width with even, bounded gaps.

    Drops segments from the end until what remains fits, so a narrow terminal
    loses its least important column rather than gaining a row of ellipses.
    Gaps are capped: two items spread across ninety columns reads as a bug,
    not as breathing room, so any slack past the cap is simply left over.

    `fixed_gap` pitches the segments at a constant spacing instead of
    spreading them. A row of gauges wants an even pitch; only the context
    line wants to fill its width.
    """
    items = [s for s in segments if s]
    while items:
        content = sum(len(strip_ansi(i)) for i in items)
        gaps = len(items) - 1
        needed = fixed_gap if fixed_gap is not None else 2
        if content + gaps * needed + lead <= width_avail:
            if gaps == 0:
                return " " * lead + items[0]
            if fixed_gap is not None:
                return " " * lead + (" " * fixed_gap).join(items)
            spare = width_avail - lead - content
            base, extra = divmod(spare, gaps)
            if base > MAX_GAP:
                base, extra = MAX_GAP, 0
            out = " " * lead
            for index, item in enumerate(items):
                out += item
                if index < gaps:
                    out += " " * (base + (1 if index < extra else 0))
            return out
        items.pop()
    return " " * lead


def interactive() -> bool:
    """Whether the framed interface can run at all."""
    setting = CONFIG["display"].get("command_bar", "auto")
    if setting == "never" or not _RAW_AVAILABLE:
        return False
    if setting == "always":
        return True
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def _term_size() -> tuple[int, int]:
    try:
        size = shutil.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 80, 24


def open_scroll_region() -> None:
    """Frame the screen: status box on top, command bar below.

    DECSTBM restricts scrolling to the middle band, so prose scrolls between
    the two fixed panels without ever touching them and neither has to be
    redrawn on every print. This is what keeps native scrollback, which is
    why this is ANSI rather than curses.
    """
    if not framed():
        return
    header_rows, bar_rows = frame_geometry()
    _, rows = _term_size()
    top = header_rows + 1
    bottom = max(top, rows - bar_rows)
    sys.stdout.write(f"\033[{top};{bottom}r")
    sys.stdout.write(f"\033[{bottom};1H")
    sys.stdout.flush()


def close_scroll_region() -> None:
    """Hand the whole terminal back. Must run on every exit path."""
    if not interactive():
        return
    header_rows, bar_rows = frame_geometry()
    _, rows = _term_size()
    sys.stdout.write("\033[r")
    for row in list(range(1, header_rows + 1)) + list(range(max(1, rows - bar_rows), rows + 1)):
        sys.stdout.write(f"\033[{row};1H\033[2K")
    sys.stdout.write(f"\033[{max(1, rows - bar_rows)};1H\033[?25h")
    sys.stdout.flush()


def install_resize_handler(redraw) -> None:
    """Re-frame the screen when the terminal is resized.

    Without this the scroll region keeps the old geometry after a resize and
    prose starts scrolling through the panels.
    """
    if not interactive():
        return
    try:
        import signal
    except ImportError:                              # pragma: no cover
        return

    def handler(_signum, _frame):
        open_scroll_region()
        try:
            redraw()
        except Exception:
            pass

    try:
        signal.signal(signal.SIGWINCH, handler)
    except (AttributeError, ValueError):             # pragma: no cover
        pass


def read_key() -> str:
    """Block for one keypress. Returns a name for special keys, else the char.

    Reads through `os.read` on the raw file descriptor rather than
    `sys.stdin.read`. Python's buffered reader will happily pull a whole
    escape sequence into its own buffer, at which point `select` on the fd
    reports "nothing waiting" and an arrow key gets mistaken for a bare
    Escape followed by two letters - which is exactly what the first version
    of this did.
    """
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)

        def _read(count: int = 1, timeout: float | None = None) -> bytes:
            if timeout is not None and not _select.select([fd], [], [], timeout)[0]:
                return b""
            try:
                return os.read(fd, count)
            except OSError:
                return b""

        first = _read()
        if not first:
            raise EOFError
        char = first.decode("utf-8", "replace")
        if char == "\x03":
            raise KeyboardInterrupt
        if char == "\x04":
            raise EOFError
        if char in ("\r", "\n"):
            return "ENTER"
        if char in ("\x7f", "\b"):
            return "BACKSPACE"
        if char == "\t":
            return "TAB"
        if char != "\x1b":
            return char
        rest = _read(6, timeout=0.05)
        if not rest:
            return "ESC"
        sequence = rest.decode("utf-8", "replace")
        if sequence[:1] not in ("[", "O"):
            return "ESC"
        return {
            "A": "UP", "B": "DOWN", "C": "RIGHT", "D": "LEFT",
            "H": "HOME", "F": "END",
        }.get(sequence[1:2], "ESC")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)


# --- the persistent status box ---------------------------------------------

def meter(label: str, value: int, maximum: int, size: int = 8,
          invert: bool = False) -> str:
    """A small labelled bar, coloured by how healthy the value is.

    `invert` is for meters where a high number is the bad news - exhaustion,
    intoxication - so the colour still reads "green good, red trouble"
    without the player having to remember which way each one runs.
    """
    ratio = (value / maximum) if maximum else 0.0
    filled = max(0, min(size, int(round(size * ratio))))
    health = (1.0 - ratio) if invert else ratio
    if health >= 0.6:
        colour = PALETTE["green"]
    elif health >= 0.3:
        colour = PALETTE["gold"]
    else:
        colour = PALETTE["crimson"]
    bar = paint("█" * filled, colour) + paint("·" * (size - filled), PALETTE["dim"])
    return paint(label, PALETTE["dim"]) + " " + bar


def delta_mark(change: int) -> str:
    """An arrow for a gauge that just moved, or a blank of equal width.

    Fixed width on purpose: a status row that reflows whenever a number
    changes is harder to read than one that holds still.
    """
    if not change:
        return "    "
    arrow = "▲" if change > 0 else "▼"
    colour = PALETTE["green"] if change > 0 else PALETTE["crimson"]
    return " " + paint(f"{arrow}{min(abs(change), 99)}".ljust(3)[:3], colour)

def draw_header(title: str, rows_of_segments: list[list[str]]) -> None:
    """Draw the boxed status panel, adapting to the terminal.

    Each row is a list of segments in priority order. `justify` spreads them
    evenly and drops the least important from the right when space runs out,
    so a narrow terminal loses a column rather than gaining a row of
    ellipses. The box itself disappears entirely on short terminals.
    """
    header_rows, _ = frame_geometry()
    if header_rows == 0:
        return
    cols, _ = _term_size()
    inner = max(10, cols - 2)

    heading_text = f" {title} "
    if len(heading_text) > inner - 4:
        heading_text = heading_text[: inner - 5] + "… "
    fill = "─" * max(0, inner - len(heading_text))

    out = [paint("┌" + heading_text + fill + "┐", PALETTE["dim"])]
    for row_index, segments in enumerate(rows_of_segments[: header_rows - 2]):
        # Row 0 is context and fills the width; the rest are gauges and want a
        # constant pitch so the eye can compare them.
        line = justify(segments, inner, fixed_gap=None if row_index == 0 else 2)
        pad = inner - len(strip_ansi(line))
        out.append(
            paint("│", PALETTE["dim"]) + line + " " * max(0, pad)
            + paint("│", PALETTE["dim"])
        )
    while len(out) < header_rows - 1:
        out.append(paint("│" + " " * inner + "│", PALETTE["dim"]))
    out.append(paint("└" + "─" * inner + "┘", PALETTE["dim"]))

    sys.stdout.write("\033[s")
    for index, line in enumerate(out, start=1):
        sys.stdout.write(f"\033[{index};1H\033[2K{line}")
    sys.stdout.write("\033[u")
    sys.stdout.flush()


# --- the command bar --------------------------------------------------------

def _fit(labels: list[str], focus: int, width_avail: int,
         dividers: set | None = None) -> tuple[list[str], int, bool, bool]:
    """Window the verb list so the focused item is always visible.

    The separators are inserted after this runs, so their width has to be
    counted here or the row silently overflows the terminal - which it did,
    clipping the last verb with no scroll marker to say so.
    """
    gap = 2
    dividers = dividers or set()

    def cost(index: int) -> int:
        return len(labels[index]) + gap + (3 if index in dividers else 0)

    if sum(cost(i) for i in range(len(labels))) <= width_avail:
        return labels, 0, False, False
    start = 0
    while True:
        used = 0
        end = start
        while end < len(labels) and used + cost(end) <= width_avail - 6:
            used += cost(end)
            end += 1
        if focus < start:
            start = focus
            continue
        if focus >= end:
            start += 1
            continue
        return labels[start:end], start, start > 0, end < len(labels)


def _state_case(label: str, focused: bool, chosen: bool, transform: bool) -> str:
    """Three visual states, shared by both selectors.

    available -> lower case, dim
    focused   -> UPPER CASE, bright
    chosen    -> UPPER CASE, bold gold

    `transform` is off for dialogue lines: those are whole sentences of
    speech, and upper-casing them reads as shouting rather than as focus.
    They get the brightness and weight changes without the case change.
    """
    if chosen:
        text = label.upper() if transform else label
        return paint(text, PALETTE["gold"], STYLE_BOLD)
    if focused:
        text = label.upper() if transform else label
        return paint(text, PALETTE["white"])
    text = label.lower() if transform else label
    return paint(text, PALETTE["dim"])


def draw_bar(verbs: list[str], focus: int, selected: bool, hint: str = "",
             dividers: set | None = None) -> None:
    """Render the rule and the command row into the reserved bottom rows.

    `dividers` holds the indices after which to draw a faint separator, so
    the row reads as groups - what you can do here, what you can consult,
    housekeeping - rather than one long undifferentiated list.
    """
    header_rows, bar_rows = frame_geometry()
    if bar_rows == 0:
        return
    cols, rows = _term_size()
    window, offset, more_left, more_right = _fit(verbs, focus, cols - 2, dividers)

    pieces = []
    for index, label in enumerate(window):
        real = index + offset
        pieces.append(_state_case(label, real == focus,
                                  selected and real == focus, True))
        if dividers and real in dividers:
            pieces.append(paint("│", PALETTE["dim"]))
    line = ("  " if not more_left else paint("‹ ", PALETTE["dim"])) + "  ".join(pieces)
    if more_right:
        line += paint("  ›", PALETTE["dim"])

    sys.stdout.write("\033[s")
    sys.stdout.write(f"\033[{rows - bar_rows + 1};1H\033[2K")
    sys.stdout.write(paint("─" * cols, PALETTE["dim"]))
    sys.stdout.write(f"\033[{rows - bar_rows + 2};1H\033[2K")
    sys.stdout.write(line)
    if bar_rows < 3:
        sys.stdout.write("\033[u")
        sys.stdout.flush()
        return
    sys.stdout.write(f"\033[{rows};1H\033[2K")
    keys = paint("← →  move    enter  choose    esc  quit", PALETTE["dim"])
    plain_keys = "← →  move    enter  choose    esc  quit"
    if hint and len(hint) + len(plain_keys) + 9 <= cols:
        sys.stdout.write("  " + paint(hint, PALETTE["gold"], STYLE_ITALIC)
                         + paint("     ", PALETTE["dim"]) + keys)
    elif hint:
        sys.stdout.write("  " + paint(hint[: cols - 4], PALETTE["gold"], STYLE_ITALIC))
    else:
        sys.stdout.write("  " + keys)
    sys.stdout.write("\033[u")
    sys.stdout.flush()


def bar_choose(verbs: list[str], focus: int = 0, hints: dict | None = None,
               dividers: set | None = None) -> tuple[str, int]:
    """Drive the horizontal bar. Returns (result, focus).

    Returns the chosen verb, or "__QUIT__". There is no typing path: a letter
    jumps between verbs sharing that initial, and anything unrecognised is
    ignored. Every interaction in the framed interface is a selection.
    """
    focus = max(0, min(focus, len(verbs) - 1))
    hints = hints or {}
    while True:
        draw_bar(verbs, focus, selected=False,
                 hint=hints.get(verbs[focus], ""), dividers=dividers)
        key = read_key()
        if key == "LEFT":
            focus = (focus - 1) % len(verbs)
        elif key == "RIGHT":
            focus = (focus + 1) % len(verbs)
        elif key == "HOME":
            focus = 0
        elif key == "END":
            focus = len(verbs) - 1
        elif key in ("ENTER", " "):
            draw_bar(verbs, focus, selected=True,
                     hint=hints.get(verbs[focus], ""), dividers=dividers)
            return verbs[focus], focus
        elif key == "ESC":
            return "__QUIT__", focus
        elif len(key) == 1 and key.isprintable():
            matches = [i for i, v in enumerate(verbs) if v.lower().startswith(key.lower())]
            if matches:
                focus = matches[0] if focus not in matches else matches[
                    (matches.index(focus) + 1) % len(matches)
                ]


def vertical_choose(
    options: list[str],
    title: str = "",
    allow_blank: bool = False,
    transform_case: bool = False,
    cancel_index: int | None = None,
) -> int:
    """A vertical selector drawn into the prose flow. Returns the index, or -1.

    Same three states as the bar: lower case and dim when available, UPPER
    CASE and bright under the cursor, bold gold when chosen.

    Options wrap over as many lines as they need. The first version of this
    printed only the first wrapped line, which silently swallowed the tail of
    every long dialogue option - the numbered menu it replaced had never done
    that.

    `transform_case` is set for target lists - things to look at, people to
    talk to, ways out - and left off for dialogue, whose options are whole
    sentences that read as shouting in upper case.

    `cancel_index` marks an option that means "never mind": choosing it wipes
    the list off the screen and returns -1, so backing out leaves no dead menu
    behind in the log. Choosing anything else leaves the list standing with
    the chosen line bold, as a record of what was picked.
    """
    if not options:
        return -1

    # Keep the list inside the scrolling band. A twenty-item object list on a
    # short terminal would otherwise push its own top off the screen.
    header_rows, bar_rows = frame_geometry()
    _, term_rows = _term_size()
    band = term_rows - header_rows - bar_rows if framed() else term_rows
    # Budget: title, both "n more" markers, the hint row, and a line of slack.
    # Without the full allowance the title scrolls off the top of the band.
    visible = max(3, band - 5)

    def window_for(focus: int) -> tuple[int, int]:
        if len(options) <= visible:
            return 0, len(options)
        start = max(0, min(focus - visible // 2, len(options) - visible))
        return start, start + visible

    def render(focus: int, chosen: bool) -> int:
        """Draw the list; return how many terminal lines it occupied."""
        count = 0
        start, end = window_for(focus)
        if title:
            suffix = "" if end - start == len(options) else f"   ({focus + 1}/{len(options)})"
            sys.stdout.write("\033[2K")
            _emit(paint("  " + title + suffix, PALETTE["dim"]))
            count += 1
        if start > 0:
            sys.stdout.write("\033[2K")
            _emit(paint(f"   ↑ {start} more", PALETTE["dim"]))
            count += 1
        for index, option in list(enumerate(options))[start:end]:
            focused = index == focus
            # A trailing "  [Skill 14 — WHITE, ...]" annotation is mechanical
            # information, not part of the line being spoken. Recess it.
            body, _, annotation = option.partition("  [")
            lines = _wrap(body, "", "     ")
            for offset, line in enumerate(lines):
                marker = paint("›", PALETTE["gold"]) if (focused and offset == 0) else " "
                sys.stdout.write("\033[2K")
                _emit(f" {marker} {_state_case(line, focused, chosen and focused, transform_case)}")
                count += 1
            if annotation:
                sys.stdout.write("\033[2K")
                _emit("   " + paint("[" + annotation, PALETTE["dim"], STYLE_ITALIC))
                count += 1
        if end < len(options):
            sys.stdout.write("\033[2K")
            _emit(paint(f"   ↓ {len(options) - end} more", PALETTE["dim"]))
            count += 1
        sys.stdout.write("\033[2K")
        _emit(paint("   ↑ ↓  move    enter  choose", PALETTE["dim"]))
        count += 1
        sys.stdout.flush()
        return count

    def _erase(lines: int) -> None:
        sys.stdout.write(f"\033[{lines}A")
        for _ in range(lines):
            sys.stdout.write("\033[2K\n")
        sys.stdout.write(f"\033[{lines}A")
        sys.stdout.flush()

    focus = 0
    height = render(focus, False)
    while True:
        key = read_key()
        if key == "UP":
            focus = (focus - 1) % len(options)
        elif key == "DOWN":
            focus = (focus + 1) % len(options)
        elif key == "HOME":
            focus = 0
        elif key == "END":
            focus = len(options) - 1
        elif key == "ENTER":
            if focus == cancel_index:
                _erase(height)
                return -1
            sys.stdout.write(f"\033[{height}A")
            render(focus, True)
            _emit("")
            return focus
        elif key == "ESC" and allow_blank:
            _erase(height)
            return -1
        elif key.isdigit() and 1 <= int(key) <= len(options):
            focus = int(key) - 1
            sys.stdout.write(f"\033[{height}A")
            render(focus, True)
            _emit("")
            return focus
        else:
            continue
        sys.stdout.write(f"\033[{height}A")
        height = render(focus, False)


# --- the interactive character sheet ---------------------------------------

def skill_browser(groups, detail_for, status_lines=None, title="Character") -> None:
    """A scrollable sheet: skills on the left, the highlighted one explained
    in a panel at the top right.

    `groups` is [(attribute_label, [(skill_id, row_label, value_text), ...])].
    `detail_for(skill_id)` returns a list of paragraphs.

    This is a modal: it takes over the scrolling band, draws absolutely, and
    clears itself on exit. It is the one screen in the game that is a
    *browser* rather than a narrative beat, and browsing twenty-four skills
    by scrolling a static block of text was the alternative - which is how
    the sheet worked when there were six of them and it did not survive the
    roster growing.
    """
    if not interactive():
        # Piped: fall back to printing everything once, in order.
        for label, rows in groups:
            _emit(paint(label.upper(), PALETTE["gold"], STYLE_BOLD))
            for _sid, row, value in rows:
                _emit(f"  {row:<24}{value}")
        for line in status_lines or []:
            _emit(line)
        return

    header_rows, bar_rows = frame_geometry()
    cols, rows_total = _term_size()
    top = header_rows + 1
    bottom = rows_total - bar_rows
    band = max(6, bottom - top)

    # Flatten to a navigable list; headers are not selectable.
    flat: list[tuple[str | None, str, str]] = []
    for label, entries in groups:
        flat.append((None, label, ""))
        for sid, row, value in entries:
            flat.append((sid, row, value))
    selectable = [i for i, (sid, _r, _v) in enumerate(flat) if sid]
    if not selectable:
        return

    left_w = max(26, min(38, cols // 2 - 2))
    right_x = left_w + 3
    right_w = max(20, cols - right_x - 1)

    focus = 0  # index into `selectable`

    def draw() -> None:
        out = []
        current = selectable[focus]
        # Window the list so the focused row stays visible.
        start = max(0, min(current - band // 2, max(0, len(flat) - band)))
        visible = flat[start:start + band]

        for offset, (sid, row, value) in enumerate(visible):
            y = top + offset
            if sid is None:
                text = paint(row.upper(), PALETTE["gold"], STYLE_BOLD)
            else:
                line = f"{row:<20}{value}"[:left_w]
                if start + offset == current:
                    text = paint("› " + line, PALETTE["white"], STYLE_BOLD)
                else:
                    text = paint("  " + line, PALETTE["dim"])
            out.append((y, 1, text))

        # The description panel, top right.
        sid = flat[current][0]
        paras = detail_for(sid) if sid else []
        panel: list[str] = []
        heading = flat[current][1].strip(" *")
        panel.append(paint("┌─ " + heading + " " + "─" * max(0, right_w - len(heading) - 5) + "┐",
                           PALETTE["dim"]))
        body: list[str] = []
        # Wrap to the *panel* width. Wrapping to the terminal width and then
        # truncating each line is what the first version did, and it sliced
        # every line off mid-word.
        for index, para in enumerate(paras):
            if index:
                body.append("")
            body.extend(textwrap.wrap(para, width=max(10, right_w - 4)) or [""])
        for line in body[: band - 2]:
            panel.append(
                paint("│ ", PALETTE["dim"])
                + paint(line.ljust(right_w - 4), PALETTE["narration"])
                + paint(" │", PALETTE["dim"])
            )
        panel.append(paint("└" + "─" * (right_w - 2) + "┘", PALETTE["dim"]))
        for offset, line in enumerate(panel):
            out.append((top + offset, right_x, line))

        sys.stdout.write("\033[s")
        for y in range(top, bottom):
            sys.stdout.write(f"\033[{y};1H\033[2K")
        for y, x, text in out:
            if top <= y < bottom:
                sys.stdout.write(f"\033[{y};{x}H{text}")
        # Status strip along the bottom of the band.
        if status_lines:
            y = bottom - 1
            sys.stdout.write(f"\033[{y};1H\033[2K")
            sys.stdout.write(paint("  " + "   ".join(status_lines)[: cols - 4],
                                   PALETTE["dim"]))
        sys.stdout.write("\033[u")
        sys.stdout.flush()

    draw()
    while True:
        key = read_key()
        if key == "UP":
            focus = (focus - 1) % len(selectable)
        elif key == "DOWN":
            focus = (focus + 1) % len(selectable)
        elif key == "HOME":
            focus = 0
        elif key == "END":
            focus = len(selectable) - 1
        elif key in ("ESC", "ENTER", "q", " "):
            break
        else:
            continue
        draw()

    sys.stdout.write("\033[s")
    for y in range(top, bottom):
        sys.stdout.write(f"\033[{y};1H\033[2K")
    sys.stdout.write(f"\033[{top};1H")
    sys.stdout.write("\033[u")
    sys.stdout.flush()
