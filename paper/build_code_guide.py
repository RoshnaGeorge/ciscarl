"""Build the complete code and file guide."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from code_guide_content import ENTRIES

ROOT = Path(r"C:\Users\roshn\OneDrive\Desktop\Amrita\SEM 5\ML\Project")
OUT = ROOT / "paper" / "CISCaRL_Complete_Code_and_File_Guide.docx"

BLACK = RGBColor(0, 0, 0)
FONT = "Calibri"


def set_run(run, size=12, bold=False, italic=False):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = BLACK
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), FONT)
    return run


def base_style(doc):
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(12)
    st.font.color.rgb = BLACK
    rpr = st.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), FONT)
    st.paragraph_format.space_after = Pt(5)
    st.paragraph_format.line_spacing = 1.12
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name, size in (("Heading 1", 16), ("Heading 2", 13), ("Title", 26)):
        h = doc.styles[name]
        h.font.name = FONT
        h.font.size = Pt(size)
        h.font.bold = True
        h.font.color.rgb = BLACK
        h.font.italic = False
        rpr = h.element.get_or_add_rPr()
        rfonts = rpr.find(qn("w:rFonts"))
        if rfonts is None:
            rfonts = OxmlElement("w:rFonts")
            rpr.append(rfonts)
        for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
            rfonts.set(qn(attr), FONT)
        h.paragraph_format.keep_with_next = True
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(5)
        h.paragraph_format.line_spacing = 1.0


def page_border(section):
    sectPr = section._sectPr
    old = sectPr.find(qn("w:pgBorders"))
    if old is not None:
        sectPr.remove(old)
    pg = OxmlElement("w:pgBorders")
    pg.set(qn("w:offsetFrom"), "page")
    for edge in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "12")
        el.set(qn("w:space"), "24")
        el.set(qn("w:color"), "000000")
        pg.append(el)
    sectPr.append(pg)


def para_border(par, size=6, color="000000"):
    pPr = par._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(size))
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), color)
    pbdr.append(bottom)
    pPr.append(pbdr)


def p(doc, text="", size=12, bold=False, italic=False, align=None,
      space_before=0, space_after=5, keep=False):
    par = doc.add_paragraph()
    set_run(par.add_run(text), size=size, bold=bold, italic=italic)
    if align is not None:
        par.alignment = align
    par.paragraph_format.space_before = Pt(space_before)
    par.paragraph_format.space_after = Pt(space_after)
    par.paragraph_format.keep_with_next = keep
    return par


def bullet(doc, label, text):
    q = doc.add_paragraph(style="List Bullet")
    set_run(q.add_run(label), 12, bold=True)
    set_run(q.add_run(text), 12)
    q.paragraph_format.space_after = Pt(1)
    q.paragraph_format.keep_together = True
    return q


def field(par, code):
    run = par.add_run()
    b = OxmlElement("w:fldChar")
    b.set(qn("w:fldCharType"), "begin")
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = code
    s = OxmlElement("w:fldChar")
    s.set(qn("w:fldCharType"), "separate")
    t = OxmlElement("w:t")
    t.text = "1"
    e = OxmlElement("w:fldChar")
    e.set(qn("w:fldCharType"), "end")
    for x in (b, it, s, t, e):
        run._r.append(x)
    set_run(run, 9)


doc = Document()
base_style(doc)

sec = doc.sections[0]
sec.page_width = Cm(21.0)
sec.page_height = Cm(29.7)
sec.top_margin = Cm(1.9)
sec.bottom_margin = Cm(1.9)
sec.left_margin = Cm(2.1)
sec.right_margin = Cm(2.1)
page_border(sec)

head = sec.header.paragraphs[0]
head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
set_run(head.add_run("CISCaRL — Complete Code and File Guide"), 9, italic=True)

foot = sec.footer.paragraphs[0]
foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(foot.add_run("Page "), 9)
field(foot, "PAGE")
set_run(foot.add_run(" of "), 9)
field(foot, "NUMPAGES")

# ---------------------------------------------------------------- title
for _ in range(3):
    p(doc, "", space_after=0)

t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(t.add_run("CISCaRL"), 30, bold=True)
t.paragraph_format.space_after = Pt(2)

t2 = doc.add_paragraph()
t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(t2.add_run("Complete Code and File Guide"), 20, bold=True)
t2.paragraph_format.space_after = Pt(4)

t3 = doc.add_paragraph()
t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(t3.add_run("Every code file and every project area, in plain language"), 13, italic=True)
t3.paragraph_format.space_after = Pt(18)

rule = doc.add_paragraph()
rule.alignment = WD_ALIGN_PARAGRAPH.CENTER
para_border(rule, size=12)
rule.paragraph_format.space_after = Pt(18)

for line in (
    "Support-constrained interpretable subgroup discovery for survival outcomes",
    "Dataset: ACTG175, arms 0 and 1, n = 1,054",
    "Final model: C200-I  ·  horizon: 730 days",
    "Prepared: November 2026",
):
    q = doc.add_paragraph()
    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(q.add_run(line), 12)
    q.paragraph_format.space_after = Pt(2)

p(doc, "", space_after=0)
p(doc, "", space_after=0)
note = doc.add_paragraph()
note.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(note.add_run("This guide covers all 84 code files in the project, the 31 notebook steps, "
                     "and every non-code area: data, results, figures, reports and configuration."),
        12, italic=True)

doc.add_page_break()

# ---------------------------------------------------------------- coverage
h = doc.add_heading("Coverage at a glance", level=1)
h.paragraph_format.page_break_before = False

table = doc.add_table(rows=0, cols=2)
table.style = "Table Grid"
table.alignment = WD_TABLE_ALIGNMENT.CENTER
rows = [
    ("Code files explained", "84 of 84: ciscarl2 (74), ciscarl2/external (2), run_all.py (1), paper builders and content (7)"),
    ("Notebook steps", "31 of 31, each with code, plain explanation, result and decision"),
    ("Result files", "293 files: 121 Markdown records and 167 CSV tables"),
    ("Paper figures", "38 files: 19 PNG and 19 PDF versions"),
    ("Report exhibits", "42 images: 38 exact console screenshots and 4 notebook plots"),
    ("Docs and config", "README, requirements, .gitignore, LICENSE, data, notebook, report, paper"),
]
for k, v in rows:
    cells = table.add_row().cells
    cells[0].width = Cm(4.4)
    cells[1].width = Cm(12.0)
    cells[0].text = ""
    cells[1].text = ""
    set_run(cells[0].paragraphs[0].add_run(k), 12, bold=True)
    set_run(cells[1].paragraphs[0].add_run(v), 12)
    cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    cells[0].paragraphs[0].paragraph_format.space_after = Pt(2)
    cells[1].paragraphs[0].paragraph_format.space_after = Pt(2)

p(doc, "", space_after=2)
p(doc, "How to read each entry", size=13, bold=True, keep=True)
p(doc, ("Every code file is shown with its path, a status label, and three bullets: what it is, "
        "what it does, and what it produced. Historical gates are kept because they explain why a "
        "choice was made or rejected; they are not needed to run the final model."))

p(doc, "Status labels", size=13, bold=True, keep=True, space_before=4)
for text, meaning in (
    ("Final pipeline", "part of the model that produces the final rule or decision"),
    ("Final evidence", "a gate or check that supports a final choice"),
    ("Historical evidence", "an earlier experiment kept for the audit trail"),
    ("Tested and rejected", "an alternative that was implemented, run and not adopted"),
    ("Support", "helper code with no experimental output"),
    ("External dependency", "the SCRE baseline; not used by the final model"),
    ("Build tool", "code that rebuilds the notebook, report, figures or paper"),
):
    q = doc.add_paragraph(style="List Bullet")
    set_run(q.add_run(text + " — "), 12, bold=True)
    set_run(q.add_run(meaning), 12)
    q.paragraph_format.space_after = Pt(0)

doc.add_page_break()

# ---------------------------------------------------------------- code sections
h = doc.add_heading("Part A — Every code file", level=1)
h.paragraph_format.page_break_before = False

GROUP_ORDER = ["Core model", "Gates 1–4", "Gates 5–15", "Gates 16–30",
               "Gates 31–44", "Gates 45–48", "Diagnostics and variants",
               "External and build"]

for group in GROUP_ORDER:
    h = doc.add_heading(group, level=2)
    h.paragraph_format.keep_with_next = True
    entries = [e for e in ENTRIES if e[0] == group]
    p(doc, f"{len(entries)} files in this group.", italic=True, size=12)
    for _, status, path, what, does, produced in entries:
        fh = doc.add_paragraph()
        set_run(fh.add_run(path), 12, bold=True)
        set_run(fh.add_run(f"  —  {status}"), 12, italic=True)
        fh.paragraph_format.space_before = Pt(8)
        fh.paragraph_format.space_after = Pt(2)
        fh.paragraph_format.keep_with_next = True
        para_border(fh, size=4, color="808080")
        bullet(doc, "What it is: ", what)
        bullet(doc, "What it does: ", does)
        bullet(doc, "What it produced: ", produced)

doc.add_page_break()
# ---------------------------------------------------------------- non-code
h = doc.add_heading("Part B — Every non-code project area", level=1)
h.paragraph_format.page_break_before = False

p(doc, "Data and configuration", size=13, bold=True, keep=True)
for label, text in (
    ("ACTG175.csv: ", "the raw trial file at the project root: 1,054 patients in arms 0/1, "
                      "27 columns; SHA-256 debab27b…c7141a."),
    ("data/ACTG175.csv: ", "the same file at the path used by the code; both copies have the "
                           "same checksum."),
    ("README.md: ", "the project guide: layout, install, run commands, seeds and limits."),
    ("requirements.txt: ", "pinned Python 3.11 packages: numpy 2.4.6, pandas 2.2.3, scikit-learn "
                           "1.9.1, scikit-survival 0.28.0, lifelines 0.30.3, and the rest."),
    (".gitignore: ", "keeps cache, virtual-environment and temporary files out of Git."),
    ("LICENSE: ", "the MIT licence for the code."),
):
    bullet(doc, label, text)

p(doc, "Notebook", size=13, bold=True, keep=True, space_before=6)
for label, text in (
    ("notebooks/CISCaRL_31_steps.ipynb: ", "the 31-step executable record: 136 cells, 52 code "
                                           "cells, 0 error cells; runs in 1–2 minutes in evidence mode."),
    ("notebooks/CISCaRL_31_steps.html: ", "the same notebook exported for reading without Jupyter."),
):
    bullet(doc, label, text)

p(doc, "Results", size=13, bold=True, keep=True, space_before=6)
for label, text in (
    ("results/CANONICAL_RESULTS.md: ", "the single source of truth for every reported number."),
    ("results/CLAIMS_v1.17.md: ", "the final list of defensible and withdrawn claims."),
    ("results/EVIDENCE_EXTENSION.md: ", "the Gates 31–44 summary."),
    ("*_PREREGISTRATION.md: ", "the question, criteria and decision rule written before each gate ran."),
    ("*_verdict.md: ", "the measured finding and decision for each gate."),
    ("*_summary.csv: ", "the average result per configuration; *replications.csv holds the raw runs."),
    ("diagnostics_*.csv: ", "proportional hazards, calibration, ties and weight-cap diagnostics."),
    ("sweep1000_*.csv: ", "1,000-replication assessment sweeps; nested_tuning.csv and "
                          "split_study_*.csv hold the tuning and split-ratio studies."),
    ("results/historical/: ", "three pre-canonical ACTG175 records, kept only because FINAL_AUDIT.md "
                              "cites them; their numbers are superseded."),
):
    bullet(doc, label, text)

p(doc, "Paper and figures", size=13, bold=True, keep=True, space_before=6)
for label, text in (
    ("paper/CISCaRL_Engineering_Report_v2.docx/.pdf: ", "the 40-page engineering report."),
    ("paper/CISCaRL_IEEE_conference_detailed.docx/.pdf: ", "the 8-page IEEE-style paper: 15 figures, "
                                                           "10 tables."),
    ("paper/CISCaRL_Model_Creation_31_Steps_Detailed.docx/.pdf: ", "the 42-page step-by-step report "
                                                                   "with 52 exact exhibits."),
    ("paper/figs/: ", "38 files: 19 PNG and 19 PDF figures generated from the result CSVs."),
    ("paper/exhibits/: ", "42 images used by the 31-step report: 38 console screenshots and 4 plots."),
    ("paper/*.py: ", "the builders and content files for the figures, the IEEE paper and the "
                     "31-step report."),
):
    bullet(doc, label, text)

doc.add_page_break()
# ---------------------------------------------------------------- checklist
h = doc.add_heading("Part C — Coverage checklist", level=1)
h.paragraph_format.page_break_before = False
p(doc, ("Every code file appears below. The letter is its status: F = final pipeline, E = final "
        "evidence, H = historical, R = tested and rejected, S = support, X = external, B = build."))

codes = {"Final pipeline": "F", "Final evidence": "E", "Historical evidence": "H",
         "Tested and rejected": "R", "Support": "S", "External dependency": "X",
         "Build tool": "B"}
items = [(e[2], codes[e[1]]) for e in ENTRIES]
half = (len(items) + 1) // 2
left, right = items[:half], items[half:]

ct = doc.add_table(rows=1, cols=4)
ct.style = "Table Grid"
ct.alignment = WD_TABLE_ALIGNMENT.CENTER
for i, text in enumerate(("File", "S", "File", "S")):
    c = ct.rows[0].cells[i]
    c.text = ""
    set_run(c.paragraphs[0].add_run(text), 11, bold=True)

for i in range(half):
    cells = ct.add_row().cells
    values = [left[i][0], left[i][1], "", ""]
    if i < len(right):
        values[2], values[3] = right[i]
    for j, v in enumerate(values):
        cells[j].text = ""
        set_run(cells[j].paragraphs[0].add_run(v), 11)
        cells[j].paragraphs[0].paragraph_format.space_after = Pt(0)

doc.add_page_break()
# ---------------------------------------------------------------- glossary
h = doc.add_heading("Part D — Plain-language glossary", level=1)
h.paragraph_format.page_break_before = False
terms = [
    ("Estimand", "the exact quantity being estimated. Here it is the difference in 730-day survival "
                 "probability between treatment and control."),
    ("AIPW", "a doubly robust way to estimate a treatment effect. It combines a prediction model with "
             "the observed outcome, so it can still be right if one model is wrong."),
    ("Cox model", "a common survival model that estimates how patient characteristics change the risk "
                  "of the event over time."),
    ("Censoring", "when a patient's event is not observed before the end of follow-up or before they "
                  "leave the study."),
    ("Cross-fitting", "splitting the data into folds so a patient's own outcome is not used to predict "
                      "that patient. It prevents optimistic bias."),
    ("CART", "a small decision tree that splits patients into groups using simple yes/no rules."),
    ("Leaf / rule", "one end point of the tree. Its path from the root is an if-then rule."),
    ("Support", "the number of discovery patients who satisfy a rule. A small support means the rule "
                "may be a lucky accident."),
    ("Purity", "the share of treated patients in the rule who truly benefit."),
    ("Capture", "the share of the total true benefit that the rule finds."),
    ("LCB", "lower confidence bound: the pessimistic end of an interval. The model treats only when it "
            "is above zero."),
    ("Calibration", "adjusting predicted effects so they match observed effects on average."),
    ("Isotonic calibration", "a flexible calibration that only allows the predicted effect to rise, "
                             "never fall, as the raw score rises."),
    ("Influence function", "a formula for the uncertainty of an estimate; it gives the standard error "
                           "used in the interval."),
    ("Bootstrap", "repeating an analysis on resampled data to see how much the answer moves."),
    ("TMLE", "a targeted estimator that updates nuisance predictions toward the effect of interest. "
             "The fixed-horizon version was tested and rejected."),
    ("SCRE", "a survival causal rule ensemble; the external baseline, not the final model."),
    ("Jaccard", "the overlap between two sets of patients, from 0 (no overlap) to 1 (identical)."),
    ("Operating range", "the sample sizes where the model reliably beats the constant baseline."),
    ("Abstention", "the model's decision to recommend no treatment when the evidence is too weak."),
]
for term, text in terms:
    q = doc.add_paragraph(style="List Bullet")
    set_run(q.add_run(term + ": "), 12, bold=True)
    set_run(q.add_run(text), 12)
    q.paragraph_format.space_after = Pt(2)

doc.add_page_break()
# ---------------------------------------------------------------- close
h = doc.add_heading("Where to start", level=1)
h.paragraph_format.page_break_before = False
for text in (
    "Read the 31-step report first: it tells the story from the raw file to the frozen model, with "
    "the exact output of every step.",
    "Use this guide when you need to know what a specific file does, or whether a file is part of the "
    "final model or only the audit trail.",
    "Read CANONICAL_RESULTS.md for the numbers and CLAIMS_v1.17.md for what may and may not be said.",
    "Run python run_all.py --dry-run to see the commands, --quick for a safe smoke test, or the full "
    "command to rebuild the evidence.",
):
    q = doc.add_paragraph(style="List Bullet")
    set_run(q.add_run(text), 12)
    q.paragraph_format.space_after = Pt(2)

p(doc, ("Every claim in the project can be traced from a code file to a result file to a report "
        "sentence. That traceability is the point of this guide."), 12, italic=True, space_before=6)

doc.core_properties.title = "CISCaRL — Complete Code and File Guide"
doc.core_properties.author = "CISCaRL project"
doc.core_properties.subject = "Every code file and project area explained in plain language"
doc.core_properties.keywords = "code guide; reproducibility; survival analysis; subgroup discovery"

doc.save(OUT)
print("written", OUT)
