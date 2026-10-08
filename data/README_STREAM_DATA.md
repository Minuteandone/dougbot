# Dougbot stream-derived training data

This folder is an augmentation pass for Dougbot.

## Sources used

1. **I trained an Ai on 380,000 Twitch Chat messages (VOD)** — recorded 2024-11-14
   - https://www.youtube.com/watch?v=Q2wpD47uDTo
   - Used for behavioral situations around training/testing a chat model, reacting to model failures, comparing an AI to live chat, and turning debugging into a stream bit.

2. **Twitch Chat makes a painting for Charity (then Doug and Chat play Worms WMD)** — streamed 2024-06-24
   - Source summary: Doug-hole Wiki stream list
   - Edited video: https://www.youtube.com/watch?v=6N3GoKZbzQM
   - Used for behavioral situations around crowd coordination, voting, collaborative art, schedule derailment, factional chat behavior, and turning the process itself into the bit.

## Important provenance note

The environment could locate the VODs and public summaries but could not retrieve YouTube's full auto-caption transcript endpoint. Therefore these examples are **not represented as transcripts** and are not verbatim DougDoug dialogue.

Rows marked `stream-derived-synthetic` are newly-written conversations derived from the real stream setup/interaction pattern. They include stream title, date, URL, derivation note, and `verbatim: false` metadata.

## Counts

- `stream_training.jsonl`: 1,800 rows
  - 1,440 stream-derived synthetic interactions
  - 360 normal-conversation / identity-preservation examples
- `train_2227.jsonl`: 2,227 rows
  - original 427-row Dougbot starter corpus
  - plus the 1,800 rows above

## LoRA experiment

`lora_stream_v1/` is a genuine PEFT LoRA experiment targeting q/v projections in transformer layers 20-23 (45,056 trainable parameters). The 8-step checkpoint is included for reproducibility, **but it is rejected as a final adapter** because held-out behavior was still too generic and one innocuous governance-style prompt triggered an unnecessary refusal. Do not treat it as the shipping model.

The useful artifact from this pass is primarily the improved source-labelled dataset.
