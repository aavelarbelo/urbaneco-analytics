DROP TABLE IF EXISTS fact_listings CASCADE;
DROP TABLE IF EXISTS dim_energy CASCADE;
DROP TABLE IF EXISTS dim_parish CASCADE;

CREATE TABLE dim_energy (
    energy_class TEXT PRIMARY KEY,
    energy_score NUMERIC(4,3),
    is_efficient BOOLEAN
);

INSERT INTO dim_energy VALUES
('A+',1.000,TRUE),('A',0.875,TRUE),('B',0.750,TRUE),('B-',0.625,TRUE),
('C',0.500,FALSE),('D',0.375,FALSE),('E',0.250,FALSE),('F',0.125,FALSE);

CREATE TABLE dim_parish (
    parish TEXT PRIMARY KEY,
    municipality TEXT DEFAULT 'Porto'
);

INSERT INTO dim_parish (parish) VALUES
('Cedofeita'),('Paranhos'),('Lordelo Do Ouro'),('Ramalde'),
('Campanha'),('Bonfim'),('Aldoar'),('Se'),('Vitoria');

CREATE TABLE fact_listings (
    listing_id SERIAL PRIMARY KEY,
    listing_url TEXT,
    scraped_at TEXT,
    price_type TEXT DEFAULT 'asking_price',
    municipality TEXT DEFAULT 'Porto',
    parish TEXT,
    title TEXT,
    property_type TEXT,
    typology TEXT,
    typology_clean TEXT,
    bedrooms INTEGER,
    price NUMERIC(12,2),
    area_m2 NUMERIC(8,2),
    price_m2 NUMERIC(10,2),
    energy_class TEXT,
    has_energy_class BOOLEAN,
    energy_score NUMERIC(4,3),
    price_score NUMERIC(6,4),
    evi_score NUMERIC(4,1),
    segment TEXT,
    segment_valid BOOLEAN,
    condition TEXT,
    has_garage BOOLEAN,
    has_elevator BOOLEAN,
    has_balcony BOOLEAN,
    has_parking BOOLEAN,
    page_number INTEGER
);

SELECT 'Tabelas criadas com sucesso' AS status;
