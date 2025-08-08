import streamlit as st
import pandas as pd
import requests

# ⚙️ Paramètres
BASE_URL = "http://localhost:5000/dashboard"
PARENT_ID = "+1"
KID_INDEX = 0
PERIOD = "weekly"

# 📡 Appel API
url = f"{BASE_URL}/{PARENT_ID}/{KID_INDEX}/{PERIOD}"
res = requests.get(url)

if res.status_code == 200:
    data = res.json()

    # 🧾 Affichage résumé global (1 ligne)
    st.subheader("Vue d'ensemble")
    df_summary = pd.DataFrame([{
        "Total Quizzes": data["total_quizzes"],
        "Completed": data["completed_quizzes"],
        "Completion Rate": data["completion_rate"],
        "Average Score": data["average_score"],
        "Time Spent": data["time_spent"],
        "Abandon Rate": data["abandon_rate"],
        "Fail Rate": data["fail_rate"]
    }])
    st.dataframe(df_summary)

    # 📊 Détail par chapitre
    st.subheader("Statistiques par chapitre")
    df_chapters = pd.DataFrame(data["chapters"])
    st.dataframe(df_chapters)

else:
    st.error(f"Erreur API {res.status_code} : {res.text}")
