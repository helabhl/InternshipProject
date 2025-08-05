import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from scipy.interpolate import make_interp_spline

# --------------------------
# 🎨 Load external CSS
# --------------------------
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --------------------------
# ⚙️ Page config
# --------------------------
st.set_page_config(page_title="Parent Dashboard", layout="wide")

# --------------------------
# 📅 Load data
# --------------------------
df = pd.read_csv('quiz_attempts.csv', parse_dates=['start_time', 'end_time'])
df['completed'] = df['completed'].astype(bool)
df['abandoned'] = df['abandoned'].astype(bool)
df['failed'] = df['failed'].astype(bool)

# --------------------------
# 📅 Add week number
# --------------------------
df['week_number'] = df['start_time'].dt.isocalendar().week
weeks_available = sorted(df['week_number'].unique())

# --------------------------
# 🧰 Session state for week navigation
# --------------------------
if 'current_week_idx' not in st.session_state:
    st.session_state.current_week_idx = len(weeks_available) - 1

# --------------------------
# 📌 Sidebar
# --------------------------
with st.sidebar:
    st.title("Parent Dashboard")
    selected_child = st.selectbox("Select child:", df['child_id'].unique())

# --------------------------
# 📆 Navigation buttons
# --------------------------
col_prev, col_next = st.columns([1, 1])
with col_prev:
    if st.button("⬅️ Previous week"):
        if st.session_state.current_week_idx > 0:
            st.session_state.current_week_idx -= 1

with col_next:
    if st.button("Next week ➡️"):
        if st.session_state.current_week_idx < len(weeks_available) - 1:
            st.session_state.current_week_idx += 1

current_week = weeks_available[st.session_state.current_week_idx]

# --------------------------
# 🔍 Filter data
# --------------------------
child_data = df[df['child_id'] == selected_child]
week_data = child_data[child_data['week_number'] == current_week].copy()

# --------------------------
# 📊 KPIs
# --------------------------
main_col1, main_col2 = st.columns([3, 1])

