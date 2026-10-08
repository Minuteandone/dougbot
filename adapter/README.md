# Dougbot v5 LoRA adapter

A PEFT LoRA adapter for **Qwen2.5-0.5B-Instruct**, not a standalone base model. The repository's `src/dougbot_model.py` loads the base model plus this adapter.

## Model card

This is a fan-made, DougDoug-inspired comedy bot intended for local chat and Delve Town conversation. It is **not DougDoug**, is not affiliated with him, and does not represent his actual opinions. Generated replies may be repetitive, unreliable, inappropriate or nonsensical; review them before publishing if that matters.

The current `adapter_config.json` specifies rank 16, alpha 32, projections q/k/v/o and gate/up/down, and layers 12–23. The `V5_TRAINING_STATE.json` describes a 181-row pass of paraphrased VOD-inspired conversations and Delve transfer examples. These are training details, **not a performance benchmark**.

See the [main README](../README.md) for setup and base-model selection, [data/SOURCES.md](../data/SOURCES.md) for data provenance, and `docs/history/` for older training reports. Do not mistake old v2/v3 metadata for the current adapter.

The underlying Qwen2.5-0.5B-Instruct model has its own Apache-2.0 terms and model card. Review upstream licensing and all training data rights before redistributing altered model weights.
