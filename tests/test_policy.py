from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROLES = (
    "scout",
    "Explore",
    "mech-executor",
    "executor",
    "verifier",
    "security-executor",
)


class PolicyContractTests(unittest.TestCase):
    def test_version_stamps_move_together(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        policy = (ROOT / "templates/claude-md.orchestration.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(f"<!-- pilotfish v{version} -->", policy)

        for readme in ("README.md", "README.zh-TW.md"):
            content = (ROOT / readme).read_text(encoding="utf-8")
            self.assertIn(f"git clone --branch v{version} --depth 1", content)

    def test_every_named_role_owns_its_model(self) -> None:
        policy = (ROOT / "templates/claude-md.orchestration.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("omit the `model` argument entirely", policy)
        self.assertIn("invocation-level model overrides the role definition", policy)
        self.assertIn("ad-hoc agent that has no named role definition", policy)

        for role in ROLES:
            agent = (ROOT / "templates" / "agents" / f"{role}.md").read_text(
                encoding="utf-8"
            )
            frontmatter = agent.split("---", 2)[1]
            self.assertRegex(frontmatter, rf"(?m)^name:\s*{re.escape(role)}\s*$")
            self.assertRegex(frontmatter, r"(?m)^model:\s*\S+\s*$")
            self.assertIn(f"`{role}`", policy)


    def test_no_role_is_told_to_detach_a_process(self) -> None:
        """Verified empirically (2026-07-13): when a subagent's foreground command
        exceeds its `timeout`, the harness promotes it to a background task. In an
        agent spawned with `run_in_background: true` that promoted process survives,
        completes, is captured, and its completion notification re-invokes the agent.
        In an agent spawned in the FOREGROUND it is SIGTERMed seconds after the agent
        returns — the work is destroyed and the captured output truncated.

        `nohup`/`setsid` dodge that SIGTERM by escaping the process group, but they
        also escape the harness's task tracking — no task id, no captured output, no
        notification — so the result is orphaned instead. That is how a handoff strands.

        No role may therefore be told to detach; the orchestrator owns long processes.
        """
        for role in ROLES:
            agent = (ROOT / "templates" / "agents" / f"{role}.md").read_text(
                encoding="utf-8"
            )
            for marker in ("nohup", "setsid", "disown"):
                self.assertNotIn(
                    marker,
                    agent.lower().replace(f"no `{marker}`", ""),
                    msg=(
                        f"{role} is told to detach a process. Detaching escapes the "
                        "harness's task tracking and orphans the result."
                    ),
                )

        policy = (ROOT / "templates/claude-md.orchestration.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Long-running processes are yours, not a subagent's", policy)
        self.assertIn("run_in_background: true", policy)


if __name__ == "__main__":
    unittest.main()
