-- DATABASE INITIALIZATION SCRIPT FOR FILMY

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

CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    version TEXT,
    trained_on TIMESTAMP,
    dataset_version TEXT,
    metrics JSONB,
    status TEXT,
    model_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);