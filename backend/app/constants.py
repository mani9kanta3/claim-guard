ROLES = ["CUSTOMER", "OFFICER", "ADMIN"]

POLICY_STATUSES = ["ACTIVE", "EXPIRED", "CANCELLED"]

CLAIM_STATUSES = [
    "SUBMITTED",
    "UNDER_REVIEW",
    "INVESTIGATION",
    "APPROVED",
    "REJECTED",
    "SETTLED",
]

DIAGNOSIS_CATEGORIES = [
    "FEVER",
    "FRACTURE",
    "CARDIAC",
    "MATERNITY",
    "SURGERY_MINOR",
    "SURGERY_MAJOR",
    "RESPIRATORY",
    "OTHER",
]

RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]

DOCUMENT_TYPES = ["HOSPITAL_BILL", "DISCHARGE_SUMMARY"]

EXTRACTION_STATUSES = ["PENDING", "DONE", "FAILED"]

RULE_CODES = ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]

MAX_FILE_SIZE = 2 * 1024 * 1024

CATEGORY_AMOUNT_RANGES = {
    "FEVER": (15000, 60000),
    "FRACTURE": (40000, 150000),
    "CARDIAC": (150000, 400000),
    "MATERNITY": (50000, 120000),
    "SURGERY_MINOR": (30000, 90000),
    "SURGERY_MAJOR": (150000, 500000),
    "RESPIRATORY": (25000, 80000),
    "OTHER": (10000, 50000),
}

CATEGORY_AVERAGE_AMOUNT = {
    category: (low + high) / 2 for category, (low, high) in CATEGORY_AMOUNT_RANGES.items()
}

RULE_POINTS = {
    "R1": 25,
    "R2": 40,
    "R3": 15,
    "R4": 20,
    "R5": 10,
    "R6": 15,
    "R7": 20,
    "R8": 15,
}

HIGH_RISK_SCORE = 60
MEDIUM_RISK_SCORE = 30


def sql_in(column, values):
    quoted = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({quoted})"
