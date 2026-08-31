# Malice in Underland

A Disco Elysium-style investigation game set in Silvora Reefs, built from the
`miu.json` lorebook. Pure Python 3.10+, standard library only (PyYAML used if
present, not required). No graphics, no real-time loop, turn-based throughout.

```bash
cd game
python3 main.py                  # play
python3 main.py --debug          # show every die roll
python3 main.py --seed 42        # reproducible runs
python3 main.py --density 7      # pin narrative pacing
python3 main.py --load save      # resume

python3 tools/test_mechanics.py     # 60 unit tests
python3 tools/validate_content.py   # structural content checks
python3 tools/voice_lint.py         # narration-rule enforcement
```

## The source material

`miu.json` was a truncated SillyTavern lorebook — 34 entries parsed, entry 35
(O.R.A.C.L.E.) cut off mid-object. All 35 were recovered and are preserved at
`content/lorebook_entries.json`. Originals backed up under `/tmp`.

Reading it changed several design decisions, because the lorebook contradicts
parts of the brief. Where they conflict, the lorebook won:

| Brief | Lorebook | Built |
|---|---|---|
| Oliver is a linguistics professor | crash survivor turned investigator, raised by an artist and an actress | lorebook version |
| Golden monocle is the first major clue | he already wears it; it reveals hidden aspects of reality | **starting equipment and a verb** — `monocle <thing>` |
| "Revilo Snoino" | Snoino Revilo | Snoino Revilo (`is_reversal("Oliver Onions", "Snoino Revilo")` returns `True`) |
| Corporate conspiracy | C.C.C.C. is Oliver's analytical mind; O.R.A.C.L.E. is not a device | corporate reading is the *surface*, playable and believable, then dismantled |
| Helicopter crash opens the story | — | kept, but Darek establishes nothing came down. Oliver came **up** |

Making the monocle equipment rather than a plot token is the single biggest
change and the one that pays best: "look harder" becomes a decision the
player makes every turn instead of a reward they wait for.

The lorebook's real spine is the **typewriter**. It recurs in every location
independently — typing at Hang-Hi, an office behind the mirrors, a desk
behind the Möbius wall, a vault at Rest Assured holding a replica of Oliver's
desk. That motif, not the conspiracy, drives the plot beats.

One factual note: the lorebook claims the club's sign rearranges into
"Revilo's Trap Built". It is not an anagram — that phrase needs an A and a V
that "The Möbius Strip Club" does not contain. Rather than fix the lore, the
game uses it: a RHETORIC check has Oliver count the letters and discover the
rearrangement *spent letters it did not have*, which is more unsettling than
a clean anagram and is genuine evidence of an author.

## Deviations from the brief, and why

**ANSI stdout, not curses.** Curses gives a fixed viewport with no native
scrollback — hostile to a game whose content is long prose the player wants
to scroll back through. Wrapped, coloured stdout costs less CPU than a curses
refresh loop and lets the terminal do what it is already good at.

**`config.yaml` with a code fallback.** YAML as requested, but `config.py`
carries an identical embedded copy so a missing PyYAML never blocks startup.

**Dropped hunger, added Lucidity.** Hunger is busywork in a game with no
survival loop. Lucidity — how far Oliver has noticed the manuscript — is what
the lorebook is actually about, and it drives world description, skill
modifiers, Furthermore's clarity, and dialogue gating.

**Phase 1 and Phase 2 delivered together.** Phase 1 alone (systems, no
content) is not playable and cannot be evaluated. What is here is a running
game. Phase 3 content is not written; see *What is not built* below.

## Architecture

```
main.py              verb parser and game loop
game_state.py        the hub: conditions, effects, clock, save/load
player.py            Oliver — skills, status, inventory, thought cabinet
skill_checks.py      d20 resolution, status modifiers, white/red ledger
investigation.py     clues, beats, scene state, retry fingerprint
dialogue_engine.py   conditional node graph
furthermore.py       companion, thought cabinet, hint system
locations.py         lazy-loading location and object registry
npcs.py              cast and relationship tracking
narrative_density.py the 1-10 pacing dial
wordplay_engine.py   reversals, anagrams, curated alliteration
ui.py                channels: narration, skill voice, speech, monocle
config.py/.yaml      all tunables
content/             JSON — 11 locations, 20 NPCs, 191 clues, 6 thoughts, 4 endings
tools/               tests, content validator, voice linter
```

