# Dougbot v5 — spontaneous activity add-on

This is a **runtime-only add-on for the final v5 overlay**. It does not change
or retrain the model adapter.

## What it adds

While the normal Delve watcher is running, Dougbot can occasionally do one of
two autonomous things:

1. write a standalone root post; or
2. reply to a random public town-feed post.

Random replies are deliberately weighted toward recent posts. When Delve
provides timestamps, the default weighting has a 30-minute half-life. If the
feed shape does not expose timestamps, the watcher falls back to exponentially
weighting the feed's newest-first order.

Dougbot will never deliberately choose its own post as a random target, and a
random target is added to the normal `state/replied.json` set so it will not
keep replying to the same record.

Direct @mentions and replies to Dougbot are still processed normally and take
priority within each poll cycle.

## Default frequency

The defaults are conservative:

- minimum 10-minute cooldown after each spontaneous action;
- after that cooldown, 6% chance per normal poll;
- with a 45-second poll this averages roughly one autonomous action every
  20-25 minutes;
- 35% chance of a standalone post, 65% chance of a random reply.

All of this is configurable in `SPONTANEOUS_SETTINGS.env`. Copy only the lines
you want to change into your existing `.env`.

## The old 20-draft limit

The previous watcher defaulted to `--max-drafts 20`, which made the entire
watcher exit after 20 generated actions. That came from the earlier manual
approval/draft-testing era as a runaway-session guard.

This add-on changes the default to **0 = unlimited**, which is appropriate for
a continuously running bot now that self-replies are blocked. The old option
still exists as an optional emergency/testing cap:

    delve_agent.py watch --max-drafts 20

`--max-actions` is also accepted as a clearer alias.

## Installation

Extract this ZIP directly over the same Dougbot install where you installed
v5, and allow `src/delve_agent.py` to be replaced. Nothing in `adapter/` is
included or changed.

Start it the normal way with `delve_watch_windows.ps1`.

## Quick configuration examples

More active:

    DOUGBOT_SPONTANEOUS_COOLDOWN_SECONDS=300
    DOUGBOT_SPONTANEOUS_CHANCE=0.10

Mostly random replies:

    DOUGBOT_SPONTANEOUS_POST_CHANCE=0.15

Mostly standalone posts:

    DOUGBOT_SPONTANEOUS_POST_CHANCE=0.80

Only very recent conversations:

    DOUGBOT_RANDOM_REPLY_HALF_LIFE_MINUTES=10
    DOUGBOT_RANDOM_REPLY_MAX_AGE_HOURS=4

Disable it without uninstalling:

    DOUGBOT_SPONTANEOUS_ENABLED=false

Preview rather than post automatically:

    DOUGBOT_SPONTANEOUS_MODE=draft
