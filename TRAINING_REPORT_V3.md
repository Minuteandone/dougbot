# Dougbot v3 training report

v2 showed clear synthetic-template overfitting: 798/3012 old training conversations contained `New rule`, and several exact response openings appeared 100+ times.

v3 experiments included:
- clean-from-base rank-8 LoRA: less repetitive but too bland/literal;
- preference anti-template tuning: sometimes strengthened the wrong attractor;
- short-response curriculum: improved brevity somewhat but degraded general voice;
- effective-delta LoRA blends: did not give reliable conversation quality;
- stronger clean rank-16 LoRA: underperformed on the 0.5B base within available compute.

Shipped adapter: v2 strong LoRA followed by 48 corrective assistant-only SFT steps using aggressively deduplicated/template-filtered data, including short mentions and thread continuations. Runtime decoding additionally blocks the small set of stale phrases that remained unusually attractive.

This is still a 0.5B model. The runtime diversity guard is intentional and is not a hidden personality prompt; the personality remains in LoRA weights.