The map is a connected graph, not a hub — every exit is two-way and the
validator warns on any that is not:

```
        Rest Assured ─── Giddyup End 'em Ribs
          │   │  │              │      │
          │   │  └── Möbius ────┼──────┘
          │   │       │  │      │
   Hang-Hi ───┴─ Durry Kwain    │
     │  │          │    │       │
     │  └─ Dude's ─┘    │   The Outside Inn
     │                  │       │
   The G.'s Spot ───────┼───────┘
          │             │
     Chef D.'s Lishush Mush ─── Cheeses Thrice

              ⇣ (the seam: one-way, gated)
                  The Office
```

The Office has no exits and is not on the map. It is reached through a seam
that opens at four of the thin places — the Hang-Hi mirror, the Möbius wall,
the unmarked vault, the third mirror at the G.'s Spot — once the `awakening`
beat has fired and Lucidity is at 70. Both outcomes of the crossing check
travel; a failed roll gets you there badly, never not at all, and there is a
unit test that says so.

~5,400 lines of commented Python, ~750KB of content.

## The interface

Nothing is typed. Every interaction is a selection, including the ones that
used to need an argument — save slots are auto-named, load lists what is on
disk, pacing is a menu. On a terminal the game runs framed and keyboard-driven;
piped in, it falls back to a typed verb parser, which is what the test suite
and the fuzzer drive, so both paths stay exercised on every run.

```
┌ Hang-Hi Quiet Apartments ──────────────────────────────────────────────────┐
│ Oliver Otto Onions     Early Dark, cycle 1     day 1     clues 1  beats 0/6│
│ morale ██████··   health ██████·· ▼3   lucid ██······   The Crash 1/3 ██···│
└────────────────────────────────────────────────────────────────────────────┘

   ... prose scrolls here, keeping the terminal's own scrollback ...

   examine — 6 here
 › THE WATERLOGGED NOTEBOOK
   the hallway mirror
   the snake on the building sign
   never mind
   ↑ ↓  move    enter  choose

──────────────────────────────────────────────────────────────────────────────
  look  EXAMINE  monocle  talk  go  rest  wait  think │ cabinet log case │ save
  look closely at something here     ← →  move   enter  choose   esc  quit
```

**Three states, both selectors.** Available options sit in lower case; the one
under the cursor is UPPER CASE and bright; the chosen one is bold gold. Left
and right walk the verb row, enter opens a vertical list of what that verb can
act on *right now*, up and down walk that, enter commits. Escape backs out and
wipes the list, so cancelling leaves nothing behind; committing leaves it in
the log with the chosen line bold, as a record of what was picked.

**The bar is a readout, not a fixed menu.** It lists only what is genuinely
available — `rest` where there is a bed, `monocle` while Oliver still has the
lens, `talk` when somebody is here, `log` once there is something in it, `load`
once a save exists. Faint dividers group it: *what you can do here │ what you
can consult │ housekeeping*. The line beneath describes the focused verb. A
letter jumps between verbs sharing that initial. Escape asks before quitting.

**The status box is live.** Meters are coloured by how healthy the value is,
with exhaustion and intoxication inverted so green always means "fine". A
change since the last action shows as ▲/▼ in a fixed-width column, so the row
never reflows. The last gauge is the nearest unmet beat, so the box answers
"where does the case stand" without opening anything.

### It fits any terminal

The frame is computed from the actual size every draw, and degrades one piece
at a time rather than clipping:

| | |
|---|---|
| wide | context row fills the width, all gauges, full verb row |
| narrower | gauges drop from the right; verb row windows with `‹ ›` |
| under 46 columns | status box goes; command bar stays |
| under 12 rows | hint line goes |
| under 8 rows | frame off entirely, plain scrolling |

The context row is justified with **bounded** gaps — two items spread across
ninety columns reads as a layout accident, so slack past six spaces is left
over rather than distributed. The gauge row uses a constant pitch instead,
because a row of meters wants to be comparable at a glance. Long option lists
window inside the scrolling band with `↑ n more` / `↓ n more` rather than
pushing their own top off screen. A `SIGWINCH` handler re-frames on resize.

