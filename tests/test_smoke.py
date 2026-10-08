"""Dependency-free Dougbot runtime tests: never touch Delve or load weights."""
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import types
import unittest
from contextlib import redirect_stdout
from unittest import mock

SRC = Path(__file__).resolve().parents[1] / "src"

class FakeBot:
    device = "cpu"
    adapter = "adapter"
    def reply(self, text, context=None, max_new_tokens=None):
        return "Example reply"

def load_script(filename):
    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    model = types.ModuleType("dougbot_model")
    model.Dougbot = FakeBot
    with mock.patch.dict(sys.modules, {"dotenv": dotenv, "dougbot_model": model}):
        spec = importlib.util.spec_from_file_location("dougbot_test_" + filename, SRC / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

class RuntimeSmokeTests(unittest.TestCase):
    def test_dry_run_mention_does_not_persist_or_reply(self):
        agent = load_script("delve_agent.py")
        post = {"uri": "at://did:plc:other/town.delve.feed.post/test123", "author": "someone.delve.town", "text": "@dougbot hi"}
        with mock.patch.object(agent, "node", return_value=json.dumps({"feed": [post]})), \
             mock.patch.object(agent, "own_identity", return_value=("dougbot.delve.town", "did:plc:bot")), \
             mock.patch.object(agent, "load_seen", return_value=set()), \
             mock.patch.object(agent, "save_seen", side_effect=AssertionError("wrote seen state")), \
             mock.patch.object(agent, "maybe_spontaneous", return_value=False), \
             mock.patch.object(agent, "reply", side_effect=AssertionError("published")):
            with redirect_stdout(io.StringIO()):
                agent.watch(limit=1, max_drafts=1, draft_only=True)

    def test_dry_run_spontaneous_root_does_not_post_or_save(self):
        agent = load_script("delve_agent.py")
        config = {"DOUGBOT_SPONTANEOUS_ENABLED": "true", "DOUGBOT_SPONTANEOUS_COOLDOWN_SECONDS": "0",
                  "DOUGBOT_SPONTANEOUS_CHANCE": "1", "DOUGBOT_SPONTANEOUS_POST_CHANCE": "1"}
        state = {"last_action": 0, "actions": 0}
        with mock.patch.dict(os.environ, config), \
             mock.patch.object(agent, "post", side_effect=AssertionError("published")), \
             mock.patch.object(agent, "save_spontaneous_state", side_effect=AssertionError("saved")):
            with redirect_stdout(io.StringIO()):
                self.assertTrue(agent.maybe_spontaneous(FakeBot(), [], set(), "dougbot.delve.town", "did:plc:bot", state, draft_only=True))
        self.assertEqual(state["actions"], 1)

    def test_dry_run_random_reply_does_not_publish_or_save(self):
        agent = load_script("delve_agent.py")
        config = {"DOUGBOT_SPONTANEOUS_ENABLED": "true", "DOUGBOT_SPONTANEOUS_COOLDOWN_SECONDS": "0",
                  "DOUGBOT_SPONTANEOUS_CHANCE": "1", "DOUGBOT_SPONTANEOUS_POST_CHANCE": "0"}
        post = {"uri": "at://did:plc:other/town.delve.feed.post/abc123", "author": "someone.delve.town", "text": "hello"}
        state = {"last_action": 0, "actions": 0}
        with mock.patch.dict(os.environ, config), \
             mock.patch.object(agent, "reply", side_effect=AssertionError("published")), \
             mock.patch.object(agent, "save_seen", side_effect=AssertionError("saved")), \
             mock.patch.object(agent, "save_spontaneous_state", side_effect=AssertionError("saved")):
            with redirect_stdout(io.StringIO()):
                self.assertTrue(agent.maybe_spontaneous(FakeBot(), [post], set(), "dougbot.delve.town", "did:plc:bot", state, draft_only=True))

    def test_chat_uses_existing_adapter_attribute(self):
        chat = load_script("chat.py")
        with mock.patch("builtins.input", side_effect=["hello", KeyboardInterrupt]), redirect_stdout(io.StringIO()) as output:
            chat.main()
        self.assertIn("adapter=adapter", output.getvalue())
        self.assertIn("Example reply", output.getvalue())

if __name__ == "__main__":
    unittest.main()
