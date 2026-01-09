import pandas as pd
import pingouin as pg

# Cargar datos
df = pd.read_csv('anova.csv')

columnas_validas = [df.columns[0], 'Base', 'Sin adaptativo', 'Sin normativo', 'Sin afectivo']
df = df[columnas_validas].dropna()
df.rename(columns={df.columns[0]: 'Sujeto'}, inplace=True)

# Transformar a formato largo
df_long = df.melt(id_vars='Sujeto',
                  var_name='Configuracion',
                  value_name='Score')
df_long['Score'] = pd.to_numeric(df_long['Score'])

#print(df_long)

# Ejecutar ANOVA de medidas repetidas
print("--- Resultados ANOVA ---")
aov = pg.rm_anova(dv='Score',
                  within='Configuracion',
                  subject='Sujeto',
                  data=df_long,
                  detailed=True)
print(aov)

# Post-hoc con corrección de BONFERRONI
print("\n--- Resultados Post-hoc (Bonferroni) ---")
posthoc = pg.pairwise_tests(dv='Score',
                            within='Configuracion',
                            subject='Sujeto',
                            data=df_long,
                            padjust='bonf',
                            effsize='hedges')

print(posthoc[['A', 'B', 'T', 'p-unc', 'p-corr', 'hedges']])