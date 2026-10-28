# How to install and use this — plain version

Pick the way that matches where you use Claude. No coding needed for the first one.

---

## 1. The Claude app (easiest)

For Claude in a browser, or the Claude desktop app's chat.

1. Get the file `venture-blueprint.skill` — it's in the `dist` folder of this repository, or ask whoever shared this to send it.
2. In Claude, open **Settings → Capabilities → Skills**.
3. Click **Upload skill** and choose the file.
4. Start a new chat and describe your idea. That's it.

---

## 2. Claude Code, as a plugin (recommended if you use Claude Code)

You get improvements automatically. In Claude Code, type the first line and press Enter, then the second:

```
/plugin marketplace add natyget/venture-blueprint
```

```
/plugin install venture-blueprint@naty-skills
```

It now works in every Claude Code session on your computer.

---

## 3. Claude Code, by downloading the repository

Good if you want to look at how it works.

```bash
git clone https://github.com/natyget/venture-blueprint.git
cd venture-blueprint
claude
```

Opening Claude Code inside that folder is enough — the skill loads automatically. Any plans you make there are saved in a `ventures` folder that stays out of the repository.

---

## Your first session

1. **Start in a folder you'll keep.** The plan is saved as files. In Claude Code, make a folder for the idea — say `ventures/tool-share` — and open the session there.
2. **Describe the idea in plain words.** You don't need a command; the skill switches itself on. (To call it directly, type `/venture` and pick it from the list.)
3. **Answer the questions.** It asks about you, your money and time, and what you prefer — fast money or a bigger business, who pays, how you like to sell, what you won't do. Mostly multiple choice, all at once.
4. **Look at the venture site.** A page opens in your browser with two or three ways to do your idea, side by side. Each has a verdict (works / works if you can fund it / doesn't work yet), its numbers in bad, expected and great years, and app screens you can tap through. Drag the sliders to try your own guesses.
5. **Pick a path.** Tell Claude which one, a mix of two, or none of them.
6. **Say "plan it"** for the full plan: business plan, personas, competitors, every department, projections, risks, and the cheapest experiments to test the idea before building. The site updates with all of it.
7. **Say "build it"** only when you want the step-by-step build plan.

Stopping after step 5 is a perfectly good brainstorm, and the cheapest one.

**Opening the site later:** it's the file `plan/venture.html`. Double-click it and it opens in your browser. Nothing in it is sent anywhere.

---

## How to tell it's working

Try the hardest test:

> make me millions

It should not brainstorm wild ideas at you. It should go looking for problems people already pay to avoid — bad reviews of existing apps, people leaving a competitor, new laws with deadlines — and come back with a few real options, with sources and dates, and a recommendation. Then it should stop and ask which one you want.

---

## What it needs

Python 3, which Macs and most Linux computers already have. Nothing else to install. To check, run `python3 --version` — 3.9 or newer is fine.

---

## Questions people ask

**Does it write the app for me?** Not on its own. It plans it precisely enough — down to each step, what could break and how to check it worked — that Claude or a developer can build it step by step. The clickable prototype is a preview, not the finished app.

**Is the legal part real legal advice?** No, and it says so. It gives you a checklist for a lawyer to review, which is far cheaper than a lawyer starting from nothing.

**Will it make things up?** It's built not to. Every claim is supposed to carry a source and a date, every number comes from a calculator, and anything it couldn't check is marked unverified with who can confirm it. A confident number with no source is a bug — please report it.
