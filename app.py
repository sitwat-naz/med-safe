import streamlit as st
import json
import os
import plotly.graph_objects as go
from core.extractor import process_report
from core.tools import check_abnormalities, verify_medications
from core.summarizer import generate_combined_summary, generate_combined_physician_brief

# ── Session State ─────────────────────────────────────────
if "analyzed_reports" not in st.session_state:
    st.session_state.analyzed_reports = {}
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

# ── Helper Functions ──────────────────────────────────────
def display_doctors(doctors, specialist):
    if not doctors:
        st.warning("No results found. Try a different city name.")
        return
    st.success(f"Found {len(doctors)} nearby facilities for **{specialist.title()}**!")
    for doc in doctors:
        with st.expander(f"🏥 {doc['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**📍 Address:** {doc['address']}")
                st.markdown(f"**📞 Phone:** {doc['phone']}")
                st.markdown(f"**🏷️ Type:** {doc['type']}")
            with col2:
                st.markdown(f"[🗺️ View on Google Maps]({doc['maps_link']})")
                if doc.get("website"):
                    st.markdown(f"[🌐 Website]({doc['website']})")

def display_chart(analyzed):
    chart_data = []
    for result in analyzed:
        try:
            value = float(result.get("value", 0))
            ref = result.get("reference_range", "")
            status = result.get("status", "Normal")
            test_name = result.get("test_name", "")
            if "-" in ref:
                parts = ref.replace(" ", "").split("-")
                low = float(parts[0])
                high = float(parts[1])
            else:
                continue
            chart_data.append({
                "test": test_name[:20],
                "value": value,
                "low": low,
                "high": high,
                "status": status
            })
        except:
            continue

    if not chart_data:
        return

    colors = []
    for d in chart_data:
        if d["status"] == "Critically Abnormal":
            colors.append("#e74c3c")
        elif d["status"] == "Mildly Abnormal":
            colors.append("#f39c12")
        else:
            colors.append("#27ae60")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Normal Range",
        x=[d["test"] for d in chart_data],
        y=[d["high"] - d["low"] for d in chart_data],
        base=[d["low"] for d in chart_data],
        marker_color="rgba(200, 230, 200, 0.5)",
        marker_line_color="rgba(100, 180, 100, 0.8)",
        marker_line_width=1,
    ))
    fig.add_trace(go.Scatter(
        name="Patient Value",
        x=[d["test"] for d in chart_data],
        y=[d["value"] for d in chart_data],
        mode="markers+text",
        marker=dict(
            size=14, color=colors, symbol="diamond",
            line=dict(width=2, color="white")
        ),
        text=[str(d["value"]) for d in chart_data],
        textposition="top center",
        textfont=dict(size=10, color="black")
    ))
    fig.update_layout(
        title=dict(text="Lab Results vs Normal Range",
                   font=dict(size=16, color="#1a7a1a")),
        xaxis=dict(title="Test Name", tickangle=-35,
                   tickfont=dict(size=10)),
        yaxis=dict(title="Value"),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
        height=420, margin=dict(b=120)
    )
    fig.update_xaxes(gridcolor="#f0f0f0")
    fig.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig, use_container_width=True)

