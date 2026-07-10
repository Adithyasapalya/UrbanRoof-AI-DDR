import shutil
from pathlib import Path

import streamlit as st

from app import main

from config import (
    DATA_DIR,
    REPORT_OUTPUT,
    KNOWLEDGE_BASE_JSON,
    EXTRACTED_DIR,
)
st.set_page_config(
    page_title="UrbanRoof AI DDR Generator",
    page_icon="🏢",
    layout="wide",
)
st.title(" UrbanRoof AI DDR Generator")

st.write(
    """
Generate a Damage Detection Report (DDR)
from Inspection and Thermal PDFs.
"""
)
inspection_pdf = st.file_uploader(
    "Inspection PDF",
    type=["pdf"],
)

thermal_pdf = st.file_uploader(
    "Thermal PDF",
    type=["pdf"],
)
# -------------------------------------------------------
# Save uploaded PDFs
# -------------------------------------------------------

if st.button(" Generate DDR", use_container_width=True):

    if inspection_pdf is None or thermal_pdf is None:
        st.error("Please upload both PDFs.")
        st.stop()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    inspection_path = DATA_DIR / "inspection.pdf"
    thermal_path = DATA_DIR / "thermal.pdf"

    with open(inspection_path, "wb") as f:
        f.write(inspection_pdf.getbuffer())

    with open(thermal_path, "wb") as f:
        f.write(thermal_pdf.getbuffer())

    st.success("Files uploaded successfully.")

    progress = st.progress(0)

    status = st.empty()

    try:

        status.info("Running AI pipeline...")

        progress.progress(20)

        main()

        progress.progress(100)

        status.success("DDR generated successfully!")

    except Exception as e:

        progress.empty()

        st.exception(e)

        st.stop()

# -------------------------------------------------------
# DOWNLOADS
# -------------------------------------------------------

st.divider()

st.subheader("Downloads")

col1, col2 = st.columns(2)

# DDR Report
with col1:

    if REPORT_OUTPUT.exists():

        with open(REPORT_OUTPUT, "rb") as f:

            st.download_button(

                label=" Download DDR Report",

                data=f,

                file_name=REPORT_OUTPUT.name,

                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",

                use_container_width=True

            )

# Knowledge Base
with col2:

    if KNOWLEDGE_BASE_JSON.exists():

        with open(KNOWLEDGE_BASE_JSON, "rb") as f:

            st.download_button(

                label=" Download Knowledge Base",

                data=f,

                file_name=KNOWLEDGE_BASE_JSON.name,

                mime="application/json",

                use_container_width=True

            )


# -------------------------------------------------------
# OPTIONAL JSON DOWNLOADS
# -------------------------------------------------------

inspection_json = EXTRACTED_DIR / "inspection.json"
thermal_json = EXTRACTED_DIR / "thermal.json"

col3, col4 = st.columns(2)

with col3:

    if inspection_json.exists():

        with open(inspection_json, "rb") as f:

            st.download_button(

                label=" Download Inspection JSON",

                data=f,

                file_name="inspection.json",

                mime="application/json",

                use_container_width=True

            )

with col4:

    if thermal_json.exists():

        with open(thermal_json, "rb") as f:

            st.download_button(

                label=" Download Thermal JSON",

                data=f,

                file_name="thermal.json",

                mime="application/json",

                use_container_width=True

            )