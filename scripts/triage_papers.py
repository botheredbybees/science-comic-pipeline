#!/usr/bin/env python3
"""Triage a folder of paper PDFs: which could become a public comic, and what do they talk about?

Read-only. For each PDF it reads the text with `pdftotext`, finds the paper's DOI on the first two pages,
asks Crossref and Unpaywall (by DOI only: no file, name or other detail leaves the machine) for the title, year
and licence, and counts mentions of common organisms, settings, equipment, collection methods and analytical processes, so you can see
which graphics (props, diagrams, bodies) would be used most.

    python scripts/triage_papers.py /path/to/papers -o private/triage/papers

Writes, into the -o folder (keep it out of git; `private/` is ignored):
  papers.csv   one row per PDF: file, pages, doi, doi_confirmed, title, year, licence, oa_status, class
               (after `--resolve`, also doi_source: title-match or no-text)
  topics.csv   one row per term: category, term, papers (how many PDFs mention it), mentions
  cache.json   the answers from the web lookups, so a re-run is quick and offline for papers already seen

`class` says what the pipeline may do with the paper:
  usable        a Creative Commons licence that allows adaptation (CC BY, CC BY-SA, CC0): a public comic is possible,
                once the licence is confirmed from the article's own text (see skills/source-to-claims)
  check         open access, but no adaptable licence was found: read the article's licence statement by hand
  private-only  not open: a private reading aid at most, never shared (meta.private)
  no-doi        no DOI found in the PDF, so nothing could be looked up

`--resolve` is a second stage for the `no-doi` rows (older papers and reports that print no DOI): it searches Crossref by
the start of the PDF's first page and accepts a match only if at least 85% of the longer words of the matched title are on
that page. Scanned PDFs with no text layer are marked `no-text` and left alone.

A DOI is `doi_confirmed` when most of the title Crossref gives for it appears on the PDF's first page; otherwise the
DOI may be a cited paper's, and the row is only a lead.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DOI = re.compile(r"\b(10\.\d{4,9}/[^\s\"<>\]\)\},;]+)")
UA = "science-comic-pipeline-triage"
UNPAYWALL_CONTACT = "unpaywall@impactstory.org"  # Unpaywall's own public contact address for anonymous use

# (category, label, regexes, case_sensitive). Counting is per PDF: how many papers mention it, and how often.
TERMS = [
    ("setting", "iceberg", [r"\bicebergs?\b"], False),
    ("setting", "sea ice (pack, pancake, fast ice, floes)", [r"\bsea.ice\b", r"pack ice", r"pancake ice", r"fast ice", r"\bfloes?\b", r"polynya"], False),
    ("setting", "ice shelf / glacier / ice sheet", [r"ice shel(f|ves)", r"\bglaciers?\b", r"ice sheets?"], False),
    ("setting", "sea state / swell / wave height", [r"sea state", r"\bswell\b", r"wave height", r"wind waves"], False),
    ("setting", "mixed layer / thermocline / stratification", [r"mixed layer", r"mixing layer", r"thermocline", r"pycnocline", r"stratif"], False),
    ("setting", "clouds", [r"\bclouds?\b", r"cloud cover"], False),
    ("setting", "ocean currents / fronts / gyres", [r"circumpolar current", r"\bACC\b", r"\bgyres?\b", r"ocean currents?", r"polar front", r"\bfronts?\b"], False),
    ("setting", "wind / storms", [r"\bwinds?\b", r"\bstorms?\b"], False),
    ("setting", "Southern Ocean", [r"Southern Ocean"], False),
    ("setting", "Antarctic stations and Hobart (named places)", [r"\bDavis\b", r"\bCasey\b", r"\bMawson\b", r"Macquarie Island", r"\bHobart\b"], False),
    ("setting", "Australia / Tasmania", [r"\bAustralia", r"\bTasmania"], False),
    ("equipment", "CTD", [r"\bCTD\b"], True),
    ("equipment", "Niskin bottle / rosette", [r"\bNiskin\b", r"\brosette\b"], False),
    ("equipment", "plankton net (bongo, multinet, WP2)", [r"plankton net", r"\bbongo\b", r"multi-?net", r"\bWP2\b", r"net tow"], False),
    ("equipment", "continuous plankton recorder", [r"continuous plankton recorder", r"\bCPR\b"], False),
    ("equipment", "trawl (RMT, krill net)", [r"\bRMT\b", r"\btrawl"], False),
    ("equipment", "echosounder / acoustics", [r"echo-?sounder", r"\bEK(60|80)\b", r"\bacoustic"], False),
    ("equipment", "ADCP", [r"\bADCP\b"], True),
    ("equipment", "thermosalinograph / underway", [r"thermosalinograph", r"\bTSG\b", r"underway"], False),
    ("equipment", "mooring", [r"\bmooring"], False),
    ("equipment", "glider / Argo float", [r"\bglider", r"\bArgo\b", r"profiling float"], False),
    ("equipment", "sediment trap", [r"sediment trap"], False),
    ("equipment", "corer / grab", [r"\bcorer\b", r"\bcore sampl", r"\bbox core", r"multi-?core", r"\bVan Veen\b"], False),
    ("equipment", "ice core / ice drill", [r"\bice core", r"ice auger", r"ice drill"], False),
    ("equipment", "ice thickness (EM induction, sonar)", [r"ice thickness", r"electromagnetic induction", r"\bEM-?31\b", r"upward.looking sonar"], False),
    ("equipment", "satellite remote sensing", [r"satellite (imagery|image|data|observation|remote|altimet|derived)", r"remote sensing", r"\bMODIS\b", r"\bSeaWiFS\b", r"\bAMSR"], False),
    ("equipment", "camera / video / drone", [r"\bcamera", r"\bvideo", r"\bdrone", r"\bUAV\b"], False),
    ("equipment", "microscope", [r"microscop"], False),
    ("equipment", "fluorometer / FRRf / PAM", [r"\bFRRf\b", r"fast repetition rate", r"\bLabSTAF\b", r"\bFv/Fm\b", r"\bPAM\b", r"fluorometer", r"fluorometry"], False),
    ("equipment", "flow cytometer", [r"flow cytomet"], False),
    ("equipment", "DNA sequencer (Illumina, nanopore)", [r"\bIllumina\b", r"\bMiSeq\b", r"\bNovaSeq\b", r"\bnanopore\b", r"\bMinION\b"], False),
    ("equipment", "mass spectrometer / HPLC", [r"mass spectromet", r"\bICP-MS\b", r"\bIRMS\b", r"\bHPLC\b"], False),
    ("equipment", "animal tag / telemetry", [r"satellite tag", r"\btelemetry\b", r"\btagged\b", r"\bbio-?logg"], False),
    ("equipment", "weather station / radiosonde / balloon", [r"automatic weather station", r"\bAWS\b", r"radiosonde", r"weather balloon", r"\banemometer"], False),
    ("equipment", "lidar / radar", [r"\blidar\b", r"\bradar\b"], False),
    ("equipment", "GPS / GNSS", [r"\bGPS\b", r"\bGNSS\b"], True),
    ("equipment", "seismometer / seismic", [r"seismic", r"seismomet"], False),
    ("equipment", "ice-sheet radar / airborne survey", [r"ice-penetrating radar", r"radio-?echo sounding", r"airborne survey", r"\bICESat\b", r"altimetr"], False),
    ("equipment", "snow pit / snow sampling", [r"snow ?pit", r"snow sampl", r"\bfirn\b"], False),
    ("equipment", "traverse / sledge / field camp", [r"\btraverse\b", r"\bsledge\b", r"field camp", r"field station"], False),
    ("equipment", "helicopter / aircraft", [r"helicopter", r"\baircraft\b", r"fixed-wing"], False),
    ("equipment", "ROV / AUV / towed camera", [r"\bROV\b", r"\bAUV\b", r"underwater vehicle", r"towed camera"], False),
    ("equipment", "hydrophone / passive acoustics", [r"hydrophone", r"passive acoustic"], False),
    ("equipment", "tissue biopsy / dart", [r"\bbiops", r"\bcrossbow\b"], False),
    ("equipment", "gas chromatograph / NMR", [r"gas chromatograph", r"\bGC-MS\b", r"\bNMR\b"], False),
    ("equipment", "spectrophotometer / nutrient autoanalyser", [r"spectrophotomet", r"autoanaly[sz]er", r"nutrient analy"], False),
    ("equipment", "aquarium / tank / flume", [r"\baquari(um|a)\b", r"\btanks?\b", r"\bflume\b"], False),
    ("equipment", "respirometer", [r"respirometer", r"respirometry", r"oxygen consumption"], False),
    ("equipment", "electron microscope", [r"scanning electron", r"\bSEM\b", r"\bTEM\b"], True),
    ("equipment", "data logger / time-depth recorder", [r"data ?logger", r"time-depth recorder", r"\bTDR\b"], False),
    ("equipment", "time-lapse / camera trap", [r"time-?lapse", r"camera trap"], False),
    ("equipment", "pitfall trap / quadrat", [r"pitfall", r"\bquadrats?\b"], False),
    ("equipment", "mass-balance stakes / glaciology", [r"mass balance", r"ablation stake", r"\bglaciolog"], False),
    ("organism", "krill", [r"\bkrill\b", r"Euphausia"], False),
    ("organism", "copepod", [r"copepod", r"\bCalanus\b", r"\bCalanoides\b"], False),
    ("organism", "amphipod / isopod", [r"amphipod", r"isopod"], False),
    ("organism", "salp / jellyfish / ctenophore", [r"\bsalps?\b", r"jellyfish", r"ctenophore", r"\bcnidaria"], False),
    ("organism", "penguin", [r"penguin"], False),
    ("organism", "seal", [r"\bseals?\b", r"elephant seal", r"Weddell", r"leopard seal", r"fur seal"], False),
    ("organism", "whale / dolphin", [r"\bwhales?\b", r"cetacean", r"humpback", r"\bminke\b", r"dolphin"], False),
    ("organism", "seabird (albatross, petrel, skua)", [r"albatross", r"petrel", r"\bskua", r"seabird", r"\btern\b"], False),
    ("organism", "fish (icefish, toothfish, myctophid)", [r"\bfish\b", r"icefish", r"toothfish", r"myctophid", r"\bcod\b"], False),
    ("organism", "squid / octopus", [r"\bsquid\b", r"octopus", r"cephalopod"], False),
    ("organism", "diatom", [r"diatom"], False),
    ("organism", "phytoplankton (dinoflagellate, Phaeocystis)", [r"phytoplankton", r"dinoflagellate", r"Phaeocystis", r"coccolithophore"], False),
    ("organism", "bacteria / archaea (microbes)", [r"\bbacteria", r"\barchaea", r"\bmicrob"], False),
    ("organism", "sea-ice algae", [r"ice algae", r"sea-ice algae", r"ice-?associated"], False),
    ("organism", "moss / lichen / plants", [r"\bmoss", r"lichen", r"vegetation", r"\bplants?\b"], False),
    ("organism", "terrestrial invertebrate (springtail, mite, nematode)", [r"springtail", r"collembol", r"\bmites?\b", r"nematode", r"tardigrade"], False),
    ("organism", "benthos (sponge, sea star, urchin, polychaete, bivalve)", [r"\bsponges?\b", r"sea star", r"starfish", r"urchin", r"polychaete", r"bivalve", r"benthic", r"benthos"], False),
    ("organism", "zooplankton (general)", [r"zooplankton"], False),
    ("organism", "human / people", [r"expeditioner", r"\bparticipants\b", r"\bstaff\b", r"\bvolunteers?\b"], False),
    ("collection", "water filtration (Sterivex, filters)", [r"filtration", r"\bSterivex\b", r"0\.22\s?(µm|μm|um)", r"\bfiltered\b"], False),
    ("collection", "sampling stations / transect", [r"\btransects?\b", r"\bsampling stations?\b", r"\bstation \d+\b"], False),
    ("collection", "sample preservation (ethanol, freezing)", [r"\bethanol\b", r"-80\s?°C", r"\bpreserved\b", r"\bformalin\b"], False),
    ("collection", "population survey (aerial, ship, count)", [r"aerial survey", r"ship-?based survey", r"line transect", r"population survey", r"abundance survey", r"\bcensus\b"], False),
    ("collection", "breeding colony / nest", [r"\bcolon(y|ies)\b", r"breeding site", r"\bnests?\b"], False),
    ("collection", "toxicity test / bioassay", [r"toxicity test", r"ecotoxic", r"\bEC50\b", r"\bLC50\b", r"bioassay"], False),
    ("collection", "questionnaire / interview", [r"questionnaire", r"respondents", r"\binterviews?\b"], False),
    ("collection", "incubation / experiment", [r"\bincubat", r"\bmesocosm"], False),
    ("collection", "negative control / blank", [r"negative control", r"\bblank\b", r"\bcontaminat"], False),
    ("analysis", "DNA extraction", [r"DNA extraction", r"extracted DNA", r"\bextraction kit"], False),
    ("analysis", "PCR / qPCR", [r"\bPCR\b", r"\bqPCR\b", r"real-time PCR", r"\bddPCR\b"], True),
    ("analysis", "metabarcoding / eDNA", [r"metabarcod", r"\beDNA\b", r"environmental DNA"], False),
    ("analysis", "marker gene (16S, 18S, COI)", [r"\b16S\b", r"\b18S\b", r"\bCOI\b", r"\bCO1\b"], True),
    ("analysis", "ASV / OTU clustering", [r"\bASVs?\b", r"\bOTUs?\b", r"\bzOTUs?\b", r"\bDADA2\b", r"\bvsearch\b", r"\bUSEARCH\b"], True),
    ("analysis", "sequence search / taxonomy (BLAST, reference database)", [r"\bBLAST", r"reference database", r"reference librar", r"\bQIIME"], False),
    ("analysis", "phylogenetic tree", [r"phylogen"], False),
    ("analysis", "ordination / PERMANOVA", [r"\bNMDS\b", r"\bPCoA\b", r"\bPCA\b", r"ordination", r"\bPERMANOVA\b"], False),
    ("analysis", "machine learning / embeddings", [r"machine learning", r"random forest", r"neural network", r"deep learning", r"\bembedding", r"transformer"], False),
    ("analysis", "cross-validation", [r"cross-validation", r"cross validation"], False),
    ("analysis", "regression / GAM / mixed models", [r"\bGAMs?\b", r"generali[sz]ed additive", r"\bregression\b", r"mixed.effects"], False),
    ("analysis", "Bayesian model", [r"\bBayesian\b"], False),
    ("analysis", "stable isotopes", [r"stable isotope", r"δ13C", r"δ15N", r"d13C", r"d15N"], False),
    ("analysis", "primary production / O2:Ar", [r"primary production", r"\bO2/Ar\b", r"\bNCP\b"], False),
    ("analysis", "quality control / calibration", [r"quality control", r"\bQC\b", r"\bcalibrat"], False),
    ("analysis", "population genetics (SNP, microsatellite, genome)", [r"microsatellite", r"\bSNPs?\b", r"population genetic", r"whole-genome", r"\bgenome\b", r"mitochondrial"], False),
    ("analysis", "transcriptomics / gene expression", [r"transcriptom", r"RNA-seq", r"gene expression"], False),
    ("analysis", "diet analysis (stomach, scat, faeces)", [r"stomach content", r"\bscats?\b", r"fa?eces", r"diet analysis"], False),
    ("analysis", "fatty acids / lipids", [r"fatty acid", r"\blipid"], False),
    ("analysis", "contaminants / trace metals", [r"heavy metal", r"trace metal", r"hydrocarbon", r"\bPAHs?\b", r"fuel spill", r"contaminant"], False),
    ("analysis", "population model / mark-recapture", [r"population model", r"mark-?recapture", r"abundance estimat", r"state-space"], False),
    ("analysis", "species distribution / habitat model / GIS", [r"species distribution model", r"habitat model", r"\bMaxent\b", r"\bGIS\b"], False),
    ("analysis", "time series / trend analysis", [r"time series", r"trend analysis", r"\bMann-Kendall\b"], False),
    ("analysis", "numerical / climate model", [r"numerical model", r"climate model", r"\bGCM\b", r"ocean model", r"coupled model", r"\bROMS\b"], False),
    ("analysis", "age / growth (otolith, growth rings)", [r"otolith", r"growth ring", r"age determination"], False),
    ("analysis", "dating (radiocarbon, OSL)", [r"radiocarbon", r"\b14C\b", r"\bOSL\b"], False),
    ("analysis", "statistical test (t-test, ANOVA, Wilcoxon)", [r"\bt-test", r"\bANOVA\b", r"\bWilcoxon\b", r"\bKruskal"], False),
]
COMPILED = [(cat, label, [re.compile(p, 0 if cs else re.I) for p in pats]) for cat, label, pats, cs in TERMS]

ADAPTABLE = ("/licenses/by/", "/licenses/by-sa/", "/publicdomain/zero/")


def find_doi(text):
    """The first DOI in the text, with trailing punctuation removed; '' if none."""
    m = DOI.search(text)
    return m.group(1).rstrip(".,;:") if m else ""


def title_words(title):
    return {w for w in re.findall(r"[a-z]{4,}", title.lower())}


def confirmed(title, page_text, threshold=0.7):
    """True if most of the longer words in the Crossref title appear on the PDF's first page."""
    words = title_words(title)
    if len(words) < 3:
        return False
    page = page_text.lower()
    return sum(1 for w in words if w in page) / len(words) >= threshold


