from extractor import process_report
from tools import check_abnormalities, verify_medications
from summarizer import generate_patient_summary, generate_physician_brief
import json

# Extract
structured_data, raw_text = process_report("sample_report.pdf")
clean = structured_data.strip()
if clean.startswith("```"):
    clean = clean.split("```")[1]
    if clean.startswith("json"):
        clean = clean[4:]

data = json.loads(clean)

# Analyze
analyzed = check_abnormalities(data["lab_results"])
medications = verify_medications(data["medications"])

# Generate summaries
print("=== PATIENT SUMMARY ===\n")
patient_summary = generate_patient_summary(analyzed, data["patient_name"])
print(patient_summary)

print("\n=== PHYSICIAN BRIEF ===\n")
physician_brief = generate_physician_brief(
    analyzed, medications,
    data["patient_name"],
    data["report_date"]
)
print(physician_brief)