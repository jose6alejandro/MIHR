import pandas as pd
import pingouin as pg

# Preparar datos
df = pd.read_csv('anova.csv')

df = df.iloc[:, 0:5].dropna()

nombres_cols = ['ID', 'Base', 'Sin_Adaptativo', 'Sin_Normativo', 'Sin_Afectivo']
df.columns = nombres_cols

df_long = df.melt(id_vars='ID',
                  var_name='Configuracion',
                  value_name='Score')

df_long['Score'] = pd.to_numeric(df_long['Score'])

print(f"Analisis de supuestos sobre {len(df)} muestras por configuración.")


# 1. SUPUESTO DE ESFERICIDAD (Mauchly)
print("\n" + "="*50)
print("1. PRUEBA DE ESFERICIDAD DE MAUCHLY")
print("="*50)

sphericity = pg.sphericity(df_long, dv='Score', subject='ID', within='Configuracion')
print(sphericity)

# Interpretación
p_mauchly = sphericity.pval
if p_mauchly > 0.05:
    print(f"\n>> RESULTADO: ✅ CUMPLE Esfericidad (p={p_mauchly:.4f} > .05).")
    print("Las varianzas de las diferencias son iguales.")
    #print("usar el valor p sin corrección ('p-unc').")
else:
    print(f"\n>> RESULTADO: ⚠️ NO CUMPLE Esfericidad (p={p_mauchly:.4f} < .05).")
    print("   Interpretación: Se violó el supuesto de esfericidad.")
    #print("usar el valor corregido 'p-GG-corr' (Greenhouse-Geisser).")


# 2. SUPUESTO DE NORMALIDAD (Shapiro-Wilk)
print("\n" + "="*50)
print("2. PRUEBA DE NORMALIDAD (Shapiro-Wilk)")
print("="*50)
normality = pg.normality(df_long, dv='Score', group='Configuracion')
print(normality)

# Revisión
grupos_con_error = normality[normality['pval'] < 0.05]

if grupos_con_error.empty:
    print("\n>> RESULTADO: Todos los grupos (Base, Sin Adapt, etc.) son normales.")
else:
    print(f"\n>> RESULTADO: Hay {len(grupos_con_error)} grupos que no son normales (p < .05).")