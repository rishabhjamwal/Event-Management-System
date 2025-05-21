# Event Management System

A RESTful API for event scheduling with collaborative editing features.

## Setup

1. Clone the repository

git clone https://github.com/yourusername/event-management-system.git
cd event-management-system

2. Create and activate a virtual environment

python -m venv venv source venv/bin/activate  # On Unix/macOS
Or
venv\Scripts\activate  # On Windows

3. Install dependencies

pip install -r requirements.txt

4. Set up environment variables
Create a `.env` file in the project root with:

POSTGRES_SERVER=localhost:5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
POSTGRES_DB=EMS
DATABASE_URI=postgresql://postgres:yourpassword@localhost:5432/EMS
SECRET_KEY=your-secret-key-here

5. Run the application

uvicorn app.main:app --reload

6. Access the API documentation at `http://localhost:8000/docs`