# Third-party components and release rights

## Qwen2.5-0.5B-Instruct

Upstream model: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct  
Upstream license: **Apache-2.0** as listed by the model publisher.

Dougbot distributes a separate fan-made LoRA adapter, **not** the Qwen base weights. Review any obligations that apply to the adapter, data, and other components before public redistribution.

## Independent Delve Town client

Upstream project: https://tangled.org/void.comind.network/interacting-with-delve-town

The client is maintained independently of Dougbot. **Its redistribution license has not been verified.** Accordingly it is no longer included in the current project tree. The optional `src/setup_delve_client.py` script checks out the upstream client on the user's own machine instead of copying it into this repository. Normal local-chat setup does not download it. Do not claim the client is licensed under the license chosen for Dougbot, or re-bundle it without verifying permission.

## Data and fan project

Dougbot is a DougDoug-inspired fan project and is neither DougDoug nor affiliated with him. See `data/SOURCES.md` and `RELEASE_CHECKLIST.md` for training-data sources, attribution and the outstanding rights review.

**No project-wide license has yet been selected by the repository owner.** See `RELEASE_CHECKLIST.md` before labeling this project open source.