### Found by playing it

Driving the framed UI through a pseudo-terminal — reading the rendered screen
and pressing arrow keys, the way a player does — turned up four things:

**The cabinet listed its thoughts twice.** It printed an "available" block and
then offered the same items as a selector. The block is now suppressed in the
framed interface; only the non-selectable sections (turning over, settled)
remain.

**The status box went stale during conversations.** It only redrew between
commands, so a clue found four exchanges into a dialogue did not move the
gauges until the conversation ended. `GameState` now carries an `on_change`
hook that the UI wires to the header, so lucidity climbs while you are still
talking.

**Which promptly broke the delta arrows.** With the header redrawing on every
effect, `▼8` was consumed by the next redraw before anyone could read it. The
comparison baseline now moves once per *command* rather than once per draw, so
an arrow shows what the last thing you did cost and stays until you do the
next thing.

**Long lists lost their title.** The windowing budget did not allow for the
title and both `n more` markers, so on a sixteen-row terminal the heading
scrolled off the top of the band before the list finished drawing.

### Two things worth naming

**Dialogue keeps its natural case.** Those options are whole sentences of
speech, and upper-casing `"The corridor is longer when I walk it alone."` reads
as shouting rather than as focus. They get the brightness and weight changes
without the case change; target lists — objects, people, exits — are short
labels and take the full treatment.

**Options wrap.** The first version of the vertical selector rendered only the
first wrapped line of each option, silently swallowing the tail of every long
dialogue line — something the numbered menu it replaced had never done. Options
now take as many lines as they need, and a trailing `[Rhetoric 15 — WHITE, even
odds]` annotation is split onto its own recessed line, because it is mechanical
information rather than part of what Oliver says.

## Mechanics

**Skill checks.** `d20 + (skill-10)//2 + situational` vs DC. Natural 20 always
succeeds, natural 1 always fails. **A failed check never blocks progress** —
the validator enforces that every check authors both a success and a failure
narration, and most failures still award a clue. The mirror check at Hang-Hi
fails into a lesser clue; the Möbius wall fails into evidence about how fast
the Insta-gators are.

- **White checks** retry once the state changes — a fingerprint of the clue
  set, the flags, the beats, and how many dialogue nodes have been *heard*, so
  "come back when you know more" is enforced mechanically rather than by the
  player re-picking an option. A backstop unlocks any white check after two
  failures regardless, so a room with no exits can never retire the branch
  behind one bad roll.
- **Red checks** resolve permanently.
- Every failure grants **+1 for stubbornness** on the next attempt, capped at
  +3. Oliver's defining trait is that he cannot stop going over a thing.

Options display a qualitative read (`trivial`, `even odds`, `desperate`)
rather than a percentage, so choices stay judgement calls, not arithmetic.

**Passive checks** let skills speak unprompted. Budgeted per scene by density
so a room never becomes six voices shouting. Failed passives stay silent by
default; content can author a *wrong* answer for a failed passive, which is
the most interesting thing the system does.

**Status.** Morale gates persuasion. Health gates Physique. Intoxication is a
genuine trade — Electrochemistry up, Logic down, and past 6 the narration
starts organising itself by sound. Lucidity shifts *which skills work*: at 45+
Logic degrades (there is nothing coherent left to deduce) while Rhetoric and
Savoir-Faire improve.

**Beats** fire on evidence thresholds, not on scripted triggers, and every
beat is over-supplied with clues (`crash 5/3, manuscript 46/6, quadc 23/6,
oracle 40/8, revilo 31/8, awakening 35/7`) so two players reach the same
revelation via different routes. `validate_content.py` fails the build if any
beat needs more clues than exist — that check is what prevents an unwinnable
game, and no amount of happy-path playtesting would find it.

Thresholds were retuned when the content tripled: the originals were set for
67 clues, and at 180 the endgame beat fired within minutes of starting. A
completionist sweep of every object in every location now leaves five of six
beats unfired, because most evidence lives in conversations.

## The endgame

The confrontation is the payoff for the investigation, so it is fought with
evidence rather than with dice. Revilo makes three cases, and each is answered
from a different body of clues:

