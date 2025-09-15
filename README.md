# 💼 Job Board Platform API

A RESTful Job Board API built with **Django REST Framework**, featuring **JWT authentication**, **role-based access**, **company/job management**, **applications with file uploads**, **search/filtering with pagination**, and **automated job/application scheduling with Celery Beat**.

---

## 🗂️ Entity Relationship Diagram (ERD)

Here’s the ERD for the project:

![Job Board ERD](https://drive.google.com/uc?export=view\&id=1KUDq3uOOnSMyTpV5Zv8_1qLTsNud6xiW)

👉 [Open ERD in Google Drive](https://drive.google.com/file/d/1KUDq3uOOnSMyTpV5Zv8_1qLTsNud6xiW/view?usp=sharing)


```

## ⚙️ Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Run workers & beat for background tasks:

```bash
celery -A job_board worker -l info
celery -A job_board beat -l info
```

The API will be available at `http://127.0.0.1:8000/`

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

All protected endpoints require:

```
Authorization: Bearer <access_token>
```

---

## 👥 User Management

### List All Users (Admin only)

**GET** `/api/users/`

### View Own Applications (User/Admin)

**GET** `/api/users/{user_id}/applications/`

### Search Own Applications (User/Admin)

**GET** `/api/users/{user_id}/applications/?search=Market`

### Update Own Application (User/Admin)

**PATCH** `/api/users/{user_id}/applications/{application_id}/`

Since updates may include new files, use **multipart/form-data**:

```bash
curl -X PATCH "http://127.0.0.1:8000/api/users/{user_id}/applications/{application_id}/" \
  -H "Authorization: Bearer <your_token>" \
  -F "cover_letter=@/path/to/updated_cover_letter.pdf"
```

---

## 🏢 Company Management

### Create Company (Recruiter/Admin)

**POST** `/api/companies/`

```json
{
  "name": "RomaxCorp",
  "email": "kibet.evans95@gmail.com",
  "location": "Nairobi, Kenya",
  "industry": "Software"
}
```

### List Companies (Public)

**GET** `/api/companies/`

### Create Job under a Company (Recruiter/Admin)

**POST** `/api/companies/{company_id}/jobs/`

```json
{
  "title": "Backend Developer",
  "description": "Work on scalable APIs using Django REST Framework.",
  "category_id": 1,
  "salary": "150000.00",
  "deadline": "2025-12-31T23:59:59Z",
  "employment_type": "full_time"
}
```

### List Jobs for a Company (Public)

**GET** `/api/companies/{company_id}/jobs/`

### View Applications for a Job (Recruiter/Admin)

**GET** `/api/companies/{company_id}/jobs/{job_id}/applications/`

### Filter Applications (Recruiter/Admin)

**GET** `/api/companies/{company_id}/jobs/{job_id}/applications/?resume=true&cover_letter=true`

### Update Application Status (Recruiter/Admin)

**PATCH** `/api/companies/{company_id}/jobs/{job_id}/applications/{application_id}/`

```json
{
  "status": "accepted"
}
```

---

## 📂 Categories

### Create Category (Admin only)

**POST** `/api/categories/`

```json
{
  "name": "Software Engineering",
  "description": "Jobs related to software development."
}
```

### List Categories (Public)

**GET** `/api/categories/`

### Update Category (Admin only)

**PATCH** `/api/categories/{category_id}/`

---

## 💼 Jobs

### List All Jobs (Public)

**GET** `/api/jobs/`

### Paginated Jobs

**GET** `/api/jobs/?page=3`

### Filter & Search Jobs

* By employment type: `/api/jobs/?employment_type=full_time`
* By deadline: `/api/jobs/?deadline=2025-12-31`
* By title/company/location (search): `/api/jobs/?search=Engineer`

---

## 📝 Job Applications

### Apply to a Job (User)

**POST** `/api/jobs/{job_id}/applications/`

Requires **multipart/form-data**:

```bash
curl -X POST "http://127.0.0.1:8000/api/jobs/7/applications/" \
  -H "Authorization: Bearer <your_token>" \
  -F "cover_letter=@/path/to/cover_letter.pdf" \
  -F "resume=@/path/to/resume.pdf"
```

### View Own Applications (User/Admin)

**GET** `/api/users/{user_id}/applications/`

---

## 🔄 Scheduled Tasks (Celery Beat)

Two recurring tasks run automatically via **Celery Beat**:

1. **Deactivate expired jobs**

   * Checks jobs past their `deadline`
   * Sets `is_active = false`

2. **Send application reminders**

   * Reminds recruiters about pending applications
   * Marks applications as `is_completed = true` once finalized

Configured in **`settings.py`** with `CELERY_BEAT_SCHEDULE`.

---

## 🔐 Role-Based Access Control

| Role          | Permissions                                                            |
| ------------- | ---------------------------------------------------------------------- |
| **User**      | Apply to jobs, view & update own applications, update own profile      |
| **Recruiter** | Create companies, post jobs, view & manage applications for their jobs |
| **Admin**     | Full access: manage users, companies, jobs, categories, applications   |

---

## 📊 Response Format

Paginated list responses:

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

## 🔧 Features

* **JWT Authentication** with refresh tokens
* **File Uploads** (resumes, cover letters) via multipart/form-data
* **Advanced Filtering & Search** for jobs and applications
* **Role-Based Permissions** (User, Recruiter, Admin)
* **Pagination** for all list endpoints
* **Email Notifications** via Celery
* **Automated Scheduling with Celery Beat** (job expiry + reminders)
* **Model Enhancements**

  * `Job.is_active` → marks active/expired jobs
  * `Application.is_completed` → marks finished applications

---

## 📁 File Uploads

Supports **PDF uploads** for:

* **Resumes** (required)
* **Cover Letters** (optional)

Stored securely on the server.

---

## 🚀 Getting Started

1. Register as a **Recruiter** → create companies & jobs
2. Register as a **User** → apply for jobs
3. Use JWT tokens in request headers
4. Explore job postings, apply, and manage applications
5. Celery Beat ensures jobs expire and reminders are automated

For testing, import the provided **Postman collection**.

---




Perfect 👍 since you already have the ERD image, we can embed it in the README with a Google Drive (or GitHub repo) link.

Here’s how it fits into your updated README:

---

# 💼 Job Board Platform API

A RESTful Job Board API built with **Django REST Framework**, featuring **JWT authentication**, **role-based access**, **company/job management**, **applications with file uploads**, **search/filtering with pagination**, and **automated job/application scheduling with Celery Beat**.

---

## 🗂️ Entity Relationship Diagram (ERD)

Here’s the ERD for the project:

![Job Board ERD](https://drive.google.com/uc?export=view\&id=YOUR_FILE_ID)

👉 [Open ERD in Google Drive](https://drive.google.com/file/d/YOUR_FILE_ID/view?usp=sharing)


```


