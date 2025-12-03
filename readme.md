# Filmy

**Filmy** is an intelligent AI-powered movie recommendation platform that helps users **discover, explore, and track** movies based on their preferences. It combines **collaborative filtering**, **content-based recommendations**, and **vector embeddings** to deliver personalized movie suggestions tailored to individual tastes.

---

## 🚀 Features

- **🎬 Personalized Recommendations** — Get movie suggestions based on your viewing history and ratings
- **🔍 Smart Search & Discovery** — Explore movies by genre, language, year, and popularity
- **⭐ Interactive Watchlist** — Save and manage your favorite movies and watch later list
- **🤖 AI-Powered Similarity** — Find similar movies using advanced vector embeddings
- **📊 User Feedback System** — Rate movies and improve recommendations over time
- **🎯 Hybrid Recommendation Engine** — Combines collaborative filtering (Implicit ALS) with content-based filtering
- **⚡ Modern Stack** — FastAPI backend with React TypeScript frontend
- **🔐 User Authentication** — Secure login and personalized user profiles
- **🐳 Production Ready** — Full Docker support with MLOps pipeline

---

## 🏗️ Tech Stack

| Component            | Technology |
|----------------------|-------------|
| **Frontend**         | React + TypeScript + TailwindCSS + shadcn/ui |
| **Backend**          | FastAPI + SQLModel + Pydantic |
| **Database**         | PostgreSQL |
| **Vector DB**        | Qdrant |
| **ML Framework**     | Implicit (ALS Collaborative Filtering) |
| **Embeddings**       | Sentence Transformers |
| **Workflow Engine**  | Prefect |
| **Experiment Tracking** | MLflow |
| **Object Storage**   | MinIO |
| **Container**        | Docker + Docker Compose |
| **Build Tools**      | Make + Vite + uv |

---

## 📦 Prerequisites

Make sure you have the following installed:

