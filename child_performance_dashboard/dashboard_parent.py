import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta


st.sidebar.title("Parent Dashboard")
parent_id = st.sidebar.text_input("Parent ID:", value="+14388864855")
kid_id = st.sidebar.text_input("Child ID / Index:", value="0")

# Sélection de la période
from_date = st.sidebar.date_input("From", datetime.today() - timedelta(days=60))
to_date = st.sidebar.date_input("To", datetime.today())


try:
    performance_url = f"http://localhost:5000/attempts/performances/{parent_id}/{kid_id}"
    params = {
        "from": from_date.isoformat(),
        "to": to_date.isoformat()
    }
    resp = requests.get(performance_url, params=params)
    resp.raise_for_status()
    perf_data = resp.json()

    # Metrics
    metrics = perf_data["metrics"]
    st.metric("Total Time Spent (s)", metrics["time_spent_seconds"])
    st.metric("Completion Rate", f"{metrics['completion_rate']*100:.1f}%")
    st.metric("Average Score", f"{metrics['average_score']:.1f}")

    # Lineplot : scores over quizzes
    df_line = pd.DataFrame(perf_data["lineplot"])
    if not df_line.empty:
        df_line["start_time"] = pd.to_datetime(df_line["start_time"])
        plt.figure(figsize=(6,3))
        sns.lineplot(data=df_line, x="quizID", y="score", marker="o")
        plt.title("Scores over quizzes")
        st.pyplot(plt.gcf())

    # Barplot : number of quizzes per weekday
    df_bar = pd.DataFrame(list(perf_data["barplot"].items()), columns=["weekday", "count"])
    if not df_bar.empty:
        plt.figure(figsize=(6,3))
        sns.barplot(data=df_bar, x="weekday", y="count")
        plt.title("Number of quizzes per weekday")
        st.pyplot(plt.gcf())

except requests.exceptions.RequestException as e:
    st.error(f"Failed to fetch performance: {e}")



try:
    achievements_url = f"http://localhost:5000/attempts/achievements/{parent_id}/{kid_id}"
    params = {
        "from": from_date.isoformat(),
        "to": to_date.isoformat()
    }
    resp = requests.get(achievements_url, params=params)
    resp.raise_for_status()
    ach_data = resp.json()

    st.subheader("Achievements")
    for key, value in ach_data.items():
        st.write(f"{key}: {value}")

except requests.exceptions.RequestException as e:
    st.error(f"Failed to fetch achievements: {e}")