def display_report_compact(i, report_data):
    """Compact display for each individual report"""
    analyzed = report_data["analyzed"]
    data = report_data["data"]
    medications = report_data["medications"]
    report_type = data.get("report_type", "lab")
    report_title = data.get("report_title", "Medical Report")

    # Patient info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👤 Patient", data["patient_name"])
    with col2:
        st.metric("📅 Date", data["report_date"])
    with col3:
        st.metric("📄 Report Type", report_title)

    # ── Descriptive Report ────────────────────────────────
    if report_type == "descriptive":
        st.markdown("#### 🖼️ Findings")
        findings = data.get("findings", "")
        impression = data.get("impression", "")
        if findings:
            st.info(f"📋 **Findings:** {findings}")
        if impression:
            st.success(f"🩺 **Impression / Diagnosis:** {impression}")

    # ── Prescription ──────────────────────────────────────
    elif report_type == "prescription":
        diagnosis = data.get("diagnosis", "")
        findings = data.get("findings", "")
        if diagnosis:
            st.info(f"🩺 **Diagnosis:** {diagnosis}")
        if findings:
            st.write(f"📋 {findings}")

        if medications and "message" not in medications[0]:
            st.markdown("#### 💊 Prescribed Medications")
            for med in medications:
                name = med.get("medication_name", "Unknown")
                verified = "✅" if med.get("verified") else "⚠️"
                use = med.get("standard_use", "")
                st.write(f"{verified} **{name}** — {use}")

    # ── Lab Report ────────────────────────────────────────
    else:
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

        st.markdown("#### 🔬 Test Results")
        col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
        with col1:
            st.markdown("**Test**")
        with col2:
            st.markdown("**Value**")
        with col3:
            st.markdown("**Normal Range**")
        with col4:
            st.markdown("**Status**")
        st.markdown("---")

        # Table header
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 3, 4])
        with col1:
            st.markdown("**Test**")
        with col2:
            st.markdown("**Value**")
        with col3:
            st.markdown("**Normal Range**")
        with col4:
            st.markdown("**Status**")
        with col5:
            st.markdown("**Note**")
        st.markdown("---")

        for result in analyzed:
            status = result.get("status", "")
            explanation = result.get("explanation", "")
            # Trim explanation to half line
            short_note = (explanation[:60] + "…") \
                if len(explanation) > 60 else explanation

            icon = "🔴" if status == "Critically Abnormal" else \
                   "🟡" if status == "Mildly Abnormal" else "🟢"

            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 3, 4])
            with col1:
                st.write(f"**{result['test_name']}**")
            with col2:
                st.write(f"{result['value']} {result['unit']}")
            with col3:
                st.write(f"{result['reference_range']}")
            with col4:
                st.write(f"{icon} {status}")
            with col5:
                st.caption(short_note)

        if medications and "message" not in medications[0]:
            st.markdown("#### 💊 Medications Found")
            for med in medications:
                name = med.get("medication_name", "Unknown")
                verified = "✅" if med.get("verified") else "⚠️"
                use = med.get("standard_use", "")
                st.write(f"{verified} **{name}** — {use}")
# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="Med-Safe",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Med-Safe")
st.subheader("Medical Report Interpretation & Verification System")
st.markdown("---")

