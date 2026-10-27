---
name: handoff
description: Writes a dense HANDOFF.md at the project root so a fresh zero-context session can resume after a usage-limit reset without re-reading the old conversation, then offers to commit and push the outstanding work. Use when the user types /handoff, says they are near their 5-hour or weekly limit, asks to save state, checkpoint, hand off, or stop before quota runs out, or asks what is done and not done before a break. Separates verified-complete work from unfinished work with no ambiguity. Always write the file; never give a handoff summary as chat text instead.
allowed-tools: Bash(git status *) Bash(git log *) Bash(git diff *) Bash(git rev-parse *) Bash(git add *) Bash(git commit *) Bash(git check-ignore *) Bash(git remote *)
---

# Handoff

The next session starts with zero context and must not rebuild it by reading the repo or the old conversation. It reads HANDOFF.md, opens two or three named files, and works. A resumed session's cost is set by how much context it carries per turn, so this file exists to keep that context small and still sufficient.

Write it while the current session is alive. Once the limit hits mid-turn, nothing can be written.

## 1. Confirm you can write a file

In plan mode, file writes are blocked, and permission allow-rules do not override that. If this session is in plan mode, do not attempt the write and do not narrate the handoff in chat instead. Call ExitPlanMode with a one-line plan: "Write HANDOFF.md capturing the current state." Tell the user to pick an approve option that keeps the conversation, because an option that clears the planning context would discard the state this file is built from. Once out of plan mode, continue at step 2.

If the write is refused for any other reason, say plainly that HANDOFF.md was not written and stop. A handoff that exists only as chat text is destroyed by `/clear`, which is the exact failure this skill prevents. Never substitute a chat summary for the file.

## 2. Stop cleanly

Finish or revert the current edit so no file is left half-written. Start nothing new.

## 3. Gather state

In a git repo, one call:
`git rev-parse --show-toplevel; git rev-parse --abbrev-ref HEAD; git rev-parse --short HEAD; git status --short; git log --oneline -5`

Write HANDOFF.md at the toplevel path that returns, not in whatever subdirectory the session happens to be in, or the next session will look for it at the root and not find it.

If those commands fail, this is not a git repo: write HANDOFF.md in the current directory, skip step 5 entirely, and rely on Uncommitted and In progress to carry what commits would have held.

If HANDOFF.md already exists, read it before overwriting. Unfinished items in it may have been carried from earlier cycles and are not in this session's context at all. Carry them into the new file and drop only what is now demonstrably done. Overwriting blind loses tail work a little at a time across successive quota cycles.

Everything else comes from context already loaded. Do not re-read files or grep the repo to write the handoff.

## 4. Write HANDOFF.md

Overwrite the existing file. Write it before asking about committing, so the state survives even if the limit lands during the question.

The Done / Not done split is the core of the file. Rules:

- **Evidence, not memory.** Done requires something you can point at right now: a commit in `git log`, a command that ran clean this session, or a file you can see contains the change. Recollection is not evidence. If this conversation has been compacted, the earlier turns are a lossy summary of themselves, so anything you believe you finished but cannot point at goes under **Unverified**, however certain it feels. Overstating Done is the one error the next session cannot recover from, because it will not re-check what the file calls finished.
- **Not done** is everything remaining, ordered, phrased as actions.
- Never imply completion by omission. If part of the goal appears nowhere in the file, the next session cannot tell whether it was finished or forgotten.

```markdown
# HANDOFF <YYYY-MM-DD HH:MM> | <branch>@<sha> | paused: <5h limit / weekly limit / manual>
Resume protocol: read this file and nothing else, then open only the files under Load.
Do not scan the repo, re-read the old conversation, or re-derive what is listed here.
If HEAD is not <sha>, run `git log --oneline <sha>..HEAD` first. Start at Not done 1.
Delete this file once Not done is finished.

## Goal
<one line: the task, and what finished looks like>

## Done (verified)
- <what> (<sha> | <test or command that passed>)

## Unverified
- <changed but never run or tested, or believed done without evidence> (<sha or path>)

## Not done
1. <next concrete action, specific enough to start without asking>
2. <...>

## In progress
- <path:start-end>: <exact state, what remains in that file>

## Uncommitted
- <path>: <what changed there>

## Decisions
- <chose X over Y>: <reason, so it is not reopened>

## Dead ends
- <approach tried>: <how it failed / error signature>

## Gotchas
- <commands, env, versions, flags, where credentials live (never values)>

## Session rules
- <instructions from this session that still apply and are not in CLAUDE.md>

## Load
- <path:start-end>: <why the next step needs it>

## Verify
- `<command>` -> <expected output>
```

Density rules:
- Point, do not paste: paths with line ranges, SHAs, test names, error signatures. Paste content only if it exists nowhere on disk, under about 15 lines.
- No narrative of how the session went. A fact earns its place by changing the next action.
- Load is the biggest lever on resume cost. List the minimum for the next one or two steps.
- Never write secrets, tokens, or passwords.
- Uncommitted work needs enough detail here to be understood without a commit message. If it gets committed in step 5, that detail collapses to a SHA and the file shrinks.
- Omit sections that would be empty, except Not done: if nothing remains, say so explicitly.

## 5. Offer to commit (optional, never automatic)

Skip this step entirely outside a git repo.

Check first, then ask. Do not ask about actions that would do nothing.

- `git status --porcelain`. Empty means nothing to commit: say so and skip to step 6. Do not stage, do not create an empty commit.
- `git remote` empty means no remote: do not offer to push.
- If a remote and an upstream exist, `git log --oneline "@{u}..HEAD"` shows what is unpushed. Keep the quotes: unquoted, PowerShell reads `@{` as a hashtable and the command fails.

Then ask once, in a single message, offering: commit only / commit and push / neither. Do not proceed without an answer.

If the user chose to commit:
- Review `git diff` and `git diff --staged` before writing any message. The message describes what the change does, based on the actual diff.
- Split into small, meaningful commits when the work covers separate concerns.
- Commit messages document the work and nothing else. No mention of a handoff, a session, a quota, a skill, or an assistant. No generated-by or co-authored-by trailers, no emoji. Plain imperative, the way the user writes their own.
- Work known to be incomplete gets its own commit, with a message that says what is unfinished, for example `wip: parse quoted fields, escaping still broken`.

If the user chose to push:
- Re-check `git log --oneline "@{u}..HEAD"`. If it is empty, nothing is ahead of the remote: report that and push nothing.
- No upstream set: say so and let the user decide the branch, rather than guessing one.

After any commit, update HANDOFF.md: put the new SHA in the header line, move the newly committed items from Uncommitted into Done or Unverified with their SHA, and drop the Uncommitted section if it is now empty.

## 6. Finish

- In a git repo, if HANDOFF.md is not already ignored, append it to `.git/info/exclude` so it stays local. Do not edit a tracked .gitignore unasked.
- Reply with only this:

```
HANDOFF.md written (<N> lines). <Committed <shas> | Nothing committed>.
Run /clear now. After your limit resets, start with: Read HANDOFF.md and resume
Working on instead of clearing makes this file stale; run /handoff again before you clear.
```

- Stop. Do not continue the task.

Use `/clear`, not `/compact`. `/clear` discards the context outright. `/compact` sends the whole history to be summarized, which costs the thing being avoided.
