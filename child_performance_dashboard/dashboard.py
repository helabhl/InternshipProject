import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
from scipy.interpolate import make_interp_spline
import requests


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
# --------------------------
# ⚙️ Sidebar (sélection)
# --------------------------
st.sidebar.title("Parent Dashboard")
parent_id = st.sidebar.text_input("Parent ID:", value="+1")
child_id = st.sidebar.text_input("Child ID / Index:", value="0")
period = st.sidebar.text_input("Select Period:",value="2025-W32")


if st.sidebar.button("Load Dashboard"):
    # --------------------------
    # 📡 Appel API GET avec URL dynamique
    # --------------------------
    route = f"http://localhost:5000/attempts/{parent_id}/{child_id}/{period}"

    try:
        response = requests.get(route)
        response.raise_for_status()
        df = response.json()
        st.success("Data loaded successfully!")

        
        
        week_data = pd.DataFrame(df)
        
        # --------------------------
        # 📊 KPIs
        # --------------------------
        main_col1, main_col2 = st.columns([3, 1])

        with main_col1:
            metrics = st.columns(3)
            completion_rate = week_data['completed'].mean() * 100 if not week_data.empty else 0
            completed_quizzes = week_data['completed'].sum()  if not week_data.empty else 0
            total_quizzes = week_data['quizID'].count()  if not week_data.empty else 0

            avg_score = week_data['score'].mean() * 100 if not week_data.empty else 0
            total_time = week_data['duration'].sum()

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
                    df_sorted = week_data.sort_values('startTime').reset_index(drop=True)
                    df_sorted['quizID'] = df_sorted.index + 1

                    fig1, ax1 = plt.subplots(figsize=(5, 2.5))
                    sns.lineplot(data=df_sorted, x='quizID', y='score',
                                marker='o', linewidth=2, color=sns.color_palette("Blues")[4], ax=ax1)
                    ax1.fill_between(df_sorted['quizID'], df_sorted['score'],
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
                    week_data["startTime"] = pd.to_datetime(week_data["startTime"])

                    week_data['weekday'] = week_data['startTime'].dt.day_name()
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
            definitions = {
                "achievements": {
                    "description": "🎉 Signs that your child is doing great this week!",
                    "criteria": {
                        "High average score": "✅ Great job! The average quiz score is over 80%.",
                        "High completion rate": "✅ Amazing focus! Over 90% of quizzes were completed.",
                        "Low abandon rate": "✅ Excellent commitment! Less than 10% of quizzes were abandoned.",
                        "Consistent time spent": "✅ Well done! More than 30 minutes spent learning this week.",
                        "Streak of success": "✅ Impressive! 5 or more successful quizzes in a row."
                    }
                },

                "alerts": {
                    "description": "⚠️ Things that might need attention.",
                    "criteria": {
                        "High abandon rate": "⚠️ Your child is quitting more than 10% of quizzes. They might be tired or distracted.",
                        "Low average score": "⚠️ The average score is below 60%. Some help or revision could be useful.",
                        "Many failed attempts": "⚠️ More than 30% of quizzes ended in failure. Maybe it's time to review the content.",
                        "Very low activity": "⚠️ Fewer than 3 quizzes this week. Encourage a little more practice!",
                        "Very short quiz time": "⚠️ Average time per quiz is under 30 seconds — possibly rushing through them."
                    }
                }
            }
            
        





            num_quizzes = len(week_data)
            avg_time_spent = week_data['duration'].mean() if not week_data.empty else 0
            consecutive_success = 0
            max_consecutive = 0
            if not week_data.empty:
                week_data_sorted = week_data.sort_values('startTime')
                for success in week_data_sorted['completed']:
                    if success:
                        consecutive_success += 1
                        max_consecutive = max(max_consecutive, consecutive_success)
                    else:
                        consecutive_success = 0
            achieved_keys = []
            if avg_score > 80:
                achieved_keys.append("High average score")
            if completion_rate > 90:
                achieved_keys.append("High completion rate")
            if week_data['abandoned'].mean() < 0.1:
                achieved_keys.append("Low abandon rate")
            if (total_time / 60) > 30:
                achieved_keys.append("Consistent time spent")
            if max_consecutive >= 5:
                achieved_keys.append("Streak of success")

            alert_keys = []
            if week_data['abandoned'].mean() > 0.1:
                alert_keys.append("High abandon rate")
            if avg_score < 60:
                alert_keys.append("Low average score")
            if week_data['failed'].mean() > 0.3:
                alert_keys.append("Many failed attempts")
            if num_quizzes < 3:
                alert_keys.append("Very low activity")
            if avg_time_spent < 30:
                alert_keys.append("Very short quiz time")


            

        with detail_cols[0]:
            st.markdown(
                "<div style='background:#f6ffed; border-radius:8px; padding:10px;'>"
                f"<h4 style='color:#389e0d; margin-bottom:8px;'>🎯 Achievements</h4>"
                "<ul style='margin-top:0; padding-left:20px; font-size:13px;'>"
                + "".join(f"<li>{definitions['achievements']['criteria'][key]}</li>" for key in achieved_keys) +
                "</ul></div>",
                unsafe_allow_html=True
            )

        with detail_cols[1]:
            st.markdown(
                "<div style='background:#fff1f0; border-radius:8px; padding:10px;'>"
                f"<h4 style='color:#cf1322; margin-bottom:8px;'>⚠️ Alerts</h4>"
                "<ul style='margin-top:0; padding-left:20px; font-size:13px;'>"
                + "".join(f"<li>{definitions['alerts']['criteria'][key]}</li>" for key in alert_keys) +
                "</ul></div>",
                unsafe_allow_html=True
            )


        with main_col2:
            if not week_data.empty:
                df_chapters = week_data.groupby('chapter').agg(
                    count=('quizID', 'count'),
                    avg_score=('score', 'mean')
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
    
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to API: {e}")
    except Exception as e:
        st.error(f"Error: {e}")


