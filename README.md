# Innovet Tech: Enterprise LMS

## Project Overview

**Innovet Tech** is a high-performance Learning Management System designed for technical mentorship and enterprise-scale course management. Built with a focus on **DevSecOps**, the system ensures secure data handling, role-based access control (RBAC), and a seamless UI/UX using the "Stone & Amber" design language.

---

## Project Structure

This project follows a decoupled monolithic architecture, separating the Django REST API from the React frontend for independent scalability.

```text
innovet-tech-lms/
├── innovet_tech_sch/           # Backend (Django)
│   ├── core/                   # Shared settings & RBAC middleware
│   ├── analytics/              # Enterprise action tracking logic                
│   ├── api/                    # ViewSets & Serializers
│   ├── innovet_tech_sch/       # Authentication
│   ├── manage.py
│   └── requirements.txt
├── innovet_tech_school/        # Frontend (React + Vite)
src/
├── api/                # RTK Query service definitions (adminApi, authApi, etc.)
├── app/                # Global Redux store configuration and root reducer
├── assets/             # Global static files (images, custom fonts)
├── components/         # Reusable UI components organized by role
│   ├── admin/          # Admin-specific UI (Dashboard charts, User tables)
│   ├── analytics/      # Recharts implementation and data visualization
│   ├── auth/           # Login, Registration, and Password Reset forms
│   ├── courses/        # Course cards, Curriculum viewers, and Lesson players
│   ├── layouts/        # Shared wrappers (Navbar, Sidebar, ProtectedRoutes)
│   ├── student/        # Student-facing views (My Enrollments, Profile)
│   ├── teacher/        # Instructor tools (Course Builder, Gradebook)
│   └── ui/             # shadcn/ui primitives (Buttons, Dialogs, Inputs)
├── features/           # Specific complex logic (e.g., audit logs, file uploads)
├── lib/                # Utility configurations (Tailwind-merge, Axios instance)
├── pages/              # Root page components used by the Router
└── school/             # Project-specific constants and branding config
└── README.md

```

---

## Key Features

* **Role-Based Dashboards:** Distinct interfaces for Students, Teachers, and Admins.
* **Course Management:** Full CRUD for courses with nested Topic and Lesson logic.
* **Admin Command Center:** Real-time system metrics, user onboarding, and staff management.
* **Automated Grading:** Task submission workflow with instructor feedback loops.
* **State Management:** Global state handling with Redux Toolkit and RTK Query for "zero-refresh" UI updates.

---

## Tech Stack

### Frontend

* **Framework:** React 18 (Vite)
* **Styling:** Tailwind CSS & shadcn/ui
* **State Management:** Redux Toolkit / RTK Query
* **Icons:** Lucide React

### Backend

* **Framework:** Django 5.x & Django Rest Framework (DRF)
* **Database:** PostgreSQL (Optimized for JSONB task structures)
* **Auth:** JWT (JSON Web Tokens)

---

## Installation & Setup

### Prerequisites

* Python 3.10+
* Node.js 18+
* PowerShell (Recommended for Windows environments)

### 1. Repository Initialization

```bash
# Clone the repository
git clone https://github.com/Kwanusu/innovet_tech_sch.git
cd innovet_tech_sch

```

### 2. Backend Setup

```bash
# Navigate to project root
cd innovet_tech_sch

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the server
python manage.py runserver

```

### 3. Frontend Setup

```bash
# Navigate to client folder
cd ../innovet_tech_school

# Install packages
npm install

# Start development server
npm run dev

```

---

## Design Philosophy

### Architecture Choices

1. **Atomic Transactions:** We use `transaction.atomic` in the Django ViewSets to ensure that if a Lesson fails to save, the entire Topic isn't corrupted.
2. **Optional Chaining:** The frontend utilizes `?.` patterns extensively to handle asynchronous API states without crashing the UI.
3. **Glassmorphism:** The Navbar and Sidebar use `backdrop-blur` to create a modern, high-end feel consistent with the "Innovet" brand.

---

## Security (DevSecOps)

* **CORS Configuration:** Strictly defined to allow only trusted frontend origins.
* **Input Validation:** Serializer-level validation to prevent SQL injection and XSS.
* **Role Protection:** Custom permission classes (`IsAdminUser`, `IsTeacher`) protect sensitive endpoints.

---

## Contribution

1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Innovet Tech: Technical Evaluation Rubric

### 1. Backend Architecture (Django & DRF)

| Criterion | Needs Improvement (0-50%) | Satisfactory (50-85%) | Excellent (85-100%) |
| --- | --- | --- | --- |
| **Data Modeling** | Redundant fields or missing relationships. | Logical relational structure with proper `ForeignKeys`. | Optimized schema using annotations and efficient indexing. |
| **API Design** | Incorrect status codes. URLs are inconsistent. | Standard CRUD via ViewSets. | Implements **Atomic Transactions** and custom RBAC permissions. |
| **Serialization** | Basic ModelSerializers only. No validation logic. | Uses `SerializerMethodField` for calculated data. | Advanced nested relationship handling and sensitive field filtering. |

### 2. Frontend Implementation (React & Redux)

| Criterion | Needs Improvement (0-50%) | Satisfactory (50-85%) | Excellent (85-100%) |
| --- | --- | --- | --- |
| **State Management** | Over-reliance on local `useState`. Prop drilling. | Centralized state using Redux Toolkit slices. | Fully implemented **RTK Query** with cache invalidation (tags). |
| **Component Design** | Monolithic components. Hardcoded styles. | Functional components using Tailwind & UI primitives. | Highly modular architecture using **shadcn/ui** and custom hooks. |
| **Resilience** | App crashes on API errors. | Basic error handling via `try/catch`. | Uses **Optional Chaining** and **Loading Skeletons** for crash-free UX. |

### 3. Professional Standards (The "Innovet" Edge)

| Criterion | Needs Improvement (0-50%) | Satisfactory (50-85%) | Excellent (85-100%) |
| --- | --- | --- | --- |
| **Code Quality** | Commented-out code. No naming convention. | Clean code following PEP8/ESLint standards. | Professional documentation and strict DRY principles. |
| **UI/UX Branding** | Generic styling. Inconsistent spacing. | Follows "Stone & Amber" palette. | High-fidelity design with glassmorphism and smooth transitions. |

---

### Instructor Tip: How to Grade

* **The "404/500" Test:** If the student's dashboard crashes when the API is down, they cannot score higher than "Satisfactory" in Resilience.
* **The "Atomic" Test:** Check if they used `transaction.atomic` for complex updates. This is a hallmark of a "Lead Architect" mindset.
* **The "DevSecOps" Test:** Check if they properly restricted the Admin stats endpoint so a student cannot access it via a direct URL tool.
