````markdown
# Peblo TV Mini

A small video-content CMS and Netflix-style public viewer built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, and TypeScript.

## Features

- Shows, seasons, episodes, and artwork management
- Admin, Editor, and Viewer roles
- JWT-based authentication
- Argon2 password hashing
- PostgreSQL database
- Alembic database migrations
- Seed data with intentionally invalid records
- Full catalogue validation before publishing
- Atomic `catalogue.json` replacement
- Publish history
- Search, filtering, and pagination
- Responsive Netflix-style public viewer
- Artwork upload and validation
- Docker Compose setup
- Backend tests
- Frontend TypeScript, lint, and build checks
- GitHub Actions CI

## Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Frontend:** React, TypeScript, Vite
- **Authentication:** JWT
- **Password Hashing:** Argon2
- **Web Server:** Uvicorn and Nginx
- **Deployment:** Docker Compose
- **CI:** GitHub Actions

## Project Structure

```text
peblo-tv-mini/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   ├── tests/
│   ├── storage/
│   ├── catalogue/
│   ├── seed_shows.json
│   ├── reference.json
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── README.md
````

## Catalogue Rules

The catalogue follows these rules:

* Sections are ordered as:

  1. `featured`
  2. `series`
  3. `minisodes`
  4. `songs`
* Shows are sorted alphabetically by title
* Seasons are sorted numerically in ascending order
* Season `0` is reserved for trailers
* Season `0` is not shown as a normal season
* Episodes are sorted by episode number
* Episodes with the same `content_group` are language variants
* Language variants are collapsed into one catalogue entry
* Supported languages:

  * `en`
  * `hi`

### Artwork Requirements

| Artwork Type | Aspect Ratio | Target Size | Maximum File Size |
| ------------ | -----------: | ----------: | ----------------: |
| Poster       |          2:3 |   600 × 900 |            200 KB |
| Banner       |         16:9 |  1280 × 720 |            200 KB |
| Thumbnail    |         16:9 |   640 × 360 |            200 KB |

## How to Run the Project with Docker

### Prerequisites

Install and start Docker Desktop or Docker Engine with Docker Compose support.

Check that Docker is installed:

```bash
docker --version
docker compose version
```

### 1. Clone the Repository

```bash
git clone https://github.com/Tanmay-vats-sharma/peblo-mini-tv.git
cd peblo-mini-tv
```

### 2. Start the Project

Run this command from the project root:

```bash
docker compose up --build
```

This command starts:

* PostgreSQL database
* FastAPI backend
* React frontend served through Nginx

The backend automatically runs the Alembic database migrations before starting.

### 3. Open the Application

Public Netflix-style viewer:

```text
http://localhost:5174
```

FastAPI backend:

```text
http://localhost:8001
```

FastAPI Swagger documentation:

```text
http://localhost:8001/docs
```

FastAPI ReDoc documentation:

```text
http://localhost:8001/redoc
```

### 4. Check Running Containers

Open another terminal in the project directory and run:

```bash
docker compose ps
```

View service logs:

```bash
docker compose logs -f
```

View only backend logs:

```bash
docker compose logs -f backend
```

View only database logs:

```bash
docker compose logs -f db
```

### 5. Stop the Project

Press:

```text
Ctrl + C
```

To stop and remove the containers:

```bash
docker compose down
```

To stop containers and remove the PostgreSQL Docker volume:

```bash
docker compose down -v
```

> The `-v` option deletes the PostgreSQL data created by Docker. Use it only when you want to reset the Docker database.

### 6. Start the Project Again

If the Dockerfiles and dependencies have not changed:

```bash
docker compose up
```

Use `--build` again when you change:

* Dockerfiles
* Python dependencies
* Frontend dependencies
* Nginx configuration
* Application files that are copied into the image

```bash
docker compose up --build
```

## Running the Backend Locally

The backend can also be run without Docker.

### 1. Create a Virtual Environment

From the project root:

```bash
cd backend
python -m venv venv
```

### 2. Activate the Virtual Environment

On Windows:

```cmd
venv\Scripts\activate
```

On Linux or macOS:

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Database

Set the database connection string in the environment:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/video_cms
```

Also configure the application secret:

```text
SECRET_KEY=change-this-development-secret
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start the Backend

```bash
uvicorn app.main:app --reload
```

The backend will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

## Running the Frontend Locally

Open a second terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

## Testing

### Backend Tests

From the `backend` directory:

```bash
python -m pytest -q
```

On Windows, if temporary test files cause cleanup issues, use:

```cmd
venv\Scripts\python.exe -m pytest -q --basetemp=.\pytest-temp-clean
```

### Frontend TypeScript Check

From the `frontend` directory:

```bash
npm run type-check
```

If a separate type-check script is not configured, use:

```bash
npx tsc -b
```

### Frontend Lint

```bash
npm run lint
```

### Frontend Production Build

```bash
npm run build
```

## Database Migrations

Create a new migration after changing SQLAlchemy models:

```bash
alembic revision --autogenerate -m "describe the change"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback the latest migration:

```bash
alembic downgrade -1
```

## Catalogue Publishing

The catalogue publishing workflow:

1. Reads the stored shows, seasons, episodes, and artwork
2. Validates the complete catalogue
3. Rejects invalid records
4. Sorts sections, shows, seasons, and episodes
5. Collapses language variants by `content_group`
6. Writes the new catalogue atomically
7. Records the publish operation in publish history

The generated catalogue is stored as:

```text
backend/catalogue/catalogue.json
```

## User Roles

### Admin

* Manage catalogue content
* Manage users and roles
* Upload artwork
* Validate and publish the catalogue
* View publish history

### Editor

* Create and update shows, seasons, episodes, and artwork
* Validate catalogue data
* Publish catalogue content, according to the configured permissions

### Viewer

* Browse the public catalogue
* Search and filter content
* View shows, seasons, and episodes

## Environment Variables

The main environment variables include:

```text
DATABASE_URL
SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES
```

Example development values:

```text
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/video_cms
SECRET_KEY=change-this-development-secret
```

Do not commit real secrets or production credentials to GitHub.

## API Documentation

When the backend is running, API documentation is available at:

```text
http://localhost:8001/docs
```

The documentation can be used to:

* View available endpoints
* Test authentication
* Test CMS operations
* Validate catalogue data
* Publish the catalogue
* View publish history

## Troubleshooting

### Port Already in Use

If the default host ports are already being used, update the host-side ports in `docker-compose.yml`.

For example:

```yaml
ports:
  - "5433:5432"
```

The first port is the host port. The second port is the container port.

The backend must still connect to PostgreSQL using the Docker service name and container port:

```text
postgresql+psycopg://postgres:postgres@db:5432/video_cms
```

### Rebuild Containers

```bash
docker compose down
docker compose up --build
```

### Reset the Docker Database

```bash
docker compose down -v
docker compose up --build
```

### View Detailed Errors

```bash
docker compose logs -f backend
```

or:

```bash
docker compose logs -f frontend
```

## CI Checks

The project uses GitHub Actions to check:

* Backend installation
* Backend tests
* Frontend dependency installation
* Frontend linting
* Frontend build

## License

This project was created as a technical assessment project.

````
