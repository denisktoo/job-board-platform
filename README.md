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
* **Signals for real-time notifications**
* **Custom middleware for request logging**

---

## 🗂️ Entity Relationship Diagram (ERD)

Here’s the ERD for the project:

![Job Board ERD](https://drive.google.com/uc?export=view\&id=1x8y6ffKxhzfraZvwiieiCx8odegva9jx)

---

## ⚙️ Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Run Celery Worker

```bash
celery -A job_board_platform worker --loglevel=info --pool=threads
```

### Run Celery Beat

```bash
celery -A job_board_platform beat --loglevel=info
```

The API will be available at `http://127.0.0.1:8000/`

Production deployment available here: **[Job Board Platform on Render](https://job-board-platform-fcav.onrender.com/)**

---

## 🔐 Authentication

### Register User

**POST** `/api/register/`

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

```json
{
  "username": "TooR",
  "password": "TooR*#"
}
```

**Response:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR..."
}
```

### Logout

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

---

## 🏠 Home API Status

### Project Root (`/`)

**GET** `/`

Returns a simple JSON status confirming the API is live:

```json
{
  "message": "Job Board API is live 🚀",
  "docs": "/api/docs/",
  "api_base": "/api/"
}
```

---

### API Root (`/api/`)

**GET** `/api/`

Returns the DRF API root with resource links:

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

## 👤 Profile Management (User/Admin)

* **Create or Update Profile (User/Admin)** → `POST /api/profile/` or `PATCH /api/profile/{profile_id}/`
* **View Profile (User/Admin)** → `GET /api/profile/{profile_id}/`

Example request:

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

---

## 👥 User Management

* **List All Users (Admin only)** → `GET /api/users/`
* **View Own Applications (User/Admin)** → `GET /api/users/{user_id}/applications/`
* **Search Own Applications (User/Admin)** → `GET /api/users/{user_id}/applications/?search=Market`
* **Update Own Application (User/Admin)** → `PATCH /api/users/{user_id}/applications/{application_id}/`

Supports **multipart/form-data** for file updates:

```bash
curl -X PATCH "http://127.0.0.1:8000/api/users/{user_id}/applications/{application_id}/" \
  -H "Authorization: Bearer <your_token>" \
  -F "cover_letter=@/path/to/updated_cover_letter.pdf"
```

---

## 🏢 Company Management

* **Create Company (Recruiter/Admin)** → `POST /api/companies/`
* **List Companies (Public)** → `GET /api/companies/`
* **Create Job under a Company (Recruiter/Admin)** → `POST /api/companies/{company_id}/jobs/`
* **List Jobs for a Company (Public)** → `GET /api/companies/{company_id}/jobs/`
* **View Applications for a Job (Recruiter/Admin)** → `GET /api/companies/{company_id}/jobs/{job_id}/applications/`
* **Filter Applications (Recruiter/Admin)** → `GET /api/companies/{company_id}/jobs/{job_id}/applications/?resume=true&cover_letter=true`
* **Update Application Status (Recruiter/Admin)** → `PATCH /api/companies/{company_id}/jobs/{job_id}/applications/{application_id}/`

---

## 📂 Categories

* **Create Category (Admin only)** → `POST /api/categories/`
* **List Categories (Public)** → `GET /api/categories/`
* **Update Category (Admin only)** → `PATCH /api/categories/{category_id}/`

---

## 💼 Jobs

* **List All Jobs (Public)** → `GET /api/jobs/`
* **Paginated Jobs** → `GET /api/jobs/?page=3`
* **Filter & Search Jobs** →

  * By employment type: `/api/jobs/?employment_type=full_time`
  * By deadline: `/api/jobs/?deadline=2025-12-31`
  * By search (title/company/location): `/api/jobs/?search=Engineer`

---

## 📝 Job Applications

* **Apply to a Job (User)** → `POST /api/jobs/{job_id}/applications/`

Requires **multipart/form-data**:

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

### ✅ Celery Beat (Scheduled Tasks)

* Deactivates jobs automatically after deadline
* Sends application reminders 5 days before job deadline

### ✅ Signals

* When a new `CompanyReview` is created, a `Notification` is automatically generated via Django signals.

### ✅ Middleware

* Custom `RequestLoggingMiddleware` logs each request with timestamp, user, and path into `requests.log`.
* Integrates with JWT authentication to resolve user identity.

---

## 🚀 Getting Started

1. Register as a **Recruiter** → create companies & jobs
2. Register as a **User** → apply for jobs
3. Use JWT tokens in request headers
4. Explore job postings, apply, and manage applications
5. Create and update your profile
6. Check `requests.log` for API request history

For testing, import the provided **Postman collection**.

---

## ⚙️ CI/CD & Deployment

This project is deployed on **Render Free Tier** with CI/CD powered by **GitHub Actions**.

### 🔹 Render Config (`render.yaml`)

Defines web service & free PostgreSQL database with environment variables.

### 🔹 Continuous Integration (`.github/workflows/ci.yml`)

Runs tests on every push and pull request.

### 🔹 Continuous Deployment (`.github/workflows/dep.yml`)

Automatically triggers a Render deploy when code is pushed to `main`.

Secrets (`RENDER_API_KEY`, `RENDER_SERVICE_ID`) are configured in **GitHub Secrets**. Other sensitive values like `SECRET_KEY`, database credentials, and email configs are stored in **.env** (local) and in **Render Dashboard** (production), never hardcoded.

---
