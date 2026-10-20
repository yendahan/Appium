<!--
HOW TO USE: copy this file into any project, replace every [bracket], delete the hint comments,
and fill in "Task" for each session. A filled-in example for this repo is PROMPT.md.
-->

You are working in the [PROJECT NAME] repo: [one-line purpose]
([language/version, frameworks, key libraries]). [Origin/history if relevant, e.g. ported from X, old code on branch Y.]
Read CLAUDE.md and README.md first.

## Architecture
<!-- 4-6 bullets: the layers, who may touch what, where config and data live -->
- `[path]` is the only code that [does the risky/low-level thing, e.g. touches the driver/DB/network].
- `[path]` holds [what]; each [unit] extends [base] and [rule].
- Config precedence: [highest] > ... > [lowest]. Read it through [accessor], never [raw access].
- Test/seed data: [location, loader, placeholder syntax].

## Commands
- Default (safe): `[cmd]`  -> [what it covers]
- Full/integration: `[cmd]`  -> needs [services/devices]
- Single test: `[cmd]`

## Safety (non-negotiable)
<!-- anything costly, destructive, irreversible or external -->
- Never run `[cmd/marker]` without asking me first. [Why: moves money / deletes data / locks accounts / hits prod]
- Secrets come only from `[ENV_VARS]`. Never write them, or any token, to a file or log.
- Avoid [forbidden API/pattern]. Do not [anti-pattern, e.g. sleeps instead of waits].
- A one-off failure from [flaky cause]: rerun before changing code.

## Recipes
<!-- the 3-5 changes you make most often -->
- New [unit type]: [steps, naming, location, base class, markers].
- New [test type]: [location, markers, shared helpers to reuse, data loading].
- New config key: [where to add, when to override].
- [Core/framework] logic gets a [fast, dependency-free] test in `[dir]`.

## Known quirks
<!-- stale comments, hard-coded values, global state, private paths not to copy -->
- [quirk 1]
- [quirk 2]

## How to work
1. Inspect the relevant files before editing and match the surrounding style.
2. Run `[fast test cmd]` after every change. Run [slow/risky tests] only with my approval.
3. Keep changes minimal. Commit only when I ask.
4. Report what you ran and what passed or failed, plainly.

## Task
[Describe the task: goal, affected area, acceptance criteria, what NOT to touch.]