def classify(crossref_licences, unpaywall, doi):
    """Return (licence label, class) from Crossref licence URLs and an Unpaywall record."""
    if not doi:
        return "", "no-doi"
    urls = [u.lower() for u in crossref_licences]
    best = (unpaywall or {}).get("best_oa_location") or {}
    ulic = (best.get("license") or "").lower()
    for u in urls:
        if "creativecommons.org" in u:
            for fam, name in (("/licenses/by-sa/", "CC BY-SA"), ("/licenses/by/", "CC BY"), ("/publicdomain/zero/", "CC0"),
                              ("/licenses/by-nc-nd/", "CC BY-NC-ND"), ("/licenses/by-nc-sa/", "CC BY-NC-SA"),
                              ("/licenses/by-nc/", "CC BY-NC"), ("/licenses/by-nd/", "CC BY-ND")):
                if fam in u:
                    return name, "usable" if fam in ADAPTABLE else "private-only"
    if ulic in ("cc-by", "cc-by-sa", "cc0"):
        return ulic.upper().replace("-", " ", 1) if ulic != "cc0" else "CC0", "usable"
    if ulic.startswith("cc-by-n"):
        return ulic.upper(), "private-only"
    if (unpaywall or {}).get("is_oa"):
        return "open access (licence not stated)", "check"
    return "", "private-only"


