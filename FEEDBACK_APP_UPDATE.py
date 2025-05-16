# app.py
# -*- coding: utf-8 -*-
"""
Student Feedback Generator
"""

import streamlit as st
import pandas as pd
import json, io, zipfile
import requests
from PIL import Image

# ─── CONFIG ────────────────────────────────────────────────────────────────────
# Replace these with your GitHub user/repo/branch as needed:
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/yourUser/feedback-app/main/"

# ─── IMAGE LOADER ─────────────────────────────────────────────────────────────
def load_image_from_github(path: str) -> Image.Image:
    url = GITHUB_RAW_BASE + path
    resp = requests.get(url)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content))

# ─── LOAD YOUR TWO ROW HEADER ─────────────────────────────────────────────────
ua_logo       = load_image_from_github("assets/ua_logo_green_rgb.png")
engg_logo     = load_image_from_github("assets/copy-of-faculty-of-engineering.jpg")
feedback_icon = load_image_from_github("assets/feedback-line-icon-free-vector.jpg")

# Top row: UA on left, Engineering on right
col1, col2 = st.columns(2)
with col1:
    st.image(ua_logo, width=250)       # adjust width as desired
with col2:
    st.image(engg_logo, width=250)

# Second row: feedback icon centered
_, c2, _ = st.columns([1,2,1])
with c2:
    st.image(feedback_icon, width=120)

# ─── APP TITLE & NEW INPUTS ──────────────────────────────────────────────────
st.title("Student Feedback Generator")

course_title = st.text_input(
    "Course Title",
    placeholder="e.g. ENG 130"
)

extra_field = st.text_input(
    "Additional Info",
    placeholder="e.g. Semester or Instructor"
)

# Optional: show what the user typed
if course_title or extra_field:
    st.markdown(f"**Course:** {course_title}   |   **Info:** {extra_field}")
st.markdown("---")

# ─── ORIGINAL FEEDBACK FUNCTIONS ───────────────────────────────────────────────
def load_student_answers(file_obj):
    """Loads student answers from an Excel file object."""
    return pd.read_excel(file_obj)

def load_feedback(file_obj):
    """Loads the feedback data from a JSON file object."""
    return json.load(file_obj)

def get_feedback_for_choice(student_answer, feedback_entry):
    """Retrieves the correct answer and justification based on the student's choice."""
    student_choice = student_answer.strip().lower()
    correct_choice = feedback_entry['correct_choice_ID'].lower()
    mapping_index = ord(student_choice) - ord('a')
    if 0 <= mapping_index < len(feedback_entry['Q_justifications']):
        justification = feedback_entry['Q_justifications'][mapping_index][1]
    else:
        justification = "No justification available"
    return student_choice, correct_choice, justification

def find_matching_question_key(question_num, feedback_data):
    """Find the correct JSON key that corresponds to the given question number."""
    for key in feedback_data.keys():
        if key.startswith(f"Q{question_num}_") or f"_q_{question_num}" in key:
            return key
    return None

def generate_feedback_text(student_df, feedback_data):
    """Generate feedback text for each student's response."""
    feedback_reports = {}
    for _, row in student_df.iterrows():
        student_name = f"{row['First Name']} {row['Last Name']}"
        student_id   = row['Student No']
        scored       = str(row['Scored Responses']).replace('R=', '').strip()
        
        lines = [f"Feedback for {student_name} (ID: {student_id})\n"]
        for q_num, ans in enumerate(scored, start=1):
            if ans in ['.', '-']:
                lines.append(f"Question {q_num}: Not attempted.\n")
                continue
            key = find_matching_question_key(q_num, feedback_data)
            if key:
                entry = feedback_data[key]
                stu, cor, just = get_feedback_for_choice(ans, entry)
                lines.append(f"Question {q_num}:")
                lines.append(f"  - Your Answer: {ans.upper()}")
                if stu != cor:
                    lines.append(f"  - Correct Answer: {cor.upper()}")
                lines.append(f"  - Feedback: {just}\n")
            else:
                lines.append(f"Question {q_num}: No feedback in reference file.\n")
        feedback_reports[student_id] = "\n".join(lines)
    return feedback_reports

def create_zip_from_feedback(feedback_reports):
    """Creates a zip in-memory with one text file per student."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for sid, text in feedback_reports.items():
            z.writestr(f"feedback_{sid}.txt", text)
    buf.seek(0)
    return buf

# ─── FILE UPLOADERS & MAIN LOGIC ───────────────────────────────────────────────
st.write("Upload the Excel file containing student answers and the JSON file with feedback data.")

excel_file = st.file_uploader("📄 Student Answers (Excel)", type=["xlsx"])
json_file  = st.file_uploader("📝 Feedback Data (JSON)",  type=["json"])

if excel_file and json_file:
    if st.button("Generate Feedback"):
        try:
            df      = load_student_answers(excel_file)
            fdata   = load_feedback(json_file)
            reports = generate_feedback_text(df, fdata)
            zipbuf  = create_zip_from_feedback(reports)

            st.success("🎉 Feedback reports generated successfully!")
            st.download_button(
                label="📥 Download All Feedback (ZIP)",
                data=zipbuf,
                file_name="feedback_reports.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Please upload both files to proceed.")
