import random
import string
from faker import Faker
from sqlalchemy.orm import Session
import os
import sys

from app.core.db import get_global_db_session
from app.services.auth_service import AuthService
from app.model_handlers.user_feedback_handler import UserFeedbackHandler
from app.model_handlers.movie_handler import MovieHandler
from app.model_handlers.user_handler import UserCreate
from app.model_handlers.user_feedback_handler import UserFeedbackCreate


fake = Faker()

GENRES = [
  "Action",
  "Adventure",
  "Animation",
  "Comedy",
  "Crime",
  "Documentary",
  "Drama",
  "Family",
  "Fantasy",
  "History",
  "Horror",
  "Music",
  "Mystery",
  "Romance",
  "Science Fiction",
  "TV Movie",
  "Thriller",
  "War",
  "Western"
]

USERS_TO_CREATE = 10
FEEDBACKS_PER_USER = 300

def random_password(length=10):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))


def pick_user_genre_preferences():
    """Pick 3 distinct genres for cold-start behavior."""
    return random.sample(GENRES, 3)


def generate_synthetic_users_and_feedbacks():
    db: Session = next(get_global_db_session())
    auth_service = AuthService(db)
    movie_handler = MovieHandler(db)
    feedback_handler = UserFeedbackHandler(db)

    movies = movie_handler.list_all(skip=0, limit=50_000)
    if not movies:
        print("❌ No movies found in DB. Cannot generate feedback.")
        return

    print(f"🎬 Loaded {len(movies)} movies from DB.")

    created_users = []

    # ------------------------------
    # STEP 1: Create 10 Users
    # ------------------------------
    for i in range(USERS_TO_CREATE):
        email = f"user{i+1}_{random.randint(1000,9999)}@example.com"
        firstname = fake.first_name()
        lastname = fake.last_name()
        password = random_password()

        user_in = UserCreate(
            email=email,
            firstname=firstname,
            lastname=lastname,
            hashed_password=password,   # your AuthService will hash internally
        )

        user = auth_service.register(user_in)
        user.genre_preferences = ",".join(pick_user_genre_preferences())
        db.commit()

        created_users.append(user)
        print(f"🧑‍💻 Created User {user.id}: {email} | Genres: {user.genre_preferences}")

    # ------------------------------
    # STEP 2: Generate Feedbacks
    # ------------------------------
    for user in created_users:
        print(f"\n🎯 Generating feedback for User {user.id}...")

        # Weight sampling toward user genre preferences
        preferred = user.genre_preferences.split(",")

        def score_movie(movie):
            score = 0
            for g in preferred:
                if g.lower() in (movie.genres or "").lower():
                    score += 1
            return score

        # Sort movies by relevance to user preferences
        ranked_movies = sorted(movies, key=lambda m: score_movie(m), reverse=True)

        # Pick 300 movies for feedback
        selected_movies = random.sample(ranked_movies[:2000], FEEDBACKS_PER_USER)

        for m in selected_movies:
            rating = random.choices(
                population=[5, 4, 3, 2, 1],
                weights=[0.35, 0.30, 0.20, 0.10, 0.05],  # prefer higher ratings
                k=1
            )[0]

            feedback = UserFeedbackCreate(
                user_id=user.id,
                movie_id=m.id,
                rating=rating,
                review=None,
                status="watched"
            )

            feedback_handler.create(feedback)

        print(f"✅ Added {FEEDBACKS_PER_USER} feedback entries for user {user.id}")

    print("\n🎉 Synthetic User + Feedback Generation Complete!")


if __name__ == "__main__":
    generate_synthetic_users_and_feedbacks()
