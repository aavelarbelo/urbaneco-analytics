"""
UrbanEco Analytics — Pipeline de Calculo EVI
=============================================
ODS 11: Energy Efficiency Profitability in Porto's Real Estate Market

Autor: Andressa Belo (coordenacao tecnica e analitica)
Data:  Junho 2026

O que este script faz:
    1. Le o dataset de scraping (Excel ou CSV)
    2. Limpa e normaliza os dados
    3. Calcula price_m2, energy_score, price_score e evi_score
    4. Exporta 4 CSVs prontos para Power BI
    5. (Opcional) Carrega na base de dados PostgreSQL

Outputs:
    data/processed/fact_listings_final.csv
    data/processed/segment_stats_final.csv
    data/processed/top20_evi_final.csv
    data/processed/parish_energy_gap_final.csv

Instalacao:
    pip install pandas sqlalchemy psycopg2-binary python-dotenv openpyxl

Uso:
    python scripts/calcular_evi.py
"""

import os
import re
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────
# Configuracao
# ─────────────────────────────────────────────────────────────────────

# Caminho para o dataset do scraping
# Aceita .xlsx ou .csv
INPUT_PATH = Path("data/raw/DataSet_Scraping_FINAL.xlsx")

OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Mapeamento de classe energetica para score numerico
# A+ = mais eficiente (1.0), F = menos eficiente (0.125)
ENERGY_MAP = {
    "A+": 1.000,
    "A":  0.875,
    "B":  0.750,
    "B-": 0.625,
    "C":  0.500,
    "D":  0.375,
    "E":  0.250,
    "F":  0.125,
}

# Apenas classes validas do sistema SCE/ADENE Portugal
VALID_ENERGY_CLASSES = set(ENERGY_MAP.keys())

# Filtro de sanidade para price_m2
PRICE_M2_MIN = 500
PRICE_M2_MAX = 25_000

# Amostra minima por segmento para calculos estatisticos
MIN_SEGMENT_SIZE = 3


# ─────────────────────────────────────────────────────────────────────
# 1. Leitura do dataset
# ─────────────────────────────────────────────────────────────────────

def load_dataset(path: Path) -> pd.DataFrame:
    print(f"\n[1/6] A ler dataset: {path}")

    if path.suffix == ".xlsx":
        df = pd.read_excel(path)
    elif path.suffix == ".csv":
        df = pd.read_csv(path, encoding="utf-8-sig")
    else:
        raise ValueError(f"Formato nao suportado: {path.suffix}")

    print(f"      Shape inicial: {df.shape}")
    print(f"      Colunas: {list(df.columns)}")
    return df


# ─────────────────────────────────────────────────────────────────────
# 2. Limpeza e normalizacao
# ─────────────────────────────────────────────────────────────────────

def clean_price(value) -> float | None:
    """Converte preco de texto para float. Ex: '350.000 €' -> 350000.0"""
    if pd.isna(value):
        return None
    try:
        clean = str(value).replace(".", "").replace(",", "").replace("€", "").strip()
        return float(re.sub(r"[^\d.]", "", clean))
    except (ValueError, TypeError):
        return None


def clean_area(value) -> float | None:
    """Converte area de texto para float. Ex: '85 m²' -> 85.0"""
    if pd.isna(value):
        return None
    try:
        clean = str(value).replace("m²", "").replace(",", ".").strip()
        return float(re.sub(r"[^\d.]", "", clean))
    except (ValueError, TypeError):
        return None


def clean_typology(value: str | None) -> str | None:
    """Normaliza tipologia para T0-T5. Ex: 'T2+' -> 'T2'"""
    if not value or pd.isna(value):
        return None
    match = re.match(r"T([0-5])", str(value).upper().strip())
    return f"T{match.group(1)}" if match else None


