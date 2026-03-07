from extractor import process_report

result, raw = process_report("sample_report.pdf")
print("=== STRUCTURED DATA ===")
print(result)
print("\n=== RAW TEXT ===")
print(raw)