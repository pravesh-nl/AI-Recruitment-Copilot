import streamlit as st
import requests
import pandas as pd
import json
import time 
from ui.sidebar import show_sidebar

# ===========================
# PAGE CONFIG
# ===========================
st.set_page_config(
    page_title="AI Recruitment Copilot",
    page_icon="🤖",
    layout="wide"
)
if "upload_progress" not in st.session_state:
    st.session_state.upload_progress = 0

if "upload_status" not in st.session_state:
    st.session_state.upload_status = ""
# ===========================
# LOAD STATS
# ===========================
try:
    stats = requests.get(
        "http://127.0.0.1:8000/stats"
    ).json()
except:
    stats = {
        "resume_processed": 0,
        "parsing_accuracy": 0,
        "profiles_created": 0
    }

# ===========================
# LOAD CANDIDATES
# ===========================
try:
    candidates = requests.get(
        "http://127.0.0.1:8000/candidates"
    ).json()

    latest_candidate = candidates[-1] if candidates else None

except:
    candidates = []
    latest_candidate = None

# ===========================
# SIDEBAR
# ===========================
selected = show_sidebar()
# ===========================
# CUSTOM CARD CSS
# ===========================

st.markdown("""
<style>

.metric-card{
    background:white;
    border-radius:16px;
    padding:20px;
    text-align:center;
    border-bottom:5px solid #1f77ff;
    box-shadow:0 4px 12px rgba(0,0,0,.08);
}
button[kind="secondary"]{
    border-radius:8px;
}

hr{
    margin-top:2px !important;
    margin-bottom:2px !important;
}
.metric-card:hover{
    transform:translateY(-4px);
    box-shadow:0px 8px 20px rgba(0,0,0,0.12);
}

.metric-icon{
    font-size:30px;
}

.metric-title{
    font-size:15px;
    color:#666666;
    margin-top:8px;
}

.streamlit-expanderHeader{
    font-size:15px !important;
    font-weight:600 !important;
}

.metric-value{
    font-size:34px;
    font-weight:bold;
    color:#1f77ff;
    margin-top:8px;
}

</style>
""", unsafe_allow_html=True)
# ===========================
# HEADER
# ===========================
st.title("Resume Parsing & Candidate Profiling")

st.caption(
    "Upload and process resumes to create structured candidate profiles."
)

st.markdown("<br>", unsafe_allow_html=True)

# ===========================
# MAIN LAYOUT
# ===========================
left, right = st.columns([1, 1])

# =====================================================
# LEFT CARD
# =====================================================
with left:

    with st.container(border=True):

        st.subheader("📄 Upload Resume")

        uploaded_file = st.file_uploader(
            "Drag and drop resumes or click to browse",
            type=["pdf", "docx"]
        )

        st.caption("Supported formats: PDF, DOCX")

        if st.button(
            "⬆ Upload Resume",
            use_container_width=True
        ):

            if uploaded_file is None:

                st.warning("Please select a resume.")

            else:

                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type
                    )
                }

            # Update progress bar (RIGHT CARD)
                st.session_state.upload_progress = 10
                st.session_state.upload_status = "Uploading Resume..."

                time.sleep(0.3)

                st.session_state.upload_progress = 40
                st.session_state.upload_status = "Reading Resume..."

                time.sleep(0.3)

                st.session_state.upload_progress = 70
                st.session_state.upload_status = "Extracting Candidate Details..."

                response = requests.post(
                    "http://127.0.0.1:8000/upload",
                    files=files
                )

                st.session_state.upload_progress = 100
                st.session_state.upload_status = "Resume Parsed Successfully"

                time.sleep(0.5)

                # Reset progress after completion
                st.session_state.upload_progress = 0
                st.session_state.upload_status = ""

                if response.status_code == 200:

                    st.success("Resume uploaded successfully.")

                    st.rerun()

                else:

                    st.error(response.text)

                if response.status_code == 200:

                    st.success("Resume uploaded successfully.")

                    st.rerun()

                else:

                    st.error(response.text)

