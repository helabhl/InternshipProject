import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from analyse import  analyze_weaknesses_by_chapter

# Charger les données
df = pd.read_csv("quiz_attempts.csv")

# Préparer colonnes dérivées
df['start_time'] = pd.to_datetime(df['start_time'])
df['end_time'] = pd.to_datetime(df['end_time'])
df['time_per_question'] = np.where(df['correct_count'] == 0, 0, df['time_spent'] / df['correct_count'])

# Sidebar : choisir l'enfant
child_ids = df['child_id'].unique()
selected_child = st.sidebar.selectbox("Choisir un enfant", child_ids)

# Filtrer les données pour cet enfant
child_df = df[df['child_id'] == selected_child]

# Sidebar : choisir le subject à analyser
subjects = child_df['subject'].unique()
selected_subject = st.sidebar.selectbox("Choisir un sujet", subjects)

# Filtrer encore : pour cet enfant + ce sujet
child_subject_df = child_df[child_df['subject'] == selected_subject]

# === TITRE ===
st.title(f"📊 Dashboard - Enfant: {selected_child} | Sujet: {selected_subject}")

# === Statistiques globales sur ce sujet ===
avg_success = child_subject_df['final_score'].mean()
total_quiz = len(child_subject_df)
avg_time = child_subject_df['time_per_question'].mean()

st.subheader("Statistiques globales (pour ce sujet)")
col1, col2, col3 = st.columns(3)
col1.metric("Taux de réussite moyen", f"{avg_success:.1f}%")
col2.metric("Nombre de quizzes", total_quiz)
col3.metric("Temps moyen par question (sec)", f"{avg_time:.1f}")



# === Progression dans le temps ===


TOTAL_QUIZZES_PER_CHAPTER = 30

st.subheader("📚 Progression par chapitre (quizzes uniques complétés)")

# Étape 1 : trouver les quizzes complétés sans doublons
unique_completed_quizzes = (
    child_subject_df.groupby(['chapter', 'quiz_id'])['completed']
    .max()
    .reset_index()
)
unique_completed_quizzes = unique_completed_quizzes[unique_completed_quizzes['completed'] == 1]

# Étape 2 : compter combien de quizzes complétés par chapter
chapter_progress = unique_completed_quizzes.groupby('chapter').size().reset_index(name='quizzes_completed')

# Étape 3 : calculer le pourcentage
chapter_progress['completion_rate'] = (chapter_progress['quizzes_completed'] / TOTAL_QUIZZES_PER_CHAPTER) * 100
chapter_progress['completion_rate'] = chapter_progress['completion_rate'].round(1)
for _, row in chapter_progress.iterrows():
    chapter = row['chapter']
    completed = int(row['quizzes_completed'])
    completion_rate = row['completion_rate']
    
    st.markdown(f"**{chapter}** – {completed}/{TOTAL_QUIZZES_PER_CHAPTER} quizzes complétés ({completion_rate}%)")
    
    # Afficher une petite barre de progression horizontale
    st.progress(min(completion_rate / 100, 1.0))


from datetime import datetime, timedelta

# Filtrer sur les 30 derniers jours
date_threshold = datetime.now() - timedelta(days=30)
child_subject_recent = child_subject_df[child_subject_df['start_time'] >= date_threshold]

child_subject_sorted = child_subject_recent.sort_values('start_time').copy()
child_subject_sorted['cumulative_success_rate'] = (
    child_subject_sorted['final_score'].expanding().sum()
)

st.subheader(f"📈 Progression du score ({selected_subject})")

if not child_subject_sorted.empty:
    fig = px.line(
        child_subject_sorted,
        x='start_time',
        y='cumulative_success_rate',
        markers=True,
        title=f'Score cumulatif au fil du temps ({selected_subject})'
    )
    fig.update_yaxes(title_text='Moyenne cumulative du success_rate')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Pas de données pour ce sujet.")



# === Quiz problématiques (beaucoup d'essais mais pas complété) ===


from datetime import datetime, timedelta
# Définir la période : ici les 7 derniers jours
nb_days = 30
date_threshold = datetime.now() - timedelta(days=nb_days)

st.subheader(f"⚠️ Quiz problématiques (tentés ≥3 fois, jamais complétés, ces {nb_days} derniers jours)")

# Filtrer les quizzes des derniers jours
recent_quiz = child_subject_df[child_df['start_time'] >= date_threshold]

# Garder ceux avec attempts_count >=3 et completed ==0
problem_quiz = recent_quiz[(recent_quiz['attempts_count'] >= 3) & (recent_quiz['completed'] == 0)]

# Retirer les doublons : même quiz_id gardé une seule fois
problem_quiz_unique = problem_quiz.drop_duplicates(subset=['quiz_id'])

# Afficher
if not problem_quiz_unique.empty:
    st.write("L'enfant a eu du mal avec ces quizzes récemment :")
    st.dataframe(problem_quiz_unique[['quiz_id', 'subject', 'chapter', 'attempts_count', 'final_score']])
else:
    st.write("✅ Aucun quiz problématique détecté récemment.")



# Analyser
weakness_df, skill_profiles = analyze_weaknesses_by_chapter(df)

st.title(f"📊 Dashboard – Analyse des faiblesses pour l’enfant {selected_child} par chapitre")

# Récupérer profil
child_profile = skill_profiles.get(selected_child, {})

if child_profile:
    st.subheader("📚 Détails par chapitre")
    for chapter, stats in child_profile['chapters'].items():
        with st.expander(f"Chapitre : {chapter}"):
            st.write(f" Faiblesses détectées : {', '.join(stats['weaknesses'])}")

# Optionnel : dataframe détaillé
with st.expander("📄 Voir le DataFrame détaillé"):
    child_data = weakness_df[weakness_df['child_id'] == selected_child]
    st.dataframe(child_data[['chapter', 'avg_success_rate', 'avg_time_spent',
                             'num_unique_quizzes', 'weaknesses']])