- [Python 3.11](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Fast Python package manager
- [Node.js 18+](https://nodejs.org/)
- [Docker](https://docs.docker.com/get-started/get-docker/)
- [GNU Make](https://www.gnu.org/software/make)

---

## ⚙️ Setup

### Clone the repository
```bash
git clone https://github.com/rohith-vasu/filmy.git
cd filmy
```

### Environment variables

**Backend** (`backend/.env.dev` and `backend/.env.prod`)

```bash
ENV_FOR_DYNACONF=development  # or production

# Database
POSTGRES_USER=filmy
POSTGRES_PASSWORD=your_db_password
POSTGRES_DB=filmy_db
POSTGRES_HOST=localhost  # or postgres for Docker
POSTGRES_PORT=5432

# TMDB API (for movie data)
TMDB_API_KEY=your_tmdb_api_key

# MLflow & MinIO
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123
AWS_ACCESS_KEY_ID=minio
AWS_SECRET_ACCESS_KEY=minio123

# Prefect
PREFECT_API_URL=http://localhost:4200/api # or http://prefect:4200/api for Docker

# Qdrant
QDRANT_HOST=localhost  # or qdrant for Docker
QDRANT_PORT=6333

# JWT Secret
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Frontend** (`frontend/.env`)

```bash
VITE_BASE_API_URL=http://localhost:8000/api/v1
```

---

## 🛠️ Development Setup

Filmy is composed of a backend (FastAPI) and a frontend (React).

### 1. Start dependencies via Docker

From the project root:

```bash
make up-deps
```

This spins up all required services:

- **Qdrant** — Vector database for movie embeddings
- **PostgreSQL** — Main database for users, movies, and feedback
- **PgAdmin** — Database management UI
- **MinIO** — Object storage for ML artifacts
- **MLflow** — Experiment tracking and model registry
- **Prefect** — Workflow orchestration

### 2. Start the backend

```bash
cd backend
./start.sh
```

This runs the FastAPI app in development mode with hot reload at `http://localhost:8000`.

**API Documentation** will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

This runs the Vite-powered React app at `http://localhost:8001`.

---

## 🎬 Data Ingestion & Model Training

### Ingest TMDB Movie Data

```bash
make ingest-tmdb
```

This fetches popular movies from The Movie Database (TMDB) API and stores them in PostgreSQL and Qdrant.

### Generate Synthetic User Feedback

For development and testing:

```bash
make generate-synthetic-feedbacks
```

This creates synthetic user ratings to bootstrap the recommendation system.

### Train Recommendation Model

```bash
make train-model
```

This trains the **Implicit ALS** collaborative filtering model using user feedback data. The trained model is stored in MLflow and used for generating personalized recommendations.

---

## 🚀 Production Setup

For production deployment (all services in Docker):

```bash
make up-prod-build
```

This builds and runs:
- Backend (FastAPI)
- Frontend (React, served statically)
- All dependencies (PostgreSQL, Qdrant, MLflow, Prefect, MinIO)

The app will be available at: `http://localhost:8001`

To start production without rebuilding:

```bash
make up-prod
```

---

## 🎯 How It Works

### Recommendation Pipeline

1. **User Registration** — Users create accounts and start rating movies
2. **Data Collection** — User interactions (ratings, watchlist additions) are captured
3. **Collaborative Filtering** — Implicit ALS model finds patterns in user-movie interactions
4. **Content-Based Filtering** — Vector embeddings capture movie metadata and descriptions
5. **Hybrid Recommendations** — Combines both approaches for personalized suggestions
6. **Continuous Learning** — Model retraining with new feedback via Prefect workflows

### Movie Similarity

When a user views a movie, the system:
1. Retrieves the movie's vector embedding from Qdrant
2. Performs semantic search to find similar movies
3. Ranks results by relevance and popularity
4. Returns top similar movies with metadata

---

## 📂 Project Structure

```
filmy/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── routes/              # API endpoints
│   │   ├── models/              # SQLModel database schemas
│   │   ├── model_handlers/      # ML model inference
│   │   ├── pipelines/           # Data ingestion & training
│   │   ├── services/            # Business logic
│   │   └── utils/               # Helper functions
│   ├── config/                  # Dynaconf settings
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/               # Route pages
│   │   ├── components/          # Reusable UI components
│   │   ├── hooks/               # Custom React hooks
│   │   └── stores/              # Zustand state management
│   └── package.json
├── ops/
│   ├── docker-compose.yaml      # Production orchestration
│   └── Dockerfile.*             # Container definitions
└── Makefile                     # Development commands
```

---

## 🔧 Useful Commands

| Command | Description |
|---------|-------------|
| `make up-deps` | Start only dependencies (DB, vector DB, etc.) |
| `make up-prod` | Start full production stack |
| `make up-prod-build` | Build and start production stack |
| `make down` | Stop all containers |
| `make nuke` | Stop containers and remove volumes |
| `make logs` | View container logs |
| `make ps` | Show container status |
| `make train-model` | Train recommendation model |
| `make ingest-tmdb` | Fetch movies from TMDB |
| `make generate-synthetic-feedbacks` | Create test user data |

---

## 🌐 Service URLs

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:8001 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **PgAdmin** | http://localhost:5050 |
| **Qdrant Dashboard** | http://localhost:6333/dashboard |
| **MLflow UI** | http://localhost:5500 |
| **Prefect UI** | http://localhost:4200 |
| **MinIO Console** | http://localhost:9001 |

---

## 🧪 Development Tips

- **Backend Hot Reload**: The FastAPI server automatically reloads on code changes
- **Frontend Hot Reload**: Vite provides instant feedback on UI changes
- **Database Migrations**: Use SQLModel's `create_all()` for initial schema setup
- **Model Versioning**: All trained models are tracked in MLflow with metrics and artifacts
- **Clean Rebuild**:
  ```bash
  make down
  make build-nc
  make up-prod
  ```

---

## 🎨 Key Features Explained

### Collaborative Filtering (Implicit ALS)
- Analyzes user-movie interaction patterns
- Handles implicit feedback (ratings, watchlist additions)
- Generates personalized recommendations based on similar users

### Vector Search
- Movie descriptions and metadata converted to embeddings
- Semantic similarity matching using Qdrant
- Fast, scalable nearest-neighbor search

### Hybrid Approach
- Combines collaborative and content-based filtering
- Leverages strengths of both methods
- Provides diverse and accurate recommendations

### MLOps Pipeline
- **Prefect**: Orchestrates data pipelines and model training
- **MLflow**: Tracks experiments, hyperparameters, and model versions
- **MinIO**: Stores model artifacts and datasets
- **DVC**: Version control for data and models (optional)

---

## 📝 API Endpoints

### Authentication
- `POST /api/v1/auth/register` — Create new user account
- `POST /api/v1/auth/login` — User login

### Movies
- `GET /api/v1/movies/explore` — Browse movies with filters
- `GET /api/v1/movies/{movie_id}` — Get movie details
- `GET /api/v1/movies/{movie_id}/similar` — Find similar movies

### Recommendations
- `GET /api/v1/recommendations/` — Get personalized recommendations
- `GET /api/v1/recommendations/trending` — Get trending movies

### User Feedback
- `POST /api/v1/feedback/rating` — Submit movie rating
- `POST /api/v1/feedback/watchlist` — Add/remove from watchlist
- `GET /api/v1/feedback/watchlist` — Get user's watchlist

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [The Movie Database (TMDB)](https://www.themoviedb.org/) for movie data
- [Implicit](https://github.com/benfred/implicit) for collaborative filtering
- [Qdrant](https://qdrant.tech/) for vector search capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the amazing backend framework
- [shadcn/ui](https://ui.shadcn.com/) for beautiful UI components

---

**Built with ❤️ by [Rohith Vasu](https://github.com/RohithVasu)**