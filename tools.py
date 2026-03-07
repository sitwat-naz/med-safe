import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

# ── Tool 1: Abnormality Detection ──────────────────────────
def check_abnormalities(lab_results: list) -> list:
    """
    Compare lab values against reference ranges.
    Classifies each as Normal, Mildly Abnormal, or Critically Abnormal.
    """
    analyzed = []

    for test in lab_results:
        test_name = test.get("test_name", "")
        value = test.get("value", "")
        reference = test.get("reference_range", "")
        unit = test.get("unit", "")

        prompt = f"""
        You are a clinical lab analyst.
        
        Test: {test_name}
        Patient Value: {value} {unit}
        Reference Range: {reference}
        
        Classify this result as exactly one of:
        - Normal
        - Mildly Abnormal
        - Critically Abnormal
        
        Also give a one-sentence plain English explanation.
        
        Return ONLY a JSON object like this:
        {{
            "test_name": "{test_name}",
            "value": "{value}",
            "unit": "{unit}",
            "reference_range": "{reference}",
            "status": "Normal or Mildly Abnormal or Critically Abnormal",
            "explanation": "one sentence explanation"
        }}
        Return ONLY JSON. No extra text.
        """

        response = llm.invoke(prompt)
        content = response.content.strip()

        # Clean markdown if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        try:
            result = json.loads(content)
        except:
            result = {
                "test_name": test_name,
                "value": value,
                "unit": unit,
                "reference_range": reference,
                "status": "Could not analyze",
                "explanation": content
            }

        analyzed.append(result)

    return analyzed


# ── Tool 2: Drug Verification ──────────────────────────────
def verify_medications(medications: list) -> list:
    """
    Verify medication details using LLM knowledge.
    Flags any hallucinated or suspicious claims.
    """
    if not medications:
        return [{"message": "No medications found in this report."}]

    verified = []

    for med in medications:
        name = med.get("name", "")
        dosage = med.get("dosage", "")
        frequency = med.get("frequency", "")

        prompt = f"""
        You are a clinical pharmacist.
        
        Medication: {name}
        Dosage mentioned: {dosage}
        Frequency mentioned: {frequency}
        
        Verify this medication and return ONLY a JSON object:
        {{
            "medication_name": "{name}",
            "is_valid_medication": true or false,
            "standard_use": "what this medication is typically used for",
            "dosage_assessment": "whether the dosage seems typical or unusual",
            "safety_note": "any important safety information",
            "verified": true or false
        }}
        Return ONLY JSON. No extra text.
        """

        response = llm.invoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        try:
            result = json.loads(content)
        except:
            result = {
                "medication_name": name,
                "verified": False,
                "safety_note": content
            }

        verified.append(result)

    return verified