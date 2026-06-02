-- ============================================================
-- UrbanEco Analytics
-- Script: 01_create_database.sql
-- Purpose: Create the main PostgreSQL database for the project
-- Database: urbaneco_dw
-- PostgreSQL version: 16
-- ============================================================

-- This script is mainly intended for manual/local database setup.
-- In the Docker environment, the database is automatically created
-- through the POSTGRES_DB variable defined in infra/docker-compose.yml.

CREATE DATABASE urbaneco_dw;