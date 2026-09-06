# Peblo TV Mini

A small video-content CMS and Netflix-style public viewer built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, React, and TypeScript.

## Features

- Shows, seasons, episodes, and artwork management
- Admin, Editor, and Viewer roles
- JWT authentication
- PostgreSQL database with Alembic migrations
- Seed data with intentionally invalid records
- Catalogue validation before publishing
- Atomic `catalogue.json` replacement
- Publish history
- Search, filtering, and pagination
- Responsive public viewer
- Artwork upload and validation
- Docker Compose configuration
- Backend and frontend tests/checks

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
│   ├── migrations/
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