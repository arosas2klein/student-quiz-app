import streamlit as st
import hashlib
import random
import pandas as pd
import datetime
import os

# --- 1. DATA LOADING ---
user_df = pd.read_csv("users.csv")
USERS = dict(zip(user_df['username'].astype(str), user_df['password'].astype(str)))

df = pd.read_csv("questions.csv")
TESTS = {}

for test_name, group in df.groupby("Test Name"):
    TESTS[test_name] = []
    for _, row in group.iterrows():
        TESTS[test_name].append({
            "q": row["Question"],
            "options": [str(row["Option A"]), str(row["Option B"]), str(row["Option C"])],
            "correct": str(row["Correct Answer"])
        })

# --- 2. LOGIC FUNCTIONS ---
def log_result(user, test, score, total):
    file_path = "test_results.csv"
    new_data = pd.DataFrame([{
        "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Student": user,
        "Test": test,
        "Score": f"{score}/{total}",
        "Percentage": f"{(score/total)*100:.1f}%"
    }])
    # Save record to CSV
    new_data.to_csv(file_path, mode='a', index=False, header=not os.path.exists(file_path))

# --- 3. APP INTERFACE ---
st.set_page_config(page_title="Secure Exam Portal", layout="wide")

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

# Authenticated Area
else:
    st.sidebar.title(f"Welcome, {st.session_state.user}")
    
    # --- TEACHER DASHBOARD (Only for you) ---
    # Replace 'arosas2' with your actual username from users.csv
    if st.session_state.user == 'arosas2':
        st.sidebar.divider()
        st.sidebar.subheader("🍎 Teacher Tools")
        show_records = st.sidebar.checkbox("View Student Records")
        
        if show_records:
            st.title("📊 Student Activity Log")
            if os.path.exists("test_results.csv"):
                records_df = pd.read_csv("test_results.csv")
                # Show newest results first
                st.dataframe(records_df.iloc[::-1], use_container_width=True)
                
                # Option to download the log
                csv = records_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Full Report (CSV)", csv, "class_results.csv", "text/csv")
            else:
                st.info("No records found yet. Once students submit a test, they will appear here.")
            st.stop() # Stops the quiz from showing when you are looking at records

    # --- QUIZ SECTION ---
    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.rerun()

    test_name = st.selectbox("Select your assigned test:", list(TESTS.keys()))
    
    if 'quiz_questions' not in st.session_state or st.button("New Question Shuffle"):
        questions = TESTS[test_name].copy()
        random.shuffle(questions)
        for q in questions:
            random.shuffle(q['options'])
        st.session_state.quiz_questions = questions

    with st.form("exam_form"):
        st.header(test_name)
        answers = []
        for i, q_data in enumerate(st.session_state.quiz_questions):
            st.write(f"**Question {i+1}**")
            ans = st.radio(q_data['q'], q_data['options'], key=f"q_{i}", index=None)
            answers.append((ans, q_data['correct']))
        
        submitted = st.form_submit_button("Submit Exam")

        if submitted:
            if any(user_ans is None for user_ans, correct in answers):
                st.error("⚠️ Please answer all questions before submitting.")
            else:
                score = sum(1 for user_ans, correct in answers if user_ans == correct)
                total = len(answers)
                
                st.divider()
                st.header(f"Results for {st.session_state.user}")
                st.metric("Final Score", f"{score} / {total}", f"{(score/total)*100:.1f}%")
                
                log_result(st.session_state.user, test_name, score, total)
                
                # Review Section
                for i, (user_ans, correct) in enumerate(answers):
                    question_text = st.session_state.quiz_questions[i]['q']
                    if user_ans == correct:
                        st.success(f"✅ Q{i+1}: Correct")
                    else:
                        st.error(f"❌ Q{i+1}: Incorrect. (Correct: {correct})")
                
                if score == total:
                    st.balloons()