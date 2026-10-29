# FastAPI Enterprise Student & Group Management Service

> **High-concurrency RESTful microservice architected with FastAPI, PostgreSQL persistence via SQLAlchemy ORM, asynchronous Redis read-through caching with automated invalidation, Alembic schema migrations, and JWT role-based authentication.**

[![CI](https://github.com/NURJAKS/fastapi-user-management-api/actions/workflows/ci.yml/badge.svg)](https://github.com/NURJAKS/fastapi-user-management-api/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Alembic](https://img.shields.io/badge/Alembic-Migrations-orange)](https://alembic.sqlalchemy.org/)

---

## Pitch & Executive Summary

**FastAPI Student & Group Service** is a reference RESTful backend engineered for high read throughput and strict relational data integrity. Designed around decoupled architecture patterns, the service pairs a high-performance **FastAPI (ASGI)** runtime with **SQLAlchemy ORM** and an asynchronous **Redis** caching tier. 

By intercepting repetitive read requests at the Redis layer and enforcing automated cache invalidation upon record mutation, the system maximizes I/O operations per second while preserving ACID guarantees in **PostgreSQL**.

---

## Architecture Overview

The application follows an asynchronous n-tier architecture separating HTTP routing, authentication middleware, caching policies, and relational data access:

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        HTTPClient["HTTP REST Client / OpenAPI Consumer"]
    end

    subgraph Service ["Application Tier (FastAPI / ASGI)"]
        Router["API Gateway & Routers (Auth / Students / Groups)"]
        AuthMiddleware["JWT Token & Session Verification"]
        Validation["Pydantic DTO Serialization & Schema Guards"]
    end

    subgraph CacheTier ["In-Memory Caching Tier"]
        RedisClient["Async Redis Client (aioredis)"]
        CacheStore[("Redis Cache Key-Value Store")]
    end

    subgraph DBTier ["Persistence Layer"]
        ORM["SQLAlchemy Session Pool"]
        Postgres[("PostgreSQL Database (Users / Groups / Students)")]
        AlembicEngine["Alembic Versioned Migration Chain"]
    end

    HTTPClient -->|REST API Requests| Router
    Router --> AuthMiddleware
    AuthMiddleware --> Validation

    Validation -->|1. Check Cache (GET /students)| RedisClient
    RedisClient <-->|Cache Hit / Miss| CacheStore

    RedisClient -->|2. On Cache Miss / Mutation| ORM
    ORM <-->|SQL Queries / Atomic Commits| Postgres
    ORM -.->|3. Invalidate Cache on Write| RedisClient

    AlembicEngine -.->|Schema Versioning| Postgres
```

### Architectural Highlights

- **Asynchronous Read-Through Caching:** Read endpoints (`GET /students`, `GET /students/{id}`) check Redis before hitting the database. Cache keys follow structured namespaces (`students:all`, `student:{id}`) with explicit Time-To-Live (TTL) policies.
- **Automated Cache Invalidation:** Write operations (`POST`, `PUT`, `DELETE`) automatically purge related cache keys to prevent stale read anomalies.
- **Stateless & Session Authentication:** Implements JWT Bearer token generation with bcrypt password hashing alongside Starlette session cookies for flexible client integration.
- **Database Schema Migrations:** All schema evolutions are versioned through **Alembic**, enabling deterministic database state reproducibility across environments.

---

## Key Enterprise Features

### 1. Dual-Layer Caching Strategy
- Redis in-memory storage accelerates read latency down to single-digit milliseconds.
- Non-blocking Redis I/O avoids thread starvation during concurrent query bursts.

### 2. Relational Integrity & ORM Abstraction
- Normalized database schema modeling `Users`, `Groups`, and `Students` with foreign key relationships, cascade rules, and query optimizations.
- Dynamic data filtering supporting `skip` and `limit` pagination parameters.

### 3. Role-Based Access Control (RBAC) & Route Protection
- Secure user registration and login pipelines issuing signed cryptographic JWT tokens.
- Dependency injection pattern (`Depends(get_current_user)`) enforcing role privileges and blocking unauthorized access to administrative endpoints.

### 4. Typed DTO Contracts (Pydantic)
- Strict request validation stripping unpermitted attributes and validating data formats (emails, string lengths, integer constraints).
- Response serialization isolating internal database structures from public API consumers.

---

## Tech Stack & Architectural Rationale

| Layer | Technology | Architectural Rationale |
| :--- | :--- | :--- |
| **Framework** | **FastAPI 0.104+** | Asynchronous ASGI execution engine with automatic OpenAPI documentation and native dependency injection. |
| **Persistence** | **PostgreSQL & SQLAlchemy** | Robust ACID-compliant relational data management with expressive ORM entity abstractions. |
| **Caching** | **Redis** | In-memory key-value engine providing ultra-fast read responses and distributed session support. |
| **Migrations** | **Alembic** | Reliable declarative schema evolution tooling preventing drift across development and staging databases. |
| **Validation** | **Pydantic v2** | High-performance C-based data parsing and schema validation. |
| **Authentication** | **PyJWT & Passlib (Bcrypt)** | Industry-standard cryptographic token issuance and salted password hashing. |

---

## Repository Structure

```text
├── api/
│   ├── app.py                   # FastAPI application initialization & route registration
│   ├── auth_routes.py           # Authentication endpoints (Register, Login, Token)
│   ├── protected_routes.py      # Role-guarded endpoint controllers
│   ├── schemas.py               # Pydantic domain transfer objects (Group, Student)
│   └── schemas_auth.py          # Authentication request/response schemas
├── models/
│   ├── group.py                 # SQLAlchemy Group model definition
│   ├── student.py               # SQLAlchemy Student model definition
│   └── user.py                  # SQLAlchemy User & Role model definition
├── db/
│   ├── database.py              # Engine setup, sessionmaker, and get_db dependency
│   └── redis_client.py          # Redis connection pool and async client factory
├── alembic/                     # Versioned database migration scripts
├── alembic.ini                  # Alembic environment and connection configuration
├── queries.py                   # Helper query scripts and data seeding routines
├── requirements.txt             # Pinned Python dependencies
└── README.md                    # Technical documentation
```

---

## Getting Started

### Prerequisites

- **Python 3.10+**
- Running **PostgreSQL** instance
- Running **Redis** instance

---

### Step 1: Clone & Configure Virtual Environment

```bash
git clone https://github.com/NURJAKS/FastAPI-pet-project.git
cd FastAPI-pet-project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Step 2: Configure Database & Redis

Ensure PostgreSQL and Redis connection parameters in:
- `db/database.py` (Database URL)
- `db/redis_client.py` (Redis host/port)

Apply database migrations:
```bash
alembic upgrade head
```

Optional: Seed initial test data:
```bash
python main.py
```

---

### Step 3: Launch Service

```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

Access Interactive Documentation:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Verification & Workflow Test

| Endpoint | Method | Expected Output |
| :--- | :---: | :--- |
| `/auth/register` | POST | Creates user account with bcrypt-hashed credentials |
| `/auth/token` | POST | Returns bearer JWT access token |
| `/students` | GET | First call: fetches from PostgreSQL & populates Redis; Second call: served from Redis cache |
| `/students` | POST | Creates student record and invalidates `students:all` cache key |

---

## License

This project is licensed under the MIT License.
