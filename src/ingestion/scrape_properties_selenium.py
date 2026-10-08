"""
SuperCasa Selenium scraper — UrbanEco Analytics
================================================
ODS 11: Energy Efficiency Profitability in Porto's Real Estate Market

Outputs:
    data/raw/supercasa_raw.csv
    data/processed/supercasa_valid.csv
"""

import re
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from webdriver_manager.chrome import ChromeDriverManager


# ─────────────────────────────────────────────────────────────────────
# Project paths
# ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_OUTPUT_PATH   = PROJECT_ROOT / "data" / "raw"       / "supercasa_raw.csv"
VALID_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "supercasa_valid.csv"


# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

SOURCE = "SuperCasa"

MAIN_TARGET_VALID_LISTINGS        = 5_000
MINIMUM_ACCEPTABLE_VALID_LISTINGS = 4_000
IDEAL_MIN_VALID_LISTINGS          = 5_000
IDEAL_MAX_VALID_LISTINGS          = 7_000

MAX_PAGES = 2

# Confirmed via browser inspector on /comprar-casas/porto/com-novo:
# div.list__properties > div.list__properties-main > article.property-card
CARDS_CONTAINER_SELECTOR = "div.list__properties-main"
PROPERTY_CARD_SELECTOR   = "article.property-card"

# Real URLs confirmed from SuperCasa browser filter
CONDITION_URLS = {
    "novo":           "https://supercasa.pt/comprar-casas/porto/com-novo",
    "usado":          "https://supercasa.pt/comprar-casas/porto/com-bom-estado",
    "para_recuperar": "https://supercasa.pt/comprar-casas/porto/com-para-reformar",
    "em_construcao":  "https://supercasa.pt/comprar-casas/porto/com-em-construcao",
}

# Porto parishes
PORTO_PARISHES = [
    "Bonfim", "Campanhã", "Cedofeita", "Lordelo do Ouro",
    "Massarelos", "Paranhos", "Ramalde", "Santo Ildefonso",
    "São Nicolau", "Sé", "Vitória", "Aldoar", "Foz do Douro",
    "Nevogilde",
]

VALID_ENERGY_CLASSES = {"A+", "A", "B", "B-", "C", "D", "E", "F"}


# ─────────────────────────────────────────────────────────────────────
# Selenium setup
# ─────────────────────────────────────────────────────────────────────

def create_driver(headless: bool = False) -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument(r"--user-data-dir=C:\selenium-supercasa-profile")
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


# ─────────────────────────────────────────────────────────────────────
# Safe element helpers
# ─────────────────────────────────────────────────────────────────────

def get_text_safe(parent, selector: str) -> str | None:
    try:
        el   = parent.find_element(By.CSS_SELECTOR, selector)
        text = el.text.strip()
        return text if text else None
    except Exception:
        return None


def get_attribute_safe(parent, selector: str, attribute: str) -> str | None:
    try:
        el    = parent.find_element(By.CSS_SELECTOR, selector)
        value = el.get_attribute(attribute)
        return value if value else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────
# Field extractors
# ─────────────────────────────────────────────────────────────────────

def extract_price_numeric(card) -> float | None:
    """
    Price lives in div.property-card__price
    Example text: "355.000 €"
    """
    price_text = get_text_safe(card, "div.property-card__price")
    if not price_text:
        return None
    # Remove €, spaces, dots (thousands separator)
    clean = re.sub(r"[€\s\.]", "", price_text)
    clean = clean.replace(",", ".")
    match = re.search(r"\d{4,}", clean)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None
    return None


def extract_area_m2(card, full_text: str) -> float | None:
    """Area in m² — try dedicated selector first, fallback to full text."""
    area_text = get_text_safe(card, "[class*='area']") or full_text
    if not area_text:
        return None
    match = re.search(r"(\d+[,.]?\d*)\s*m²", area_text, re.IGNORECASE)
    if match:
        try:
            v = float(match.group(1).replace(",", "."))
            # Sanity check: area between 10 and 2000 m²
            return v if 10 <= v <= 2000 else None
        except ValueError:
            return None
    return None


def calculate_price_m2(price: float | None, area_m2: float | None) -> float | None:
    if price and area_m2 and area_m2 > 0:
        v = round(price / area_m2, 2)
        # Sanity check: €/m² between 500 and 25000
        return v if 500 <= v <= 25_000 else None
    return None


def extract_typology(full_text: str) -> str | None:
    if not full_text:
        return None
    match = re.search(r"\bT([0-9]\+?)\b", full_text, re.IGNORECASE)
    if match:
        return f"T{match.group(1).upper()}"
    return None


def extract_bedrooms(typology: str | None) -> int | None:
    if not typology:
        return None
    match = re.search(r"T(\d)", typology)
    return int(match.group(1)) if match else None


def extract_property_type(full_text: str) -> str | None:
    if not full_text:
        return None
    lowered = full_text.lower()
    if any(w in lowered for w in ["apartamento", "flat", "duplex", "estudio"]):
        return "Apartamento"
    if any(w in lowered for w in ["moradia", "vivenda", "villa"]):
        return "Moradia"
    return None


