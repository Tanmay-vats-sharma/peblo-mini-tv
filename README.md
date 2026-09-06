# Peblo TV Mini

A small video-content CMS and Netflix-style public viewer built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, and TypeScript.

## Features

- Shows, seasons, episodes, and artwork management
- Admin, Editor, and Viewer roles
- JWT authentication with Argon2 password hashing
- PostgreSQL database with Alembic migrations
- Seed data with intentionally invalid records
- Catalogue validation before publishing
- Atomic `catalogue.json` replacement
- Publish history
- Search, filtering, and pagination
- Responsive Netflix-style public viewer
- Artwork upload and validation
- Docker Compose configuration
- Backend tests and frontend checks

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy
- Database: PostgreSQL
- Migrations: Alembic
- Frontend: React, TypeScript, Vite
- Authentication: JWT
- Password hashing: Argon2
- Deployment: Docker Compose
- CI: GitHub Actions

## Project Structure

```text
peblo-tv-mini/
├── backend/
│   ├── app/
│   ├── alembic/
│   ├── tests/
│   ├── seed_shows.json
│   ├── reference.json
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── docker-compose.yml
└── README.md