# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/itserwe/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/itserwe/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

A one-page newspaper front page summing up the world's news of Monday 23 November 2026: the Iran war widens as Tehran hits Bahrain and mines two tankers in the Strait of Hormuz, the COP31 blame game begins after the "worst ever" summit, and NATO holds an emergency session after Russian missiles fell in Poland — plus 34 more stories, a UTC timeline, a numbers strip and a world map of where it all happened. The page is drawn with PIL (see `build/compose.py`); every story carries a CONFIRMED / REPORTED / CLAIMED status and a source, and a date-check box keeps out events from other days.

## Run it

```
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```
