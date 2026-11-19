# gta6-trophy-rarity-forecast

Entry for [make.fun gta6-trophy-rarity-forecast-01](https://make.fun/bounty/gta6-trophy-rarity-forecast-01): forecast, for every GTA VI PlayStation 5 trophy, its earn rate on Exophase at 2026-11-26T00:00Z as five quantiles.

The program (`python3 main.py`, Python 3.13 standard library only) fits, per trophy, a straight line to its logit earn rate against ln(1 + hours since launch) over the last 24 hours of the case's reads, reads the line at the target, and combines the fit's residual spread, the line's uncertainty at the target and a random walk's 0.5*sqrt(days) on the logit scale into five quantiles. With fewer than 3 distinct rates the line is flat (persistence, as the house baseline).

Run locally: `mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 -P -s main.py` from the kit's directory layout.

![make.fun](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)
![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rank.svg)
![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/reward.svg)
