# Dougbot v4 — VOD-trained final

Fresh LoRA trained from clean Qwen2.5-0.5B-Instruct.

Training:
- 70-row primary pass: mostly safe, paraphrased conversational reactions from the user-supplied DougDoug VOD + a small Delve transfer slice
- 33-row fresh corrective pass: brevity, absurdity recognition, completed actions, thread grounding, stopping/changing a bit
- 18-row runtime-alignment pass using the exact runtime system prompt: `You are Dougbot.`
- all passes use unique assistant responses; no v2/v3 weights

Architecture:
- LoRA rank 16, alpha 32
- last 12 transformer layers
- q/k/v/o + gate/up/down projections

Use the existing v3 Delve runtime and replace its `adapter` directory with this adapter.
