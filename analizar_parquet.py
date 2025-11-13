import pandas as pd

df = pd.read_parquet('data/processed/dataset_forecasting_completo.parquet')

print("="*80)
print("ANÁLISIS DEL PARQUET")
print("="*80)

print(f"\nColumnas ({len(df.columns)}):")
for col in df.columns:
    print(f"  - {col}")

print(f"\n\nShape: {df.shape}")
print(f"\nPrimeras 3 filas:")
print(df.head(3))

print(f"\n\n" + "="*80)
print("VALORES NO NULOS POR COLUMNA")
print("="*80)

for col in df.columns:
    n_valores = df[col].notna().sum()
    total = len(df)
    pct = (n_valores / total) * 100
    print(f"{col:40} : {n_valores:3}/{total:3} ({pct:6.1f}%)")
