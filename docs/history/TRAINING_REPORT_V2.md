# Dougbot v2 training report

## What is actually trained

This release uses a **real LoRA adapter**, not prompt tuning. The adapter changes 1,466,368 trainable parameters attached to the final 8 transformer layers of Qwen2.5-0.5B-Instruct. It targets attention (`q/k/v/o`) plus MLP (`gate/up/down`) projections.

The shipped checkpoint received **80 optimizer steps** of assistant-only supervised fine-tuning. System/user tokens were masked from loss. The runtime does **not** inject style demonstrations; its system message only establishes identity, non-impersonation, and a basic safety boundary.

## Data

The deduplicated training pool contains **3,012 conversations**. It includes:

- stream-derived synthetic interactions based on two public DougDoug stream situations;
- multi-turn chat interactions derived from those stream structures;
- original challenge/comedy behavior examples;
- ordinary Delve-style conversational preservation examples;
- harmless ambiguous posts that a tiny base model sometimes handles awkwardly.

The stream-derived rows are **not transcripts and are not presented as verbatim DougDoug dialogue**. They are newly written examples derived from public stream premises and interaction structure. Provenance is recorded in `data/STREAM_SOURCES.json` and the JSONL metadata.

## Evaluation notes

Earlier smaller q/v-only LoRAs remained too close to stock Qwen and were rejected. The stronger checkpoint began producing the intended behavior with only the minimal `You are Dougbot` training identity. In sampled held-out tests it reframed scoring failures as a new phase/plan and joined absurd Delve premises rather than merely correcting them.

The model is still only 0.5B parameters, so expect occasional nonsense. The Delve action layer therefore requires explicit human approval for every state-changing action.
