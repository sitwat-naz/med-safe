import streamlit as st
import json
import os
import plotly.graph_objects as go
from core.extractor import process_report
from core.tools import check_abnormalities, verify_medications
from core.summarizer import generate_patient_summary, generate_physician_brief

# ── Session State Init ────────────────────────────────────
if "analyzed_reports" not in st.session_state:
    st.session_state.analyzed_reports = {}
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False

# ── Helper Functions ──────────────────────────────────────
def display_doctors(doctors, specialist):
    if not doctors:
        st.warning("No results found. Try a different city name.")
        return

    st.success(
        f"Found {len(doctors)} nearby facilities "
        f"for **{specialist.title()}**!"
    )

    for doc in doctors:
        with st.expander(f"🏥 {doc['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**📍 Address:** {doc['address']}")
                st.markdown(f"**📞 Phone:** {doc['phone']}")
                st.markdown(f"**🏷️ Type:** {doc['type']}")
            with col2:
                st.markdown(
                    f"[🗺️ View on Google Maps]({doc['maps_link']})"
                )
                if doc.get("website"):
                    st.markdown(
                        f"[🌐 Website]({doc['website']})"
                    )

def display_chart(analyzed):
    st.markdown("### 📊 Lab Results Visual Analysis")
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

    if chart_data:
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
                size=14,
                color=colors,
                symbol="diamond",
                line=dict(width=2, color="white")
            ),
            text=[str(d["value"]) for d in chart_data],
            textposition="top center",
            textfont=dict(size=10, color="black")
        ))
        fig.update_layout(
            title=dict(
                text="Lab Results vs Normal Range",
                font=dict(size=16, color="#1a7a1a")
            ),
            xaxis=dict(
                title="Test Name",
                tickangle=-35,
                tickfont=dict(size=10)
            ),
            yaxis=dict(title="Value"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=450,
            margin=dict(b=120)
        )
        fig.update_xaxes(gridcolor="#f0f0f0")
        fig.update_yaxes(gridcolor="#f0f0f0")
        st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("🟢 **Normal** — within range")
        with col2:
            st.markdown("🟠 **Mildly Abnormal** — monitor")
        with col3:
            st.markdown("🔴 **Critical** — see doctor")
    else:
        st.info("No numeric range data available for chart.")

def display_report(i, report_data):
    analyzed = report_data["analyzed"]
    medications = report_data["medications"]
    patient_summary = report_data["patient_summary"]
    physician_brief = report_data["physician_brief"]
    data = report_data["data"]

    # ── Patient Info ───────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👤 Patient", data["patient_name"])
    with col2:
        st.metric("📅 Report Date", data["report_date"])

    # ── Summary Counts ─────────────────────────────────────
    st.markdown("### 🔬 Lab Results Analysis")
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

    # ── Visual Chart ───────────────────────────────────────
    display_chart(analyzed)

    # ── Detailed Results ───────────────────────────────────
    st.markdown("### 🔬 Detailed Results")
    for result in analyzed:
        status = result.get("status", "")
        if status == "Critically Abnormal":
            color = "🔴"
        elif status == "Mildly Abnormal":
            color = "🟡"
        else:
            color = "🟢"
        with st.expander(f"{color} {result['test_name']} — {status}"):
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

    # ── Summaries ──────────────────────────────────────────
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

    # ── Medications ────────────────────────────────────────
    if medications and "message" not in medications[0]:
        st.markdown("---")
        st.markdown("### 💊 Medication Verification")
        for med in medications:
            with st.expander(
                f"💊 {med.get('medication_name', 'Unknown')}"
            ):
                st.write(med)

    # ── Nearby Doctors ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🏥 Find Nearby Specialist Doctors")

    abnormal_results = [r for r in analyzed
                        if r.get("status") in
                        ["Mildly Abnormal", "Critically Abnormal"]]

    if abnormal_results:
        from core.doctor_finder import (get_specialist_type,
                                        find_nearby_doctors,
                                        find_doctors_by_city)

        specialist = get_specialist_type(abnormal_results)
        st.info(
            f"🩺 Based on your results, recommended specialist: "
            f"**{specialist.title()}**"
        )

        location_method = st.radio(
            "Choose location method:",
            ["📍 Use My GPS Location", "🏙️ Enter City Manually"],
            horizontal=True,
            key=f"loc_{i}"
        )

        if location_method == "📍 Use My GPS Location":
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input(
                    "Latitude", value=24.8607,
                    key=f"lat_{i}",
                    help="Your GPS latitude"
                )
            with col2:
                lng = st.number_input(
                    "Longitude", value=67.0011,
                    key=f"lng_{i}",
                    help="Your GPS longitude"
                )
            st.caption(
                "💡 Default is Karachi. "
                "Update coordinates for your city."
            )
            if st.button("🔍 Find Nearby Doctors", key=f"find_{i}"):
                with st.spinner(
                    "Searching for specialists near you..."
                ):
                    doctors = find_nearby_doctors(
                        lat, lng, specialist
                    )
                    st.session_state[f"doctors_{i}"] = doctors

        else:
            city = st.text_input(
                "Enter your city:",
                placeholder="e.g. Karachi, Lahore, Islamabad",
                key=f"city_{i}"
            )
            if st.button("🔍 Search Doctors", key=f"search_{i}"):
                if city:
                    with st.spinner(
                        f"Searching for {specialist} "
                        f"in {city}..."
                    ):
                        doctors = find_doctors_by_city(
                            city, specialist
                        )
                        st.session_state[f"doctors_{i}"] = doctors

        # Display doctors from session state
        if f"doctors_{i}" in st.session_state:
            display_doctors(
                st.session_state[f"doctors_{i}"],
                specialist
            )

    # ── Disclaimer ─────────────────────────────────────────
    st.warning(
        "⚠️ DISCLAIMER: Med-Safe is an AI-powered assistant "
        "and does NOT replace professional medical advice. "
        "Always consult a qualified healthcare professional."
    )

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
    st.success(
        f"✅ {len(uploaded_files)} file(s) uploaded successfully!"
    )

    if st.button("🔍 Analyze All Reports", type="primary"):
        st.session_state.analyzed_reports = {}
        st.session_state.analysis_done = False

        for i, uploaded_file in enumerate(uploaded_files):
            file_ext = uploaded_file.name.split(".")[-1].lower()
            temp_path = f"temp_report_{i}.{file_ext}"

            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())

            with st.spinner(
                f"Analyzing {uploaded_file.name}..."
            ):
                try:
                    structured_data, raw_text = process_report(
                        temp_path
                    )

                    clean = structured_data.strip()
                    if clean.startswith("```"):
                        clean = clean.split("```")[1]
                        if clean.startswith("json"):
                            clean = clean[4:]

                    data = json.loads(clean)
                    analyzed = check_abnormalities(
                        data["lab_results"]
                    )
                    medications = verify_medications(
                        data["medications"]
                    )
                    patient_summary = generate_patient_summary(
                        analyzed, data["patient_name"]
                    )
                    physician_brief = generate_physician_brief(
                        analyzed, medications,
                        data["patient_name"],
                        data["report_date"]
                    )

                    st.session_state.analyzed_reports[i] = {
                        "name": uploaded_file.name,
                        "analyzed": analyzed,
                        "medications": medications,
                        "patient_summary": patient_summary,
                        "physician_brief": physician_brief,
                        "data": data
                    }

                except Exception as e:
                    st.error(
                        f"❌ Could not analyze "
                        f"{uploaded_file.name}: {str(e)}"
                    )

            if os.path.exists(temp_path):
                os.remove(temp_path)

        st.session_state.analysis_done = True

# ── Display Results from Session State ───────────────────
if (st.session_state.analysis_done and
        st.session_state.analyzed_reports):
    for i, report_data in (
        st.session_state.analyzed_reports.items()
    ):
        st.markdown("---")
        st.markdown(
            f"## 📋 Report {i+1}: {report_data['name']}"
        )
        display_report(i, report_data)

    st.markdown("---")
    st.success("✅ All reports analyzed successfully!")