def clean_energy_class(value) -> str | None:
    """Normaliza classe energetica. Rejeita I, G e outros invalidos."""
    if pd.isna(value):
        return None
    candidate = str(value).upper().strip()
    return candidate if candidate in VALID_ENERGY_CLASSES else None


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[2/6] A limpar e normalizar...")

    # Detectar nomes de colunas (dataset pode ter variantes)
    col_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if "pre" in col_lower and "o" in col_lower:
            col_map["preco"] = col
        elif "area" in col_lower and ("util" in col_lower or "tl" in col_lower):
            col_map["area_util"] = col
        elif "area" in col_lower and "brut" in col_lower:
            col_map["area_bruta"] = col
        elif "tipolog" in col_lower:
            col_map["tipologia"] = col
        elif "fregu" in col_lower or "parish" in col_lower:
            col_map["freguesia"] = col
        elif "certif" in col_lower or "energ" in col_lower or "class" in col_lower:
            col_map["classe_energetica"] = col
        elif "url" in col_lower:
            col_map["url"] = col
        elif "garag" in col_lower:
            col_map["garagem"] = col
        elif "elevad" in col_lower:
            col_map["elevador"] = col
        elif "estado" in col_lower:
            col_map["estado"] = col

    print(f"      Mapeamento de colunas: {col_map}")

    out = pd.DataFrame()

    # Preco
    if "preco" in col_map:
        out["preco"] = df[col_map["preco"]].apply(clean_price)

    # Area util -> area bruta como fallback
    if "area_util" in col_map:
        out["area_util"] = df[col_map["area_util"]].apply(clean_area)
    if "area_bruta" in col_map:
        out["area_bruta"] = df[col_map["area_bruta"]].apply(clean_area)

    out["area_final"] = out.get("area_util", pd.Series(dtype=float)).fillna(
        out.get("area_bruta", pd.Series(dtype=float))
    )

    # Tipologia
    if "tipologia" in col_map:
        out["tipologia_clean"] = df[col_map["tipologia"]].apply(
            lambda x: clean_typology(str(x) if not pd.isna(x) else None)
        )

    # Freguesia
    if "freguesia" in col_map:
        out["freguesia"] = df[col_map["freguesia"]].astype(str).str.strip()

    # Classe energetica
    if "classe_energetica" in col_map:
        out["classe_energetica"] = df[col_map["classe_energetica"]].apply(clean_energy_class)

    # Campos opcionais
    for field in ["url", "garagem", "elevador", "estado"]:
        if field in col_map:
            out[field] = df[col_map[field]]

    # Remover duplicados
    if "url" in out.columns:
        before = len(out)
        out = out.drop_duplicates(subset=["url"])
        print(f"      Duplicados removidos: {before - len(out)}")

    # Calcular price_m2
    out["price_m2"] = (out["preco"] / out["area_final"]).round(2)

    # Filtrar outliers
    before = len(out)
    out = out[
        out["price_m2"].between(PRICE_M2_MIN, PRICE_M2_MAX) &
        out["preco"].notna() &
        out["area_final"].notna() &
        (out["area_final"] > 0)
    ].copy()
    print(f"      Registos apos limpeza: {len(out)} (removidos {before - len(out)} outliers)")

    return out


# ─────────────────────────────────────────────────────────────────────
# 3. Segmentacao
# ─────────────────────────────────────────────────────────────────────

