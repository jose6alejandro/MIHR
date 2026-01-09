import pandas as pd
import pingouin as pg

# Preparar datos
df = pd.read_csv('anova3.csv')

df = df.iloc[:, 0:13].dropna()

# E1 = Estudiante 1, E2 = Estudiante 2, E3 = Estudiante 3
nombres_cols = [
    'Sesion_ID',
    'E1_Base', 'E1_SinAdapt', 'E1_SinNorm', 'E1_SinAfec',
    'E2_Base', 'E2_SinAdapt', 'E2_SinNorm', 'E2_SinAfec',
    'E3_Base', 'E3_SinAdapt', 'E3_SinNorm', 'E3_SinAfec'
]
df.columns = nombres_cols

df_long = df.melt(id_vars='Sesion_ID',
                  var_name='Grupo',
                  value_name='Score')

df_long['Score'] = pd.to_numeric(df_long['Score'])

#print(df_long)

#print(f"Total de observaciones: {len(df_long)} (10 sesiones x 12 grupos)")

# 1. ANOVA DE MEDIDAS REPETIDAS (Una Vía)
print("\n" + "="*80)
print("TABLA ANOVA (12 GRUPOS)")
print("="*80)

anova = pg.rm_anova(dv='Score',
                    within='Grupo',
                    subject='Sesion_ID',
                    data=df_long,
                    detailed=True,
                    effsize='np2')
print(anova)

# 2. POST-HOC: TODAS LAS COMPARACIONES (BONFERRONI)
print("\n" + "="*80)
print("POST-HOC COMPLETO (TODAS LAS COMBINACIONES)")
print("="*80)

# Hay 66 comparaciones
posthoc = pg.pairwise_tests(dv='Score',
                            within='Grupo',
                            subject='Sesion_ID',
                            data=df_long,
                            padjust='bonf',
                            effsize='hedges')

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

group_means = df_long.groupby('Grupo')['Score'].mean()
posthoc['mean(A)'] = posthoc['A'].map(group_means)
posthoc['mean(B)'] = posthoc['B'].map(group_means)

print(posthoc[['A', 'B', 'mean(A)', 'mean(B)', 'p-unc', 'p-corr', 'hedges']].sort_values('p-corr'))