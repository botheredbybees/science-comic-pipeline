---
name: source-to-claims
description: Use first, when turning a scientific paper into a comic. Fetches the paper, checks its licence, and writes the claims ledger: every statement the comic may rely on, each with a verbatim quote and the page it is on, checked by script.
---

# Source to claims

**Goal:** a `claims.yaml` that lists what the paper says, so that nothing in the comic is
the author's memory of the paper. Nothing later is allowed to state a fact that is not in this ledger.

**You need:** a DOI or PMC id (or a PDF), this repo's `scripts/`, and a working folder
`examples/<paper-slug>/` (or `private/<slug>/` if the licence is not confirmed).

## 1. Get the text and the licence

```bash
python scripts/fetch_source.py --doi <doi> -o sources/<slug>
```

- It prints the licence first. Only **CC BY, CC BY-SA and CC0** can be adapted; the script refuses
  anything else (a NoDerivatives licence rules the paper out). CC BY-SA means the comic must be CC BY-SA.
- No PMC full text? Convert the PDF with `pdftotext` (pages are separated by form feeds) and use
  `check_quotes.py --text`. Then check the licence by hand in the paper, and note where you found it.
- The paper's text lands in `sources/<slug>/pages/pNNN.txt`, one paragraph or caption per file. A claim's
  `page` is that number. `page-map.txt` lists them with their section. Sources stay out of git.

## 2. Read it all before writing anything

Read every page, including captions and the limitations paragraph. Note where the abstract and the body
disagree (they do more often than you would think), and where the text and a figure disagree.

## 3. Write the claims

One statement per claim. Aim for the paper's whole argument, not a sample: background the story needs,
the methods in a sentence each, every result you might draw, the authors' interpretation, and **their
caveats**. Caveats are claims too; they are usually the most honest and often the funniest material.

```yaml
claims:
- id: C12
  text: "Diatoms dominated the community, an average of 41% of all reads."   # what the comic may say
  kind: result            # background | method | result | interpretation | caveat
  source:
    locator: "Results, paragraph 2"
    page: 9
    quote: "diatoms dominated the community, an average of 41% of all reads"
  status: verified        # verified | abstract_only | unverified
  note: "Reads, not biomass."   # optional: what a panel must not overstate
```

Rules for the text:
- **Say no more than the quote supports.** Keep the hedge ("may", "suggests", "likely"). Keep the
  direction (correlated is not caused). Keep the scope (in this region, in these stations).
- Numbers go in verbatim, with their units and statistics. Do not round, convert or combine them.
- Separate what the authors found from what they cite. "X is known to Y [12]" is background, not a result.
- A claim that only a figure shows (a value you read off a chart) is `unverified` with a note, never `verified`.

Rules for the quote:
- Copy it from the page file, at least a clause long, containing **every number in the claim**.
- It must not start or end on a word with a digit stuck to it (older text keeps footnote digits, "density1").
- The page is the page it is on. Do not guess.

## 4. Check by script, then by reading

```bash
python scripts/check_quotes.py examples/<slug>/claims.yaml --pages-dir sources/<slug>/pages
```

(The ledger is a YAML file with a `claims:` list. Several files are fine: `claims-A.yaml` and so on. Later,
`build_storyboard.py` keeps only the claims the panels cite.) It errors when a `verified` claim has no quote, or the quote is not on
its page, and warns when a number in the claim is not in its quote. Fix every error and warning.

The script cannot tell you whether a claim says more than its quote. **Do a second pass yourself:** read
each claim against its quote and ask "what would make this overstated?" Remove or weaken the claim, or
set `unverified`, when the answer is anything.

Do not trust a summary from another agent or from your own earlier work: open the file and run the checker.

## 5. Record what you found

Write `CLAIM-CHECK.md` in the folder: the date, the source and how you got it, the licence and where you read
it, the check results, and anything odd (abstract against body, a likely typo, a figure the text does not
match). The comic must not repeat an error you found. Fill `meta.source` (title, authors, year, doi, url,
licence, licence_checked) from `source.json`.

**Done when:** `check_quotes.py` reports 0 errors and 0 warnings, and every claim is either `verified` or
explicitly `unverified` with a note.