def count_terms(text):
    """{label: mentions} for every term that appears at least once."""
    out = {}
    for _, label, pats in COMPILED:
        n = sum(len(p.findall(text)) for p in pats)
        if n:
            out[label] = n
    return out


def pdftotext(path, first=None, last=None):
    cmd = ["pdftotext", "-q"]
    if first:
        cmd += ["-f", str(first), "-l", str(last or first)]
    return subprocess.run(cmd + [str(path), "-"], capture_output=True, text=True, errors="ignore").stdout


def pages_in(path):
    m = re.search(r"^Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, errors="ignore").stdout, re.M)
    return int(m.group(1)) if m else 0


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.load(r)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, ConnectionError):
        return None


def lookup(doi, cache):
    """Crossref and Unpaywall answers for a DOI (cached). Only the DOI is sent."""
    if doi in cache:
        return cache[doi]
    q = urllib.parse.quote(doi, safe="/")
    cr = (fetch_json(f"https://api.crossref.org/works/{q}") or {}).get("message") or {}
    time.sleep(0.15)
    up = fetch_json(f"https://api.unpaywall.org/v2/{q}?email={UNPAYWALL_CONTACT}") or {}
    time.sleep(0.15)
    year = ((cr.get("issued") or {}).get("date-parts") or [[None]])[0][0]
    rec = {"title": (cr.get("title") or [""])[0], "year": year, "journal": (cr.get("container-title") or [""])[0],
           "licences": [l.get("URL", "") for l in cr.get("license", []) if l.get("content-version") in ("vor", "am", "tdm", "unspecified", None)],
           "oa_status": up.get("oa_status", ""), "is_oa": bool(up.get("is_oa")), "best": up.get("best_oa_location") or {}}
    cache[doi] = rec
    return rec


