import requests
import os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GOOGLE_PLACES_KEY")

# Test with Karachi coordinates
url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
params = {
    "location": "24.8607,67.0011",
    "radius": 5000,
    "keyword": "doctor",
    "key": key
}

response = requests.get(url, params=params)
data = response.json()

print("STATUS:", data.get("status"))
print("ERROR:", data.get("error_message", "None"))
print("RESULTS COUNT:", len(data.get("results", [])))
if data.get("results"):
    print("FIRST RESULT:", data["results"][0]["name"])