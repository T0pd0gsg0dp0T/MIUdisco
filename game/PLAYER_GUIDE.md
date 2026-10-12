# Malice in Underland — Player Guide

> *You are lying on your back in shallow water, and the sky above is doing what it apparently always does: bruising slowly from violet into a crimson it never quite commits to.*

---

## Prologue: The Sentence Unfinished

The rotor blades are still turning above the fog. Unhurried. Patient. Entirely unbothered by having arrived in a town where, and this arrives with total confidence and no source whatsoever, **nobody owns a helicopter**.

You are wet. Your watch says 3:33 — and has always said 3:33. Your pockets have been gone through by the tide and are still full of gold. Your monocle is intact, cold against your chest, and through it the world admits things it would rather not: that the green lampposts throw shadows that don't agree with their flames, that the floor of the corridor is longer than the building that contains it, that the name *Silvora* sits at the front of your head with no paperwork to support it.

You do not know your name.

This is not distressing yet. It sits in you the way a missing tooth sits in a jaw — not painful, simply a place the tongue keeps going back to, testing, finding nothing, going back again. It is the first item on a list, and some part of you that has done this kind of work before is already fairly certain the list is going to get longer.

Somewhere to your left, an elephant the colour of a bruise is waiting for you to finish a sentence you do not remember starting.

He has been waiting a very long time.

Behind you, half in the shallows and half up the shingle where it stopped, is the thing you came down in. It is large and it is broken and it is broken in a way that objects of that size are not supposed to break. The smell coming off it is hot metal apologising. The harbour is full of it.

**Darek will tell you later: nothing came down. You came *up*.**

The gull that goes over — or the thing shaped approximately like one — does not call. Gulls call.

Ahead, past the harbour wall, the green lampposts go up a street in a line. Each one throws considerably more shadow than its flame can account for. The shadows do not agree with one another about where the light is coming from. Nobody has apparently ever raised this at a parish meeting.

The water comes in at the pace of something with nowhere in particular to be, turning over the shingle, going out again, coming back with the same shingle in a slightly different order. It has been going through your pockets since before you woke up. Whatever it wanted, it has either taken or decided against.

Your attention goes round the place and comes back holding: your own hands, the wreckage, the things in your pockets, the harbour wall and the street beyond, and the waterline.

It will keep going back to them until they have been dealt with. That is the whole of your method. And most of your problem.

---

