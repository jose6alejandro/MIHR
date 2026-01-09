import pandas as pd
import pingouin as pg
import matplotlib.pyplot as plt
import seaborn as sns

# Preparar datos
df = pd.read_csv('anova3.csv')

# Seleccionamos las columnas útiles (ID + 12 grupos)
df = df.iloc[:, 0:13].dropna()

# Renombramos para facilitar la lectura
nombres_cols = [
    'Sesion_ID',
    'E1_Base', 'E1_SinAdapt', 'E1_SinNorm', 'E1_SinAfec',
    'E2_Base', 'E2_SinAdapt', 'E2_SinNorm', 'E2_SinAfec',
    'E3_Base', 'E3_SinAdapt', 'E3_SinNorm', 'E3_SinAfec'
]
df.columns = nombres_cols

# Convertimos a formato largo
df_long = df.melt(id_vars='Sesion_ID', var_name='Grupo', value_name='Score')
df_long['Score'] = pd.to_numeric(df_long['Score'])

print(f"Analizando supuestos para {len(df)} muestras x 12 grupos.")

# ESFERICIDAD (Prueba de Mauchly)
print("\n" + "="*50)
print("1. TEST DE ESFERICIDAD DE MAUCHLY")
print("="*50)

sphericity = pg.sphericity(df_long, dv='Score', subject='Sesion_ID', within='Grupo')
print(sphericity)

# Interpretación automática
p_mauchly = sphericity.pval
if p_mauchly > 0.05:
    print(f"\n>> RESULTADO: CUMPLE Esfericidad (p={p_mauchly:.4f}).")
    #print("usar 'p-unc'.")
else:
    print(f"\n>> RESULTADO: NO CUMPLE Esfericidad (p={p_mauchly:.4f}).")
    #print("usar 'p-GG-corr' (Greenhouse-Geisser).")

# SUPUESTO DE NORMALIDAD (Shapiro-Wilk)
print("\n" + "="*50)
print("2. TEST DE NORMALIDAD (Shapiro-Wilk por Grupo)")
print("="*50)

normality = pg.normality(df_long, dv='Score', group='Grupo')
print(normality)

# Resumen
fallos = normality[normality['pval'] < 0.05]

if fallos.empty:
    print("\n>> RESULTADO: Todos los grupos son normales.")
else:
    print(f"\n>> RESULTADO: {len(fallos)} de 12 grupos no son normales.")
    print("   Detalle de los que fallaron:")
    print(fallos[['pval', 'normal']])
    #print("\n es robusto pero se reporta esto como limitación.")