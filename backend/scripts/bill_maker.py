import random
from datetime import date
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

DIAGNOSIS_NAMES = {
    "FEVER": ["Dengue fever", "Viral fever", "Typhoid fever"],
    "FRACTURE": ["Fracture of right radius", "Ankle fracture", "Fracture of left femur"],
    "CARDIAC": ["Acute myocardial infarction", "Angina pectoris", "Coronary artery disease"],
    "MATERNITY": ["Normal delivery", "Caesarean section delivery"],
    "SURGERY_MINOR": ["Appendectomy", "Hernia repair", "Cataract surgery"],
    "SURGERY_MAJOR": ["Knee replacement", "Spinal fusion surgery", "Bypass surgery"],
    "RESPIRATORY": ["Pneumonia", "Acute bronchitis", "Asthma attack"],
    "OTHER": ["Food poisoning", "Kidney stone", "Gastroenteritis"],
}

LINE_ITEM_NAMES = [
    "Room charges",
    "Doctor consultation",
    "Pharmacy and medicines",
    "Laboratory tests",
    "Procedure charges",
    "Nursing charges",
]

LAYOUTS = ["table", "plain", "gst"]


def rupees(amount):
    return f"Rs. {amount:,.2f}"


def date_text(value, layout):
    if layout == "table":
        return value.strftime("%d-%b-%Y")
    if layout == "plain":
        return value.strftime("%d/%m/%Y")
    return value.isoformat()


def split_amount(total, parts):
    weights = [random.uniform(0.5, 2.0) for _ in range(parts)]
    amounts = [round(total * weight / sum(weights), 2) for weight in weights]
    amounts[-1] = round(total - sum(amounts[:-1]), 2)
    return amounts


def make_bill_truth(patient_name, hospital_name, city, admission_date, discharge_date, category, total_amount, layout):
    item_count = random.randint(3, 5)

    if layout == "gst":
        subtotal = round(total_amount / 1.05, 2)
        gst = round(total_amount - subtotal, 2)
        amounts = split_amount(subtotal, item_count) + [gst]
        names = random.sample(LINE_ITEM_NAMES, item_count) + ["GST @ 5%"]
    else:
        amounts = split_amount(total_amount, item_count)
        names = random.sample(LINE_ITEM_NAMES, item_count)

    return {
        "patient_name": patient_name,
        "hospital_name": hospital_name,
        "city": city,
        "admission_date": admission_date.isoformat(),
        "discharge_date": discharge_date.isoformat(),
        "diagnosis": random.choice(DIAGNOSIS_NAMES[category]),
        "line_items": [{"description": name, "amount": amount} for name, amount in zip(names, amounts)],
        "total_amount": round(total_amount, 2),
        "layout": layout,
    }


def make_bill_pdf(truth, bill_number):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    layout = truth["layout"]
    admission = date.fromisoformat(truth["admission_date"])
    discharge = date.fromisoformat(truth["discharge_date"])

    story = [
        Paragraph(truth["hospital_name"], styles["Title"]),
        Paragraph(f"{truth['city']}, India", styles["Normal"]),
        Spacer(1, 6 * mm),
        Paragraph("<b>FINAL HOSPITAL BILL</b>", styles["Heading2"]),
        Paragraph(f"Bill No: {bill_number}", styles["Normal"]),
        Paragraph(f"Patient Name: {truth['patient_name']}", styles["Normal"]),
        Paragraph(f"Date of Admission: {date_text(admission, layout)}", styles["Normal"]),
        Paragraph(f"Date of Discharge: {date_text(discharge, layout)}", styles["Normal"]),
        Paragraph(f"Diagnosis: {truth['diagnosis']}", styles["Normal"]),
        Spacer(1, 6 * mm),
    ]

    if layout == "plain":
        for item in truth["line_items"]:
            story.append(Paragraph(f"{item['description']} ........ {rupees(item['amount'])}", styles["Normal"]))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(f"<b>Net Amount Payable: {rupees(truth['total_amount'])}</b>", styles["Normal"]))
    else:
        rows = [["S.No", "Description", "Amount"]]
        for number, item in enumerate(truth["line_items"], start=1):
            rows.append([str(number), item["description"], rupees(item["amount"])])
        rows.append(["", "Grand Total", rupees(truth["total_amount"])])

        table = Table(rows, colWidths=[15 * mm, 110 * mm, 40 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ]
            )
        )
        story.append(table)

    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("This is a computer generated bill. Synthetic data for testing only.", styles["Italic"]))

    SimpleDocTemplate(buffer, pagesize=A4, title=f"Bill {bill_number}").build(story)
    return buffer.getvalue()
