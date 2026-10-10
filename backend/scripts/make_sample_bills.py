import json
import random
from datetime import date, timedelta
from pathlib import Path

from app.constants import CATEGORY_AMOUNT_RANGES
from scripts.bill_maker import LAYOUTS, make_bill_pdf, make_bill_truth

random.seed(11)

OUTPUT_FOLDER = Path(__file__).resolve().parent / "sample_bills"
TRUTH_PATH = OUTPUT_FOLDER / "bills_truth.json"
TOTAL_BILLS = 30

PATIENTS = ["Ravi Kumar", "Priya Sharma", "Arjun Reddy", "Sneha Iyer", "Vikram Singh", "Lakshmi Nair"]
HOSPITALS = [
    ("Sunrise Multispeciality Hospital", "Hyderabad"),
    ("City Care Clinic", "Bengaluru"),
    ("Lotus Heart Institute", "Chennai"),
    ("Green Valley Hospital", "Chennai"),
    ("Metro Lifeline Hospital", "Delhi"),
]


def make_bills():
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    all_truth = {}

    for number in range(1, TOTAL_BILLS + 1):
        category = random.choice(list(CATEGORY_AMOUNT_RANGES))
        hospital_name, city = random.choice(HOSPITALS)
        admission = date(2026, 1, 1) + timedelta(days=random.randint(0, 250))
        discharge = admission + timedelta(days=random.randint(1, 6))
        total = round(random.uniform(*CATEGORY_AMOUNT_RANGES[category]), 2)

        truth = make_bill_truth(
            random.choice(PATIENTS), hospital_name, city, admission, discharge, category, total,
            LAYOUTS[number % len(LAYOUTS)],
        )
        file_name = f"bill_{number:02d}.pdf"
        (OUTPUT_FOLDER / file_name).write_bytes(make_bill_pdf(truth, f"INV-{number:04d}"))
        all_truth[file_name] = truth

    TRUTH_PATH.write_text(json.dumps(all_truth, indent=2))
    print(f"Saved {TOTAL_BILLS} bills and ground truth to {OUTPUT_FOLDER}")


if __name__ == "__main__":
    make_bills()
