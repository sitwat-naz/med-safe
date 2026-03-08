import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def check_abnormalities(lab_results: list) -> list:
    """
    Batch check ALL lab results in ONE single LLM call.
    Much faster and uses far fewer API requests.
    """

    if not lab_results:
        return []

    prompt = f"""
    You are a clinical lab analyst.
    
    Analyze ALL of the following lab results at once.
    For each test, classify it and provide an explanation.
    
    Lab Results:
    {json.dumps(lab_results, indent=2)}
    
    Return ONLY a JSON array with this exact structure:
    [
        {{
            "test_name": "test name here",
            "value": "value here",
            "unit": "unit here",
            "reference_range": "range here",
            "status": "Normal or Mildly Abnormal or Critically Abnormal",
            "explanation": "one sentence plain English explanation"
        }}
    ]
    
    Rules:
    - Status must be exactly one of: Normal, Mildly Abnormal, Critically Abnormal
    - Include ALL tests from the input
    - Return ONLY the JSON array, no extra text
    """

    response = llm.invoke(prompt)
    content = response.content.strip()

    # Clean markdown if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    try:
        results = json.loads(content)
        return results
    except:
        # Fallback — return original with unknown status
        fallback = []
        for test in lab_results:
            fallback.append({
                "test_name": test.get("test_name", ""),
                "value": test.get("value", ""),
                "unit": test.get("unit", ""),
                "reference_range": test.get("reference_range", ""),
                "status": "Could not analyze",
                "explanation": "Analysis failed for this test."
            })
        return fallback


def verify_medications(medications: list) -> list:
    """
    Batch verify ALL medications in ONE single LLM call.
    """

    if not medications:
        return [{"message": "No medications found in this report."}]

    prompt = f"""
    You are a clinical pharmacist.
    
    Verify ALL of the following medications at once.
    
    Medications:
    {json.dumps(medications, indent=2)}
    
    Return ONLY a JSON array with this exact structure:
    [
        {{
            "medication_name": "name here",
            "is_valid_medication": true or false,
            "standard_use": "what this medication is typically used for",
            "dosage_assessment": "whether the dosage seems typical or unusual",
            "safety_note": "any important safety information",
            "verified": true or false
        }}
    ]
    
    Return ONLY the JSON array, no extra text.
    """

    response = llm.invoke(prompt)
    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    try:
        results = json.loads(content)
        return results
    except:
        fallback = []
        for med in medications:
            fallback.append({
                "medication_name": med.get("name", "Unknown"),
                "verified": False,
                "safety_note": "Could not verify this medication."
            })
        return fallback