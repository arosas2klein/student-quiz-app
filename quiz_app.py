import streamlit as st
import hashlib
import random
import pandas as pd
import datetime
import os

# Load users from the CSV file
user_df = pd.read_csv("users.csv")
# This creates a dictionary where the username is the key and password is the value
USERS = dict(zip(user_df['username'].astype(str), user_df['password'].astype(str)))

import pandas as pd

# 1. Load the CSV file from your folder
df = pd.read_csv("questions.csv")

# 2. Prepare the empty dictionary
TESTS = {}

# 3. Fill the dictionary using the CSV data
for test_name, group in df.groupby("Test Name"):
    TESTS[test_name] = []
    for _, row in group.iterrows():
        TESTS[test_name].append({
            "q": row["Question"],
            "options": [str(row["Option A"]), str(row["Option B"]), str(row["Option C"])],
            "correct": str(row["Correct Answer"])
        })

# --- 2. LOGIC FUNCTIONS ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def log_result(user, test, score, total):
    file_path = "test_results.csv"
    new_data = pd.DataFrame([{
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Student": user,
        "Test": test,
        "Score": f"{score}/{total}",
        "Percentage": f"{(score/total)*100:.1f}%"
    }])
    # Append to CSV
    new_data.to_csv(file_path, mode='a', index=False, header=not os.path.exists(file_path))

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="Secure Exam Portal")

if 'auth' not in st.session_state:
    st.session_state.auth = False

# Login Screen
if not st.session_state.auth:
    st.title("🔐 Student Login")
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Enter Exam"):
        if user_input in USERS and pass_input == USERS[user_input]:
            st.session_state.auth = True
            st.session_state.user = user_input
            st.rerun()
        else:
            st.error("Access Denied: Incorrect credentials.")

# Exam Screen
else:
    st.sidebar.title(f"User: {st.session_state.user}")
    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.rerun()

    test_name = st.selectbox("Select your assigned test:", list(TESTS.keys()))
    
    # Initialize/Shuffle questions for this specific session
    if 'quiz_questions' not in st.session_state or st.button("New Question Shuffle"):
        questions = TESTS[test_name].copy()
        random.shuffle(questions)
        # Also shuffle the options within each question
        for q in questions:
            random.shuffle(q['options'])
        st.session_state.quiz_questions = questions

    with st.form("exam_form"):
        st.header(test_name)
        answers = []
        for i, q_data in enumerate(st.session_state.quiz_questions):
            st.write(f"**Question {i+1}**")
            ans = st.radio(q_data['q'], q_data['options'], key=f"q_{i}")
            answers.append((ans, q_data['correct']))
        
       # This line creates the actual button and names it 'submitted'
        submitted = st.form_submit_button("Submit Exam")

        if submitted:
            # Calculate the score
            score = sum(1 for user_ans, correct in answers if user_ans == correct)
            total = len(answers)
            
            st.divider()
            st.header(f"Results for {st.session_state.user}")
            st.metric("Final Score", f"{score} / {total}", f"{(score/total)*100:.1f}%")
            
            # --- REVIEW SECTION ---
            st.subheader("Review your answers:")
            for i, (user_ans, correct) in enumerate(answers):
                question_text = st.session_state.quiz_questions[i]['q']
                
                if user_ans == correct:
                    st.success(f"✅ Question {i+1}: {question_text}")
                    st.write(f"Your answer: **{user_ans}** (Correct!)")
                else:
                    st.error(f"❌ Question {i+1}: {question_text}")
                    st.write(f"Your answer: **{user_ans}**")
                    st.write(f"The correct answer was: **{correct}**")
            
            # Save to the CSV file
            log_result(st.session_state.user, test_name, score, total)
            
            if score == total:
                st.balloons()