# =====================================================
# RIGHT CARD
# =====================================================
with right:

    with st.container(border=True):

        st.subheader("📊 Parsing Progress")

        display_progress = max(
            stats["parsing_accuracy"],
            st.session_state.upload_progress
        )

        st.progress(display_progress / 100)

        if st.session_state.upload_status:
            st.caption(st.session_state.upload_status)

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">📄</div>
                <div class="metric-title">Resume Processed</div>
                <div class="metric-value">{stats['resume_processed']}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">🎯</div>
                <div class="metric-title">Parsing Accuracy</div>
                <div class="metric-value">{stats['parsing_accuracy']}%</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon">👤</div>
                <div class="metric-title">Profiles Created</div>
                <div class="metric-value">{stats['profiles_created']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(
    "<hr style='margin:4px 0;'>",
    unsafe_allow_html=True
)

        st.subheader("Extracted Information")

        if latest_candidate:

            try:
                skills = ", ".join(
                    json.loads(latest_candidate["skills"])
                )
            except:
                skills = latest_candidate["skills"]

            try:
                education = ", ".join(
                    json.loads(latest_candidate["education"])
                )
            except:
                education = latest_candidate["education"]

            try:
                certifications = ", ".join(
                    json.loads(latest_candidate["certifications"])
                )
            except:
                certifications = latest_candidate["certifications"]

            try:
                projects = ", ".join(
                    json.loads(latest_candidate["projects"])
                )
            except:
                projects = latest_candidate["projects"]

            st.write(
                "**Name:**",
                latest_candidate["name"]
            )

            st.write(
                "**Email:**",
                latest_candidate["email"]
            )

            st.write(
                "**Phone:**",
                latest_candidate["phone"]
            )

            st.write(
                "**Education:**",
                education
            )

            st.write(
                "**Experience:**",
                latest_candidate["experience"]
            )

            st.write(
                "**Skills:**",
                skills
            )

            st.write(
                "**Certifications:**",
                certifications
            )

            st.write(
                "**Projects:**",
                projects
            )

        else:

            st.info("No resume uploaded yet.")

st.markdown("<br>", unsafe_allow_html=True)

# =====================================================
# TABLE
# =====================================================
# =====================================================
# RECENTLY PROCESSED CANDIDATES
# =====================================================

st.subheader("👥 Recently Processed Candidates")

COLUMN_WIDTHS = [2.5, 3.8, 2.2, 1.5, 1.2]

if candidates:

    # -----------------------------
    # SESSION STATE
    # -----------------------------
    if "expanded_candidate" not in st.session_state:
        st.session_state.expanded_candidate = None

    # -----------------------------
    # TABLE HEADER
    # -----------------------------
    header = st.columns(COLUMN_WIDTHS)

    header[0].markdown("#### Name")
    header[1].markdown("#### Email")
    header[2].markdown("#### Phone")
    header[3].markdown("#### Status")
    header[4].markdown("#### Action")

    st.markdown(
        "<hr style='margin:4px 0;'>",
        unsafe_allow_html=True
    )

    # -----------------------------
    # TABLE ROWS
    # -----------------------------
    for i, c in enumerate(reversed(candidates)):

        try:
            skills = ", ".join(json.loads(c["skills"]))
        except:
            skills = c["skills"]

        try:
            education = ", ".join(json.loads(c["education"]))
        except:
            education = c["education"]

        try:
            experience = ", ".join(json.loads(c["experience"]))
        except:
            experience = c["experience"]

        try:
            projects = ", ".join(json.loads(c["projects"]))
        except:
            projects = c["projects"]

        try:
            certifications = ", ".join(json.loads(c["certifications"]))
        except:
            certifications = c["certifications"]

        # -----------------------------
        # TABLE ROW
        # -----------------------------
        row = st.columns(COLUMN_WIDTHS)

        row[0].markdown(
            f"<div style='padding-top:6px'>{c.get('name') or 'N/A'}</div>",
            unsafe_allow_html=True
        )

        row[1].markdown(
            f"<div style='padding-top:6px'>{c.get('email') or 'N/A'}</div>",
            unsafe_allow_html=True
        )

        row[2].markdown(
            f"<div style='padding-top:6px'>{c.get('phone') or 'N/A'}</div>",
            unsafe_allow_html=True
        )

        row[3].markdown(
            """
            <div style='text-align:center;
                        color:green;
                        font-weight:bold;
                        padding-top:6px;'>
                🟢 Processed
            </div>
            """,
            unsafe_allow_html=True
        )

        with row[4]:

            if st.button(
                "▲ Hide" if st.session_state.expanded_candidate == i else "▼ View",
                key=f"toggle_{i}",
                use_container_width=True
            ):

                if st.session_state.expanded_candidate == i:
                    st.session_state.expanded_candidate = None
                else:
                    st.session_state.expanded_candidate = i

                st.rerun()

        # -----------------------------
        # PROFILE CARD
        # -----------------------------
        if st.session_state.expanded_candidate == i:

            st.markdown(
                "<div style='margin-top:6px'></div>",
                unsafe_allow_html=True
            )

            with st.container(border=True):

                st.subheader("👤 Candidate Profile")

                left, right = st.columns(2)

                with left:

                    st.markdown("### 🎓 Education")
                    st.write(education if education else "N/A")

                    st.markdown("### 💼 Experience")
                    st.write(experience if experience else "N/A")

                with right:

                    st.markdown("### 🛠 Skills")
                    st.write(skills if skills else "N/A")

                    st.markdown("### 🚀 Projects")
                    st.write(projects if projects else "N/A")

                    st.markdown("### 📜 Certifications")
                    st.write(certifications if certifications else "N/A")

        st.markdown(
            "<hr style='margin:2px 0;'>",
            unsafe_allow_html=True
        )

else:

    st.info("No candidates found.")