st.markdown("### 📂 Upload Medical Reports")
uploaded_files = st.file_uploader(
    "Upload one or more PDF or Image medical reports",
    type=["pdf", "jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded!")

    if st.button("🔍 Analyze All Reports", type="primary"):
        st.session_state.analyzed_reports = {}
        st.session_state.analysis_done = False

        for i, uploaded_file in enumerate(uploaded_files):
            file_ext = uploaded_file.name.split(".")[-1].lower()
            temp_path = f"temp_report_{i}.{file_ext}"

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            with st.spinner(f"Analyzing {uploaded_file.name}..."):
                try:
                    structured_data, raw_text = process_report(temp_path)
                    clean = structured_data.strip()
                    if clean.startswith("```"):
                        clean = clean.split("```")[1]
                        if clean.startswith("json"):
                            clean = clean[4:]

                    data = json.loads(clean)
                    report_type = data.get("report_type", "lab")
                    
                    if report_type == "lab":
                        analyzed = check_abnormalities(
                            data.get("lab_results", []))
                        medications = verify_medications(
                            data.get("medications", []))
                    else:
                        analyzed = []
                        medications = verify_medications(
                            data.get("medications", []))

                    st.session_state.analyzed_reports[i] = {
                        "name": uploaded_file.name,
                        "analyzed": analyzed,
                        "medications": medications,
                        "data": data
                    }

                except Exception as e:
                    st.error(f"❌ Could not analyze {uploaded_file.name}: {str(e)}")

            if os.path.exists(temp_path):
                os.remove(temp_path)

        st.session_state.analysis_done = True

# ── Display Results ───────────────────────────────────────
if st.session_state.analysis_done and st.session_state.analyzed_reports:

    all_reports = list(st.session_state.analyzed_reports.values())

    # ── Individual Reports (compact) ──────────────────────
    for i, report_data in st.session_state.analyzed_reports.items():
        st.markdown("---")
        report_title = report_data["data"].get("report_title", report_data['name'])
        st.markdown(f"### 📋 Report {i+1}: {report_title}")
        display_report_compact(i, report_data)

    # ── Combined Analysis ─────────────────────────────────
    st.markdown("---")
    st.markdown("## 🔗 Combined Analysis")

    # Collect all data
    all_analyzed = []
    all_medications = []
    patient_name = all_reports[0]["data"]["patient_name"]

    for r in all_reports:
        all_analyzed.extend(r["analyzed"])
        all_medications.extend(r["medications"])

    # Combined counts
    total_critical = [r for r in all_analyzed
                      if r.get("status") == "Critically Abnormal"]
    total_mild = [r for r in all_analyzed
                  if r.get("status") == "Mildly Abnormal"]
    total_normal = [r for r in all_analyzed
                    if r.get("status") == "Normal"]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📋 Total Tests", len(all_analyzed))
    with c2:
        st.metric("🔴 Critical", len(total_critical))
    with c3:
        st.metric("🟡 Mild", len(total_mild))
    with c4:
        st.metric("🟢 Normal", len(total_normal))

    # Combined chart
    st.markdown("### 📊 Combined Visual Analysis")
    display_chart(all_analyzed)

    # Combined summaries
    with st.spinner("Generating combined analysis..."):
        all_reports_data = [r["data"] for r in all_reports]
        combined_patient = generate_combined_summary(
            all_analyzed, patient_name, all_reports_data)
        combined_physician = generate_combined_physician_brief(
            all_analyzed, all_medications, patient_name,
            all_reports_data)

    tab1, tab2 = st.tabs([
        "👤 Combined Patient Summary",
        "👨‍⚕️ Combined Physician Brief"
    ])
    with tab1:
        st.markdown("### Patient-Friendly Summary")
        st.write(combined_patient)
    with tab2:
        st.markdown("### Clinical Physician Brief")
        st.write(combined_physician)

    # ── Smart Specialist Finder ────────────────────────────
    st.markdown("---")
    st.markdown("### 🏥 Find Nearby Specialist Doctors")

    from core.doctor_finder import (get_combined_specialist,
                                    find_doctors_by_city,
                                    find_nearby_doctors,
                                    get_specialist_type)

    # Collect abnormal lab results
    all_abnormal = [r for r in all_analyzed
                    if r.get("status") in
                    ["Mildly Abnormal", "Critically Abnormal"]]

    # Also collect descriptive report findings
    all_reports_data = [r["data"] for r in all_reports]
    descriptive_items = []
    for d in all_reports_data:
        if d.get("report_type") == "descriptive":
            findings = d.get("findings", "")
            impression = d.get("impression", "")
            title = d.get("report_title", "")
            combined_text = f"{title} {findings} {impression}".lower()
            descriptive_items.append({
                "test_name": combined_text,
                "status": "Mildly Abnormal",
                "findings": combined_text
            })

    # Combine both for specialist detection
    all_items_for_specialist = all_abnormal + descriptive_items

    if all_items_for_specialist:
        specialists = get_combined_specialist(all_items_for_specialist)
        primary = specialists["primary"]
        additional = specialists["additional"]

        st.info(f"🩺 **Primary Specialist Recommended:** {primary.title()}")
        for spec in additional:
            st.warning(
                f"⚠️ **Also consult:** {spec.title()} "
                f"(Critical findings detected)"
            )

        # Location method
        location_method = st.radio(
            "Find specialists near you:",
            ["🏙️ Enter City", "📍 Use GPS Coordinates"],
            horizontal=True,
            key="combined_loc"
        )

        if location_method == "🏙️ Enter City":
            city = st.text_input(
                "Enter your city:",
                placeholder="e.g. Karachi, Lahore, Islamabad",
                key="combined_city"
            )
            if st.button("🔍 Search Specialists", key="combined_search",
                          type="primary"):
                if city:
                    with st.spinner(f"Searching in {city}..."):
                        doctors = find_doctors_by_city(city, primary)
                        st.session_state["combined_doctors"] = doctors
                else:
                    st.warning("Please enter a city name first.")

        else:
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input("Latitude", value=24.8607,
                                       key="combined_lat")
            with col2:
                lng = st.number_input("Longitude", value=67.0011,
                                       key="combined_lng")
            st.caption("💡 Default coordinates are set to Karachi.")
            if st.button("🔍 Find Specialists", key="combined_find",
                          type="primary"):
                with st.spinner("Searching nearby..."):
                    doctors = find_nearby_doctors(lat, lng, primary)
                    st.session_state["combined_doctors"] = doctors

        if "combined_doctors" in st.session_state:
            display_doctors(
                st.session_state["combined_doctors"], primary)

    else:
        st.success("✅ No significant abnormalities detected. "
                   "Regular checkup with a general physician recommended.")

    st.warning(
        "⚠️ DISCLAIMER: Med-Safe is an AI-powered assistant "
        "and does NOT replace professional medical advice. "
        "Always consult a qualified healthcare professional."
    )