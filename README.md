# CS2 Loadout Analyzer

A command-line tool that parses CS2 demo files (`.dem`) and outputs the per-round loadout of a specified player.

## Requirements

- Python 3.8+
- [demoparser2](https://github.com/LaihoE/demoparser) (must be up to date)
- pandas

Install dependencies:

```
pip install --upgrade demoparser2 pandas
```

> **Important:** An outdated version of `demoparser2` will cause `EntityNotFound` errors. Always ensure you are on the latest version.

## Usage

```
python loadoutv2.py -p <path> -n <player name>
```

### Arguments

| Argument | Description |
|----------|-------------|
| `-p` / `--path` | Path to a single `.dem` file, or a directory containing multiple `.dem` files |
| `-n` / `--name` | The in-game name of the player to analyze (case-sensitive) |

### Examples

**Single demo file:**
```
python loadoutv2.py -p C:\demos\THGDemo.dem -n THG
```

**Directory of demos:**
```
python loadoutv2.py -p C:\demos -n THG
```

When a directory is provided, the script processes every `.dem` file found in it. Any demo that does not contain the specified player is skipped automatically.

## Output

For each demo, the script prints the player's loadout at the start of every round, sorted by category:

```
>>> Processing: THGDemo.dem
   --- Loadout for THG ---
   Round 1: Glock-18
   Round 2: Desert Eagle
   Round 3: AK-47, Glock-18
   Round 4: AK-47, Glock-18, Flashbang, High Explosive Grenade, Smoke Grenade
   ...
```

## Loadout Categories

Items are sorted in the following order within each round:

1. **Primary weapons** — Rifles, SMGs, Shotguns, LMGs, Snipers
2. **Pistols** — Non-default pistols listed first, default pistols (Glock-18, USP-S, P2000) last
3. **Zeus x27**
4. **Grenades** — Molotov/Incendiary, HE, Flashbang, Smoke, Decoy
5. **Equipment** — Kevlar, Kevlar + Helmet, Defuse Kit

Knives, charms, name tags, and C4 are excluded from the output.

## Notes

- Player names are **case-sensitive** and must match the in-game name exactly.
- The script samples inventory at freeze time, 5 seconds in, and 10 seconds in per round to account for late buys.
- If a player is dead or carries only a knife at round start, the round is shown as `Knife Only / Dead`.
