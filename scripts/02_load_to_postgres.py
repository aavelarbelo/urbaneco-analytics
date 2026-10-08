import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path

import os
from dotenv import load_dotenv

load_dotenv()
# Credenciais lidas do ficheiro .env (ver .env.example); nunca escritas no código.
DATABASE_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"
)

ENERGY_MAP = {
    'A+':1.000,'A':0.875,'B':0.750,'B-':0.625,
    'C':0.500,'D':0.375,'E':0.250,'F':0.125
}

print("A carregar CSV...")
df = pd.read_csv("data/processed/supercasa_valid.csv", encoding="utf-8-sig")
print(f"  {len(df)} registos")

df['energy_score'] = df['energy_class'].map(ENERGY_MAP)

seg_stats = (
    df[df['segment_valid']==True]
    .groupby('segment')['price_m2']
    .median()
    .rename('median_price_m2')
)
df = df.merge(seg_stats, on='segment', how='left')

df['price_score'] = (1 - (df['price_m2']/df['median_price_m2']).clip(0,2)/2)

mask = df['energy_score'].notna() & df['price_score'].notna()
df.loc[mask,'evi_raw'] = (df.loc[mask,'energy_score']*0.55 + df.loc[mask,'price_score']*0.45)
df['evi_score'] = (df['evi_raw']*9+1).round(1).clip(1,10)

print(f"  EVI calculado: {df['evi_score'].notna().sum()} registos")
print(f"  EVI mediano: {df['evi_score'].median():.1f}")

cols = ['listing_url','scraped_at','price_type','municipality','parish',
        'title','property_type','typology','typology_clean','bedrooms',
        'price','area_m2','price_m2','energy_class','has_energy_class',
        'energy_score','price_score','evi_score','segment','segment_valid',
        'condition','has_garage','has_elevator','has_balcony','has_parking','page_number']

cols_ok = [c for c in cols if c in df.columns]
df_load = df[cols_ok].copy()

print("A ligar ao PostgreSQL...")
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    conn.execute(text("DELETE FROM fact_listings"))
    conn.commit()

df_load.to_sql('fact_listings', engine, if_exists='append', index=False, chunksize=200)

with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) FROM fact_listings")).fetchone()[0]
    print(f"Registos carregados: {n}")

out = Path("data/processed")
df.to_csv(out/"fact_listings.csv", index=False, encoding="utf-8-sig")

seg = df[df['segment_valid']==True].groupby(['segment','parish','typology_clean'])['price_m2'].agg(
    n_listings='count', median_price_m2='median',
    p25=lambda x:x.quantile(0.25), p75=lambda x:x.quantile(0.75)
).round(2).reset_index()
seg.to_csv(out/"segment_stats.csv", index=False, encoding="utf-8-sig")

top20 = df.nlargest(20,'evi_score')[['title','parish','typology_clean','price_m2','energy_class','evi_score','listing_url']]
top20.to_csv(out/"top20_evi.csv", index=False, encoding="utf-8-sig")

df['efficient'] = df['energy_class'].isin(['A+','A','B','B-'])
gap = df[df['energy_class'].notna()].groupby('parish').apply(lambda g: pd.Series({
    'n_total':len(g),
    'n_efficient':g['efficient'].sum(),
    'n_inefficient':(~g['efficient']).sum(),
    'gap_pct':round((~g['efficient']).sum()/len(g)*100,1)
})).reset_index()
gap.to_csv(out/"parish_energy_gap.csv", index=False, encoding="utf-8-sig")

print("")
print("=== CONCLUIDO ===")
print(f"fact_listings.csv")
print(f"segment_stats.csv  ({len(seg)} segmentos)")
print(f"top20_evi.csv")
print(f"parish_energy_gap.csv  ({len(gap)} freguesias)")
print("4 ficheiros prontos para Power BI!")
