import streamlit as st
import pandas as pd
import json, io, zipfile, os
from PIL import Image

# ─── Load your images ─────────────────────────────────────────────────────────
# (make sure these paths are correct relative to where you run `streamlit run`)
ua_logo       = Image.open("ua_logo_green_rgb.png")
engg_logo     = Image.open("copy-of-faculty-of-engineering.jpg")
feedback_icon = Image.open("feedback-line-icon-free-vector.jpg")

# ─── HEADER WITH LOGOS ────────────────────────────────────────────────────────
# three columns: UAlberta logo | Engineering faculty logo | feedback icon
c1, c2, c3 = st.columns([1, 3, 1])
with c1:
    st.image(ua_logo, width=80, caption="University of Alberta")
with c2:
    st.image(engg_logo, width=350, caption="Faculty of Engineering")
with c3:
    st.image(feedback_icon, width=80, caption="Feedback")

# ─── APP TITLE & NEW INPUTS ──────────────────────────────────────────────────
st.title("Student Feedback Generator")

# NEW: course title input
course_title = st.text_input(
    "Course Title",
    value="",
    placeholder="e.g. ENG 130"
)

# NEW: second input — rename the label to whatever you need
extra_field = st.text_input(
    "Additional Info",
    value="",
    placeholder="e.g. Semester or Instructor"
)

st.write(f"**Course:** {course_title}   |   **Info:** {extra_field}")
st.markdown("---")

# ─── EXISTING FILE UPLOADERS & LOGIC ─────────────────────────────────────────
st.write("Upload the Excel file containing student answers and the JSON file with feedback data.")

excel_file = st.file_uploader("Upload Student Answers (Excel)", type=["xlsx"])
json_file  = st.file_uploader("Upload Feedback Data (JSON)",  type=["json"])

if excel_file and json_file:
    if st.button("Generate Feedback"):
        try:
            # your existing functions…
            student_df    = load_student_answers(excel_file)
            feedback_data = load_feedback(json_file)
            feedback_reports = generate_feedback_text(student_df, feedback_data)
            zip_file = create_zip_from_feedback(feedback_reports)

            st.success("Feedback reports generated successfully!")
            st.download_button(
                label="Download Feedback Reports Zip",
                data=zip_file,
                file_name="feedback_reports.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Please upload both the Excel and JSON files to proceed.")
