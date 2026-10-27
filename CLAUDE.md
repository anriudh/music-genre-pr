# Project instructions

`PROJECT_BRIEF.md` is the spec for this project. Follow it.

## Git
- Commit in small, meaningful increments with plain, short, human commit messages. No em dashes.
- No AI/Claude attribution or generated-by trailers in commits (no `Co-Authored-By`, `Claude-Session`, `Generated with Claude Code`).
- Push after every commit. Cloud session storage is temporary, so anything unpushed can be lost.

## Handoff and resuming
- On "Read HANDOFF.md and resume": read HANDOFF.md, then open only the files under its Load section. Do not scan the repo, list directories broadly, grep for orientation, or re-read files whose work is listed as Done. Ask me before reading anything not named in the file.
- Treat HANDOFF.md as authoritative on what is finished. Done means verified; Unverified means check it before relying on it.
- Never write a handoff summary as chat text. Use the handoff skill (`.claude/skills/handoff`) so it lands in HANDOFF.md.
- I cannot be warned automatically about my 5-hour limit, so when a milestone finishes, remind me once to check /usage and to run /handoff if I am past roughly 80%.
- Override for the handoff skill in this repo: commit and push HANDOFF.md instead of adding it to `.git/info/exclude`. Cloud sessions start from a fresh clone, so an unpushed HANDOFF.md never reaches the next session.
