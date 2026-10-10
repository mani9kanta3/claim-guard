import json
import time
from pathlib import Path

from app import create_app
from app.services.extraction import extract_bill
from app.services.risk_rules import names_match

BILLS_FOLDER = Path(__file__).resolve().parent / "sample_bills"
TRUTH_PATH = BILLS_FOLDER / "bills_truth.json"
REPORT_PATH = Path(__file__).resolve().parents[1] / "ml" / "extraction_report.json"

PAUSE_SECONDS = 2

FIELDS = ["patient_name", "hospital_name", "admission_date", "discharge_date", "total_amount"]


def field_is_correct(field, expected, found):
    if found is None:
        return False
    if field == "total_amount":
        return abs(float(found) - float(expected)) <= 1
    if field in ("patient_name", "hospital_name"):
        return names_match(str(found), str(expected))
    return str(found) == str(expected)


def evaluate():
    truth = json.loads(TRUTH_PATH.read_text())
    correct = {field: 0 for field in FIELDS}
    failed = 0
    providers = {}

    for file_name, expected in truth.items():
        status, data = extract_bill((BILLS_FOLDER / file_name).read_bytes())
        time.sleep(PAUSE_SECONDS)

        if status != "DONE":
            failed += 1
            print(f"{file_name}: FAILED ({data.get('error')})")
            continue

        providers[data["provider"]] = providers.get(data["provider"], 0) + 1
        wrong = []
        for field in FIELDS:
            if field_is_correct(field, expected[field], data.get(field)):
                correct[field] += 1
            else:
                wrong.append(field)
        print(f"{file_name} ({expected['layout']}): {'all correct' if not wrong else 'wrong: ' + ', '.join(wrong)}")

    total = len(truth)
    report = {
        "bills": total,
        "failed": failed,
        "providers_used": providers,
        "field_accuracy": {field: round(count / total, 3) for field, count in correct.items()},
    }
    report["overall_accuracy"] = round(sum(correct.values()) / (total * len(FIELDS)), 3)
    REPORT_PATH.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    with create_app().app_context():
        evaluate()