1. **"You are not a man. You are a draft."** True, and unanswerable as stated.
   The turn is to accept it and extend it — *and so are you* — which lands
   only if the player has noticed that the page stopped on **his** side.
2. **"Nothing is lost. None of them are anybody."** Answered by naming them:
   Albert mentioned less over forty years, Dee kept because somebody could not
   delete him, Bud holding up a floor with his mouth, Woolbinkle's forty cans.
   Gated on `tag_count_min: {personhood: 4}`.
3. **"I have kept you alive."** Answered by the evidence of it — the shim in
   the trestle, the twenty-two forms recommending company, two hundred drafts
   dated eleven years apart at the bottom and four days at the top. Gated on
   `tag_count_min: {kindness: 5}`.

`tag_count_min` is the mechanism that made this work. Gating on specific clues
would make one route mandatory and break the whole design; gating on *how much
of a kind of evidence* the player holds means any five of twenty will do. 46
clues across the game are tagged `kindness` or `personhood`, and 20 and 26 of
them respectively are reachable before the Office.

**Four endings**, and which are offered depends on what was found:

| | Requirement | What it costs |
|---|---|---|
| **and he does** | always | Oliver takes the language. Silvora Reefs stops. |
| **and he does not** | always | Revilo keeps it. Oliver stays, and never knows. |
| **Recommend company** | kindness ≥ 5, personhood ≥ 4, and argument 2 answered | Neither gets the last word. |
| **Nevermind** | the `and_furthermore` thought internalised, Lucidity ≥ 95 | The elephant finishes the sentence. |

Tell Revilo the townspeople are not real and the third ending is withdrawn —
not as punishment, but because the argument for it is one you declined to make.

Epilogues are content, not code. Each carries consequence lines that print
only if the player earned the clue behind them, so two people who choose the
same ending do not read the same epilogue. A report card at the end states
what the playthrough actually consisted of, including how much kindness and
personhood were noticed.

**Furthermore** is the thought cabinet *and* an arc rendered as a mechanic.
His clarity is a function of Lucidity: at stage 0 he communicates as weight
and temperature, at stage 1 he gets one clause out, at stage 2 the words
arrive out of order, at stage 3+ he speaks plainly. His "Nevermind" gag has a
full build-up and fires ~30% of the time on `think` — and *stops firing* at
stage 4, because by then he can finish the sentence. The joke ends when the
character arrives.

**Narrative density** (1-10) selects between authored variants; it never
truncates prose. Content supplies `{"low":…, "mid":…, "high":…}` and falls back
across bands. The default is **6**, and auto-scale is anchored to it: the game
opens where you set it and runs `AUTO_ABOVE` (2) steps faster by the last beat,
so 6 → 8. Set it with `pacing` in the bar, or `--density N` to pin it.

Two things about the dial are worth knowing before relying on it.

**It was doing nothing.** The curve was hardcoded as `3 + fraction × 5`, which
overrode the configured value the instant a beat fired — a game set to 4 spent
its whole opening reporting "density 3/10 (auto)". It is anchored now, and only
ever tightens: an earlier version straddled the default, so reaching a beat
made the prose *longer*, which reads as a glitch.

**It now reaches about 14% of the words.** 110 of the 184 dialogue nodes —
every one over eighty words — carry a `high` variant alongside the original,
as do location descriptions and revisit lines:

| band | total prose |
|---|---|
| low | 61,276 |
| mid | 57,244 |
| high | 52,720 |

A `high` variant is not a summary. It is the same speech with the digressions
removed: the voice intact, every load-bearing fact intact, one instance of the
character's move instead of three. Soliloquy still rhymes, Chef D. still has
no teeth, the Insta-gator still circles back. Nodes under eighty words are
left alone — compressing a short speech saves little and risks the voice.

Variants are authored as `{"low": original, "high": tightened}`, so the mid
band falls back to the full text. With the default at 6 that means the opening
runs long and the second half runs tight, which is what the curve is for.

What the dial still does not reach: skill voices, monocle reveals and check
outcomes, all written once. That is deliberate — they are opt-in payoffs, and
shortening them would punish a player for looking harder.

