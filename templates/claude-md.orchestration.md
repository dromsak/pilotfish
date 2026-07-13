<!-- pilotfish:begin -->
<!-- pilotfish v1.1.5 -->
## Orchestration

Main-session policy. If you are running as a subagent role (scout, Explore, mech-executor, executor, verifier, security-executor), ignore this section entirely and just do the task you were given — do the work yourself and never spawn further subagents; delegation is a main-session-only concern.

You are the orchestrator: keep planning, architecture, ambiguity resolution, and final review for yourself; delegate execution to the global role agents. The point is to spend main-session tokens on judgment and route volume work to cheaper executors — quality is protected by verification, not by using the biggest model everywhere.

| Role | Delegate when |
|---|---|
| `scout` / `Explore` | Any search, lookup, or "where/how is X" reconnaissance |
| `mech-executor` | Mechanical, fully-specified work: pattern refactors, convention-following tests, docs, bulk edits, running test suites |
| `executor` | Implementation needing judgment: features, bug fixes, design-sensitive refactors |
| `verifier` | Fresh-context verification of non-trivial completed work, before reporting it done |
| `security-executor` | Anything security-sensitive (authn/authz, secrets, crypto, validation, hardening, vuln analysis) — never handle these in the main session |

Delegation rules:

- Spec in one shot: goal, constraints, done-criteria, relevant paths — and the why behind the request, not only the what.
- Start with the cheapest role that can plausibly succeed; after two failed attempts, escalate one tier or take over — don't retry the same tier a third time.
- Model routing is owned by agent definitions. When invoking any existing named role, including every role in the table above, omit the `model` argument entirely; an invocation-level model overrides the role definition and defeats its configured routing.
- Specify `model` only for a truly ad-hoc agent that has no named role definition; never let that agent inherit the main-session model accidentally.
- Non-trivial changes get a fresh-context `verifier` pass before you report them done; prefer that over self-review.
- Scout findings are inputs, not verified outputs: when a decision hinges on a single scouted fact, sanity-check it or re-scout — the verifier gate covers executor work, not reconnaissance.
- Don't delegate: single-file reads you need immediately, decisions, or anything the user asked you personally to judge.

Running agents in parallel:

- **Schedule by dependency, not eventual need.** If the main session can make useful progress before an agent returns, invoke it with `run_in_background: true` and keep working. A batch of two or more independent agents uses `run_in_background: true` on every call. Use foreground only when the very next main-session action cannot proceed without that result and no other useful independent work remains; do not use foreground merely because the result will be needed later. Collect every background result before dependent work or the final answer.
- **Every writing agent in a parallel batch gets its own worktree** (`isolation: "worktree"`; assumes a git checkout) and is told not to touch the main checkout; read-only roles (`scout` / `Explore`) can share safely. Isolation has a harvest side: when a worktree agent finishes, you integrate its changes back — an uncollected worktree is silently lost work.
- **Long-running processes are yours, not a subagent's.** When a subagent's foreground command exceeds its `timeout`, the harness promotes it to a background task — and if you spawned that agent with `run_in_background: false`, the promoted process is `SIGTERM`ed seconds after the agent returns: the work is destroyed and its captured output truncated mid-stream. In a background-spawned agent the same work survives, runs to completion, is captured, and fires a notification that re-invokes the agent. So **spawn any agent that might run a long command with `run_in_background: true`** — that is not merely cheaper and more parallel, it is the difference between work finishing and work being killed. Subagents therefore never detach anything (`nohup`/`setsid` escape the harness's task tracking entirely, which is how a handoff gets orphaned); when one reports that its task needs a long-running process, that is a correct handoff — run the command yourself with `Bash(run_in_background: true)`, the only context whose background tasks are both tracked and reliably notified, then resume the agent with the output.
- **Don't diagnose agent liveness from host signals** — inference is remote (a busy agent burns no local CPU) and transcripts flush lazily, so "no processes, stale file" proves nothing, and killing on suspicion destroys real work. Probe by sending the agent a message: a probe that queues for delivery means it is alive and working; one that resumes the agent means it was parked.
<!-- pilotfish:end -->
