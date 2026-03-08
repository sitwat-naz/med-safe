import requests
import time

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "MedSafe-App/1.0 (medical report assistant)"}

SPECIALIST_MAP = {
    "hemoglobin": "hematologist",
    "hb": "hematologist",
    "pcv": "hematologist",
    "platelet": "hematologist",
    "wbc": "hematologist",
    "rbc": "hematologist",
    "glucose": "endocrinologist",
    "hba1c": "endocrinologist",
    "insulin": "endocrinologist",
    "thyroid": "endocrinologist",
    "tsh": "endocrinologist",
    "cholesterol": "cardiologist",
    "lipid": "cardiologist",
    "triglyceride": "cardiologist",
    "ecg": "cardiologist",
    "echo": "cardiologist",
    "creatinine": "nephrologist",
    "kidney": "nephrologist",
    "urea": "nephrologist",
    "gfr": "nephrologist",
    "liver": "gastroenterologist",
    "bilirubin": "gastroenterologist",
    "alt": "gastroenterologist",
    "ast": "gastroenterologist",
    "sgpt": "gastroenterologist",
    "ct scan": "radiologist",
    "x-ray": "radiologist",
    "xray": "radiologist",
    "mri": "radiologist",
    "ultrasound": "radiologist",
    "bone": "orthopedist",
    "chest": "pulmonologist",
    "lung": "pulmonologist",
    "gallstone": "gastroenterologist",
    "gallbladder": "gastroenterologist",
    "urine": "urologist",
    "psa": "urologist",
    "vitamin": "general physician",
    "iron": "hematologist",
    "calcium": "endocrinologist",
    "sodium": "nephrologist",
    "potassium": "nephrologist",
}

SPECIALIST_SEARCH_TERMS = {
    "hematologist":       ["hematology hospital", "blood diseases hospital", "hematology clinic"],
    "endocrinologist":    ["diabetes hospital", "endocrinology center", "diabetes clinic"],
    "cardiologist":       ["heart hospital", "cardiac center", "cardiology hospital"],
    "nephrologist":       ["kidney hospital", "nephrology center", "renal hospital"],
    "gastroenterologist": ["gastroenterology hospital", "liver hospital", "gastro clinic"],
    "radiologist":        ["diagnostic center", "radiology clinic", "imaging center"],
    "orthopedist":        ["orthopedic hospital", "bone hospital", "orthopedic clinic"],
    "pulmonologist":      ["chest hospital", "pulmonology center", "respiratory hospital"],
    "urologist":          ["urology hospital", "urology clinic"],
    "general physician":  ["general hospital", "medical center", "healthcare clinic"],
}

def get_specialist_type(abnormal_results: list) -> str:
    counts = {}
    for result in abnormal_results:
        test = result.get("test_name", "").lower()
        for keyword, specialist in SPECIALIST_MAP.items():
            if keyword in test:
                counts[specialist] = counts.get(specialist, 0) + 1
    if not counts:
        return "general physician"
    return max(counts, key=counts.get)

def get_combined_specialist(all_abnormal: list) -> dict:
    counts = {}
    critical_specialists = set()
    for result in all_abnormal:
        test = result.get("test_name", "").lower()
        status = result.get("status", "")
        findings = result.get("findings", "").lower()
        search_text = test + " " + findings
        for keyword, specialist in SPECIALIST_MAP.items():
            if keyword in search_text:
                counts[specialist] = counts.get(specialist, 0) + 1
                if status == "Critically Abnormal":
                    critical_specialists.add(specialist)
    if not counts:
        return {"primary": "general physician", "additional": []}
    primary = max(counts, key=counts.get)
    additional = [s for s in critical_specialists if s != primary]
    return {"primary": primary, "additional": additional}

def search_in_city(search_term: str, city: str) -> list:
    """
    Search strictly within a city in Pakistan.
    Forces Pakistan by appending country to query.
    """
    # Build query with city + Pakistan explicitly
    query = f"{search_term} {city} Pakistan"

    params = {
        "q": query,
        "format": "json",
        "limit": 10,
        "addressdetails": 1,
        "countrycodes": "pk",   # strict Pakistan only
    }

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=10
        )
        time.sleep(1)
        if resp.status_code == 200:
            results = resp.json()
            # Extra filter: only keep results that mention the city
            city_lower = city.lower()
            filtered = [
                r for r in results
                if city_lower in r.get("display_name", "").lower()
            ]
            return filtered if filtered else results
    except Exception as e:
        print(f"Search error: {e}")
    return []

