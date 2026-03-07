import streamlit as st
import json
import os
from extractor import process_report
from tools import check_abnormalities, verify_medications
from summarizer import generate_patient_summary, generate_physician_brief

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="Med-Safe",
    page_icon="🏥",
    layout="wide"
)

# ── Header ─────────────────────────────────────────────────
st.title("🏥 Med-Safe")
st.subheader("Medical Report Interpretation & Verification System")
st.markdown("---")

# ── File Upload ────────────────────────────────────────────
st.markdown("### 📂 Upload Medical Reports")
uploaded_files = st.file_uploader(
    "Upload one or more PDF or Image medical reports",
    type=["pdf", "jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded successfully!")

    if st.button("🔍 Analyze All Reports", type="primary"):

        for i, uploaded_file in enumerate(uploaded_files):

            st.markdown("---")
            st.markdown(f"## 📋 Report {i+1}: {uploaded_file.name}")

            # Save file temporarily
            file_ext = uploaded_file.name.split(".")[-1].lower()
            temp_path = f"temp_report_{i}.{file_ext}"

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            with st.spinner(f"Analyzing {uploaded_file.name}..."):

                try:
                    # Step 1: Extract
                    structured_data, raw_text = process_report(temp_path)

                    # Clean JSON
                    clean = structured_data.strip()
                    if clean.startswith("```"):
                        clean = clean.split("```")[1]
                        if clean.startswith("json"):
                            clean = clean[4:]

                    data = json.loads(clean)

                    # Step 2: Analyze
                    analyzed = check_abnormalities(data["lab_results"])
                    medications = verify_medications(data["medications"])

                    # Step 3: Generate summaries
                    patient_summary = generate_patient_summary(
                        analyzed, data["patient_name"]
                    )
                    physician_brief = generate_physician_brief(
                        analyzed, medications,
                        data["patient_name"],
                        data["report_date"]
                    )

                    # ── Patient Info ───────────────────────────────
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("👤 Patient", data["patient_name"])
                    with col2:
                        st.metric("📅 Report Date", data["report_date"])

                    # ── Lab Results ────────────────────────────────
                    st.markdown("### 🔬 Lab Results Analysis")

                    # Summary counts
                    critical = [r for r in analyzed 
                                if r.get("status") == "Critically Abnormal"]
                    mild = [r for r in analyzed 
                            if r.get("status") == "Mildly Abnormal"]
                    normal = [r for r in analyzed 
                              if r.get("status") == "Normal"]

                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("🔴 Critical", len(critical))
                    with c2:
                        st.metric("🟡 Mild", len(mild))
                    with c3:
                        st.metric("🟢 Normal", len(normal))

                    st.markdown(" ")

                    for result in analyzed:
                        status = result.get("status", "")
                        if status == "Critically Abnormal":
                            color = "🔴"
                        elif status == "Mildly Abnormal":
                            color = "🟡"
                        else:
                            color = "🟢"

                        with st.expander(
                            f"{color} {result['test_name']} — {status}"
                        ):
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Value",
                                    f"{result['value']} {result['unit']}")
                            with col2:
                                st.metric("Reference Range",
                                    result['reference_range'])
                            with col3:
                                st.metric("Status", status)
                            st.info(result.get("explanation", ""))

                    # ── Summaries ──────────────────────────────────
                    st.markdown("---")
                    tab1, tab2 = st.tabs(
                        ["👤 Patient Summary", "👨‍⚕️ Physician Brief"]
                    )

                    with tab1:
                        st.markdown("### Patient-Friendly Summary")
                        st.write(patient_summary)

                    with tab2:
                        st.markdown("### Clinical Physician Brief")
                        st.write(physician_brief)

                    # ── Medications ────────────────────────────────
                    if medications and "message" not in medications[0]:
                        st.markdown("---")
                        st.markdown("### 💊 Medication Verification")
                        for med in medications:
                            with st.expander(
                                f"💊 {med.get('medication_name', 'Unknown')}"
                            ):
                                st.write(med)

                except Exception as e:
                    st.error(f"❌ Could not analyze {uploaded_file.name}: {str(e)}")

            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

            # Disclaimer per report
            st.warning(
                "⚠️ DISCLAIMER: Med-Safe is an AI-powered assistant "
                "and does NOT replace professional medical advice. "
                "Always consult a qualified healthcare professional."
            )

        st.markdown("---")
        st.success("✅ All reports analyzed successfully!")