import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# --------------------------
# 📊 1) Simuler des données
# --------------------------

# Deux enfants
children = [
    {'id': 1, 'Nom': 'Amine', 'Âge': 9, 'Classe': 'CM1'},
    {'id': 2, 'Nom': 'Yasmine', 'Âge': 7, 'Classe': 'CE1'}
]

# Résumé global simulé par enfant
summary_data = {
    1: {'Taux de complétion': '72 %', 'Score moyen': '84 %', 'Temps total cette semaine': '2h15', 'Objectifs atteints': '4 / 5'},
    2: {'Taux de complétion': '80 %', 'Score moyen': '88 %', 'Temps total cette semaine': '1h45', 'Objectifs atteints': '5 / 5'}
}

# Evolution du score (même structure pour les deux enfants)
score_evolution_data = {
    1: pd.DataFrame({'Semaine': ['S1', 'S2', 'S3', 'S4'], 'Score moyen': [75, 80, 83, 84]}),
    2: pd.DataFrame({'Semaine': ['S1', 'S2', 'S3', 'S4'], 'Score moyen': [82, 85, 87, 88]})
}

# Scores par matière
scores_subjects_data = {
    1: pd.DataFrame({'Matière': ['Maths', 'Français', 'Sciences'], 'Score': [82, 88, 80]}),
    2: pd.DataFrame({'Matière': ['Maths', 'Français', 'Sciences'], 'Score': [90, 85, 88]})
}

# Détails récents
recent_quiz_data = {
    1: pd.DataFrame({
        'Date': ['20/07', '18/07', '16/07'],
        'Quiz': ['Additions niveau 1', 'Lecture phrases', 'Multiplication'],
        'Sujet': ['Maths', 'Français', 'Maths'],
        'Score': ['85 %', '90 %', '50 %'],
        'Durée': ['6 min', '4 min', '3 min'],
        'Statut': ['Terminé', 'Terminé', 'Abandonné']
    }),
    2: pd.DataFrame({
        'Date': ['21/07', '19/07', '17/07'],
        'Quiz': ['Multiplication', 'Orthographe', 'Sciences niveau 1'],
        'Sujet': ['Maths', 'Français', 'Sciences'],
        'Score': ['95 %', '80 %', '90 %'],
        'Durée': ['5 min', '6 min', '4 min'],
        'Statut': ['Terminé', 'Terminé', 'Terminé']
    })
}

# Badges et objectifs communs pour simplifier
badges = ['⭐ Débutant', '🏅 Série de 5', '📚 Lecture active']
goals = ['✅ Faire 5 quiz sans abandonner', '✅ Passer 30 min sur la lecture']
alerts = ['⚠️ Tendance à abandonner en géométrie', '⚠️ Score en multiplication faible']

# --------------------------
# 🖼 2) Streamlit UI
# --------------------------

st.set_page_config(page_title="Dashboard Parent", layout="wide")
st.title("📊 Dashboard de suivi - Parent")

# --------------------------
# 🔧 Sélecteur d'enfant
# --------------------------
child_names = [child['Nom'] for child in children]
selected_child_name = st.selectbox("Choisir l'enfant :", child_names)

# Trouver l'enfant sélectionné
selected_child = next(child for child in children if child['Nom'] == selected_child_name)
child_id = selected_child['id']

# --------------------------
# 🔧 Sélecteur de matière
# --------------------------
all_subjects = ['Toutes'] + scores_subjects_data[child_id]['Matière'].tolist()
selected_subject = st.selectbox("Filtrer par matière :", all_subjects)

# --------------------------
# 🧩 Header avec infos
# --------------------------
st.subheader(f"Enfant : {selected_child['Nom']} | Âge : {selected_child['Âge']} ans | Classe : {selected_child['Classe']}")

# Bloc indicateurs principaux
st.markdown("### Vue d'ensemble")
summary = summary_data[child_id]
col1, col2, col3, col4 = st.columns(4)
col1.metric("✅ Taux de complétion", summary['Taux de complétion'])
col2.metric("🧠 Score moyen", summary['Score moyen'])
col3.metric("🕒 Temps total (semaine)", summary['Temps total cette semaine'])
col4.metric("🎯 Objectifs atteints", summary['Objectifs atteints'])

# --------------------------
# 📈 Evolution du score
# --------------------------
st.markdown("### Évolution du score moyen")
fig, ax = plt.subplots()
sns.lineplot(data=score_evolution_data[child_id], x='Semaine', y='Score moyen', marker='o', ax=ax)
ax.set_ylim(0, 100)
st.pyplot(fig)

# --------------------------
# 📊 Scores par matière
# --------------------------
st.markdown("### Forces et faiblesses (par matière)")
fig2, ax2 = plt.subplots()

# Filtrer si une matière est choisie
scores_df = scores_subjects_data[child_id]
if selected_subject != 'Toutes':
    scores_df = scores_df[scores_df['Matière'] == selected_subject]

sns.barplot(data=scores_df, y='Matière', x='Score', palette='pastel', ax=ax2)
ax2.set_xlim(0, 100)
st.pyplot(fig2)

# --------------------------
# 📋 Détails récents
# --------------------------
st.markdown("### Derniers quiz")

recent_df = recent_quiz_data[child_id]
if selected_subject != 'Toutes':
    recent_df = recent_df[recent_df['Sujet'] == selected_subject]

st.dataframe(recent_df, use_container_width=True)

# --------------------------
# 🏅 Badges et objectifs
# --------------------------
st.markdown("### Badges obtenus")
st.write(", ".join(badges))

st.markdown("### Objectifs de la semaine")
for goal in goals:
    st.write(goal)

# --------------------------
# ⚠️ Alertes / conseils
# --------------------------
st.markdown("### Alertes / points d’attention")
for alert in alerts:
    st.warning(alert)

st.markdown("---")
st.caption("📌 Prototype Streamlit interactif - à personnaliser selon vos besoins")
