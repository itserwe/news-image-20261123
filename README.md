# The World Today — 23 November 2026

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/itserwe/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/itserwe/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

A single-page newspaper front page for Monday 23 November 2026: the Iran
war widens, COP31 ends in the blame game, and NATO meets in emergency
session after Russian missiles land in Poland — with 34 more stories, a UTC
timeline of the day, a numbers strip, and a map of where it all happened.
Every item carries a CONFIRMED, REPORTED or CLAIMED mark plus its source,
and a date-check box leaves out events that happened on other days.

## How the page is made

`main.py` draws `entry.png` (1024 × 1024) with Pillow — masthead,
headlines, lead stories, secondaries, map, briefs, everything. No image
generator is involved; run the script and the page comes out again.

## Regenerate

```
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png` and refreshes the `entry.png` next to the script.