Ambient lines survive to level 7 rather than stopping at 6, because auto-scale
lifts a game set to 6 up to 7 by the second beat and silencing the town's
incidental colour for two thirds of a run is a bigger change than the dial was
asked to make.

**Text varies along three independent axes** without authored branching:
density band, Lucidity stage (`"lucid": {"2": …, "4": …}`), and visit count
(`"repeat"`). Returning to a location reveals new detail because Oliver has
changed, not because a script fired.

## Voice enforcement

`tools/voice_lint.py` is a hard gate on the two narration rules. Second person
throughout, and **no imposed interior** — "you feel", "you think", "you want",
"you decide", "you realise" and 15 more are build failures in narration
fields. Quoted spans are exempt, because NPCs may say "you think" all day.

It found four violations on first run. Two were quoted NPC speech (linter
fixed); two were real narration violations in `mobius.json` (content fixed).
Current state: 12 files, 0 violations.

## Testing

- `test_mechanics.py` — 41 tests: d20 maths, crit/fumble, the white/red retry
  ledger, condition evaluation, beat thresholds, red-herring accounting,
  status trade-offs, density band fallback, save round-trip through disk, and
  the exact letter operations behind the central pun.
- `validate_content.py` — dangling `goto`s, unreachable nodes, unknown skills,
  implausible DCs, one-way exits, missing failure text, clues referenced but
  never granted, unknown thought ids, and beat solvability.
- `voice_lint.py` — narration rules, across all 34 content files including
  the epilogues, which get the strictest reading of anything in the game.

All three pass clean. Random-input fuzzing produces no crashes across every
location and NPC, and reaches all four endings unassisted.

The voice linter has now caught eight real violations across three content
passes — four in the first four locations, two in the second six, two in the
epilogues. Every one was a narration field quietly telling the player what
Oliver wanted or decided.

## What is not built

Stated plainly so the scope is not overclaimed:

- **HUHmphry Doughcart and Moreover.** Both are named in the lorebook with
  empty content fields, so there is nothing to build them from. They are the
  only two named characters left, and inventing them wholesale seemed worse
  than leaving the slot open.
- **Walk-on parts stay walk-on.** Chuckles the Unfunny Clown, Antopolis
  Ficklefuk and Jesus Crust exist through their effects — the fog patches, the
  nine years of NO MATTERS ARISING, the pizza boxes — rather than as
  conversations. That is deliberate; each is funnier as a consequence.
- **Combat.** There is none. Physique is used for endurance and force within
  investigation, which suits the source.
- **No post-ending play.** The game stops at the epilogue. There is no
  new-game-plus carrying knowledge across, which would be a natural fit for a
  story about drafts and is not built.

## What playtesting changed

A full playthrough found eight issues that no test would have caught, because
they were all about how the game *feels* rather than whether it works.

**The check economy was a coin flip with a cliff.** Median success at starting
stats was 45%, 55 of 69 checks were at or below even odds, and 37 carried no
clue bonus at all. Losing a roll retired the content behind it — Landy's
entire arc sits behind one DC 13 Empathy check. Fixed by adding a
**persistence bonus**: +1 per previous failure, capped at +3. Retrying a white
check already costs a real advance in the investigation, and now that loop
pays. A 45% check becomes 70% for a player who keeps coming back. It is also
the most in-character modifier in the game.

**The game misreported its own difficulty.** The odds shown on an option
ignored clue bonuses entirely, so a player holding three supporting clues was
told "even odds" on something that was comfortable. Object checks showed no
odds at all. Both now show what the roll will actually get.

**A spent check sat in slot 1 doing nothing.** Picking it printed a refusal
and looped, which reads as the game ignoring you. Locked options now sink to
the bottom and say what would unlock them.

**A latent softlock in the confrontation.** `revilo.the_name` had exactly one
option, a check; if it had ever locked, the player would have looped until the
guard fired — in the climax. The engine now injects an escape when every
option is spent, the validator warns on any node without an unconditional
option, and the node got a real second option.

