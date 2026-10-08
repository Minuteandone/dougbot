# Training-data sources and provenance

Dougbot is trained to imitate broad comedic *behavior*, not to reproduce transcripts.

## Doug-hole Wiki

Source pages:
- https://dougdoug.fandom.com/wiki/DougDoug
- https://dougdoug.fandom.com/wiki/DougDougAI

The wiki states that community content is available under CC-BY-SA unless otherwise noted.
Only a tiny number of short, safe catchphrase-pattern anchors are used by `build_data.py`.
Most examples are synthetic transformations of high-level traits such as absurd challenge premises,
overengineering, food analogies, confident reframing after failure, and Twitch-chat-as-collaborator/antagonist.

## YouTube title dataset

Dataset: `AdamLucek/youtube-titles`
- https://huggingface.co/datasets/AdamLucek/youtube-titles
- License listed by the dataset card: MIT

`build_data.py --include-youtube-titles` downloads the public JSONL splits, keeps only rows whose
`channel_name` is DougDoug, and turns the provided prompt/title pairs into a small auxiliary dataset.
It intentionally does not train on video-description text.

## Delve client

The bundle does not redistribute the independent Delve client. Setup scripts clone it from:
- https://tangled.org/void.comind.network/interacting-with-delve-town

That client is used because Delve Town uses custom ATProto lexicons (`town.delve.*`) rather than
ordinary Bluesky post records, and the client verifies writes through Delve's AppView.
