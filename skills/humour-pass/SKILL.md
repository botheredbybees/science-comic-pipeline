---
name: humour-pass
description: Use after the storyboard validates, to propose jokes that leave every claim intact. Drafts a few, attaches each as a flagged humour block, and checks that none changes a number, a hedge or a cause. Optional, and a human decides.
---

# Humour pass

**Goal:** make the comic easier to like without making it say anything the paper does not. Humour is
optional, drafted separately, and flagged. **If a joke would change a claim, the claim wins.**

## 1. Find the places where a joke can live

Good raw material is already in the paper:

- **The authors' own caveats played straight.** A solemn caption beside an absurd picture of the limitation.
- **Deadpan understatement.** A large effect, a plain statement. The deadpan face and a `wide` quiet panel
  do the timing.
- **Scale.** A tiny organism treated as a celebrity; a 4.3% group with 78% of the reads.
- **A running gag** the cast can carry across beats (a repeated line, a prop, one character's catchphrase);
  it needs two or three appearances, not ten.
- **The method as an adventure.** The ship, the sampling, the instrument that did not do what was hoped.
- **The reader's own reaction** voiced by a character ("Surely.", "Surely not.").

A face or a pose can be the joke (a deadpan salp, a smile beside a number). If it is, say so in the note and treat it
as a joke; if it is only tone, keep it neutral where a cited claim is negative or hedged.

## 2. Draft a few, not many

Propose at most one joke per beat, and fewer is better. A comic that is funny three times is stronger than one
that tries on every panel. Put the joke in a character's line, a picture, or an unlabelled prop; **keep the
caption that carries the claim free of it**. If the joke needs the claim's wording altered, drop the joke.

## 3. Attach and flag each one

```yaml
humour:
  note: "Dot celebrates a 41% share as if it were a trophy. The caption is the paper's number; the joke is the pose."
  keeps_claims_intact: false     # leave false until the check below
```

The validator warns about any joke until `keeps_claims_intact: true`, on a panel with claims or without. That warning is
the flag: a joke you are unsure about keeps it, and waits for a human.

## 4. Check each joke before setting `keeps_claims_intact: true`

Answer in writing (in the note) for each, briefly: a note such as "1 no change; 2 reads as the comic's voice;
3 organisms; 4 no; 5 yes" is enough, with a sentence only where an answer is not a plain no:

1. Does any number, unit, hedge ("may", "suggests"), scope or direction change? (They must not.)
2. Could a reader take the joke as something the paper reported? If so, make it unmistakably the comic's
   voice, or cut it. Say in `CLAIM-CHECK.md` where the comic added its own cross-reference or aside.
3. Who is the butt of it? Never the authors, the participants or any group of people. Organisms, the
   weather, instruments and the narrator's own confidence are fair game.
4. Does it play down a caveat or a limitation? Then it is not a joke the comic can make.
5. Would it still read as honest to the authors?

Leave `keeps_claims_intact` false, and the humour block in place, when you are not sure. A person decides;
you propose.

## Output

`humour` blocks on a few panels, each with a note, and a list in your reply of the jokes proposed, which
you consider safe, and which you want a human to look at first. Re-run
`validate_storyboard.py --strict`: it should show no errors and exactly one warning for each joke you left
`false`, and so **exit 1 is the right end state** while a joke awaits a human. Any other warning is a defect.

**Done when:** each joke has passed the five questions (`keeps_claims_intact: true`), or is left `false` and on
the list for the reviewer, or has been removed.
