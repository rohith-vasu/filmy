-- =========================================
-- CREATE DATABASES
-- =========================================

-- MLflow tracking database
CREATE DATABASE mlflow_db;

-- Prefect database
CREATE DATABASE prefect;

-- MLflow DB user
CREATE USER mlflow WITH PASSWORD 'mlflow';
GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO mlflow;
GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO filmy;

-- Prefect DB user
CREATE USER prefect WITH PASSWORD 'prefect';
GRANT ALL PRIVILEGES ON DATABASE prefect TO prefect;
GRANT ALL PRIVILEGES ON DATABASE prefect TO filmy;

-- =========================================
-- SCHEMA FOR filmy_db
-- =========================================
\c filmy_db;

-- Movies table
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    tmdb_id BIGINT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    overview TEXT,
    genres TEXT,
    original_language TEXT,
    tagline TEXT,
    keywords TEXT,
    runtime INT,
    popularity FLOAT,
    poster_path TEXT,
    release_year INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    genre_preferences TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User feedback table
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    movie_id INT REFERENCES movies(id) ON DELETE CASCADE,
    rating FLOAT CHECK (rating BETWEEN 0.5 AND 5),
    review TEXT,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_movie UNIQUE (user_id, movie_id)
);
