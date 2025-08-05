import pandas as pd

def analyze_weaknesses_by_chapter(df):
    # Step 1️⃣ : stats moyennes par enfant et chapter
    child_chapter_stats = df.groupby(['child_id', 'chapter']).agg({
        'final_score':'mean',
        'time_spent':'mean',
        'attempts_count':'mean',
        'quiz_id':'nunique'
    }).reset_index().rename(columns={
        'final_score':'avg_success_rate',
        'time_spent':'avg_time_spent',
        'attempts_count':'avg_attempts',
        'quiz_id':'num_unique_quizzes'
    })

    # Step 2️⃣ : stats globales par enfant
    child_avg_stats = df.groupby('child_id').agg({
        'final_score':'mean',
        'time_spent':'mean',
        'quiz_id':'nunique'
    }).reset_index().rename(columns={
        'final_score':'child_avg_success_rate',
        'time_spent':'child_avg_time_spent',
        'quiz_id':'total_unique_quizzes'
    })

    # Step 3️⃣ : moyennes du groupe par chapter
    group_chapter_avg = df.groupby('chapter').agg({
        'final_score':'mean',
        'time_spent':'mean',
        'quiz_id':'nunique'
    }).reset_index().rename(columns={
        'final_score':'group_avg_success_rate',
        'time_spent':'group_avg_time_spent',
        'quiz_id':'group_num_quizzes'
    })

    
    # Step 4️⃣ : fusionner
    merged = child_chapter_stats.merge(child_avg_stats, on='child_id')
    merged = merged.merge(group_chapter_avg, on='chapter')

    # Step 5️⃣ : détecter les faiblesses
    def flag_weaknesses(row):
        weaknesses = []
        if row['avg_success_rate'] < row['group_avg_success_rate'] * 0.65:
            weaknesses.append('low_accuracy')
        if row['avg_time_spent'] > row['group_avg_time_spent'] * 1.2:
            weaknesses.append('slow_processing')
        if (row['avg_time_spent'] < row['group_avg_time_spent'] * 1.2 and
            row['avg_success_rate'] < row['group_avg_success_rate'] * 0.5):
            weaknesses.append('impulsive')
        if row['num_unique_quizzes'] < row['group_num_quizzes'] * 0.5:
            weaknesses.append('low_practice')
        return weaknesses if weaknesses else ['no_weakness']

    merged['weaknesses'] = merged.apply(flag_weaknesses, axis=1)

    # Step 6️⃣ : construire le profil global
    skill_profiles = {}
    for child_id, group in merged.groupby('child_id'):
        profile = {
            'chapters': {},
            'global_stats': {
                'avg_success_rate': round(group['child_avg_success_rate'].iloc[0], 2),
                'avg_time_spent': round(group['child_avg_time_spent'].iloc[0], 2),
                'total_unique_quizzes': int(group['total_unique_quizzes'].iloc[0])
            }
        }
        for _, row in group.iterrows():
            profile['chapters'][row['chapter']] = {
                'attempts': round(row['avg_attempts'], 2),
                'final_score': round(row['avg_success_rate'], 2),
                'avg_time_spent': round(row['avg_time_spent'], 2),
                'weaknesses': row['weaknesses']
            }
        skill_profiles[child_id] = profile

    return merged, skill_profiles
