import pandas as pd
import pingouin as pg

# Cargar datos
df = pd.read_csv('anova_2.csv')
## columnas (ID + 8 grupos)
df = df.iloc[:, 0:9]

nombres_cols = [
    'ID',
    'Base (M)', 'SinAdapt (M)', 'SinNorm (M)', 'SinAfec (M)',
    'Base (E)', 'SinAdapt (E)', 'SinNorm (E)', 'SinAfec (E)'
]
df.columns = nombres_cols

df = df.dropna()

df_long = df.melt(id_vars='ID',
                  var_name='Configuracion',
                  value_name='Score')

df_long['Score'] = pd.to_numeric(df_long['Score'])

#print(df_long)

# Ejecutar ANOVA de medidas repetidas
print("--- Resultados ANOVA ---")
anova = pg.rm_anova(dv='Score',
                    within='Configuracion',
                    subject='ID',
                    data=df_long,
                    detailed=True,
                    effsize='np2')
print(anova)

# Post-hoc con corrección de BONFERRONI
print("\n--- Resultados Post-hoc (Bonferroni) ---")
posthoc = pg.pairwise_tests(dv='Score',
                            within='Configuracion',
                            subject='ID',
                            data=df_long,
                            padjust='bonf',
                            effsize='hedges')

pd.set_option('display.max_rows', None)

group_means = df_long.groupby('Configuracion')['Score'].mean()
posthoc['mean(A)'] = posthoc['A'].map(group_means)
posthoc['mean(B)'] = posthoc['B'].map(group_means)

columns_to_print = ['A', 'B', 'mean(A)', 'mean(B)', 'p-unc', 'p-corr']
#columns_to_print = ['A', 'B', 'mean(A)', 'mean(B)', 'p-unc', 'p-corr', 'hedges']

print(posthoc[columns_to_print])