## Table of Contents
1. [What Is This Game?](#what-is-this-game)
2. [Getting Started](#getting-started)
3. [The Interface](#the-interface)
4. [The Verbs — What You Can Do](#the-verbs--what-you-can-do)
5. [Character Creation](#character-creation)
6. [Build Archetype Guide](#build-archetype-guide)
7. [Core Mechanics](#core-mechanics)
8. [The World: Silvora Reefs](#the-world-silvora-reefs)
9. [Content Map](#content-map)
10. [Key Characters](#key-characters)
11. [Investigation & Progression](#investigation--progression)
12. [Save Strategy](#save-strategy)
13. [The Endgame](#the-endgame)
14. [Tips for New Players](#tips-for-new-players)
15. [Quick Reference Card](#quick-reference-card)
16. [Glossary](#glossary)
17. [Accessibility Notes](#accessibility-notes)
18. [FAQ](#faq)
19. [Commands Reference](#commands-reference)
20. [Files of Interest](#files-of-interest)

---

## What Is This Game?

**Malice in Underland** is a text-based investigation game in the spirit of *Disco Elysium*. You play **Oliver Onions** — a man who has crashed from the sky into the harbour of Silvora Reefs, with no name, no memory, and a gold monocle that shows things as they actually are.

There is no combat. No inventory puzzles. No fail states that end the game. The investigation *is* the game: you examine, you talk, you think, and the town reveals itself through what you notice and what you choose to pursue.

**Design philosophy:** A failed check never blocks progress. It gives you a different clue, a different angle, or costs you something — but the story continues. Your build decides *how* you solve things, not *whether* you can.

---

## Getting Started

### Requirements
- Python 3.10+
- Standard library only (PyYAML optional — embedded fallback included)

### Launch
```bash
cd /home/t0nt0n/MIUdisco/game
python3 main.py                 # normal play
python3 main.py --debug         # show every die roll
python3 main.py --seed 42       # reproducible run
python3 main.py --density 7     # pin narrative pacing (1-10)
python3 main.py --load save-1   # resume a save
```

### First Run
1. **Character creation** — pick an archetype or build custom (8 attribute points, 4 skill points, 1 signature skill).
2. **The opening** — you wake in the wreckage. Read. The monocle is already in your pocket.
3. **Play** — the bottom bar shows available verbs. Navigate with arrow keys, Enter to choose, Esc to back out.

---

## The Interface

### The Status Box (top)
```
┌ Hang-Hi Quiet Apartments ──────────────────────────────────────────────────┐
│ Oliver Otto Onions     Early Dark, cycle 1     day 1     clues 1  beats 0/6│
│ morale ██████··   health ██████·· ▼3   lucid ██······   The Crash 1/3 ██···│
└────────────────────────────────────────────────────────────────────────────┘
```
- **Name / Time / Day / Clues / Beats** — context at a glance.
- **Meters** — Morale, Health, Lucidity, Exhaustion (green = good; exhaustion/intoxication inverted so green always means "fine").
- **Delta arrows** (▲/▼) — show what the *last command* changed. They persist until your next action.
- **Nearest unmet beat** — the last gauge tells you where the case stands.

### The Command Bar (bottom)
```
look  EXAMINE  monocle  talk  go  rest  wait  think │ cabinet log case │ save
look closely at something here     ← →  move   enter  choose   esc  quit
```
- **Three groups** divided by faint separators: *World actions* | *Information* | *Housekeeping*.
- **Only shows what's actually available** — `rest` only where there's a bed, `monocle` only while you have the lens, `talk` only when someone's here.
- **Left/Right** = switch verb. **Enter** = open target list. **Up/Down** = pick target. **Enter** = commit. **Esc** = cancel (wipes the list clean).
- **Letter keys** jump between verbs sharing that initial (e.g., `l` cycles look → log → load).

### Prose Area (middle)
Long-form narration. Uses your terminal's native scrollback — scroll up with your terminal's scroll wheel or `Shift+PageUp`.

---

## The Verbs — What You Can Do

| Verb | Target | What It Does |
|------|--------|--------------|
| **survey** | — | Re-read the full location description. |
| **examine** / `look at` | object | Main verb. Reads the object, fires passive skill voices, grants clues/effects on first look, offers active checks. |
| **monocle** | object | Look through the gold monocle. Reveals hidden truth (monocle-specific text + effects). Costs 1 cycle. |
| **talk** / `talk to` | NPC | Opens a dialogue tree. Options show skill checks with qualitative odds (`even odds`, `desperate`). |
| **who** | — | Lists everyone at the current location with their standing toward you. |
| **go** / `go to` | location | Travel. `go` alone lists exits with flavour blurbs. `go to <place>` moves you there (1 cycle). |
| **rest** | — | Sleep at your flat (Hang-Hi) or the Outside Inn. Clears exhaustion, heals health, costs 4 cycles. |
| **wait** | — | Spend 1 cycle doing nothing. Time passes. |
| **think** | — | Ask **Furthermore** (the elephant) for a hint. Falls back to Oliver reasoning it out in a skill voice if the elephant isn't clear enough yet. Costs 1 cycle. |
| **log** | — | Investigation log: clues grouped by beat, with progress counters. |
| **case** | — | Your current theory: each beat shown as ✓ (solved), · (in progress), or blank (untouched). |
| **sheet** | — | Character browser: 24 skills under 4 attributes. Interactive scroll + detail panel. |
| **cabinet** | — | Thought cabinet. Internalise known thoughts (costs cycles, raises skills when settled). Max 2 slots. |
| **save** / `load` / `saves` | slot | Auto-named slots (`save-1`, `save-2`...). `load` lists timestamps. |
| **help** / `?` | — | Shows the verb reference. |
| **quit** | — | Confirms before exiting. |

---

## Character Creation

### Four Archetypes (or Custom)
| Archetype | Focus | Signature Skill |
|-----------|-------|-----------------|
| **The Analyst** | Intellect-heavy | Logic |
| **The Face** | Psyche-heavy | Rhetoric |
| **The Survivor** | Fortitude-heavy | Physique |
| **The Operator** | Motorics-heavy | Hand-Eye |

**Custom build:** Distribute 8 attribute points (on top of 1 in each), spend 4 individual skill points, pick any signature skill.

### Attributes → Skills (6 each)
| Intellect | Psyche | Fortitude | Motorics |
|-----------|--------|-----------|----------|
| Logic | Empathy | Physique | Hand-Eye |
| Rhetoric | Suggestion | Pain-Threshold | Reaction-Speed |
| Encyclopedia | Authority | Shivers | Interfacing |
| Visual-Calculus | Esprit de Corps | Electrochemistry | Savoir-Faire |
| Conceptualisation | Volition | Endurance | Composure |
| Etymology | Inland-Empire | Half-Light | Sea-Legs |

**Rolls:** `2d6 + skill value` vs DC. The number on your sheet *is* the modifier.
- DC 9 — most people, most days
- DC 11 — coin flip for someone who invested
- DC 12 — 28% untrained, 58% specialist
- DC 14 — go become someone else first

Natural 12 (boxcars) always succeeds. Natural 2 (snake eyes) always fails.

---

## Build Archetype Guide

> *Your build decides how you solve things, not whether you can.*

### First Run? Play **The Analyst**.
- **Stats:** Intellect 4, Psyche 1, Fortitude 1, Motorics 1 (then +2 Intellect, +1 Psyche, +1 Fortitude)
- **Skills:** Logic 6, Encyclopedia 4, Visual-Calculus 3, Rhetoric 3, Empathy 2
- **Signature:** Logic
- **Why:** You see the contradictions first. The corridor *is* longer than the building. The lampposts *do* throw wrong shadows. Logic + Visual-Calculus + Etymology means the world explains itself to you. Passive voices fire constantly. You'll reach Lucidity stage 3 before anyone else.

### Want to Talk Your Way Through? Play **The Face**.
- **Stats:** Intellect 1, Psyche 4, Fortitude 1, Motorics 1 (then +2 Psyche, +1 Intellect, +1 Motorics)
- **Skills:** Rhetoric 6, Empathy 4, Suggestion 3, Authority 3, Savoir-Faire 2
- **Signature:** Rhetoric
- **Why:** Morale economy is real. Dialogue is net +25 morale with 278 recovery available. You'll pass Persuasion checks that lock others out. NPCs open up. The confrontation's three arguments are *rhetorical* — you answer them with words, not dice. Furthermore speaks to you earlier.

### Want to Tank the Town? Play **The Survivor**.
- **Stats:** Intellect 1, Psyche 1, Fortitude 4, Motorics 1 (then +2 Fortitude, +1 Psyche, +1 Motorics)
- **Skills:** Physique 6, Pain-Threshold 4, Endurance 3, Electrochemistry 3, Half-Light 2
- **Signature:** Physique
- **Why:** Health gates Physique checks. Exhaustion accrues slower (you feel it less). You can `rest` less often. Intoxication is a genuine trade you can afford. The Möbius and Outside Inn lucidity dips hurt less. You *endure* the investigation.

### Want to Move Like Water? Play **The Operator**.
- **Stats:** Intellect 1, Psyche 1, Fortitude 1, Motorics 4 (then +2 Motorics, +1 Intellect, +1 Fortitude)
- **Skills:** Hand-Eye 6, Reaction-Speed 4, Interfacing 3, Savoir-Faire 3, Composure 2
- **Signature:** Hand-Eye
- **Why:** The town's mechanisms are all somewhere else. Interfacing sees the lift without a motor room, the lamps without a supply. Savoir-Faire finds the half-second where the room looks elsewhere. You cross floors without being a thing that happened. Sea-Legs reads the vessel-floor.

### Custom Builds — Three Templates
| Template | Attribute Split | Skill Focus | Signature | Playstyle |
|----------|-----------------|-------------|-----------|-----------|
| **The Scholar** | 3/2/1/2 | Logic, Encyclopedia, Etymology, Rhetoric | Logic | Deep lore, early Lucidity, monocle-heavy |
| **The Confessor** | 2/3/1/2 | Empathy, Suggestion, Authority, Volition | Empathy | People-first, morale engine, dialogue completionist |
| **The Witness** | 2/1/3/2 | Visual-Calculus, Shivers, Pain-Threshold, Perception | Visual-Calculus | Environmental storytelling, passive voice collector |

> **Rule of thumb:** Your signature skill *will* dominate passive voices. Pick the one you want to hear.

---

## Core Mechanics

### Skill Checks
- **White checks** — retryable. Lock until the *state changes* (new clue, new beat, new dialogue heard, flag flipped). Backstop: after 2 failures they unlock regardless.
- **Red checks** — one-shot. Resolve permanently.
- **Persistence bonus** — +1 per previous failure on the same check (capped at +3). *Oliver cannot stop going over a thing.*
- **Odds shown** — qualitative (`trivial`, `even odds`, `desperate`), not percentages. Clue bonuses are factored in.

### Passive Skill Voices
Skills speak unprompted when you examine things or enter locations. Budgeted by **Narrative Density** so a room never becomes six voices shouting.
- Lines are offered in descending order of skill value — your loud skills dominate.
- A line **failed** at a given skill value stays failed until that skill grows. This makes your build *feel* different: two archetypes share only 25–43% of what they hear.

### Status Effects
| Stat | Range | Gates | Notes |
|------|-------|-------|-------|
| **Morale** | 0–100 | Persuasion checks | Dialogue net +25; objects net −105. People build you up; investigating alone grinds you down. |
| **Health** | 0–100 | Physique checks | 0 = collapse (game over). |
| **Lucidity** | 0–100 | *Everything* | **The central mechanic.** How far Oliver has noticed the manuscript. Grants diminishing returns (asymptotic). At 45+: Logic degrades, Rhetoric & Savoir-Faire improve. |
| **Exhaustion** | 0–10 | Logic, Savoir-Faire (−2 at 10) | Accrues 1 per 5 cycles. Cleared by `rest`. |
| **Intoxication** | 0–10 | Electrochemistry ↑, Logic ↓ | Past 6: narration organises by sound. A genuine trade. |

### Lucidity Stages
| Stage | Range | Effect |
|-------|-------|--------|
| 0 | 0–14 | The elephant communicates as weight and temperature. |
| 1 | 15–29 | One clause gets through. |
| 2 | 30–49 | Words arrive out of order. |
| 3 | 50–69 | Speaks plainly. |
| 4 | 70–84 | The "Nevermind" gag stops — he can finish the sentence. |
| 5 | 85–100 | Full clarity. |

### Narrative Density (1–10)
Selects between authored variants (`low` / `mid` / `high`). Never truncates — `high` is the same speech with digressions removed.
- Default: **6** (auto-scales up by 2 steps by the last beat → 8).
- Change with `pacing` in the bar or `--density N` at launch.
- Ambient lines survive to level 7 (not 6) so the town doesn't go silent too early.

### The Monocle
**Starting equipment and a verb.** The lorebook says Oliver already wears it; it reveals hidden aspects of reality.
- `monocle <thing>` — costs 1 cycle, shows monocle-specific reveal (or confirms the thing is exactly what it appears to be, which is its own category of evidence).
- Some objects have `monocle_effects` that grant clues or shift flags.

### Thought Cabinet
- **Known thoughts** appear when conditions are met (clues, beats, lucidity).
- **Internalise** a thought → occupies a slot (max 2), takes cycles (usually 4), raises skills when settled.
- **Slots are limited** — you must choose. Nothing new goes in until something settles.
- The `and_furthermore` thought unlocks the **Nevermind** ending at Lucidity ≥ 95.

---

## The World: Silvora Reefs

A parish where names are arguments that won. The fog has rotors in it. The lampposts burn green flame with no copper for forty miles. The clocks disagree by a slightly different margin each day. The floor tilts — vessels do, not floors.

### The Map (Connected Graph)
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
- **Every exit is two-way** (validator enforces this).
- **The Office** — no exits, not on the map. Reached through a *seam* at four thin places (Hang-Hi mirror, Möbius wall, Rest Assured vault, G.'s Spot third mirror) once `awakening` beat fires and Lucidity ≥ 70. Both outcomes of the crossing check travel; failure gets you there badly, never not at all.

### Key Locations
| Location | What You'll Find |
|----------|------------------|
| **Hang-Hi** | Your flat. Bed. Hallway mirror (thin place). Waterlogged notebook. |
| **Durry Kwain** | The friendly Russian. The squeegee man. Fog patches. |
| **Dude's Dews** | Chuckles the Unfunny Clown (fog). Nine years of NO MATTERS ARISING. |
| **The G.'s Spot** | Security with a hidden card. Third mirror (thin place). |
| **Möbius Strip Club** | The wall (thin place). Insta-gators circle. Names are not references — they *are* the thing. |
| **Rest Assured** | Vault with replica of Oliver's desk (thin place). Bud holds up a floor with his mouth. |
| **Outside Inn** | Seven a night. Ceiling with wrong stars. Barney. Bed. |
| **Giddyup End 'em Ribs** | Chef D. (no teeth). Pizza boxes. |
| **Cheeses Thrice** | Woolbinkle's forty cans. |
| **Lishush Mush** | The woman at the stove (hasn't tasted since 1971, hasn't been wrong since 1974). |
| **Crash Site** | The wreckage. Rotor blades above the fog. No helicopter in town. |

---

## Content Map

### Beat → Location Dependency Graph
| Beat | Primary Locations (clue-dense) | Secondary Locations | Key NPCs |
|------|-------------------------------|---------------------|----------|
| **Crash** (3/19) | Crash Site, Hang-Hi | Durry Kwain | Darek, Friendly Russian |
| **Manuscript** (6/70) | Hang-Hi, Rest Assured, Möbius, Lishush Mush | G.'s Spot, Outside Inn | Ben, Bud, Chef D., Woman at stove |
| **Quadc** (6/35) | Crash Site, G.'s Spot, Möbius | Durry Kwain, Rest Assured | Ben, Bud, Security |
| **Oracle** (8/63) | Rest Assured, Möbius, G.'s Spot | Hang-Hi, Lishush Mush | Bud, Ben, Chef D. |
| **Revilo** (8/44) | Hang-Hi, G.'s Spot, Möbius, Outside Inn | Durry Kwain, Cheeses Thrice | Barney, Woolbinkle, Security |
| **Awakening** (7/60) | Hang-Hi (mirror), Möbius (wall), Rest Assured (vault), G.'s Spot (3rd mirror) | — | Furthermore (elephant) |

> **The Seam** (Awakening gate): Requires Lucidity ≥ 70 + Awakening beat fired. Four thin places, all one-way into The Office. No exits from The Office.

### NPC → Location Map
| NPC | Home Location | Beat Contributions |
|-----|---------------|-------------------|
| Furthermore (elephant) | Everywhere | All beats (hints, lucidity progression) |
| Darek | Hang-Hi / Crash Site | Crash |
| Friendly Russian | Durry Kwain | Crash, Manuscript |
| Barney | Outside Inn | Revilo, Awakening |
| Chef D. | Giddyup / Lishush Mush | Manuscript, Oracle |
| Ben | G.'s Spot | Manuscript, Quadc, Oracle, Revilo |
| Bud Onkuhdonk | Rest Assured | Manuscript, Quadc, Oracle |
| Woolbinkle | Cheeses Thrice | Revilo |
| Sir Jerry | Hang-Hi | (Exhaustion relief only) |

### Location → Exit Map (All Two-Way Unless Noted)
```
Hang-Hi ────────────────── Durry Kwain ────────────────── Dude's Dews
   │                           │                              │
   │                           │                              │
   └───────────────────────────┼──────────────────────────────┘
                               │
                    The G.'s Spot ────────────────────────── Möbius Strip Club
                       │                   │                      │
                       │                   │                      │
              Chef D.'s Lishush Mush      │              Rest Assured
                       │                   │                      │
                       └───────────────────┼──────────────────────┘
                                           │
                                    Cheeses Thrice
                                           │
                                      Outside Inn
                                           │
                                      (The Seam) ⇣ ONE-WAY
                                           │
                                      The Office
```

> **Validator note:** Every exit is two-way. The only one-way transition is The Seam into The Office (by design, gated on Awakening + Lucidity 70).

---

## Key Characters

| NPC | Location | Role |
|-----|----------|------|
| **Furthermore (the elephant)** | Everywhere | Your companion. Hint system. Clarity = f(Lucidity). "Nevermind" gag (~30% on `think`, stops at stage 4). |
| **Revilo Snoino** | The Office | The confrontation. Three arguments. Your mirror? Your author? |
| **Darek** | Hang-Hi / Crash Site | Establishes nothing came down. You came *up*. |
| **The Friendly Russian** | Durry Kwain | First conversation. Teaches the dialogue system. |
| **Barney** | Outside Inn | Innkeeper. "Weather included" every time. |
| **Chef D.** | Giddyup / Lishush Mush | No teeth. Food that isn't merely food. |
| **Ben** | The G.'s Spot | Masks on the wall. Security with leverage. |
| **Bud Onkuhdonk** | Rest Assured | Holds up a floor with his mouth. Pushes lucidity down. |
| **Woolbinkle** | Cheeses Thrice | Forty cans. |
| **Sir Jerry** | Hang-Hi | Haircut (−2 exhaustion, the only relief in the original build). |
| **Albert** | (mentioned) | Mentioned less over forty years. |
| **Dee** | (mentioned) | Kept because somebody could not delete him. |

> **Amnesia rule:** You don't know names until you earn them. The status bar reads *the man from the harbour* until you find your flat. NPCs are descriptions — *the friendly Russian*, *the man with the squeegee* — until you speak to them. The elephant is *the elephant* until the thought that names him arrives.

---

## Investigation & Progression

### Beats (The Case Spine)
Six beats, each over-supplied with clues so two players reach the same revelation via different routes:

| Beat | Clues | Threshold | What It Unlocks |
|------|-------|-----------|-----------------|
| **Crash** | 19 | 3 | You came up, not down. |
| **Manuscript** | 70 | 6 | The typewriter motif. The drafts. |
| **Quadc** | 35 | 6 | The helicopter / quadcopter. The rotor sound. |
| **Oracle** | 63 | 8 | O.R.A.C.L.E. is not a device — it's Oliver's analytical mind. |
| **Revilo** | 44 | 8 | Snoino Revilo = reversal of Oliver Onions. |
| **Awakening** | 60 | 7 | The seam to The Office. |

**Validator guarantee:** No beat needs more clues than exist. `validate_content.py` fails the build if any beat is unsolvable.

### Clues
- **Tagged** — `kindness` (46 clues), `personhood` (26 clues), `red herring` (flagged but don't count toward beats).
- **Tag-count gates** — Endings check `kindness ≥ 5`, `personhood ≥ 4` — *any* 5 of 20, *any* 4 of 26. Not specific clues.

### Dialogue
- **Node graph** with conditions/effects. Options show skill checks.
- **Stage directions** (third-person about speaker, second-person about player) render on the narration channel, not as speech.
- **Morale economy** — objects net −105 morale; dialogue net +25 with 278 recovery available. Investigating alone grinds you down; people build you back up.

---

## Save Strategy

### When to Save
| Moment | Why |
|--------|-----|
| **After character creation** | Baseline. Archetype choice is permanent. |
| **Before first `go to`** | First travel = first cycle expenditure. |
| **After each beat fires** | Major progress markers (Crash → Manuscript → Quadc → Oracle → Revilo → Awakening). |
| **Before The Seam** | **Critical.** One-way transition into The Office (no exits). Lucidity ≥ 70 + Awakening beat required. |
| **Before confrontation** | The Office has no exits, nothing to examine. Evidence gates endings — you can't grind more clues there. |
| **After major dialogue branches** | Some NPC conversations gate endings (e.g., telling Revilo townspeople aren't real withdraws "Recommend company"). |

### Save Slots
- **Auto-named:** `save-1`, `save-2`, `save-3`... (timestamped)
- **No limit** on slots. Disk space only.
- **Overwrite protection:** `save` menu shows "overwrite save-1" explicitly.
- **Load menu** shows timestamp: `save-3   (2026-01-15 22:47)`.

### Recommended Minimum
Keep **3 slots** rotating:
1. **Pre-Seam** (lucidity 70+, awakening done)
2. **Pre-Confrontation** (all evidence gathered)
3. **Latest** (current position)

> **No new-game-plus.** The game stops at the epilogue. No carryover. Saves are for *this* run only.

---

## The Endgame

The confrontation in **The Office** (no exits, nothing left to examine) is fought with **evidence, not dice**. Revilo makes three cases:

1. **"You are not a man. You are a draft."** — Accept and extend: *and so are you*. Requires noticing the page stopped on **your** side.
2. **"Nothing is lost. None of them are anybody."** — Name them: Albert, Dee, Bud, Woolbinkle. Gated on `personhood ≥ 4`.
3. **"I have kept you alive."** — Evidence: the shim, the 22 forms, the 200 drafts dated 11 years apart at the bottom and 4 days at the top. Gated on `kindness ≥ 5`.

### Four Endings
| Ending | Requirement | Cost |
|--------|-------------|------|
| **and he does** | Always | Oliver takes the language. Silvora Reefs stops. |
| **and he does not** | Always | Revilo keeps it. Oliver stays, never knows. |
| **Recommend company** | Kindness ≥ 5, Personhood ≥ 4, Argument 2 answered | Neither gets the last word. |
| **Nevermind** | `and_furthermore` internalised, Lucidity ≥ 95 | The elephant finishes the sentence. |

> Tell Revilo the townspeople are not real → third ending withdrawn (not punishment — you declined the argument).

**Epilogues** carry consequence lines that only print if you earned the clue behind them. Two players choosing the same ending read different epilogues.

**Report card** at the end: clues, beats, locations, people, lucidity, cycles, kindness, personhood.

---

## Tips for New Players

1. **Examine everything first.** `look at` is your main verb. First examination grants clues/effects; re-examining gives condensed text.
2. **Use the monocle.** It's not a plot token — it's a standing decision. `monocle <thing>` every room.
3. **Talk to everyone.** Morale recovery lives in conversation. The shallow run (objects only) ends at morale ~20; the deep run (all dialogue) sits at 98–100.
4. **Fail forward.** White checks retry on state change. Red checks are final. The persistence bonus (+1/failed attempt, cap +3) means a 45% check becomes 70% if you keep coming back.
5. **Rest.** Exhaustion accrues 1 per 5 cycles. Your flat (Hang-Hi) and the Outside Inn have beds. `rest` clears exhaustion, heals 12 health, costs 4 cycles.
6. **Think when stuck.** `think` always returns something actionable. Early on, Oliver reasons it out in his best skill voice; later, Furthermore speaks.
7. **Internalise thoughts.** Two slots. They raise skills permanently. The first thought teaches the mechanic.
8. **Watch Lucidity.** It's the game's spine. Gains diminish (asymptotic). It dips at Möbius and Outside Inn (Insta-gators, Bud). At 45+ Logic degrades but Rhetoric/Savoir-Faire improve.
9. **Density is a preference, not difficulty.** Default 6 runs long early, tight late. Set `--density 4` for tighter prose throughout; `--density 9` for maximal digression.
10. **Save often.** `save` auto-names slots. `load` lists timestamps. No penalty for saving.

---

## Quick Reference Card

### Verb Bar Layout (Interactive Mode)
```
[WORLD ACTIONS]          [INFORMATION]         [HOUSEKEEPING]
survey  examine  monocle  talk  go  rest  wait  think  │  cabinet  log  case  │  save  load  quit
        look at    look       who           │  thoughts notes theory  │
```

### Key Bindings
| Key | Action |
|-----|--------|
| `←` `→` | Cycle verbs (Left/Right) |
| `Enter` | Open target list / Confirm selection |
| `↑` `↓` | Navigate target list |
| `Esc` | Cancel (wipes list) / Back out of menus |
| `l` / `t` / `g` / `s` | Jump to verb by initial (cycles if multiple) |
| `?` | Help (shows verb reference) |

### Check Odds Cheat Sheet
| Displayed Odds | Approximate Success (with avg stats) |
|----------------|--------------------------------------|
| `trivial` | 85%+ |
| `good odds` | 65–84% |
| `even odds` | 45–64% |
| `poor odds` | 25–44% |
| `desperate` | <25% |
| *+1 per previous failure (cap +3)* | Persistence bonus |

### Status Meter Colors
| Meter | Green = Good | Red = Bad | Inverted (Green = Low) |
|-------|--------------|-----------|------------------------|
| Morale | High | Low | — |
| Health | High | Low | — |
| Lucidity | High | Low | — |
| Exhaustion | — | — | **Yes** (0 = fresh) |
| Intoxication | — | — | **Yes** (0 = sober) |

### Density Bands
| Flag | Prose Style |
|------|-------------|
| `--density 1–3` | Maximal digression, every ambient line |
| `--density 4–6` | Default (6). Full early, tight late (auto-scales +2) |
| `--density 7–10` | Tight throughout. Digressions removed, voice intact |

### Lucidity Stage Quick Ref
| Stage | Range | Furthermore | Logic/Rhetoric/Savoir-Faire |
|-------|-------|-------------|----------------------------|
| 0 | 0–14 | Weight/temperature | Normal |
| 1 | 15–29 | One clause | Normal |
| 2 | 30–49 | Out of order | Normal |
| 3 | 50–69 | Plain speech | Normal |
| 4 | 70–84 | **Nevermind gag stops** | Logic ↓, Rhetoric/Savoir-Faire ↑ |
| 5 | 85–100 | Full clarity | Logic ↓↓, Rhetoric/Savoir-Faire ↑↑ |

---

## Glossary

| Term | Definition |
|------|------------|
| **2d6** | Two six-sided dice. Bell curve (2–12), not flat. Your skill value *is* the modifier. |
| **Awakening** | Sixth beat. Fires at 7/60 clues. Gates The Seam to The Office. |
| **Beat** | Investigation milestone. Six total: Crash, Manuscript, Quadc, Oracle, Revilo, Awakening. Each over-supplied with clues. |
| **Boxcars** | Natural 12 on 2d6. Always succeeds. |
| **Clue** | Evidence entry. Tagged: `kindness` (46), `personhood` (26), `red herring` (flagged, don't count). |
| **Confrontation** | Final scene in The Office. Fought with evidence, not dice. Three arguments from Revilo. |
| **C.C.C.C.** | Oliver's analytical mind (lorebook). Not a corporate conspiracy. |
| **Density** | Narrative pacing dial (1–10). Selects `low`/`mid`/`high` prose variants. Never truncates. |
| **Delta arrows** | ▲/▼ on status meters. Show what *last command* changed. Persist until next action. |
| **Diminishing returns** | Lucidity gains scale by remaining headroom. Asymptotic — waking up takes real investigation. |
| **Elephant** | Furthermore. Your companion. Clarity = f(Lucidity). "Nevermind" gag ~30% on `think`, stops at stage 4. |
| **Ending** | Four: *and he does*, *and he does not*, *Recommend company*, *Nevermind*. Gated on tag-counts. |
| **Epilogue** | Ending-specific aftermath. Consequence lines only print if you earned the backing clue. |
| **Exhaustion** | 0–10. Accrues 1/5 cycles. −2 Logic/Savoir-Faire at 10. Cleared by `rest` (bed required). |
| **Furthermore** | The elephant. Also: the thought `and_furthermore` (unlocks Nevermind ending at Lucidity ≥ 95). |
| **Gull** | Does not call. Gulls call. (First ambient clue something is wrong.) |
| **Hook** | Your method: attention circles evidence until dealt with. "That is the whole of your method and most of your problem." |
| **Internalise** | Commit a known thought to cabinet (costs cycles, occupies slot, raises skills when settled). |
| **Intoxication** | 0–10. Electrochemistry ↑, Logic ↓. Past 6: narration organises by sound. Genuine trade. |
| **Kindness** | Clue tag (46 clues). Gates *Recommend company* ending (≥5) and Argument 3 (≥5). |
| **Lucidity** | **Central mechanic (0–100).** How far Oliver has noticed the manuscript. Gates skills, Furthermore clarity, world description, seam. |
| **Manuscript** | Second beat (6/70). The typewriter motif. Drafts. Replica desk in Rest Assured vault. |
| **Monocle** | Starting equipment + verb. `monocle <thing>` reveals hidden truth. Costs 1 cycle. |
| **Morale** | 0–100. Gates persuasion. Objects net −105; dialogue net +25 (278 recovery available). |
| **Nevermind** | Elephant's gag. Fires ~30% on `think` until stage 4. Also: fourth ending (Lucidity ≥ 95 + thought internalised). |
| **O.R.A.C.L.E.** | Not a device. Oliver's analytical mind. Corporate reading is the surface, then dismantled. |
| **Persistence bonus** | +1 per previous failure on same check (cap +3). "Oliver cannot stop going over a thing." |
| **Personhood** | Clue tag (26 clues). Gates *Recommend company* ending (≥4) and Argument 2 (≥4). |
| **Quadc** | Third beat (6/35). Helicopter/quadcopter. Rotor sound above fog. |
| **Red check** | One-shot skill check. Resolves permanently. No retry. |
| **Red herring** | Clue flag. Doesn't count toward beats. Marked "(red herring?)" in log. |
| **Report card** | End-of-game summary: clues, beats, locations, people, lucidity, cycles, kindness, personhood. |
| **Revilo** | Fifth beat (8/44). Snoino Revilo = reversal of Oliver Onions. Confrontation antagonist. |
| **Save slot** | Auto-named (`save-1`, `save-2`...). Timestamped. No limit. Overwrite explicit. |
| **Seam** | One-way transition into The Office. Four thin places (mirrors, wall, vault). Requires Awakening + Lucidity ≥ 70. |
| **Shivers** | Skill. "Silvora Reefs arriving on the skin all at once." Environmental awareness. |
| **Snake eyes** | Natural 2 on 2d6. Always fails. |
| **Tag-count gate** | Ending requirement: *any* N clues of a tag (kindness/personhood). Not specific clues. |
| **Thought cabinet** | Internalise known thoughts (max 2 slots). Costs cycles. Raises skills when settled. |
| **White check** | Retryable skill check. Locks until state changes (new clue/beat/dialogue/flag). Backstop: unlocks after 2 failures. |
| **3:33** | Watch time. Has always said 3:33. Second hand held — "by somebody with better things to do." |

---

## Accessibility Notes

### Terminal Compatibility
- **No curses** — uses ANSI stdout. Works in any terminal (xterm, kitty, alacritty, Windows Terminal, iTerm2, tmux, screen, SSH).
- **Graceful degradation** — frame computes from actual terminal size every draw:
  - Wide: full context row, all gauges, full verb row
  - Narrower: gauges drop from right; verb row windows with `‹ ›`
  - <46 cols: status box hidden; command bar stays
  - <12 rows: hint line hidden
  - <8 rows: frame off entirely, plain scrolling
- **SIGWINCH handler** — re-frames on resize automatically.

### Visual Accessibility
- **Colour-blind safe palette** — UI uses distinct hues + intensity + symbols (██████·· bars, not colour alone).
- **Inverted meters** — Exhaustion/Intoxication use green = low (good) so "green always means fine."
- **No flashing** — no animations, no blinking, no seizure triggers.
- **High contrast** — default palette works on light or dark backgrounds.

### Cognitive Accessibility
- **Narrative Density (1–10)** — reduces prose volume without truncation. `high` variant = same speech, digressions removed. Set `--density 3` for minimal cognitive load.
- **Qualitative odds** — checks show `even odds` / `desperate`, not percentages. Judgement calls, not arithmetic.
- **No time pressure** — turn-based. `wait` / `rest` advance time deliberately. No real-time elements.
- **Never trapped** — `Esc` always backs out. Blank input = "not now" on cabinet. `quit` confirms.

### Screen Readers
- **Plain text output** — no curses/TUI control codes that confuse screen readers.
- **Structured headers** — status box, verb bar, prose area are linear readable.
- **Verb hints** — `look closely at something here` read aloud on focus.
- **Typed parser fallback** — `python3 main.py` piped input works entirely via stdin/stdout.

### Audio
- `--voice` flag enables Piper TTS (optional, requires `piper-tts` + audio player). Speaks all narration.

---

## FAQ

### Can I fail / get a game over?
**Health 0 = collapse** (game over). Otherwise: no. Failed checks give different clues/angles. White checks retry. The story continues.

### Do I need to read everything?
No. **Density** controls volume. `--density 4` gives tight prose throughout. `think` always gives actionable hints. The log (`log`) summarises clues by beat.

### What does the monocle actually do?
`monocle <thing>` shows a **different description** (monocle reveal) + may grant clues/effects. Some things are "exactly what they appear to be" — which is itself evidence. Costs 1 cycle. Use it every room.

### Is there a time limit?
No hard limit. **Cycles** advance on actions (examine, travel, wait, think, rest). Exhaustion accrues 1/5 cycles. `rest` clears it (4 cycles). You can take 300+ cycles.

### Can I respec / change build mid-game?
No. Character creation is once. Thought cabinet (2 slots) raises skills permanently when thoughts settle — that's your progression.

### What's the difference between white and red checks?
**White** = retryable (locks until state changes, backstop after 2 failures). **Red** = one-shot (permanent). Most object checks are white; vices (drinks) are repeatable; confrontation checks are red.

### Why does Lucidity go down sometimes?
Möbius (Insta-gators) and Outside Inn (Bud Onkuhdonk) push it down. This is intentional — lucidity *dips* are visible now that gains are asymptotic.

### Do I need to play Disco Elysium first?
No. Inspired by, not dependent on. The mechanics are explained in-game and in this guide.

### Can I play with a keyboard only / no mouse?
Yes. **Entirely keyboard-driven.** Arrow keys, Enter, Esc, letter keys. No mouse required.

### What's the "reversal" thing?
**Snoino Revilo** = letter-perfect reversal of **Oliver Onions**. `is_reversal("Oliver Onions", "Snoino Revilo")` returns `True`. Central to the lorebook and the confrontation.

### Are there missable endings?
**Nevermind** requires `and_furthermore` thought internalised + Lucidity ≥ 95. **Recommend company** requires kindness ≥ 5, personhood ≥ 4, and answering Argument 2. If you tell Revilo townspeople aren't real, Recommend company is withdrawn. Other two always available.

### How long is a playthrough?
- **Focused run** (objects + main dialogue): ~8–12 hours, 2 endings
- **Completionist** (all dialogue, all objects, all thoughts): ~20–30 hours, 4 endings
- **Speedrun** (known path, minimal dialogue): ~2–3 hours

### Where are my saves?
`game/saves/` — JSON files. Portable. Copy them between machines.

---

## Commands Reference (Typed Parser)

If you prefer typing (or are piping input), the typed verb parser accepts:

```
survey / look / l / look around
look at <thing> / examine <thing> / x <thing> / inspect <thing>
monocle <thing> / look through monocle at <thing>
talk to <person> / talk <person> / speak to <person> / ask <person>
who / people
go / exits / leave
go to <place> / go <place> / travel to <place>
log / clues / notes
case / theory
sheet / stats / character / me
cabinet / thoughts
think / furthermore / hint
wait / z
rest / sleep / lie down
save [slot] / load [slot] / saves
help / ? / commands
quit / exit / q
```

---

## Files of Interest

| File | Purpose |
|------|---------|
| `main.py` | Entry point, verb parser, game loop |
| `game_state.py` | Hub: conditions, effects, clock, save/load |
| `player.py` | Oliver — skills, status, inventory, thoughts |
| `skill_checks.py` | 2d6 resolution, white/red ledger, persistence |
| `investigation.py` | Clues, beats, scene state, retry fingerprint |
| `dialogue_engine.py` | Conditional node graph |
| `furthermore.py` | Companion, thought cabinet, hints |
| `locations.py` | Lazy-loading location/object registry |
| `npcs.py` | Cast and relationship tracking |
| `narrative_density.py` | The 1–10 pacing dial |
| `wordplay_engine.py` | Reversals, anagrams, alliteration |
| `ui.py` | Channels: narration, skill voice, speech, monocle |
| `config.yaml` / `config.py` | All tunables |
| `content/` | JSON — locations, NPCs, clues, thoughts, endings |
| `tools/test_mechanics.py` | 85 unit tests |
| `tools/validate_content.py` | Structural content checks |
| `tools/voice_lint.py` | Narration-rule enforcement |

---

## Final Note

> *The game renders at what the old dial called density 1 — the fullest telling, every object described in full, ambient lines firing freely. The thinner authored variants are still in the content files, unreachable, because they are real writing and deleting them would be irreversible in a way that removing a menu entry is not.*

You are not here to win. You are here to notice.

**Good luck, Oliver.**