def extract_parish(full_text: str) -> str | None:
    if not full_text:
        return None
    text_lower = full_text.lower()
    for parish in PORTO_PARISHES:
        if parish.lower() in text_lower:
            return parish
    return None


def extract_listing_url(card) -> str | None:
    """URL from div.property-card__title a — confirmed via inspector."""
    url = get_attribute_safe(card, "div.property-card__title a", "href")
    if not url:
        url = get_attribute_safe(card, "a", "href")
    if url and url.startswith("/"):
        url = "https://supercasa.pt" + url
    return url


def extract_title(card) -> str | None:
    """Title from div.property-card__title a — confirmed via inspector."""
    return get_text_safe(card, "div.property-card__title a")


def extract_energy_class(card, full_text: str) -> str | None:
    for selector in ["[class*='energy']", "[class*='energet']",
                     "[class*='certificado']", ".energy-badge", "span[data-energy]"]:
        try:
            for el in card.find_elements(By.CSS_SELECTOR, selector):
                text = el.text.strip().upper()
                if text in VALID_ENERGY_CLASSES:
                    return text
        except Exception:
            continue
    if full_text:
        match = re.search(r"\b(A\+|A|B-|B|C|D|E|F)\b", full_text, re.IGNORECASE)
        if match:
            candidate = match.group(1).upper()
            if candidate in VALID_ENERGY_CLASSES:
                return candidate
    return None


def extract_extras(full_text: str) -> dict:
    lowered = full_text.lower() if full_text else ""
    return {
        "has_garage":   any(w in lowered for w in ["garagem", "garage"]),
        "has_elevator": any(w in lowered for w in ["elevador", "elevator"]),
        "has_balcony":  any(w in lowered for w in ["varanda", "terraço", "balcony"]),
        "has_parking":  any(w in lowered for w in ["estacionamento", "parking"]),
    }


# ─────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────

def is_valid_residential_sale(p: dict) -> bool:
    if not p.get("source"):      return False
    if not p.get("listing_url"): return False
    if not p.get("scraped_at"):  return False
    if not p.get("price_m2") or p["price_m2"] <= 0: return False
    if not p.get("parish"):      return False
    if p.get("property_type") not in ["Apartamento", "Moradia"]: return False
    return True


def has_energy_class(p: dict) -> bool:
    return bool(p.get("energy_class"))


# ─────────────────────────────────────────────────────────────────────
# URL builder — confirmed pagination format for /com-xxx/ URLs
# Page 1: /com-novo
# Page 2: /com-novo?pagina=2
# ─────────────────────────────────────────────────────────────────────

def build_page_url(base_url: str, page_number: int) -> str:
    if page_number == 1:
        return base_url
    return f"{base_url}?pagina={page_number}"


# ─────────────────────────────────────────────────────────────────────
# Per-condition scraping pass
# ─────────────────────────────────────────────────────────────────────

def scrape_condition(driver, condition_key: str, base_url: str,
                     scraped_at: str) -> list[dict]:
    properties = []
    wait = WebDriverWait(driver, 120)

    print(f"\n{'='*70}")
    print(f"CONDITION : {condition_key}")
    print(f"URL       : {base_url}")
    print(f"{'='*70}")

    for page_number in range(1, MAX_PAGES + 1):
        target_url = build_page_url(base_url, page_number)
        print(f"\n  [Page {page_number}] {target_url}")
        driver.get(target_url)
        print("  URL REAL:", driver.current_url)
        print("  TITLE:", driver.title)
        print("  ARTICLES:", len(driver.find_elements(By.TAG_NAME, "article")))
        print("  DIVS:", len(driver.find_elements(By.TAG_NAME, "div")))

        # Wait for the cards container — confirmed selector from inspector
        try:
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, CARDS_CONTAINER_SELECTOR)
            ))
            # Extra wait for JS to finish rendering cards
            time.sleep(2)
        except TimeoutException:
            print("  Cards container not found — stopping this condition.")
            break

        # Find all cards inside the container
        try:
            container = driver.find_element(By.CSS_SELECTOR, CARDS_CONTAINER_SELECTOR)
            property_cards = container.find_elements(By.CSS_SELECTOR, PROPERTY_CARD_SELECTOR)
        except Exception:
            property_cards = []

        print(f"  Cards found: {len(property_cards)}")

        if len(property_cards) == 0:
            print("  Empty page — stopping this condition.")
            break

        for card in property_cards:
            full_text = card.text.strip()

            listing_url   = extract_listing_url(card)
            title         = extract_title(card)
            property_type = extract_property_type(full_text)
            typology      = extract_typology(full_text)
            bedrooms      = extract_bedrooms(typology)
            parish        = extract_parish(full_text)
            price_raw     = extract_price_numeric(card)
            area_m2       = extract_area_m2(card, full_text)
            price_m2      = calculate_price_m2(price_raw, area_m2)
            energy_class  = extract_energy_class(card, full_text)
            extras        = extract_extras(full_text)

            property_data = {
                "source":            SOURCE,
                "listing_url":       listing_url,
                "scraped_at":        scraped_at,
                "page_number":       page_number,
                "price_type":        "asking_price",
                "municipality":      "Porto",
                "parish":            parish,
                "title":             title,
                "property_type":     property_type,
                "typology":          typology,
                "bedrooms":          bedrooms,
                "price_m2":          price_m2,
                "price":             price_raw,
                "area_m2":           area_m2,
                "energy_class":      energy_class,
                "condition":         condition_key,
                "has_garage":        extras["has_garage"],
                "has_elevator":      extras["has_elevator"],
                "has_balcony":       extras["has_balcony"],
                "has_parking":       extras["has_parking"],
                "construction_year": None,
                "floor":             None,
                "bathrooms":         None,
            }

            property_data["is_valid"]         = is_valid_residential_sale(property_data)
            property_data["has_energy_class"] = has_energy_class(property_data)

            properties.append(property_data)

        valid_so_far = sum(p["is_valid"] for p in properties)
        print(f"  Collected: {len(properties)} raw / {valid_so_far} valid")

    return properties