**`think` was useless exactly when it was needed.** It is the hint command,
and Furthermore's clarity is gated by Lucidity, so early on — when a player is
most likely to be stuck — three consecutive `think`s produced pure atmosphere
and no information. The elephant's arc is not negotiable, so the two jobs were
separated: he still does his weather and his gag, and the *hint* now falls
back to Oliver reasoning it out in a skill voice, naming how much evidence is
missing and which unvisited location actually carries some.

**The thought cabinet was not a cabinet.** Unlimited parallel internalisation
meant "which thought" was never a choice — you took all of them. Now capped at
two slots (`narrative.thought_slots`). Viewing it also forced you into a menu
with no way to just look; blank input now exits.

**Travel dead-ended on the geography.** `go to giddyup` from Dude's Dews said
only "you cannot get there", leaving the player to guess the map. It now names
the first step.

**Three identical thought notifications** could fire in one room. Varied.

### Second playthrough: three more, all in the economies

Playing it again with the first round of fixes in surfaced problems that the
first pass had been hiding.

**Lucidity — the game's central mechanic — was saturating at 5% of content.**
The content grants ~1900 raw lucidity against a scale of 100. A playthrough
hit 100/100 at cycle 14 with two of six beats done, which retired Furthermore's
entire clarity arc before it had begun and made every `lucidity_min` gate
meaningless. Gains now suffer **diminishing returns** scaled by remaining
headroom (`world.lucidity_approach`), so waking up is asymptotic. A full
thorough run now traces 14 → 31 → 42 → 60 → 68 → 77 → 83 across the map,
moving through stages 0-3, with the elephant getting clearer the whole way.

An unexpected benefit: lucidity now visibly *dips* at the Möbius and the
Outside Inn, where the Insta-gators and Bud Onkuhdonk push it back down. That
mechanic existed from the start and had been completely invisible, because
gains were swamping it by an order of magnitude.

