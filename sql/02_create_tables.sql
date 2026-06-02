-- ============================================================
-- UrbanEco Analytics
-- Script: 02_create_tables.sql
-- Purpose: Create dimensional model tables for the MVP database
-- Database: urbaneco_dw
-- PostgreSQL version: 16
-- ============================================================

-- This schema maps the real property-level variables defined by the team
-- into a dimensional model for ingestion, validation, analytics, and dashboarding.

-- ============================================================
-- 1. Dimension: Location
-- Variables covered:
-- FREGUESIA, CONCELHO, MORADA, GPS LATITUDE, GPS LONGITUDE
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_location (
    location_id SERIAL PRIMARY KEY,
    freguesia VARCHAR(120) NOT NULL,
    concelho VARCHAR(120) NOT NULL,
    morada TEXT,
    gps_latitude NUMERIC(10, 7),
    gps_longitude NUMERIC(10, 7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 2. Dimension: Property
-- Variables covered:
-- TIPOLOGIA, ÁREA UTIL, ÁREA BRUTA, ANO DE CONSTRUÇÃO,
-- ESTADO DA HABITAÇÃO, WC, GARAGEM, VARANDA, ANDAR,
-- ELEVADOR, EQUIPAMENTO, PISCINA, ARRUMOS,
-- TERRENO/JARDIM, PISOS
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_property (
    property_id SERIAL PRIMARY KEY,
    tipologia VARCHAR(20) NOT NULL,
    area_util NUMERIC(10, 2) NOT NULL,
    area_bruta NUMERIC(10, 2),
    ano_construcao INTEGER,
    estado_habitacao VARCHAR(120),
    wc INTEGER,
    garagem BOOLEAN,
    varanda BOOLEAN,
    andar VARCHAR(50),
    elevador BOOLEAN,
    equipamento TEXT,
    piscina BOOLEAN,
    arrumos BOOLEAN,
    terreno_jardim BOOLEAN,
    pisos INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. Dimension: Energy
-- Variables covered:
-- CLASSE ENERGÉTICA
-- ============================================================

CREATE TABLE IF NOT EXISTS dim_energy (
    energy_id SERIAL PRIMARY KEY,
    classe_energetica VARCHAR(10),
    energy_class_rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 4. Fact Table: Property Energy Value
-- Variables covered:
-- PREÇO, ESTADO ANUNCIO, DATA PUBLICAÇÃO, URL
-- Foreign keys:
-- location_id, property_id, energy_id
-- Analytical metrics:
-- price_per_m2, energy_value_index
-- ============================================================

CREATE TABLE IF NOT EXISTS fact_property_energy_value (
    fact_id SERIAL PRIMARY KEY,
    location_id INTEGER NOT NULL,
    property_id INTEGER NOT NULL,
    energy_id INTEGER,

    preco NUMERIC(14, 2) NOT NULL,
    estado_anuncio VARCHAR(120),
    data_publicacao DATE,
    url TEXT NOT NULL,

    price_per_m2 NUMERIC(14, 2),
    energy_value_index NUMERIC(10, 4),

    source_name VARCHAR(120) DEFAULT 'CasaSafari',
    is_synthetic BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_fact_location
        FOREIGN KEY (location_id)
        REFERENCES dim_location(location_id),

    CONSTRAINT fk_fact_property
        FOREIGN KEY (property_id)
        REFERENCES dim_property(property_id),

    CONSTRAINT fk_fact_energy
        FOREIGN KEY (energy_id)
        REFERENCES dim_energy(energy_id)
);

-- ============================================================
-- 5. Indexes for analytical queries and dashboard performance
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_dim_location_concelho
    ON dim_location(concelho);

CREATE INDEX IF NOT EXISTS idx_dim_location_freguesia
    ON dim_location(freguesia);

CREATE INDEX IF NOT EXISTS idx_dim_property_tipologia
    ON dim_property(tipologia);

CREATE INDEX IF NOT EXISTS idx_dim_energy_classe
    ON dim_energy(classe_energetica);

CREATE INDEX IF NOT EXISTS idx_fact_data_publicacao
    ON fact_property_energy_value(data_publicacao);

CREATE INDEX IF NOT EXISTS idx_fact_is_synthetic
    ON fact_property_energy_value(is_synthetic);

CREATE INDEX IF NOT EXISTS idx_fact_source_name
    ON fact_property_energy_value(source_name);