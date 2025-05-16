# app.py
# -*- coding: utf-8 -*-
"""
Student Feedback Generator
"""

import streamlit as st
import pandas as pd
import json, io, zipfile, os
from PIL import Image

# ─── Functions for processing files and generating feedback ─────────────────
def load_student_answers(file_obj):
    return pd.read_excel(file_obj)

def load_feedback(file_obj):
    return json.load(file_obj)

def get_feedback_for_choice(student_answer, feedback_entry):
    student_choice = student_answer.strip().lower()
    correct_choice = feedback_entry['correct_choice_ID'].lower()
    idx = ord(student_choice) - ord('a')
    if 0 <= idx < len(feedback_entry['Q_justifications']):
        justification = feedback_entry['Q_justifications'][idx][1]
    else:
        justification = "No justification available"
    return student_choice, correct_choice, justification

def find_matching_question_key(qnum, feedback_data):
    for key in feedback_data:
        if key.startswith(f"Q{qnum}_") or f"_q_{qnum}" in key:
            return key
    return None

def generate_feedback_text(df, feedback_data, course_title, extra_field):
    reports = {}
    for _, row in df.iterrows():
        name = f"{row['First Name']} {row['Last Name']}"
        sid  = row['Student No']
        scored = str(row['Scored Responses']).replace('R=', '').strip().split()
        
        # Build header for each feedback file
        lines = [
            f"Course: {course_title}",
            f"Additional Info: {extra_field}",
            "",
            f"Feedback for {name} (ID: {sid})",
            "-" * 40,
            ""
        ]
        
        for i, ans in enumerate(scored, start=1):
            if ans in ['.', '-']:
                lines.append(f"Question {i}: Not attempted.\n")
                continue
            key = find_matching_question_key(i, feedback_data)
            if key:
                entry = feedback_data[key]
                stu, cor, just = get_feedback_for_choice(ans, entry)
                lines.append(f"Question {i}:")
                lines.append(f"  - Your Answer: {ans.upper()}")
                if stu != cor:
                    lines.append(f"  - Correct Answer: {cor.upper()}")
                lines.append(f"  - Feedback: {just}\n")
            else:
                lines.append(f"Question {i}: No feedback provided.\n")
        
        reports[sid] = "\n".join(lines)
    return reports

def create_zip_from_feedback(reports):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for sid, text in reports.items():
            z.writestr(f"feedback_{sid}.txt", text)
    buf.seek(0)
    return buf

# ─── HEADER WITH TWO LOGOS ────────────────────────────────────────────────────
ua_logo       = Image.open("ua_logo_green_rgb.png")
engg_logo     = Image.open("copy-of-faculty-of-engineering.jpg")
feedback_icon = Image.open("feedback-line-icon-free-vector.jpg")

# Top row: UAlberta logo on left, Faculty of Engineering logo on right
col1, col2 = st.columns(2)
with col1:
    st.image(ua_logo, width=250)
with col2:
    st.image(engg_logo, width=250)

# ─── TITLE WITH FEEDBACK ICON ────────────────────────────────────────────────
title_col, icon_col = st.columns([5, 1])
with title_col:
    st.title("Student Feedback Generator")
with icon_col:
    st.image(feedback_icon, width=60)

# ─── INPUTS ──────────────────────────────────────────────────────────────────
course_title = st.text_input("Course Title", placeholder="e.g. ENG 130")
extra_field  = st.text_input("Additional Info", placeholder="e.g. Semester or Instructor")

st.markdown("---")

# ─── FILE UPLOADERS & MAIN LOGIC ─────────────────────────────────────────────
st.write("Upload the Excel file containing student answers and the JSON file with feedback data.")

excel_file = st.file_uploader("Upload Student Answers (Excel)", type=["xlsx"])
json_file  = st.file_uploader("Upload Feedback Data (JSON)",  type=["json"])

if excel_file and json_file:
    if st.button("Generate Feedback"):
        try:
            df      = load_student_answers(excel_file)
            fdata   = load_feedback(json_file)
            reports = generate_feedback_text(df, fdata, course_title, extra_field)
            zipbuf  = create_zip_from_feedback(reports)

            st.success("Feedback reports generated successfully!")
            st.download_button(
                "Download Feedback Reports (ZIP)",
                data=zipbuf,
                file_name="feedback_reports.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Please upload both the Excel and JSON files to proceed.")