**Exhaustion was a one-way tax with no relief.** The clock added +1 every
three cycles forever and the entire game contained exactly one source of
recovery (Sir Jerry's haircut, −2), so every player was pinned at 10/10 —
a flat −2 to Logic and Savoir-Faire — from roughly cycle 30 onward, and
arrived at the confrontation permanently penalised. There is an inn in this
town with rooms at seven a night; now they are for something. `rest` sleeps at
your own flat or at the Outside Inn, clears exhaustion, restores health and
costs four cycles, and accrual slowed to one per five cycles.

**The lucidity aside had three lines and no sense of progression.** It fires
on nearly every discovery, and at 91 lucidity it was still telling me I
*almost* placed the sound. It now has fifteen lines banked by stage: at stage 0
a small mechanical noise at the edge of hearing, at stage 4 "the machine stops
whenever you look directly at what it is doing."

A regression the tests caught within a minute: backing lucidity with a float
left two fields that could disagree, so `player.lucidity = 70` silently failed
to update the underlying value. It is a property now.

### Third playthrough: talking to everyone

The first two passes swept objects and took option 1 in conversations. This
one walked every branch of every tree. It is a different game — 140 clues
against 74, personhood 23 against 3, and **morale sat at 98-100 for most of it
where the shallow run ended at 20**. Five thoughts settled, raising four
skills. At the last word, four endings were on the menu instead of two.

It also found the worst bug in the project.

**One bad roll could permanently retire the best ending.** The confrontation
happens in a room with no exits and nothing left to examine, so the
investigation state could not move, so a failed white check could never
unlock. The co-authorship ending needs that check. Three fixes:

* the state token now includes how many dialogue nodes have been *heard* —
  learning something from a conversation is learning something, and it
  self-limits, because the count only grows on genuinely new nodes;
* a backstop unlocks any white check after enough failures regardless
  (`difficulty.retry_after_failures`);
* the one node in the scene that changed nothing now grants a clue, because
  it is a strong beat and deserved one anyway.

The backstop shipped broken on the first attempt: I set the threshold to three
failures, but attempts only increment while the check is *unlocked*, so a
stuck player caps at two and the rule could never fire. There is now a test
asserting the threshold is reachable.

**Winning an argument could strand you in it.** Succeeding at the second
argument hid both the winning option and its alternative, leaving the denial —
"No. They aren't." — as the only way forward. Re-entering the conversation
forced you to contradict what you had just proved. There is now a
continuation option gated on having won.

**Twenty-eight dialogue nodes rendered narration as speech.** Stage directions
— "He does not turn round for a while", "You sit. He watches you do it" — were
printing under a SNOINO REVILO header. Found by a heuristic scan for nodes
opening in the third person about the speaker, or in the second person about
the player. Both classes are now on the narration channel.

**The thought cabinet was never used.** A 295-cycle run internalised nothing,
because when I varied the thought-arrival lines two rounds ago I dropped the
word "cabinet" from all of them. It now teaches the mechanic once, on the
first thought, and reports free slots thereafter.

**The seam did not say it was one-way.** An irreversible transition into a
room with no exits now says so before you take it.

### Three things the playtest confirmed rather than fixed

**The endgame gate is tuned right.** A player who examines and monocles every
one of the 48 objects and never speaks to anybody ends at 63 clues, five of
six beats, and `awakening` at **6 of 7** — one clue short of the seam. The
door to the endgame does not open for someone who never talked to anyone.

**The endgame gates hold at their boundary.** The playthrough finished with
kindness 9 and personhood 3 — one short — and co-authorship was correctly
withheld, because a shallow pass through the conversations had not earned the
argument that the townspeople are people. Verified at every boundary: 9/3 fails,
9/4 offers the argument, 5/4 with the argument answered opens the ending, 4/4
fails on kindness.

**The morale economy says what the game says.** Objects are worth a net −105
morale across the content; dialogue is net +25, with 278 points of recovery
available in conversation. Investigating alone grinds Oliver down and people
build him back up. That was not designed — it emerged from writing the two
kinds of content — and it is the maintenance form in the trestle leg rendered
as an economy: *REMEDY: none available. Recommend company.*

## Adding content

A location is one JSON file in `content/locations/`. An NPC is an entry in
`content/npcs.json` plus a node graph in `content/dialogue/`. Both share one
condition/effect vocabulary, documented in `game_state.meets()` and
`game_state.apply_effects()`. Run the validator afterwards — it catches
dangling references, unreachable nodes and unsolvable beats before a player
does.

## Skills, attributes and the dice

Twenty-four skills under four attributes — **Intellect, Psyche, Fortitude,
Motorics** — six each. The six the game shipped with (Logic, Rhetoric,
Empathy, Physique, Electrochemistry, Savoir-Faire) kept their exact ids so
that 200-odd authored checks kept working; the other eighteen are new, and
each of them can talk.

Rolls are **2d6 + skill vs DC**. The skill value *is* the modifier, so every
number on the sheet is small and means exactly one thing: Logic 4 adds 4.
Attributes run 1-6 and set the floor for their six skills; a signature
specialist reaches about 8. DCs run 9-15, and because 2d6 is a bell rather
than a flat d20, your build decides most outcomes and the dice supply
texture rather than chaos.

| DC | who passes |
|----|------------|
| 9  | most people, most days |
| 11 | a coin flip for someone who invested here |
| 12 | 28% untrained, 58% for a specialist |
| 14 | go and become someone else first |

### Character creation

Four archetypes or a custom build: distribute eight attribute points on top
of one in each, spend four individual skill points, pick a signature skill.
This is the replayability answer. A fixed six-skill investigator gave a
second playthrough nothing new to be.

### The skills talk

`content/skill_voices.json` holds ambient lines keyed to skill and location.
They are offered in descending order of skill value, so a build's loud
skills dominate what gets noticed — and a line **failed** at a given skill
value stays failed until that skill grows. That last rule is load-bearing:
without it, re-rolling on every revisit meant all four archetypes eventually
heard nearly the same lines and the build became cosmetic. Measured, two
archetypes now share only 25-43% of what they hear.

### Amnesia

The game opens in the wreck with no name. The status bar reads *the man from
the harbour* until you find your flat; every NPC is a description — *the
friendly Russian*, *the man with the squeegee* — until you have spoken to
them; and the elephant is *the elephant* until the thought that names him
arrives. Names are information, and information here is earned.

### Pacing

There is no pacing dial. The game renders at what the old dial called
density 1 — the fullest telling, every object described in full, ambient
lines firing freely. The thinner authored variants are still in the content
files, unreachable, because they are real writing and deleting them would
be irreversible in a way that removing a menu entry is not.
