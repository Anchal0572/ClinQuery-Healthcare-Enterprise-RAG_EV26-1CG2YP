"""
Synthetic Healthcare Document Generator
Creates de-identified, realistic clinical test documents across all supported formats:
1. PDF (Clinical Protocol with sections & tables)
2. DOCX (ICU Clinical Practice Guideline with tables)
3. CSV (Antimicrobial Formulary & Dosing Table)
4. XLSX (Critical Laboratory Reference Intervals)
5. TXT (Clinical Protocol & Decision Tree)
"""

import os
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import docx
import openpyxl

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")
os.makedirs(SAMPLE_DIR, exist_ok=True)


def create_synthetic_pdf():
    pdf_path = os.path.join(SAMPLE_DIR, "synthetic_cardiology_hf_guideline.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=18, leading=22, textColor=colors.HexColor("#1A365D"))
    heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], fontSize=13, leading=16, textColor=colors.HexColor("#2B6CB0"))
    body_style = styles["Normal"]

    story.append(Paragraph("AHA/ACC Synthetic Clinical Guideline: HFrEF Pharmacotherapy", title_style))
    story.append(Paragraph("Document Version: 2.1 | Department: Cardiology | Effective Date: 2024-06-01", styles["Italic"]))
    story.append(Spacer(1, 12))

    # Section 1
    story.append(Paragraph("Section 1: Initial Clinical Assessment and Quadruple Therapy", heading_style))
    story.append(Paragraph(
        "For patients diagnosed with symptomatic Stage C Heart Failure with Reduced Ejection Fraction (HFrEF, LVEF <= 40%), "
        "guideline-directed medical therapy (GDMT) comprises quadruple pharmacotherapy initiated sequentially or in rapid succession. "
        "The foundational pillars include an ARNI/ACEi, evidence-based beta blocker (Carvedilol, Metoprolol Succinate, or Bisoprolol), "
        "a Mineralocorticoid Receptor Antagonist (MRA), and an SGLT2 inhibitor.",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Section 2: Table
    story.append(Paragraph("Section 2: Pharmacotherapy Dosing and Titration Table", heading_style))
    data = [
        ["Drug Class", "First-Line Agent", "Starting Dose", "Target Maintenance Dose"],
        ["ARNI", "Sacubitril/Valsartan", "49/51 mg PO BID", "97/103 mg PO BID"],
        ["Beta-Blocker", "Carvedilol", "3.125 mg PO BID", "25 mg PO BID (50 mg if >85kg)"],
        ["MRA", "Spironolactone", "12.5 - 25 mg PO Daily", "25 - 50 mg PO Daily"],
        ["SGLT2i", "Empagliflozin", "10 mg PO Daily", "10 mg PO Daily"],
    ]
    t = Table(data, colWidths=[90, 140, 130, 160])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Page Break to test multi-page extraction
    story.append(PageBreak())

    # Section 3
    story.append(Paragraph("Section 3: Renal Impairment and Hyperkalemia Monitoring", heading_style))
    story.append(Paragraph(
        "Monitor serum creatinine, estimated GFR, and serum potassium at 1 to 2 weeks post-initiation or dose escalation. "
        "A transient rise in serum creatinine of up to 30% from baseline is acceptable and reflects intraglomerular hemodynamic changes. "
        "Withhold or down-titrate MRA if serum potassium exceeds 5.5 mEq/L or eGFR drops below 20 mL/min/1.73m2.",
        body_style
    ))
    story.append(Spacer(1, 12))

    doc.build(story)
    print(f"[+] Created synthetic PDF: {pdf_path}")
    return pdf_path


def create_synthetic_docx():
    docx_path = os.path.join(SAMPLE_DIR, "synthetic_icu_sepsis_resuscitation.docx")
    doc = docx.Document()

    doc.add_heading("ICU Synthetic Protocol: Sepsis & Septic Shock Resuscitation", 0)
    p = doc.add_paragraph("Department: Intensive Care Unit (ICU) | Version: 3.4 | Status: Approved")
    p.italic = True

    doc.add_heading("Section 1: Hour-1 Emergency Bundle", level=1)
    doc.add_paragraph(
        "For patients exhibiting signs of severe sepsis or septic shock, immediate resuscitation within the first hour "
        "is mandatory to decrease in-hospital mortality. Step 1: Measure initial blood lactate level; remeasure within 2-4 hours if elevated (>2 mmol/L). "
        "Step 2: Obtain appropriate blood cultures prior to initiation of antimicrobial therapy. "
        "Step 3: Administer broad-spectrum empiric intravenous antimicrobials within 60 minutes of recognition."
    )

    doc.add_heading("Section 2: Hemodynamic Support & Vasopressors", level=1)
    doc.add_paragraph(
        "Administer 30 mL/kg of balanced crystalloid solution (e.g. Plasma-Lyte or Lactated Ringer's) for hypotension or lactate >= 4 mmol/L. "
        "If MAP remains < 65 mm Hg despite volume loading, initiate norepinephrine as first-choice vasopressor via central venous catheter."
    )

    doc.add_heading("Section 3: First-Line Antimicrobial Dosing Table", level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Pathogen Focus"
    hdr_cells[1].text = "Empiric Regimen"
    hdr_cells[2].text = "Loading Dose"
    hdr_cells[3].text = "Maintenance Infusion"

    regimens = [
        ("Broad Gram-Negative / Pseudomonas", "Piperacillin-Tazobactam", "4.5 g IV push over 30 min", "3.375 g IV Q8H extended 4h infusion"),
        ("MRSA / Resistant Gram-Positive", "Vancomycin", "25-30 mg/kg IV loading dose", "15-20 mg/kg IV Q8-12H targeted trough 15-20"),
        ("Hospital-Acquired / Ventilator", "Meropenem", "1 g IV push", "1 g IV Q8H extended 3h infusion"),
    ]
    for focus, drug, load, maint in regimens:
        row_cells = table.add_row().cells
        row_cells[0].text = focus
        row_cells[1].text = drug
        row_cells[2].text = load
        row_cells[3].text = maint

    doc.save(docx_path)
    print(f"[+] Created synthetic DOCX: {docx_path}")
    return docx_path


def create_synthetic_csv():
    csv_path = os.path.join(SAMPLE_DIR, "synthetic_emergency_drug_formulary.csv")
    headers = ["Medication_Name", "Generic_Class", "Clinical_Indication", "Route", "Standard_Dosing", "Max_Daily_Dose", "Critical_Contraindication"]
    rows = [
        ["Amiodarone HCl", "Class III Antiarrhythmic", "Ventricular Fibrillation / Pulseless VT", "IV Infusion", "300 mg IV bolus, then 150 mg second dose", "2.2 g per 24 hours", "Severe sinus-node dysfunction, 2nd/3rd degree AV block"],
        ["Atropine Sulfate", "Anticholinergic", "Symptomatic Bradycardia", "IV Push", "1.0 mg IV every 3-5 min as needed", "3.0 mg total cumulative", "Caution in myocardial ischemia / coronary disease"],
        ["Dopamine HCl", "Inotrope / Vasopressor", "Cardiogenic / Septic Shock", "IV Infusion", "5 - 20 mcg/kg/min titrated to MAP", "50 mcg/kg/min", "Pheochromocytoma, uncorrected tachyarrhythmias"],
        ["Epinephrine", "Sympathomimetic Adrenergic", "Cardiac Arrest / Anaphylaxis", "IV / IM", "1 mg (1:10,000) IV Q3-5min in arrest; 0.3 mg IM in anaphylaxis", "No strict max in arrest", "None during life-threatening cardiac arrest"],
        ["Adenosine", "Antiarrhythmic Nucleoside", "Paroxysmal Supraventricular Tachycardia", "Rapid IV Push", "6 mg rapid IV push followed by saline flush; then 12 mg", "12 mg single dose", "2nd/3rd degree AV block, sick sinus syndrome, asthma bronchospasm"],
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"[+] Created synthetic CSV: {csv_path}")
    return csv_path


def create_synthetic_xlsx():
    xlsx_path = os.path.join(SAMPLE_DIR, "synthetic_critical_lab_intervals.xlsx")
    wb = openpyxl.Workbook()

    # Sheet 1: Chemistry
    ws1 = wb.active
    ws1.title = "Chemistry Panel"
    headers_chem = ["Analyte", "Specimen", "Standard_Interval", "Units", "Critical_Low", "Critical_High", "Clinical_Action"]
    rows_chem = [
        ["Serum Potassium", "Plasma/Serum", "3.5 - 5.0", "mEq/L", "< 2.8", "> 6.0", "Stat ECG, tele monitoring, calcium gluconate if peaked T-waves"],
        ["Serum Sodium", "Plasma/Serum", "136 - 145", "mEq/L", "< 120", "> 160", "Neurology consult, correct sodium <= 8-10 mEq/L per 24h"],
        ["Serum Glucose", "Plasma", "70 - 99", "mg/dL", "< 54", "> 400", "Administer 50% Dextrose IV push or IV insulin infusion"],
        ["Serum Creatinine", "Serum", "0.7 - 1.3", "mg/dL", "N/A", "> 4.0", "Assess urine output, hold nephrotoxins, renal consult"],
        ["Serum Lactate", "Whole Blood", "0.5 - 2.0", "mmol/L", "N/A", "> 4.0", "Initiate severe sepsis resuscitation bundle, fluid challenge"],
    ]
    ws1.append(headers_chem)
    for r in rows_chem:
        ws1.append(r)

    # Sheet 2: Hematology
    ws2 = wb.create_sheet(title="Hematology Panel")
    headers_hem = ["Parameter", "Standard_Range", "Units", "Critical_Low", "Critical_High", "Urgent_Action"]
    rows_hem = [
        ["Hemoglobin", "12.0 - 17.5", "g/dL", "< 7.0", "> 20.0", "Type & Screen, PRBC transfusion if symptomatic or active hemorrhage"],
        ["Platelet Count", "150,000 - 450,000", "/mcL", "< 20,000", "> 1,000,000", "Transfuse apheresis platelets, hold antiplatelets/anticoagulation"],
        ["Absolute Neutrophil Count", "1.5 - 8.0", "10^3/mcL", "< 0.5", "N/A", "Neutropenic precautions, stat empiric broad-spectrum antibiotics if febrile"],
        ["INR (Warfarin Therapy)", "2.0 - 3.0", "Ratio", "N/A", "> 5.0", "Hold warfarin, administer oral/IV Vitamin K1 or 4-factor PCC if bleeding"],
    ]
    ws2.append(headers_hem)
    for r in rows_hem:
        ws2.append(r)

    wb.save(xlsx_path)
    print(f"[+] Created synthetic XLSX: {xlsx_path}")
    return xlsx_path


def create_synthetic_txt():
    txt_path = os.path.join(SAMPLE_DIR, "synthetic_stroke_thrombolysis_protocol.txt")
    content = """CLINICAL PRACTICE PROTOCOL: ACUTE ISCHEMIC STROKE THROMBOLYSIS
Document Version: 1.5
Department: Emergency Medicine / Neurology
Effective Date: 2024-05-15

Section 1: Inclusion Criteria for Intravenous Alteplase / Tenecteplase
1. Diagnosis of acute ischemic stroke causing measurable neurological deficit (NIHSS >= 4).
2. Onset of symptoms clearly established to be within 4.5 hours prior to initiation of treatment.
3. Patient age 18 years or older.
4. Non-contrast brain CT scan demonstrating absence of acute intracranial hemorrhage.

Section 2: Critical Contraindications
1. Active internal bleeding or acute bleeding diathesis.
2. Platelet count below 100,000/mcL.
3. Current anticoagulant use with INR > 1.7 or PT > 15 seconds.
4. Use of direct thrombin inhibitors or direct factor Xa inhibitors within prior 48 hours.
5. Systolic blood pressure > 185 mm Hg or diastolic blood pressure > 110 mm Hg refractory to acute antihypertensive treatment.

Section 3: Blood Pressure Management Prior to Thrombolysis
Administer Labetalol 10-20 mg IV over 1-2 minutes; may repeat once or administer Nicardipine IV infusion 5 mg/h, titrated by 2.5 mg/h every 5-15 minutes (max 15 mg/h) to maintain target SBP < 185 mm Hg and DBP < 110 mm Hg.
"""
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(content.strip())

    print(f"[+] Created synthetic TXT: {txt_path}")
    return txt_path


def generate_all():
    print("Generating comprehensive synthetic healthcare document suite...")
    create_synthetic_pdf()
    create_synthetic_docx()
    create_synthetic_csv()
    create_synthetic_xlsx()
    create_synthetic_txt()
    print("All synthetic test documents generated successfully!")


if __name__ == "__main__":
    generate_all()
