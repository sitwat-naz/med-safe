import requests
from dotenv import load_dotenv
load_dotenv()

SPECIALIST_MAP = {
    "hemoglobin": "hematologist",
    "hb": "hematologist",
    "rbc": "hematologist",
    "wbc": "hematologist",
    "platelet": "hematologist",
    "pcv": "hematologist",
    "packed cell": "hematologist",
    "glucose": "endocrinologist",
    "sugar": "endocrinologist",
    "hba1c": "endocrinologist",
    "insulin": "endocrinologist",
    "thyroid": "endocrinologist",
    "tsh": "endocrinologist",
    "t3": "endocrinologist",
    "t4": "endocrinologist",
    "liver": "gastroenterologist",
    "sgpt": "gastroenterologist",
    "sgot": "gastroenterologist",
    "bilirubin": "gastroenterologist",
    "alt": "gastroenterologist",
    "ast": "gastroenterologist",
    "kidney": "nephrologist",
    "creatinine": "nephrologist",
    "urea": "nephrologist",
    "blood pressure": "cardiologist",
    "bp": "cardiologist",
    "cholesterol": "cardiologist",
    "triglyceride": "cardiologist",
    "ldl": "cardiologist",
    "hdl": "cardiologist",
    "iron": "hematologist",
    "ferritin": "hematologist",
}

# Words to filter out from results
EXCLUDE_KEYWORDS = [
    "dental", "dentist", "eye", "optical", "homeo",
    "homeopathic", "veterinary", "vet", "pharmacy",
    "laboratory", "lab only", "beauty", "skin only"
]

def get_specialist_type(abnormal_results: list) -> str:
    for result in abnormal_results:
        test_name = result.get("test_name", "").lower()
        for keyword, specialist in SPECIALIST_MAP.items():
            if keyword in test_name:
                return specialist
    return "general physician"

def is_valid_result(name: str) -> bool:
    """Filter out irrelevant places"""
    name_lower = name.lower()

    # Skip generic unnamed results
    generic = ["hospital", "clinic", "doctor",
               "medical", "centre", "center"]
    if name_lower.strip() in generic:
        return False

    # Skip excluded types
    for word in EXCLUDE_KEYWORDS:
        if word in name_lower:
            return False

    return True

def find_nearby_doctors(lat: float, lng: float,
                         specialist_type: str) -> list:
    return find_doctors_by_city(
        f"{lat},{lng}", specialist_type, use_coords=True
    )

def find_doctors_by_city(city: str, specialist_type: str,
                          use_coords=False) -> list:
    headers = {"User-Agent": "MedSafe-StudentProject/1.0"}

    search_queries = [
        f"{specialist_type} hospital {city}",
        f"specialist hospital {city}",
        f"medical hospital {city}",
        f"general hospital {city}",
        f"clinic {city} Pakistan",
    ]

    results = []
    seen = set()

    for query in search_queries:
        if len(results) >= 6:
            break

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 8,
            "addressdetails": 1,
            "extratags": 1,
        }

        try:
            response = requests.get(
                url, params=params,
                headers=headers,
                timeout=10
            )
            data = response.json()

            for place in data:
                # Get clean name
                full_display = place.get("display_name", "")
                name = full_display.split(",")[0].strip()

                # Skip if invalid or already seen
                if not name or name in seen:
                    continue
                if not is_valid_result(name):
                    continue

                seen.add(name)

                lat_p = place.get("lat", "")
                lng_p = place.get("lon", "")
                maps_link = (
                    f"https://www.google.com/maps/search/"
                    f"?api=1&query={lat_p},{lng_p}"
                )

                # Clean address (skip first part = name)
                address_parts = full_display.split(",")
                address = ", ".join(
                    address_parts[1:4]
                ).strip()

                phone = place.get("extratags", {}).get(
                    "phone",
                    place.get("extratags", {}).get(
                        "contact:phone", "Not listed"
                    )
                )

                website = place.get("extratags", {}).get(
                    "website",
                    place.get("extratags", {}).get(
                        "contact:website", None
                    )
                )

                results.append({
                    "name": name,
                    "address": address,
                    "phone": phone,
                    "website": website,
                    "type": place.get(
                        "type", "medical"
                    ).replace("_", " ").title(),
                    "maps_link": maps_link,
                    "open_now": None,
                    "rating": "N/A",
                    "total_ratings": 0
                })

        except Exception as e:
            continue

    return results[:6]