def create_segments(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[3/6] A criar segmentos (freguesia x tipologia)...")

    df["segment"] = (
        df["freguesia"].fillna("DESCONHECIDA") + " | " +
        df["tipologia_clean"].fillna("SEM_TIPO")
    )

    seg_counts = df.groupby("segment")["price_m2"].count()
    valid_segs = seg_counts[seg_counts >= MIN_SEGMENT_SIZE].index
    df["segment_valid"] = df["segment"].isin(valid_segs)

    print(f"      Segmentos validos (n>={MIN_SEGMENT_SIZE}): {df['segment_valid'].sum()} imoveis")
    print(f"      Segmentos invalidos: {(~df['segment_valid']).sum()} imoveis")

    return df


# ─────────────────────────────────────────────────────────────────────
# 4. Calculo do EVI
# ─────────────────────────────────────────────────────────────────────

def calculate_evi(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[4/6] A calcular EVI...")

    # Energy Score: mapeamento directo da classe energetica
    df["energy_score"] = df["classe_energetica"].map(ENERGY_MAP)
    print(f"      Energy Score calculado: {df['energy_score'].notna().sum()} imoveis")

    # Mediana por segmento (NUNCA media — regra do projeto)
    seg_median = (
        df[df["segment_valid"]]
        .groupby("segment")["price_m2"]
        .median()
        .rename("median_price_m2")
    )
    df = df.merge(seg_median, on="segment", how="left")

    # Price Score: competitividade do preco face a mediana do segmento
    # 0 = muito caro, 1 = muito competitivo
    df["price_score"] = (
        1 - (df["price_m2"] / df["median_price_m2"]).clip(0, 2) / 2
    )

    # EVI Final: escala 1-10
    # Pesos: 55% eficiencia energetica + 45% competitividade de preco
    mask = df["energy_score"].notna() & df["price_score"].notna()

    df.loc[mask, "evi_raw"] = (
        df.loc[mask, "energy_score"] * 0.55 +
        df.loc[mask, "price_score"]  * 0.45
    )
    df["evi_score"] = (df["evi_raw"] * 9 + 1).round(1).clip(1, 10)

    n_evi = df["evi_score"].notna().sum()
    print(f"      EVI calculado: {n_evi} imoveis")
    print(f"      EVI mediano: {df['evi_score'].median():.1f}")
    print(f"      EVI maximo: {df['evi_score'].max():.1f}")

    return df


# ─────────────────────────────────────────────────────────────────────
# 5. Exportar 4 CSVs para Power BI
# ─────────────────────────────────────────────────────────────────────

def export_csvs(df: pd.DataFrame) -> None:
    print("\n[5/6] A exportar CSVs para Power BI...")

    # 1. fact_listings — todos os imoveis com metricas
    df.to_csv(
        OUTPUT_DIR / "fact_listings_final.csv",
        index=False, encoding="utf-8-sig"
    )
    print(f"      fact_listings_final.csv ({len(df)} linhas)")

    # 2. segment_stats — Eixo 1: mediana + P25/P75 por segmento
    seg = (
        df[df["segment_valid"]]
        .groupby(["segment", "freguesia", "tipologia_clean"])["price_m2"]
        .agg(
            n_listings="count",
            median_price_m2="median",
            p25=lambda x: x.quantile(0.25),
            p75=lambda x: x.quantile(0.75),
        )
        .round(2)
        .reset_index()
    )
    seg.to_csv(
        OUTPUT_DIR / "segment_stats_final.csv",
        index=False, encoding="utf-8-sig"
    )
    print(f"      segment_stats_final.csv ({len(seg)} segmentos)")

    # 3. top20_evi — Eixo 3: Top 20 imoveis por EVI
    cols_top20 = ["freguesia", "tipologia_clean", "price_m2",
                  "classe_energetica", "evi_score"]
    if "url" in df.columns:
        cols_top20.append("url")

    top20 = df.nlargest(20, "evi_score")[cols_top20]
    top20.to_csv(
        OUTPUT_DIR / "top20_evi_final.csv",
        index=False, encoding="utf-8-sig"
    )
    print(f"      top20_evi_final.csv (Top 20, EVI {top20['evi_score'].min():.1f}-{top20['evi_score'].max():.1f})")

    # 4. parish_energy_gap — Eixo 4: racio ineficiente por freguesia
    df["efficient"] = df["classe_energetica"].isin(["A+", "A", "B", "B-"])
    gap = (
        df[df["classe_energetica"].notna()]
        .groupby("freguesia")
        .apply(lambda g: pd.Series({
            "n_total":       len(g),
            "n_efficient":   g["efficient"].sum(),
            "n_inefficient": (~g["efficient"]).sum(),
            "gap_pct":       round((~g["efficient"]).sum() / len(g) * 100, 1),
        }))
        .reset_index()
        .sort_values("gap_pct", ascending=False)
    )
    gap.to_csv(
        OUTPUT_DIR / "parish_energy_gap_final.csv",
        index=False, encoding="utf-8-sig"
    )
    print(f"      parish_energy_gap_final.csv ({len(gap)} freguesias)")
    print(f"\n      Gap mais alto: {gap.iloc[0]['freguesia']} — {gap.iloc[0]['gap_pct']}% ineficiente")

    print(f"\n      Todos os ficheiros em: {OUTPUT_DIR.resolve()}")


# ─────────────────────────────────────────────────────────────────────
# 6. (Opcional) Carregar no PostgreSQL Aiven
# ─────────────────────────────────────────────────────────────────────

def load_to_aiven(df: pd.DataFrame) -> None:
    """
    Carrega fact_listings na base de dados Aiven.
    Requer variaveis de ambiente no ficheiro .env:

        DB_HOST=urbanecoproject-urbaneco.b.aivencloud.com
        DB_PORT=26021
        DB_NAME=defaultdb
        DB_USER=avnadmin
        DB_PASSWORD=<password>
        DB_SSL=require
    """
    try:
        from sqlalchemy import create_engine, text
    except ImportError:
        print("      sqlalchemy nao instalado. Corre: pip install sqlalchemy psycopg2-binary")
        return

    host     = os.getenv("DB_HOST")
    port     = os.getenv("DB_PORT", "26021")
    name     = os.getenv("DB_NAME", "defaultdb")
    user     = os.getenv("DB_USER", "avnadmin")
    password = os.getenv("DB_PASSWORD")

    if not all([host, password]):
        print("      Variaveis DB_HOST e DB_PASSWORD nao definidas no .env — a saltar carga no Aiven.")
        return

    url = f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode=require"

    print(f"\n[6/6] A carregar no Aiven PostgreSQL...")
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("      Ligacao Aiven: OK")

        cols = ["freguesia", "tipologia_clean", "price_m2", "preco", "area_final",
                "classe_energetica", "energy_score", "price_score", "evi_score",
                "segment", "segment_valid"]
        if "url" in df.columns:
            cols.append("url")

        df_load = df[[c for c in cols if c in df.columns]].copy()
        df_load.to_sql(
            "fact_listings_evi",
            engine,
            if_exists="replace",
            index=False,
            chunksize=200,
        )

        with engine.connect() as conn:
            n = conn.execute(text("SELECT COUNT(*) FROM fact_listings_evi")).fetchone()[0]
        print(f"      Registos carregados em fact_listings_evi: {n}")

    except Exception as e:
        print(f"      Erro ao ligar ao Aiven: {e}")
        print("      Os CSVs foram exportados com sucesso — Power BI funciona sem ligacao ao Aiven.")


# ─────────────────────────────────────────────────────────────────────
# Execucao principal
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("UrbanEco Analytics — Pipeline EVI")
    print("ODS 11 · ISEP Big Data 2026")
    print("Todos os precos sao asking prices")
    print("=" * 60)

    df = load_dataset(INPUT_PATH)
    df = clean_dataset(df)
    df = create_segments(df)
    df = calculate_evi(df)
    export_csvs(df)

    # Descomentar para carregar no Aiven:
    # load_to_aiven(df)

    print("\n" + "=" * 60)
    print("PIPELINE CONCLUIDO")
    print(f"Imoveis processados : {len(df)}")
    print(f"Com EVI calculado   : {df['evi_score'].notna().sum()}")
    print(f"EVI mediano         : {df['evi_score'].median():.1f}")
    print(f"4 CSVs exportados   : {OUTPUT_DIR.resolve()}")
    print("=" * 60)
