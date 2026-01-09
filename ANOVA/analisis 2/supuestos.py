import pandas as pd
import pingouin as pg

# Preparar datos
df = pd.read_csv('anova_2.csv')

df = df.iloc[:, 0:9].dropna()

nombres_cols = [
    'ID',
    'Base_M', 'SinAdapt_M', 'SinNorm_M', 'SinAfec_M',
    'Base_E', 'SinAdapt_E', 'SinNorm_E', 'SinAfec_E'
]
df.columns = nombres_cols

df_long = df.melt(id_vars='ID', var_name='Grupo', value_name='Score')
df_long['Score'] = pd.to_numeric(df_long['Score'])

print(f"Datos procesados: {len(df)} sujetos x 8 condiciones.")


# ESFERICIDAD (Prueba de Mauchly)
print("\n" + "="*50)
print("1. ESFERICIDAD (Prueba de Mauchly)")
print("="*50)

sphericity = pg.sphericity(df_long, dv='Score', subject='ID', within='Grupo')
print(sphericity)

# Interpretación
p_mauchly = sphericity.pval
if p_mauchly > 0.05:
    print(f"\n>> RESULTADO: CUMPLE Esfericidad (p={p_mauchly:.4f} > .05).")
    #print("reportar el valor 'p-unc'.")
else:
    print(f"\n>> RESULTADO: NO CUMPLE Esfericidad (p={p_mauchly:.4f} < .05).")
    #print("reportar el valor 'p-GG-corr' (Greenhouse-Geisser).")

# SUPUESTO DE NORMALIDAD (Shapiro-Wilk)
print("\n" + "="*50)
print("2. NORMALIDAD (Shapiro-Wilk por Grupo)")
print("="*50)

normality = pg.normality(df_long, dv='Score', group='Grupo')
print(normality)

# Resumen
grupos_no_normales = normality[normality['pval'] < 0.05]

if grupos_no_normales.empty:
    print("\n>> RESULTADO: Todos los grupos tienen distribución normal (p > .05).")
else:
    print(f"\n>> RESULTADO: Se detectaron desviaciones en {len(grupos_no_normales)} grupos:")
    print(grupos_no_normales[['pval', 'normal']])