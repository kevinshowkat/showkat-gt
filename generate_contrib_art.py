#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import subprocess
from pathlib import Path

# 5x7 uppercase font (columns x rows)
FONT = {
    "S": [
        "11111",
        "1....",
        "1....",
        "11111",
        "....1",
        "....1",
        "11111",
    ],
    "H": [
        "1...1",
        "1...1",
        "1...1",
        "11111",
        "1...1",
        "1...1",
        "1...1",
    ],
    "O": [
        "11111",
        "1...1",
        "1...1",
        "1...1",
        "1...1",
        "1...1",
        "11111",
    ],
    "W": [
        "1...1",
        "1...1",
        "1...1",
        "1.1.1",
        "1.1.1",
        "1.1.1",
        "1...1",
    ],
    "K": [
        "1...1",
        "1..1.",
        "1.1..",
        "11...",
        "1.1..",
        "1..1.",
        "1...1",
    ],
    "A": [
        ".111.",
        "1...1",
        "1...1",
        "11111",
        "1...1",
        "1...1",
        "1...1",
    ],
    "T": [
        "11111",
        "..1..",
        "..1..",
        "..1..",
        "..1..",
        "..1..",
        "..1..",
    ],
}

WORD = "SHOWKAT"
GRID_WEEKS = 53


def run(cmd, cwd: Path, env=None):
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True, shell=shell,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def compute_start_sunday(today: dt.date) -> dt.date:
    # Most recent Sunday on or before today
    days_since_sunday = (today.weekday() + 1) % 7  # Monday=0..Sunday=6
    end_sunday = today - dt.timedelta(days=days_since_sunday)
    start = end_sunday - dt.timedelta(weeks=52)
    return start


def render_word_positions(word: str, spacing: int = 1):
    # Returns list of (col, row) for pixels that are on.
    word = word.upper()
    cols = []
    x = 0
    for idx, ch in enumerate(word):
        if ch not in FONT:
            raise ValueError(f"Unsupported character: {ch}")
        glyph = FONT[ch]
        for row in range(7):
            row_bits = glyph[row]
            for col in range(5):
                if row_bits[col] != '.':
                    cols.append((x + col, row))
        x += 5
        if idx != len(word) - 1:
            x += spacing
    width = x
    return cols, width


def make_commits(repo: Path, positions, start_date: dt.date, offset_cols: int, intensity: int):
    art_file = repo / "art.txt"
    art_file.touch(exist_ok=True)

    # Sort by date order (earliest first)
    positions_sorted = sorted(positions, key=lambda p: (p[0], p[1]))

    total = len(positions_sorted) * intensity
    made = 0
    for col, row in positions_sorted:
        date_day = start_date + dt.timedelta(weeks=col + offset_cols) + dt.timedelta(days=row)
        # Midday baseline to keep ordering stable
        base_dt = dt.datetime.combine(date_day, dt.time(hour=12, minute=0, second=0))
        for k in range(intensity):
            stamp = base_dt + dt.timedelta(minutes=k)
            line = f"{stamp.isoformat()} col={col} row={row}\n"
            with art_file.open("a", encoding="utf-8") as fh:
                fh.write(line)
            run(["git", "add", "art.txt"], cwd=repo)
            env = os.environ.copy()
            iso = stamp.isoformat()
            env["GIT_AUTHOR_DATE"] = iso
            env["GIT_COMMITTER_DATE"] = iso
            run(["git", "commit", "-m", f"pixel col={col} row={row} [{k+1}/{intensity}]"], cwd=repo, env=env)
            made += 1
    return made


def main():
    parser = argparse.ArgumentParser(description="Generate SHOWKAT contribution art across the current contribution window.")
    parser.add_argument("--intensity", type=int, default=5, help="Commits per active day (pixel). Default: 5")
    parser.add_argument("--anchor", choices=["left", "center", "right"], default="left",
                        help="Base alignment within the rolling 52-week window. Default: left")
    parser.add_argument("--offset", type=int, default=0,
                        help="Additional column offset applied after anchoring (positive shifts right, negative left). Default: 0")
    parser.add_argument("--start-date", type=str, default=None,
                        help="Optional ISO date (YYYY-MM-DD) for the Sunday column 0 should represent.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parent

    # Initial commit if repo has no commits yet
    try:
        subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=str(repo), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        has_commit = True
    except subprocess.CalledProcessError:
        has_commit = False
    if not has_commit:
        # Create an initial commit so branch exists
        (repo / ".keep").write_text("init\n", encoding="utf-8")
        run(["git", "add", ".keep", "README.md", "generate_contrib_art.py", ".gitignore"], cwd=repo)
        run(["git", "commit", "-m", "chore: initial commit"], cwd=repo)

    positions, width = render_word_positions(WORD, spacing=1)
    if width > GRID_WEEKS:
        raise SystemExit(f"Word width {width} exceeds available {GRID_WEEKS} weeks.")

    if args.anchor == "left":
        base_offset = 0
    elif args.anchor == "right":
        base_offset = GRID_WEEKS - width
    else:  # center
        base_offset = (GRID_WEEKS - width) // 2

    effective_offset = base_offset + args.offset
    if effective_offset < 0:
        raise SystemExit("Effective offset is negative. Increase offset or choose a different anchor.")
    if effective_offset + width > GRID_WEEKS:
        raise SystemExit(
            f"Word width {width} with effective offset {effective_offset} exceeds {GRID_WEEKS} weeks. Adjust anchor/offset."
        )

    if args.start_date:
        try:
            provided = dt.datetime.strptime(args.start_date, "%Y-%m-%d").date()
        except ValueError:
            raise SystemExit("--start-date must be in YYYY-MM-DD format")
        if provided.weekday() != 6:
            raise SystemExit("--start-date must be a Sunday to align with contribution columns.")
        start_date = provided
    else:
        start_date = compute_start_sunday(dt.date.today())
    made = make_commits(repo, positions, start_date, effective_offset, max(1, args.intensity))

    print(
        f"Anchor: {args.anchor}, base offset: {base_offset}, extra offset: {args.offset}, "
        f"effective offset: {effective_offset}."
    )

    print(f"Done. Created {made} commits for '{WORD}'.")


if __name__ == "__main__":
    main()