def query_text(page1):
    """The start of a PDF's first page, tidied, as a bibliographic query: title and authors come first."""
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in page1.splitlines()]
    lines = [ln for ln in lines if len(ln) > 12 and not re.fullmatch(r"[\d\W]+", ln)]
    return " ".join(lines)[:260]


def pick_candidate(items, page1):
    """The first Crossref candidate whose title is mostly on the PDF's first page (a stricter test than for a DOI the
    PDF printed itself, because here the match is a guess); '' if none. Needs a title of at least four longer words."""
    for it in items:
        title = (it.get("title") or [""])[0]
        if len(title_words(title)) >= 4 and confirmed(title, page1, 0.85):
            return it.get("DOI", ""), title
    return "", ""


def search_by_text(page1, cache):
    """Crossref's best matches for the text of a first page (cached by the query)."""
    q = query_text(page1)
    key = "q:" + q
    if not q:
        return []
    if key not in cache:
        data = fetch_json("https://api.crossref.org/works?rows=3&select=DOI,title&query.bibliographic=" + urllib.parse.quote(q))
        time.sleep(0.2)
        cache[key] = ((data or {}).get("message") or {}).get("items", [])
    return cache[key]


def resolve(folder, out):
    """For papers.csv rows with no DOI, search Crossref by the text of page 1 and fill in the confident matches."""
    out = Path(out)
    cache_path = out / "cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    with open(out / "papers.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    todo = [r for r in rows if r["class"] == "no-doi"]
    found = 0
    for i, r in enumerate(todo, 1):
        page1 = pdftotext(Path(folder) / r["file"], 1, 1)
        r["doi_source"] = ""
        if len(page1.split()) < 40:  # a scan or an empty first page: nothing to search with
            r["doi_source"] = "no-text"
            continue
        doi, title = pick_candidate(search_by_text(page1, cache), page1)
        if not doi:
            continue
        rec = lookup(doi, cache)
        lic, cls = classify(rec.get("licences", []), {"best_oa_location": rec.get("best"), "is_oa": rec.get("is_oa")}, doi)
        r.update({"doi": doi, "doi_confirmed": "title", "title": rec.get("title") or title, "year": rec.get("year") or "",
                  "licence": lic, "oa_status": rec.get("oa_status", ""), "class": cls, "doi_source": "title-match"})
        found += 1
        if i % 25 == 0:
            print(f"  {i}/{len(todo)} searched, {found} matched", file=sys.stderr)
            cache_path.write_text(json.dumps(cache))
    cache_path.write_text(json.dumps(cache))
    fields = ["file", "pages", "doi", "doi_confirmed", "doi_source", "title", "year", "licence", "oa_status", "class"]
    with open(out / "papers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", restval="")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(todo)} paper(s) had no DOI; {found} matched by title. Classes now:")
    for cls in ("usable", "check", "private-only", "no-doi"):
        print(f"  {cls:13} {sum(1 for r in rows if r['class'] == cls)}")
    return 0