# ─────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────

def scrape_properties() -> list[dict]:
    scraped_at     = datetime.now().isoformat(timespec="seconds")
    all_properties = []

    driver = create_driver(headless=False)

    try:
        for condition_key, base_url in CONDITION_URLS.items():
            condition_properties = scrape_condition(
                driver, condition_key, base_url, scraped_at
            )
            all_properties.extend(condition_properties)

            valid_total = sum(p["is_valid"] for p in all_properties)
            print(f"\n  -- Total acumulado: {len(all_properties)} raw / {valid_total} valid --")

            if valid_total >= MAIN_TARGET_VALID_LISTINGS:
                print("  Objectivo atingido — a parar.")
                break

    except WebDriverException as err:
        print(f"WebDriver error: {err}")
    except Exception as err:
        print(f"Unexpected error: {err}")
    finally:
        driver.quit()

    return all_properties


# ─────────────────────────────────────────────────────────────────────
# Save outputs
# ─────────────────────────────────────────────────────────────────────

def save_data(properties: list[dict]) -> None:
    RAW_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    VALID_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(properties)

    before = len(df)
    df = df.drop_duplicates(subset=["listing_url"], keep="first")
    after  = len(df)
    if before != after:
        print(f"  Deduplicados: {before - after} removidos.")

    column_order = [
        "source", "listing_url", "scraped_at", "page_number", "price_type",
        "municipality", "parish",
        "title", "property_type", "typology", "bedrooms",
        "price_m2", "price", "area_m2",
        "energy_class", "condition",
        "has_garage", "has_elevator", "has_balcony", "has_parking",
        "construction_year", "floor", "bathrooms",
        "is_valid", "has_energy_class",
    ]
    existing_cols = [c for c in column_order if c in df.columns]
    df = df[existing_cols]

    df.to_csv(RAW_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    valid_df = df[df["is_valid"]].copy()
    valid_df.to_csv(VALID_OUTPUT_PATH, index=False, encoding="utf-8-sig")

    with_energy = valid_df["has_energy_class"].sum()

    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)
    print(f"  Raw recolhidos                : {len(df)}")
    print(f"  Válidos                       : {len(valid_df)}")
    print(f"  Válidos com classe energética : {with_energy} "
          f"({with_energy / max(len(valid_df), 1) * 100:.1f}%)")
    print()
    print(f"  Objectivo principal           : {MAIN_TARGET_VALID_LISTINGS}")
    print(f"  Mínimo aceitável              : {MINIMUM_ACCEPTABLE_VALID_LISTINGS}")
    print(f"  Intervalo ideal               : {IDEAL_MIN_VALID_LISTINGS} – {IDEAL_MAX_VALID_LISTINGS}")

    if len(valid_df) >= IDEAL_MIN_VALID_LISTINGS:
        print("  Status: Intervalo ideal atingido.")
    elif len(valid_df) >= MINIMUM_ACCEPTABLE_VALID_LISTINGS:
        print("  Status: Mínimo aceitável atingido.")
    else:
        print("  Status: Abaixo do mínimo.")

    print()
    print("Distribuição por condition (válidos):")
    if "condition" in valid_df.columns:
        print(valid_df["condition"].value_counts().to_string())

    print()
    print("Distribuição por freguesia (top 10):")
    if "parish" in valid_df.columns:
        print(valid_df["parish"].value_counts().head(10).to_string())

    print()
    print("Distribuição por classe energética:")
    if "energy_class" in valid_df.columns:
        print(valid_df["energy_class"].value_counts(dropna=False).to_string())

    print()
    print(f"  Raw   -> {RAW_OUTPUT_PATH}")
    print(f"  Valid -> {VALID_OUTPUT_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    scraped_properties = scrape_properties()
    save_data(scraped_properties)