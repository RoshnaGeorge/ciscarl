"""Build the detailed 31-step report with exact result exhibits."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

ROOT = Path(r"C:\Users\roshn\OneDrive\Desktop\Amrita\SEM 5\ML\Project")
FIG = ROOT / "paper" / "figs"
EXH = ROOT / "paper" / "exhibits"
OUT = ROOT / "paper" / "CISCaRL_Model_Creation_31_Steps_Detailed.docx"

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
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.15
    st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    for name, size in (("Heading 1", 15), ("Heading 2", 13), ("Title", 26)):
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
        h.paragraph_format.space_after = Pt(4)
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


def shade(par, fill="F2F2F2"):
    pPr = par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pPr.append(shd)


def p(doc, text="", size=12, bold=False, italic=False, align=None,
      space_before=0, space_after=6, keep=False):
    par = doc.add_paragraph()
    set_run(par.add_run(text), size=size, bold=bold, italic=italic)
    if align is not None:
        par.alignment = align
    par.paragraph_format.space_before = Pt(space_before)
    par.paragraph_format.space_after = Pt(space_after)
    par.paragraph_format.keep_with_next = keep
    return par


def lead(doc, label, text, shaded=False):
    par = doc.add_paragraph()
    set_run(par.add_run(label), 12, bold=True)
    set_run(par.add_run(text), 12)
    par.paragraph_format.space_before = Pt(1)
    par.paragraph_format.space_after = Pt(5)
    if shaded:
        par.paragraph_format.left_indent = Cm(0.25)
        par.paragraph_format.right_indent = Cm(0.25)
        shade(par)
    return par


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


FIGNUM = [0]


def exhibit(doc, path, caption, max_w=16.8, max_h=23.0):
    path = Path(path)
    if not path.exists():
        print("missing exhibit:", path)
        return
    w, h = Image.open(path).size
    width_cm = max_w
    height_cm = width_cm * h / w
    if height_cm > max_h:
        height_cm = max_h
        width_cm = height_cm * w / h
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.paragraph_format.space_before = Pt(2)
    par.paragraph_format.space_after = Pt(2)
    par.add_run().add_picture(str(path), width=Cm(width_cm))
    FIGNUM[0] += 1
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run(cap.add_run(f"Exhibit {FIGNUM[0]}. {caption}"), 12, italic=True)
    cap.paragraph_format.space_after = Pt(8)


from report_content import STEPS


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
set_run(head.add_run("CISCaRL — Detailed Model Creation in 31 Steps"), 9, italic=True)

foot = sec.footer.paragraphs[0]
foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(foot.add_run("Page "), 9)
field(foot, "PAGE")
set_run(foot.add_run(" of "), 9)
field(foot, "NUMPAGES")

# title
for _ in range(3):
    p(doc, "", space_after=0)

t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(t.add_run("CISCaRL"), 30, bold=True)
t.paragraph_format.space_after = Pt(2)

t2 = doc.add_paragraph()
t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(t2.add_run("Detailed Model Creation Report"), 20, bold=True)
t2.paragraph_format.space_after = Pt(4)

t3 = doc.add_paragraph()
t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
set_run(t3.add_run("31 steps, with the exact output of every step"), 13, italic=True)
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
set_run(note.add_run("Every result exhibit is the output of the executed notebook, copied verbatim. "
                     "The figures are the saved paper figures generated from the result files."),
        12, italic=True)

doc.add_page_break()

# overview
h = doc.add_heading("Project at a glance", level=1)
h.paragraph_format.page_break_before = False

table = doc.add_table(rows=0, cols=2)
table.style = "Table Grid"
table.alignment = WD_TABLE_ALIGNMENT.CENTER
rows = [
    ("Dataset", "ACTG175, arms 0 and 1, n = 1,054; 12 baseline covariates"),
    ("Estimand", "τ(730|x) = S1(730|x) − S0(730|x), composite progression-free endpoint"),
    ("Partitions", "527 discovery / 263 validation / 264 assessment (disjoint)"),
    ("Estimator", "Per-arm Cox + conditional censoring Cox, 5-fold cross-fit, AIPW"),
    ("Learner", "Depth-3 CART, minimum leaf 60, squared error"),
    ("Selection", "Highest discovery mean with support ≥ 200; fallback flagged"),
    ("Decision", "Treat only if the validation one-sided 95% lower bound is above zero"),
    ("Final ACTG175 result", "Rule support 61; validation LCB −0.250; decision INSUFFICIENT"),
]
for k, v in rows:
    cells = table.add_row().cells
    cells[0].width = Cm(4.8)
    cells[1].width = Cm(11.4)
    cells[0].text = ""
    cells[1].text = ""
    set_run(cells[0].paragraphs[0].add_run(k), 12, bold=True)
    set_run(cells[1].paragraphs[0].add_run(v), 12)
    cells[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
    cells[0].paragraphs[0].paragraph_format.space_after = Pt(2)
    cells[1].paragraphs[0].paragraph_format.space_after = Pt(2)

p(doc, "", space_after=4)
p(doc, "How to read this report", size=13, bold=True, keep=True)
p(doc, ("The report follows the 31 steps of the executed notebook. Each step begins with the code "
        "that was used, then explains what was done and why it matters. The result paragraph gives "
        "the numbers in plain language. The exhibit that follows is the exact output of that step, "
        "copied verbatim from the notebook; where a figure exists, it is shown as well. The final "
        "paragraph says what the result means and what decision it forced."))

p(doc, "What is shown for every step", size=13, bold=True, keep=True, space_before=6)
for text in (
    "Code used — the script or notebook cell that produced the result.",
    "What we did — the action in plain language.",
    "Why this step matters — the risk it controls.",
    "Result obtained — the key numbers in one short paragraph.",
    "Exact result — a picture of the console output from the executed notebook, plus any saved figure.",
    "What this means — the inference, including what is not supported.",
    "Decision at this step — the choice that was frozen or rejected.",
):
    q = doc.add_paragraph(style="List Bullet")
    set_run(q.add_run(text), 12)
    q.paragraph_format.space_after = Pt(1)

p(doc, ("The complete document is long by design: it is meant to be read beside the notebook or used "
        "as an audit trail. Every number can be found in results/ and every exhibit can be rebuilt "
        "by running the notebook or run_all.py."), 12, italic=True, space_before=4)

doc.add_page_break()

# contents
h = doc.add_heading("Contents", level=1)
h.paragraph_format.page_break_before = False
for i, step in enumerate(STEPS, 1):
    q = doc.add_paragraph()
    set_run(q.add_run(f"Step {i}.  {step['title']}"), 12)
    q.paragraph_format.space_after = Pt(1)
    q.paragraph_format.left_indent = Cm(0.5)

# steps
doc.add_page_break()
for i, step in enumerate(STEPS, 1):
    h = doc.add_heading(f"Step {i} — {step['title']}", level=1)
    h.paragraph_format.page_break_before = False
    h.paragraph_format.keep_with_next = True

    code = doc.add_paragraph()
    set_run(code.add_run("Code used: "), 12, bold=True)
    set_run(code.add_run(step["code"]), 12)
    code.paragraph_format.space_after = Pt(3)
    code.paragraph_format.keep_with_next = True
    para_border(code, size=6, color="808080")

    w = lead(doc, "What we did – ", step["what"])
    w.paragraph_format.keep_with_next = True
    lead(doc, "Why this step matters – ", step["why"])
    lead(doc, "Result obtained: ", step["result"], shaded=True)
    lead(doc, "What this means: ", step["meaning"])
    d = lead(doc, "Decision at this step: ", step["decision"])
    d.paragraph_format.space_after = Pt(8)

    lab = doc.add_paragraph()
    set_run(lab.add_run("Exact result"), 12, bold=True)
    lab.paragraph_format.space_before = Pt(4)
    lab.paragraph_format.space_after = Pt(2)
    lab.paragraph_format.keep_with_next = True

    parts = sorted(EXH.glob(f"console_{i:02d}_*.png"))
    for k, path in enumerate(parts, 1):
        suffix = f" (part {k} of {len(parts)})" if len(parts) > 1 else ""
        exhibit(doc, path,
                f"Exact console output of Step {i}{suffix}, copied verbatim from the executed notebook.",
                max_w=15.6, max_h=13.5)

    for path, caption in step["figures"]:
        exhibit(doc, path, caption, max_w=15.6, max_h=15.0)

    end = doc.add_paragraph()
    end.paragraph_format.space_after = Pt(6)
    para_border(end, size=4, color="A0A0A0")

doc.add_page_break()
h = doc.add_heading("Addendum — post-freeze tuning and explainability", level=1)
h.paragraph_format.page_break_before = False
p(doc, ("After the 31 steps were frozen, four additional audits were run. None of them changed the "
        "final rule or decision; they record what was tested and what failed."))

for text in (
    "Gate 45 tuned 540 CART configurations on ACTG175 discovery. The lowest nested MAE was 0.85982 "
    "for depth 5 / leaf 30, against 0.86379 for the frozen depth 3 / leaf 60 (rank 54 of 540). The "
    "gain was small and required five conditions, so it was not adopted.",
    "Gate 46 compared CART with random forest, extra trees, gradient boosting, histogram gradient "
    "boosting and a ridge stack. No ensemble had a capture gain with a 95% interval above zero, and "
    "costs were 4.8–65.9 s versus 0.07 s for CART. CART was retained.",
    "Gate 47 tuned 48 CART configurations on simulated subgroup performance. Depth 2 / absolute error "
    "won in simulation (validation LCB +0.0605/+0.0731), but on ACTG175 it selected 122 patients, had "
    "LCB −0.210 and abstained. The frozen tree remained.",
    "Gate 48 ran exact TreeSHAP on the final CART and LIME on 40 rule-in/rule-out patients. SHAP "
    "ranked cd40 0.128, homo 0.093, cd80 0.057 and wtkg 0.035; all other features were zero. "
    "SHAP–LIME top-5 overlap was 0.767 inside the rule and 0.700 outside; LIME stability across seeds "
    "was 0.703/0.712. This is moderate agreement, so the readable rule remains the primary "
    "explanation and SHAP/LIME are secondary audits.",
):
    q = doc.add_paragraph(style="List Bullet")
    set_run(q.add_run(text), 12)
    q.paragraph_format.space_after = Pt(2)

exhibit(doc, ROOT / "paper" / "figs" / "fig_gate48_shap_global.png",
        "SHAP global importance on the final CART. Only the four split features have non-zero values.",
        max_w=15.0, max_h=13.0)
exhibit(doc, ROOT / "paper" / "figs" / "fig_gate48_lime_example.png",
        "LIME explanation for one assessment patient, on the raw covariate scale. The local top features "
        "overlap the rule but LIME is not stable enough to replace it.",
        max_w=15.0, max_h=11.0)

# final
doc.add_page_break()
h = doc.add_heading("Final summary", level=1)
h.paragraph_format.page_break_before = False

p(doc, ("The 31 steps produce one frozen model and a complete evidence record. The table below shows "
        "what was kept and what was rejected after testing."))

t = doc.add_table(rows=1, cols=3)
t.style = "Table Grid"
t.alignment = WD_TABLE_ALIGNMENT.CENTER
t.autofit = False
widths = (Cm(3.2), Cm(4.2), Cm(8.8))
headers = ("Layer", "Kept", "Rejected after testing")
for i, text in enumerate(headers):
    cell = t.rows[0].cells[i]
    cell.text = ""
    cell.width = widths[i]
    set_run(cell.paragraphs[0].add_run(text), 12, bold=True)
    cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

final_rows = [
    ("Outcome model", "Per-arm Cox", "RSF, GBM, equal-weight and learned stacking"),
    ("Rule learner", "Depth-3 CART", "Pruned CART, PRIM, classification tree, boosting"),
    ("Estimator", "AIPW", "Pooled Cox, T-learner, IPW, plug-in, fixed-horizon IPCW-TMLE"),
    ("Selection", "Support ≥ 200", "Max mean, LCB-only, stability-weighted, two-leaf list"),
    ("Decision", "Validation LCB > 0", "No commitment, shrinkage-only, looser thresholds"),
    ("Calibration", "Isotonic (prediction only)", "None, empirical-Bayes shrinkage"),
    ("Interval", "Influence function", "Selection bootstrap, split-conformal, Bonferroni"),
    ("Folds", "5", "3, 10"),
    ("Features", "12 published covariates", "16-candidate set, lasso, RFE"),
    ("Horizon", "730 days", "365, 548, 845, 912, 965, 1,095"),
]
for row in final_rows:
    cells = t.add_row().cells
    for i, text in enumerate(row):
        cells[i].text = ""
        cells[i].width = widths[i]
        set_run(cells[i].paragraphs[0].add_run(text), 12)
        cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
        cells[i].paragraphs[0].paragraph_format.space_after = Pt(2)

p(doc, "", space_after=2)
p(doc, "The final ACTG175 result", size=13, bold=True, keep=True)
p(doc, ("Overall τ(730) is +0.124 [−0.002, +0.250]. The selected rule is "
        "cd40 ≤ 407.5 AND wtkg > 71.0 AND homo ≤ 0.5, with 61 discovery patients. Validation is "
        "+0.116 (SE 0.222; one-sided lower bound −0.250), so the model returns INSUFFICIENT and does "
        "not recommend treatment. Assessment is +0.401 [+0.033, +0.770] on 38 patients, but "
        "assessment never participates in the decision."))

p(doc, ("The result is a precision-oriented operating point with an explicit abstention layer, not "
        "a universal improvement over the average effect. The method needs roughly 4,000–6,000 "
        "patients before it reliably beats treating everyone; ACTG175 has 527 discovery patients, so "
        "abstention is the honest output."))

p(doc, "Limitations stated in the report", size=13, bold=True, keep=True, space_before=4)
for text in (
    "ACTG175 has no individual treatment-effect truth; purity, capture and MAE come from simulation.",
    "The rule is unstable: 20 different splits gave 20 different rules, with Jaccard about 0.34.",
    "The influence-function interval conditions on the selected rule; coverage is 90–95%.",
    "Fairness and transport are underpowered: every race and gender group has fewer than 30 rule patients.",
    "The 730-day horizon is retained on stability, not because it is a universal clinical optimum.",
    "Longitudinal TMLE was not implemented; the fixed-horizon version was tested and rejected.",
):
    q = doc.add_paragraph(style="List Bullet")
    set_run(q.add_run(text), 12)
    q.paragraph_format.space_after = Pt(0)

doc.core_properties.title = "CISCaRL — Detailed Model Creation Report"
doc.core_properties.author = "CISCaRL project"
doc.core_properties.subject = "31 steps from raw data to a frozen model, with exact outputs"
doc.core_properties.keywords = "survival analysis; subgroup discovery; AIPW; CART; reproducibility"

doc.save(OUT)
print("written", OUT)
