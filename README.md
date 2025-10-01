# showkat-gt

Generate GitHub contribution art that spells "SHOWKAT" across the rolling 52-week contribution window.

This repository contains a Python script that creates backdated commits on specific days to draw the text on your contributions graph. It uses a simple 5x7 bitmap font and makes several commits per active day to control the intensity.

- Word: SHOWKAT (fixed)
- Alignment: configurable (`left`, `center`, `right`). Default is `left` so the word hugs the start of the window.
- Default intensity: 5 commits per pixel (medium-dark green)

## Usage

Prereqs: Python 3 and Git.

Run from the repo root (defaults produce a single left-aligned "SHOWKAT"):

```
python3 generate_contrib_art.py --intensity 5
```

Key options:

- `--anchor`: base alignment within the 52-week window (`left`, `center`, `right`). Default: `left`.
- `--offset`: extra column shift applied after anchoring (positive moves right, negative left).
- `--start-date`: optional ISO date if you want to pin column 0 to a specific Sunday (useful for recreating past layouts).
- `--intensity`: commits per “pixel.” Higher numbers make darker squares.

After generating the commits, push to the default branch:

```
git push -u origin main
```

Notes
- Commits are attributed using the repo’s local git config. Update with:
  - `git config user.name "Your Name"`
  - `git config user.email "your-email@example.com"`
- Only pushes to a public repository’s default branch count toward your contribution graph.
- You can rerun the script after changing anchor/offset/intensity; it only appends new commits. Re-running occasionally keeps the art from slipping off the left edge as the contribution window advances.
- To recreate a specific historical arrangement, pass the earlier Sunday via `--start-date` so the pixels land on the exact same days.
