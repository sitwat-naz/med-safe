from extractor import process_report
from tools import check_abnormalities, verify_medications
import json

# Step 1: Extract
structured_data, raw_text = process_report("sample_report.pdf")

# Clean JSON string
clean = structured_data.strip()
if clean.startswith("```"):
    clean = clean.split("```")[1]
    if clean.startswith("json"):
        clean = clean[4:]

data = json.loads(clean)

# Step 2: Check abnormalities
print("=== ABNORMALITY ANALYSIS ===")
results = check_abnormalities(data["lab_results"])
for r in results:
    print(f"{r['test_name']}: {r['status']} — {r.get('explanation','')}")

# Step 3: Verify medications
print("\n=== MEDICATION VERIFICATION ===")
meds = verify_medications(data["medications"])
for m in meds:
    print(m)