# How to install this — plain version

Three ways. Pick the one that matches where you use Claude. No coding needed for the first one.

---

## 1. The Claude app (easiest — start here)

Best if you use Claude in a browser or the desktop app.

1. Get the file `venture-blueprint.skill` (whoever shared this will send it to you).
2. Open Claude, go to **Settings → Capabilities → Skills**.
3. Click **Upload skill** and pick that file.
4. Done. Start a new chat and type something like:

   > Plan out an app where neighbours lend each other tools. Market, stack, legal, money, and a build order.

Claude will pick the skill up on its own. You don't type its name.

**What you should see:** Claude starts working through numbered phases and shows you a wedge and a few candidate problems before it writes anything long. That's the skill working — it's meant to check direction with you early.

---

## 2. Claude Code, as a plugin (gets updates automatically)

Best if you use Claude Code in a terminal or the desktop app's Code tab.

Type these two lines into Claude Code, one at a time:

```
/plugin marketplace add natyget/venture-blueprint
```

```
/plugin install venture-blueprint
```

That's it. When the skill gets improved, you get the improvement.

**If the first line fails** saying it can't find the repository, it's still private. Ask the owner to either make it public or add you as a collaborator on GitHub.

---

## 3. Claude Code, as a plain folder

Best if you'd rather have the files locally and not deal with plugins.

```bash
git clone https://github.com/natyget/venture-blueprint.git
mkdir -p ~/.claude/skills
ln -s "$PWD/venture-blueprint/plugins/venture-blueprint/skills/venture-blueprint" ~/.claude/skills/venture-blueprint
```

The last line makes a shortcut rather than a copy, so `git pull` in that folder updates your skill too.

To put it in one specific project instead of everywhere, copy that same `skills/venture-blueprint` folder to `.claude/skills/venture-blueprint` inside the project and commit it. That way it also works in cloud sessions.

---

## How to tell it's working

Ask Claude: **"what skills do you have available?"** — `venture-blueprint` should be in the list.

Then try the hardest test, which is the point of the thing:

> make me millions

It should not brainstorm at you. It should go looking for problems people already pay to avoid — bad app reviews, people leaving a competitor, new laws with deadlines — and come back with a few real candidates, scored, with sources and dates, and a recommendation.

---

## What it needs

Python 3, which Macs and most Linux machines already have. Nothing else — no packages to install. The three helper scripts use only what ships with Python.

To check, run `python3 --version`. Anything 3.9 or newer is fine.

---

## Questions people ask

**Does it write the app for me?** No. It writes a plan precise enough that Claude (or a developer) can then build from it step by step, where every step says exactly which file to change, what could break, and how to prove it worked.

**Is the legal part real legal advice?** No, and the skill says so in its own output. It produces a checklist for an actual lawyer to review, which is much cheaper than a lawyer starting from nothing.

**Will it make things up?** It's built specifically not to. Every claim is supposed to carry a source and the date it was checked, and anything it couldn't verify gets flagged as unverified with a note on who can confirm it. If you see a confident number with no source, that's a bug — tell whoever shared this with you.
