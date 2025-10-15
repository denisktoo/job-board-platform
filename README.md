# 💼 Job Board Platform API

A RESTful Job Board API built with **Django REST Framework**, featuring:

* **JWT authentication**
* **Role-based access (User, Recruiter, Admin)**
* **Company & Job management**
* **Applications with file uploads**
* **Profile management (User/Admin only)**
* **Search & filtering with pagination**
* **Email notifications with Celery**
* **Automated scheduling with Celery Beat**
* **Signals for real-time notifications (reviews → notifications)**
* **Custom middleware for request logging**
* **Dockerized setup with Postgres, Redis, RabbitMQ, Celery, and Celery Beat**

---

## 🗂️ Entity Relationship Diagram (ERD)

Here’s the ERD for the project:

![Job Board ERD](https://drive.google.com/uc?export=view\&id=1x8y6ffKxhzfraZvwiieiCx8odegva9jx)

---

## ⚙️ Setup (local)

You can now run the entire stack — including **PostgreSQL**, **Redis**, **RabbitMQ**, **Celery**, and **Django** — using Docker.

### 🐳 Using Docker Compose

```bash
docker-compose up --build
```

This command:

* Builds your Docker images (based on your `Dockerfile`)
* Starts containers for:

  * PostgreSQL (Database)
  * Redis (Cache & Celery result backend)
  * RabbitMQ (Celery broker)
  * Django (web app using Gunicorn)
  * Celery worker
  * Celery Beat scheduler

Once everything is running:

* Django: `http://localhost:8000`
* RabbitMQ Dashboard: `http://localhost:15672` (user: `guest`, pass: `guest`)
* PostgreSQL, Redis, and Celery connect automatically via Docker network aliases.

### 🧩 Local Manual Setup (without Docker)

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Run Celery Worker (process tasks)

```bash
celery -A job_board_platform worker --loglevel=info --pool=threads
```

### Run Celery Beat (scheduler)

```bash
celery -A job_board_platform beat --loglevel=info
```

The API will be available at `http://127.0.0.1:8000/`

Production deployment available here: **[Job Board Platform on Render](https://job-board-platform-fcav.onrender.com/)**

---

## 🧰 Redis, Celery & RabbitMQ Configuration

The project integrates **Celery**, **Redis**, and **RabbitMQ** through the following configuration:

* **Celery Broker:** RabbitMQ (`amqp://guest:guest@rabbitmq:5672//`)
* **Celery Result Backend:** Redis (`redis://redis:6379/0`)
* **Django Cache:** Redis (`redis://redis:6379/1`)
* **Serialization:** JSON for both tasks and results
* **Timezone:** UTC

This setup ensures efficient message passing between Django, Celery workers, and scheduled tasks.

Your `Dockerfile` runs Django using:

```
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

(suitable for local development)

While in **Render**, deployment uses Gunicorn:

```
startCommand: gunicorn job_board_platform.wsgi:application --bind 0.0.0.0:$PORT
```

This distinction allows:

* **Docker** → quick local development
* **Render** → production with optimized server handling

---

## 🔐 Authentication

### Register User

**POST** `/api/register/`
Request example:

```json
{
  "username": "TooR",
  "email": "deniskiprotich7491@gmail.com",
  "first_name": "Denis",
  "last_name": "Kiprotich",
  "password": "TooR*#",
  "role": "recruiter"
}
```

### Login (JWT)

**POST** `/api/token/`
Request example:

```json
{
  "username": "TooR",
  "password": "TooR*#"
}
```

Response:

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR..."
}
```

### Refresh Token

**POST** `/api/token/refresh/`
Request: `{ "refresh": "<your_refresh_token>" }`

### Logout (blacklist refresh token)

**POST** `/api/logout/`
Request:

```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR..."
}
```

Response:

```json
{
  "message": "Logout successful"
}
```

<!-- > Notes: logout requires `rest_framework_simplejwt.token_blacklist` enabled in `INSTALLED_APPS` and `migrate` run. The endpoint blacklists the refresh token so it cannot obtain new access tokens. -->

All protected endpoints require the header:

```
Authorization: Bearer <access_token>
```

---

## 🏠 Home & API Roots

### Project Root (`/`)

**GET** `/`
Returns a simple API status JSON:

```json
{
  "message": "Job Board API is live 🚀",
  "docs": "/api/docs/",
  "api_base": "/api/"
}
```

### API Root (`/api/`)

**GET** `/api/`
DRF API root — returns links to top-level resources:

```json
{
  "users": "http://127.0.0.1:8000/api/users/",
  "companies": "http://127.0.0.1:8000/api/companies/",
  "jobs": "http://127.0.0.1:8000/api/jobs/",
  "profiles": "http://127.0.0.1:8000/api/profiles/",
  "categories": "http://127.0.0.1:8000/api/categories/"
}
```

---

## 👤 Profile Management (User/Admin only)

* **Create or Update Profile (User/Admin)** → `POST /api/profile/` or `PATCH /api/profile/{profile_id}/`
* **View Profile (User/Admin)** → `GET /api/profile/{profile_id}/`

Example request body:

```json
{
  "bio": "Passionate full-stack developer with focus on Django and React.",
  "location": "Nairobi, Kenya",
  "skills": "Python, Django, DRF, React, PostgreSQL, Celery",
  "experience": "2 years freelance web development",
  "linkedin_url": "https://www.linkedin.com/in/deniskiprotich",
  "github_url": "https://github.com/deniskiprotich",
  "portfolio_url": "https://deniskiprotich.dev"
}
```

> Notes: `user` is set from `request.user` (authenticated). Only users and admins can access these endpoints.

---

## 👥 User Management

* **List All Users (Admin only)** → `GET /api/users/`
* **View Own Applications (User/Admin)** → `GET /api/users/{user_id}/applications/`
* **Search Own Applications (User/Admin)** → `GET /api/users/{user_id}/applications/?search=Market`
* **Update Own Application (User/Admin)** → `PATCH /api/users/{user_id}/applications/{application_id}/`

Supports multipart form for file updates:

```bash
curl -X PATCH "http://127.0.0.1:8000/api/users/{user_id}/applications/{application_id}/" \
  -H "Authorization: Bearer <your_token>" \
  -F "cover_letter=@/path/to/updated_cover_letter.pdf"
```

---

## 🏢 Company Management

* **Create Company (Recruiter/Admin)** → `POST /api/companies/`
  Request example:

  ```json
  {
    "name": "Leizam Ventures",
    "location": "Nairobi, Kenya",
    "industry": "Software Development",
    "website": "https://leizamventures.com",
    "description": "A growing tech company building scalable digital solutions."
  }
  ```

* **List Companies (Public)** → `GET /api/companies/`
* **Create Job under a Company (Recruiter/Admin)** → `POST /api/companies/{company_id}/jobs/`
  ```json
  {
    "title": "Backend Developer",
    "description": "Work on scalable APIs using Django REST Framework.",
    "category": 2,
    "salary": "150000.00",
    "deadline": "2025-12-31T23:59:59Z",
    "employment_type": "full_time"
  }
  ```
* **List Jobs for a Company (Public)** → `GET /api/companies/{company_id}/jobs/`
* **View Applications for a Job (Recruiter/Admin)** → `GET /api/companies/{company_id}/jobs/{job_id}/applications/`
* **Filter Applications (Recruiter/Admin)** → `GET /api/companies/{company_id}/jobs/{job_id}/applications/?resume=true&cover_letter=true`
* **Update Application Status (Recruiter/Admin)** → `PATCH /api/companies/{company_id}/jobs/{job_id}/applications/{application_id}/`

---

## ⭐ Company Reviews & Notifications

**Company Review Endpoints**

* **Create Review (authenticated user)** → `POST /api/companies/{company_id}/reviews/`
**Request Headers:**

```
Authorization: Bearer <access_token>
```

Request example:

```json
{
  "rating": 5,
  "comment": "Great interview process and supportive team."
}
```
* **List Reviews for Company (public)** → `GET /api/companies/{company_id}/reviews/`
* **Get Review (public)** → `GET /api/companies/{company_id}/reviews/{review_id}/`

**Notifications**

* A `CompanyReview` `post_save` signal automatically creates a `Notification` for the company (via your signals).
* **List Notifications (Recruiter/Admin)** → `GET /api/companies/{company_id}/notifications/`
* **Mark Notification as Read (Recruiter/Admin)** →
  `PATCH /api/companies/{company_id}/notifications/{notification_id}/mark-as-read/`

**Request Headers:**

```
Authorization: Bearer <access_token>
```

**Response Example:**

```json
{
  "id": 5,
  "company": 1,
  "type": "review",
  "content": "New review added to your company.",
  "is_read": true,
  "created_at": "2025-09-22T12:34:56Z"
}
```

---

## 📂 Categories

* **Create Category (Admin only)** → `POST /api/categories/`
**Request Headers:**

```
Authorization: Bearer <access_token>
```

Request Example:

```json
{
  "name": "Software Engineering",
  "description": "Jobs related to software development."
}
```

* **List Categories (Authenticated users only)** → `GET /api/categories/`
* **Update Category (Admin only)** → `PATCH /api/categories/{category_id}/`

---

## 💼 Jobs

* **List All Jobs (Public)** → `GET /api/jobs/`
* **Paginated Jobs** → `GET /api/jobs/?page=3`
* **Filter & Search Jobs** →

  * By employment type: `/api/jobs/?employment_type=full_time`
  * By deadline: `/api/jobs/?deadline=true`
   > `deadline=true` → returns active jobs (future deadline)
  * Search (title/company/location): `/api/jobs/?search=Engineer`

---

## 📝 Job Applications

* **Apply to a Job (User)** → `POST /api/jobs/{job_id}/applications/`
  Requires multipart/form-data:

  ```bash
  curl -X POST "http://127.0.0.1:8000/api/jobs/7/applications/" \
    -H "Authorization: Bearer <your_token>" \
    -F "cover_letter=@/path/to/cover_letter.pdf" \
    -F "resume=@/path/to/resume.pdf"
  ```
* **View Own Applications (User/Admin)** → `GET /api/users/{user_id}/applications/`

---

## 🔐 Role-Based Access Control

| Role          | Permissions                                                            |
| ------------- | ---------------------------------------------------------------------- |
| **User**      | Apply to jobs, manage own profile, view & update own applications      |
| **Recruiter** | Create companies, post jobs, view & manage applications for their jobs |
| **Admin**     | Full access: manage users, companies, jobs, categories, applications   |

---

## 📊 Response Format

Example paginated response:

```json
{
  "count": 45,
  "total_pages": 5,
  "current_page": 1,
  "next": "http://127.0.0.1:8000/api/jobs/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## 🔧 Features & Background Tasks

### ✅ Celery (Async Emails)

* Sends emails asynchronously for:

  * Company registration confirmation
  * Job registration confirmation
  * Job application confirmation
* Uses **RabbitMQ** as the message broker (`CELERY_BROKER_URL = 'amqp://guest:guest@rabbitmq:5672//'`)
* Uses **Redis** as the result backend (`CELERY_RESULT_BACKEND = 'redis://redis:6379/0'`)

### ✅ Celery Beat (Scheduled Tasks)

* Deactivates jobs automatically after deadline
* Sends application reminders 5 days before job deadline

### ✅ RabbitMQ (Message Broker)

* Acts as the **Celery broker**, enabling task queueing and communication between Django and workers.
* Accessible locally on port `5672`, management UI at `15672`.

### ✅ Redis

* Serves dual roles:

  * **Cache backend** (`CACHES["default"]`)
  * **Celery result backend**
* Runs in its own Docker container and connects via `redis://redis:6379`.

### ✅ Signals

* Creating a `CompanyReview` triggers a `Notification` via `post_save` signal.

### ✅ Middleware

* `RequestLoggingMiddleware` logs each request (timestamp, user, path) into `requests.log`.
* If JWT is present, middleware resolves user identity using `rest_framework_simplejwt.authentication.JWTAuthentication`.

---

## ✅ Swagger / Static files (notes)

If Swagger UI looks broken (missing CSS/JS), ensure:

1. `drf_yasg` is installed and in `INSTALLED_APPS`.
2. Run `python manage.py collectstatic`.
3. For production (`DEBUG=False`), static files are served using:

   ```python
   STATIC_URL = "/static/"
   STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

   if not DEBUG:
       STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
   ```

   This works for both local (`DEBUG=True`) and Render (`DEBUG=False`) environments.

---

## 🚀 Getting Started / Workflow

1. Start containers:

   ```bash
   docker-compose up --build
   ```
2. Register as a **Recruiter** → create companies & jobs
3. Register as a **User** → apply for jobs
4. Use JWT tokens in request headers
5. Explore job postings, apply, and manage applications
6. Check `requests.log` for API request history
7. View background task execution in Celery logs

---

## ⚙️ CI/CD & Deployment

This project is deployed on **Render Free Tier** with CI/CD powered by **GitHub Actions**.

* `render.yaml` defines the web service and free PostgreSQL database.
* `.github/workflows/ci.yml` runs tests on pushes and PRs.
* `.github/workflows/dep.yml` triggers Render deploys for `main`.

**Local Development:** uses **Docker Compose** for complete stack orchestration.
**Production:** Render runs Django using **Gunicorn** and manages Postgres automatically.

**Secrets**: `RENDER_API_KEY` and `RENDER_SERVICE_ID` are stored in GitHub Secrets. Other sensitive values (`SECRET_KEY`, DB creds, email config) live in `.env` locally and in Render Dashboard for production — never hardcoded.

---
