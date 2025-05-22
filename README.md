# Event Management System

A RESTful API for event scheduling with collaborative editing features.

## 🚀 Live Demo

**API Documentation:** [https://event-management-system-production-5ff4.up.railway.app/docs](https://event-management-system-production-5ff4.up.railway.app/docs)

**Alternative Docs:** [https://event-management-system-production-5ff4.up.railway.app/redoc](https://event-management-system-production-5ff4.up.railway.app/redoc)

## Setup

### Prerequisites

- Python 3.8+
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/event-management-system.git
cd event-management-system
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# Or
venv\Scripts\activate     # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root with:

```env
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=EMS
DATABASE_URI=postgresql://postgres:yourpassword@localhost:5432/EMS
SECRET_KEY=your-secret-key-here
```

### 5. Set up the database

```bash
# Create PostgreSQL database
createdb EMS
```

### 6. Run the application

```bash
 uvicorn main:app --reload
```

### 7. Access the API documentation

- **Local Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Local ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Testing

Once the server is running, you can test the API using the interactive documentation at `http://localhost:8000/docs`

## Features

- 🔐 JWT Authentication with refresh tokens
- 📅 Event CRUD operations with conflict detection
- 🔄 Recurring events support
- 👥 Role-based permissions (Owner, Editor, Viewer)
- 📈 Complete version control and rollback functionality
- 🚀 Rate limiting for security
- 🔄 Batch operations for events

## API Docs
[NeoFi Submission](https://docs.google.com/document/d/11X9uidoriLxSABL9Lb6TQHtp3nY7S2DSK0HGxSzr7WM/edit?usp=sharing)


