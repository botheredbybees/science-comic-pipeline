---
name: promote
description: Use after a comic's PDF is finished and its jokes are decided, to write the text that promotes it (an abstract, headline candidates, short social posts) so that every sentence rests on a verified claim and none says more than the paper does. Engaging, never inflated; checked by a script.
---

# Promote

**Goal:** text that makes a person want to open the comic, and that a paper's authors would sign. A post is a second
caption: it is held to the rule that holds the panels. **Nothing in it that a cited, verified claim does not say, and no
claim made stronger.** Engaging comes from the writing (a clear contrast, a concrete number, a real question), never
from a bigger claim.

**You need:** a finished comic folder (`claims.yaml`, `head.yaml`, `beats/`, the PDF), and the user's decision on which
jokes stand. **A private comic is never promoted** (`meta.private`): the checker refuses it.

Some of this method is adapted from Sebastian Heitmann's MIT-licensed
[online-writing-skills](https://github.com/DonHeidi/online-writing-skills) (the headline "deliverability gate", the
`distill` rules, the `tldr` register rules and its list of stock phrases), changed to rest on a claims ledger; see `ATTRIBUTION.md`.

## 1. Start from the claims, not the comic

Read the ledger and `head.yaml` (`audience`, `spine`, `left_out`). Do not work from the captions: they are already
shortened, and a post built on a caption inherits its omissions. Answer in one sentence each, citing claim ids:

- **What** is the finding (the thing a reader could repeat)? **Who** is it for (`meta.audience`)? **Promise:** what does
  the reader get from opening the comic (a question answered, a surprise, a caveat they would want)?
- **What the paper does not say** (`left_out`, the authors' own limits). A post that needs one of these to be true is wrong.

Choose the claims worth a post: a result with a number, a contrast between two results, the authors' own caveat, the open
question. Most of a ledger is not post material; five good items beat twenty.

## 2. Write `PROMO.yaml` in the comic's folder

The format is in `scripts/check_post.py`'s docstring. Every item carries `claims: [...]`, the ids it rests on, and
`approved: false`. What to write:

| Item | Rule |
|---|---|
| **Abstract** | One paragraph, 100 to 150 words, neutral, in the paper's own register (descriptive stays descriptive). Lead with the finding, move through the main beats, close on what is left open. Not "This comic explores…", not a teaser, not "read on". |
| **Headlines** | Ten or so candidates, in different shapes (a contrast, a question, a number, a claim in the authors' own words). The check below is the gate. |
| **Micro posts** | At most 280 characters including the link (a link counts as 24). Each stands alone for a reader with no context, leads with its sharpest version, and has a setup and a payoff. |
| **One long post** | Up to 1200 characters: the whole comic in a few short paragraphs, with the authors' limits kept. |

**Shapes that work for a micro post** (vary them; do not write five of one kind): the *contrast* ("similar numbers of
taxa, different communities"), the *question* the authors themselves ask, the *number with its scope*, the *micro-story*
(a setup and a payoff that both come from the paper), the *naming* of something the reader has felt. Prefer the comic's own
questions and the authors' words to your own flourish.

**Keep, always:** the number and its unit; the hedge ("approximately", "may", "similar", "most, not all"); the scope (this
site, this voyage, this marker, this species); the comparison (what was compared with what). A study that found X in the
Vestfold Hills did not find it "in Antarctica". Ten laboratories that shared *aliquots of DNA* did not share "samples" (the first draft of the
eDNA posts said so, and no script can see it: this is what reading each post against its quote is for). A correlation is not a cause. A post for one of several papers says which.

**Leave out:** "scientists discover", "game-changer", "breakthrough", "proves"; "that's not X, it's Y"; "changes everything";
"imagine"; "did you know"; engagement bait ("What's your take?", "Thoughts?", "Read on"); hashtags piled up; emoji lists;
a joke that is not approved (`panel:` must not name a panel whose `humour.keeps_claims_intact` is false); anything about the
authors' motives, feelings or reputation; the funding, institution or station a claim does not name.

**Credit.** The checker writes a credit line (authors, year, DOI, licence) into `PROMO.md`. Put it in or under every post that
can carry it. Say the comic is an adaptation, and that the authors did not write or endorse it.

## 3. The deliverability gate: check it

```
python scripts/check_post.py examples/<slug>            # errors and warnings
python scripts/check_post.py examples/<slug> --write    # also PROMO.md, the text to copy with each item's evidence
```

Errors must be fixed, not argued with: a number no cited claim has (digits, and the counts "two" to "ten"), a claim
that is missing or not verified, stronger wording, engagement bait, a length limit, an unapproved joke. **Drop a headline
that fails; do not weaken the check.** A warning is a question: a dropped hedge, a quantifier ("most", "many") or an absolute
("all", "never") or a cause ("because") that the claims do not use, a post that opens with "This" or "It". Fix it or be
able to say why not. A clean run is not proof: it cannot read meaning, so **read each post against the quotes under it in
`PROMO.md`**, and ask of every sentence "would the authors accept this as a summary of what they found?"

## 4. The user decides

Posts, like jokes, are the user's call. Leave `approved: false`; show the user `PROMO.md`. When they approve an item, set
`approved: true` (`--strict` fails until every item is). Never post, send or schedule anything yourself, and never publish
a comic or text for the user. If they want a change in tone, change the wording and run the check again; if a change would
need a claim the ledger lacks, go back to `source-to-claims` and add and verify the claim first.

## Also worth doing

- **The one-page overview** (`skills/overview/SKILL.md`): a short comic for the same paper that points to the long one.
  Link it in `PROMO.yaml` as `overview:`; it is the picture to attach to a post.
- **Alt text**: each panel's `scene` is its alt text; a post that attaches a picture should say what it shows.
