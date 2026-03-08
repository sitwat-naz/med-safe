import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)

def generate_patient_summary(analyzed_results: list,
                              patient_name: str) -> str:
    """Generate plain English summary for patient"""

    abnormal = [r for r in analyzed_results
                if r.get("status") in
                ["Mildly Abnormal", "Critically Abnormal"]]
    normal = [r for r in analyzed_results
              if r.get("status") == "Normal"]

    prompt = f"""
    You are a friendly medical assistant explaining 
    lab results to a patient.
    
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
    - End with: "Please consult your doctor for 
      proper medical advice."
    
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


def generate_combined_summary(all_analyzed: list,
                               patient_name: str,
                               all_reports_data: list = None) -> str:
    """Generate combined patient summary including descriptive reports"""

    abnormal = [r for r in all_analyzed
                if r.get("status") in
                ["Mildly Abnormal", "Critically Abnormal"]]
    normal = [r for r in all_analyzed
              if r.get("status") == "Normal"]

    # Collect descriptive findings
    descriptive_findings = []
    if all_reports_data:
        for d in all_reports_data:
            if d.get("report_type") == "descriptive":
                title = d.get("report_title", "Imaging Report")
                findings = d.get("findings", "")
                impression = d.get("impression", "")
                if findings or impression:
                    descriptive_findings.append(
                        f"{title}: {findings} {impression}".strip()
                    )

    prompt = f"""
    You are a friendly medical assistant explaining 
    combined results to a patient.
    
    Patient Name: {patient_name}
    
    Lab Test Abnormalities:
    {abnormal if abnormal else "None detected"}
    
    Normal Lab Results:
    {normal if normal else "None"}
    
    Imaging & Descriptive Report Findings:
    {descriptive_findings if descriptive_findings else "None"}
    
    Write a warm, clear COMBINED summary:
    - Cover BOTH lab results AND imaging/descriptive findings
    - Use simple language (no medical jargon)
    - Start with reassuring normal findings
    - Explain abnormalities and imaging findings clearly
    - Give 3-4 lifestyle suggestions
    - End with: "Please consult your doctor for proper medical advice."
    
    Keep under 300 words.
    """
    response = llm.invoke(prompt)
    return response.content


def generate_combined_physician_brief(all_analyzed: list,
                                       all_medications: list,
                                       patient_name: str,
                                       all_reports_data: list = None) -> str:
    """Generate combined physician brief including descriptive reports"""

    descriptive_findings = []
    if all_reports_data:
        for d in all_reports_data:
            if d.get("report_type") == "descriptive":
                title = d.get("report_title", "Imaging Report")
                findings = d.get("findings", "")
                impression = d.get("impression", "")
                if findings or impression:
                    descriptive_findings.append({
                        "report": title,
                        "findings": findings,
                        "impression": impression
                    })

    prompt = f"""
    You are preparing a combined clinical brief for a physician.
    
    Patient: {patient_name}
    
    Lab Results Analysis:
    {all_analyzed}
    
    Imaging & Descriptive Reports:
    {descriptive_findings if descriptive_findings else "None"}
    
    All Medications:
    {all_medications}
    
    Generate a structured combined physician brief:
    1. PATIENT OVERVIEW
    2. CRITICAL LAB FINDINGS (if any)
    3. MILDLY ABNORMAL LAB FINDINGS
    4. IMAGING & DESCRIPTIVE FINDINGS
    5. NORMAL FINDINGS (brief)
    6. MEDICATIONS
    7. OVERALL CLINICAL RECOMMENDATIONS
    
    Use clinical language. Group related findings.
    End with disclaimer about AI-generated content.
    """
    response = llm.invoke(prompt)
    return response.content