import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_patient_summary(analyzed_results: list, patient_name: str) -> str:
    """Generate plain English summary for patient"""

    abnormal = [r for r in analyzed_results 
                if r.get("status") in ["Mildly Abnormal", "Critically Abnormal"]]
    normal = [r for r in analyzed_results 
              if r.get("status") == "Normal"]

    prompt = f"""
    You are a friendly medical assistant explaining lab results to a patient.
    
    Patient Name: {patient_name}
    
    Abnormal Results:
    {abnormal}
    
    Normal Results:
    {normal}
    
    Write a warm, clear summary for the patient:
    - Use simple language (no medical jargon)
    - Mention what is normal first (reassuring)
    - Clearly explain what is abnormal and why it matters
    - Give 2-3 general lifestyle suggestions
    - End with: "Please consult your doctor for proper medical advice."
    
    Keep it under 200 words.
    """

    response = llm.invoke(prompt)
    return response.content


def generate_physician_brief(analyzed_results: list, 
                              medication_results: list, 
                              patient_name: str,
                              report_date: str) -> str:
    """Generate technical summary for physician"""

    prompt = f"""
    You are preparing a clinical brief for a physician.
    
    Patient: {patient_name}
    Report Date: {report_date}
    
    Lab Analysis:
    {analyzed_results}
    
    Medication Verification:
    {medication_results}
    
    Generate a structured physician brief with these sections:
    1. PATIENT OVERVIEW
    2. ABNORMAL FINDINGS (with values and clinical significance)
    3. NORMAL FINDINGS (brief list)
    4. MEDICATION STATUS
    5. CLINICAL RECOMMENDATIONS
    
    Use clinical language. Be concise and precise.
    End with: "DISCLAIMER: This is an AI-generated summary. 
    Clinical judgment of a qualified physician is required."
    """

    response = llm.invoke(prompt)
    return response.content