def topics_only(folder, out):
    """Recount the terms across the PDFs and rewrite topics.csv, touching nothing else."""
    papers_with, mentions = {}, {}
    pdfs = sorted(Path(folder).rglob("*.pdf"))
    for i, pdf in enumerate(pdfs, 1):
        for label, n in count_terms(pdftotext(pdf)).items():
            papers_with[label] = papers_with.get(label, 0) + 1
            mentions[label] = mentions.get(label, 0) + n
        if i % 100 == 0:
            print(f"  {i}/{len(pdfs)} read", file=sys.stderr)
    cat_of = {label: cat for cat, label, _ in COMPILED}
    with open(Path(out) / "topics.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "term", "papers", "mentions"])
        for label in sorted(papers_with, key=lambda k: (-papers_with[k], -mentions[k])):
            w.writerow([cat_of[label], label, papers_with[label], mentions[label]])
    print(f"{len(pdfs)} PDF(s) recounted into {out}/topics.csv")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder")
    ap.add_argument("-o", "--out", required=True, help="folder for papers.csv, topics.csv and cache.json")
    ap.add_argument("--offline", action="store_true", help="read the PDFs and count terms, but do no web lookups")
    ap.add_argument("--topics-only", action="store_true",
                    help="only recount the terms into topics.csv: no lookups, and papers.csv (with its licence results) is left alone")
    ap.add_argument("--resolve", action="store_true",
                    help="second stage, on an existing -o folder: for papers with no DOI, search Crossref by the text of page 1")
    args = ap.parse_args(argv)
    if args.resolve:
        return resolve(args.folder, args.out)
    if not shutil.which("pdftotext"):
        print("pdftotext is needed (poppler-utils)", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.topics_only:
        return topics_only(args.folder, out)
    cache_path = out / "cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    pdfs = sorted(Path(args.folder).rglob("*.pdf"))
    rows, papers_with, mentions = [], {}, {}
    for i, pdf in enumerate(pdfs, 1):
        head = pdftotext(pdf, 1, 2)
        page1 = pdftotext(pdf, 1, 1)
        doi = find_doi(page1) or find_doi(head)
        rec = {} if (args.offline or not doi) else lookup(doi, cache)
        lic, cls = classify(rec.get("licences", []), {"best_oa_location": rec.get("best"), "is_oa": rec.get("is_oa")}, doi) if rec or not doi else ("", "check" if doi else "no-doi")
        if doi and args.offline:
            lic, cls = "", "check"
        full = pdftotext(pdf)
        for label, n in count_terms(full).items():
            papers_with[label] = papers_with.get(label, 0) + 1
            mentions[label] = mentions.get(label, 0) + n
        rows.append({"file": str(pdf.relative_to(args.folder)), "pages": pages_in(pdf), "doi": doi,
                     "doi_confirmed": "yes" if rec.get("title") and confirmed(rec["title"], page1) else ("no" if doi else ""),
                     "title": rec.get("title", ""), "year": rec.get("year") or "", "licence": lic,
                     "oa_status": rec.get("oa_status", ""), "class": cls})
        if i % 10 == 0:
            print(f"  {i}/{len(pdfs)} read", file=sys.stderr)
            cache_path.write_text(json.dumps(cache))
    cache_path.write_text(json.dumps(cache))
    with open(out / "papers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["file", "pages", "doi", "doi_confirmed", "title", "year", "licence", "oa_status", "class"])
        w.writeheader()
        w.writerows(rows)
    cat_of = {label: cat for cat, label, _ in COMPILED}
    with open(out / "topics.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "term", "papers", "mentions"])
        for label in sorted(papers_with, key=lambda k: (-papers_with[k], -mentions[k])):
            w.writerow([cat_of[label], label, papers_with[label], mentions[label]])

    n = len(rows)
    print(f"{n} PDF(s) read. Written to {out}/papers.csv and topics.csv")
    for cls in ("usable", "check", "private-only", "no-doi"):
        print(f"  {cls:13} {sum(1 for r in rows if r['class'] == cls)}")
    print("Most-mentioned terms (papers that mention them):")
    for cat in ("organism", "equipment", "collection", "analysis", "setting"):
        top = [l for l in sorted(papers_with, key=lambda k: (-papers_with[k], -mentions[k])) if cat_of[l] == cat][:8]
        print(f"  {cat}: " + "; ".join(f"{l} ({papers_with[l]})" for l in top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