with main_col1:
    metrics = st.columns(3)
    completion_rate = week_data['completed'].mean() * 100 if not week_data.empty else 0
    completed_quizzes = week_data['completed'].sum()  if not week_data.empty else 0
    total_quizzes = week_data['quiz_id'].count()  if not week_data.empty else 0

    avg_score = week_data['final_score'].mean() * 100 if not week_data.empty else 0
    total_time = week_data['time_spent'].sum()

    hours = int(total_time // 3600)
    minutes = int((total_time % 3600) // 60)
    time_str = f"{hours}h{minutes:02d}"

    metrics_data = [
        ("✅ Completion", f"{completed_quizzes}/ {total_quizzes}", "#e6f7ff"),
        ("🧠 Average score", f"{avg_score:.0f}%", "#fff7e6"),
        ("🕒 Time spent", time_str, "#f6ffed"),
    ]

    for col, (title, value, color) in zip(metrics, metrics_data):
        with col:
            st.markdown(
                f"<div style='background:{color}; border-radius:8px; padding:10px; text-align:center;'>"
                f"<div style='font-size:12px;'>{title}</div>"
                f"<div style='font-size:18px; font-weight:bold;'>{value}</div></div>",
                unsafe_allow_html=True
            )
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # --------------------------
    # 📊 Graphs with Seaborn
    # --------------------------
    graph_cols = st.columns(2)

    with graph_cols[0]:
        if not week_data.empty:
            df_sorted = week_data.sort_values('start_time').reset_index(drop=True)
            df_sorted['quiz_index'] = df_sorted.index + 1

            fig1, ax1 = plt.subplots(figsize=(5, 2.5))
            sns.lineplot(data=df_sorted, x='quiz_index', y='final_score',
                         marker='o', linewidth=2, color=sns.color_palette("Blues")[4], ax=ax1)
            ax1.fill_between(df_sorted['quiz_index'], df_sorted['final_score'],
                             color=sns.color_palette("Blues")[2], alpha=0.2)
            ax1.set_title("Scores over quizzes ", fontsize=12)
            ax1.set_ylabel('Score')
            ax1.set_xlabel('Quizzes')
            ax1.set_facecolor('white')
            sns.despine(left=True, bottom=True)
            st.pyplot(fig1)
        else:
            st.info("No data for this week.")

    with graph_cols[1]:
        if not week_data.empty:
            week_data['weekday'] = week_data['start_time'].dt.day_name()
            df_week = week_data.groupby('weekday').size().reindex([
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ], fill_value=0).reset_index(name='count')

            fig2, ax2 = plt.subplots(figsize=(5, 2.5))
            sns.barplot(data=df_week, x='weekday', y='count', hue='weekday',
                        palette='Blues', dodge=False, legend=False, alpha=0.8, ax=ax2)
            ax2.set_title("Number of quizzes per weekday", fontsize=12)
            ax2.set_ylabel('Number of quizzes')
            ax2.set_xlabel('')
            ax2.tick_params(axis='x', rotation=30)
            ax2.set_facecolor('white')
            sns.despine(left=True, bottom=True)
            st.pyplot(fig2)
        else:
            st.info("No weekday data for this week.")

    detail_cols = st.columns(2)

with detail_cols[0]:
    num_quizzes = len(week_data)
    avg_time_spent = week_data['time_spent'].mean() if not week_data.empty else 0
    objectives = []

    if avg_score > 80:
        objectives.append("✅ Average score above 80%")
    if completion_rate > 90:
        objectives.append("✅ Completion rate above 90%")
    if week_data['abandoned'].mean() < 0.1:
        objectives.append("✅ Less than 10% abandons")
    if (total_time / 60) > 30:
        objectives.append("✅ More than 30 minutes spent")

    consecutive_success = 0
    max_consecutive = 0
    if not week_data.empty:
        week_data_sorted = week_data.sort_values('start_time')
        for success in week_data_sorted['completed']:
            if success:
                consecutive_success += 1
                max_consecutive = max(max_consecutive, consecutive_success)
            else:
                consecutive_success = 0
    if max_consecutive >= 5:
        objectives.append("✅ 5 consecutive successful quizzes")

    st.markdown(
        "<div style='background:#f6ffed; border-radius:8px; padding:10px;'>"
        "<h4 style='color:#389e0d; margin-bottom:8px;'>🎯 Achievements</h4>"
        "<ul style='margin-top:0; padding-left:20px; font-size:13px;'>"
        + "".join(f"<li>{item}</li>" for item in objectives) +
        "</ul></div>",
        unsafe_allow_html=True
    )

with detail_cols[1]:
    alerts = []
    if week_data['abandoned'].mean() > 0.1:
        alerts.append("⚠️ High abandon rate (>10%)")
    if avg_score < 60:
        alerts.append("⚠️ Low average score (<60%)")
    if week_data['failed'].mean() > 0.3:
        alerts.append("⚠️ Too many failed quizzes (>30%)")
    if num_quizzes < 3:
        alerts.append("⚠️ Very low activity (<3 quizzes)")
    if avg_time_spent < 30:
        alerts.append("⚠️ Very short average time per quiz (<30 sec)")

    if not alerts:
        alerts = ["✅ Everything looks good!"]

    st.markdown(
        f"<div style='background:#fff1f0; border-radius:8px; padding:10px;'>"
        "<h4 style='color:#cf1322; margin-bottom:8px;'>⚠️ Alerts</h4>"
        "<ul style='margin-top:0; padding-left:20px; font-size:13px;'>"
        + "".join(f"<li>{item}</li>" for item in alerts) +
        "</ul></div>",
        unsafe_allow_html=True
    )

with main_col2:
    if not week_data.empty:
        df_chapters = week_data.groupby('chapter').agg(
            count=('quiz_id', 'count'),
            avg_score=('final_score', 'mean')
        ).sort_values(by='count', ascending=False).reset_index()

        top_chapters = df_chapters.head(3)

        for _, row in top_chapters.iterrows():
            chapter = row['chapter']
            count = int(row['count'])
            avg_score = row['avg_score'] * 100 if pd.notnull(row['avg_score']) else 0

            st.markdown(
                f"<div class='course-card'>"
                f"<div class='course-title'>{chapter}</div>"
                f"<progress value='{avg_score / 100:.2f}' max='1' style='width:100%; height:8px;'></progress>"
                f"<div style='font-size:12px; margin-top:5px;'>{count} quizzes – {avg_score:.0f}% success</div></div>",
                unsafe_allow_html=True
            )
    else:
        st.info("No chapter data for this week.")