def search_near_coords(lat: float, lon: float,
                       search_term: str) -> list:
    """Search near GPS coordinates using viewbox bounding box"""

    # Create ~10km bounding box around coords
    delta = 0.09  # roughly 10km
    viewbox = (f"{lon - delta},{lat + delta},"
               f"{lon + delta},{lat - delta}")

    params = {
        "q": search_term,
        "format": "json",
        "limit": 10,
        "addressdetails": 1,
        "countrycodes": "pk",
        "viewbox": viewbox,
        "bounded": 1,   # strictly inside viewbox
    }

    try:
        resp = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=10
        )
        time.sleep(1)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"Search error: {e}")
    return []

def filter_results(results: list) -> list:
    """Filter out irrelevant places"""
    skip_keywords = [
        "school", "college", "university", "nursing school",
        "homeo", "homoeo", "hakeem", "veterinary", "vet",
        "dental school", "pharmacy school", "beauty",
        "salon", "hotel", "restaurant", "park", "mosque",
        "church", "temple", "masjid", "petrol", "station"
    ]
    filtered = []
    seen_names = set()

    for r in results:
        display = r.get("display_name", "")
        raw_name = display.split(",")[0].strip()
        name_lower = raw_name.lower()

        if name_lower in seen_names:
            continue

        skip = any(kw in display.lower() for kw in skip_keywords)
        if skip:
            continue

        seen_names.add(name_lower)
        filtered.append(r)

    return filtered

def format_result(r: dict) -> dict:
    parts = r.get("display_name", "").split(",")
    name = parts[0].strip()
    address_parts = parts[1:4]
    address = ", ".join([p.strip() for p in address_parts])
    lat = r.get("lat", "")
    lon = r.get("lon", "")
    maps_link = f"https://www.google.com/maps?q={lat},{lon}"
    return {
        "name": name,
        "address": address or "Pakistan",
        "phone": "Contact hospital directly",
        "type": r.get("type", "healthcare").title(),
        "maps_link": maps_link,
        "website": ""
    }

def find_doctors_by_city(city: str, specialist_type: str) -> list:
    """Search for specialists strictly within given city in Pakistan"""
    search_terms = SPECIALIST_SEARCH_TERMS.get(
        specialist_type,
        ["hospital", "medical center", "clinic"]
    )

    all_results = []

    for term in search_terms:
        results = search_in_city(term, city)
        filtered = filter_results(results)
        all_results.extend(filtered)
        if len(all_results) >= 6:
            break

    # Fallback: generic hospital in city
    if len(all_results) < 3:
        results = search_in_city("hospital", city)
        filtered = filter_results(results)
        all_results.extend(filtered)

    # Deduplicate
    seen = set()
    unique = []
    for r in all_results:
        name = r.get("display_name", "").split(",")[0].strip().lower()
        if name not in seen:
            seen.add(name)
            unique.append(r)

    return [format_result(r) for r in unique[:6]]

def find_nearby_doctors(lat: float, lng: float,
                        specialist_type: str) -> list:
    """Search near GPS coordinates bounded to Pakistan"""
    search_terms = SPECIALIST_SEARCH_TERMS.get(
        specialist_type,
        ["hospital", "medical center"]
    )

    all_results = []

    for term in search_terms:
        results = search_near_coords(lat, lng, term)
        filtered = filter_results(results)
        all_results.extend(filtered)
        if len(all_results) >= 6:
            break

    # Fallback
    if len(all_results) < 3:
        results = search_near_coords(lat, lng, "hospital")
        all_results.extend(filter_results(results))

    seen = set()
    unique = []
    for r in all_results:
        name = r.get("display_name", "").split(",")[0].strip().lower()
        if name not in seen:
            seen.add(name)
            unique.append(r)

    return [format_result(r) for r in unique[:6]]