from doctor_finder import find_doctors_by_city

results = find_doctors_by_city("Karachi", "hematologist")
print(f"Found: {len(results)} results")
for r in results:
    print(f"- {r['name']} | {r['address']}")