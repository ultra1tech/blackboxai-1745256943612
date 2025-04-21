# Marketplace Web Application

## Overview
This is a real application marketplace website backend built with FastAPI, MySQL, and a frontend to be added. It supports seller and buyer accounts, product listings, orders, and authentication.

## Tech Stack
- Backend: FastAPI
- Database: MySQL
- ORM: SQLAlchemy
- Authentication: OAuth2 with JWT
- Frontend: To be added (HTML + Tailwind CSS)
- Database Management: phpMyAdmin

## Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL server running
- phpMyAdmin (optional, for DB management)

### Backend Setup

1. Clone the repository and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your MySQL database and update the `DATABASE_URL` in `.env` file:
   ```
   DATABASE_URL=mysql+mysqlconnector://user:password@localhost:3306/marketplace
   ```

5. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### phpMyAdmin Setup
- Install and configure phpMyAdmin to connect to your MySQL server.
- Access phpMyAdmin via your browser to manage the database visually.

### Frontend
- Frontend files will be added later.
- The backend API is accessible at `http://localhost:8000`.

## API Endpoints
- `POST /register` - Register a new user (buyer or seller)
- `POST /token` - Login and get JWT token
- `GET /users/me` - Get current user info

## Next Steps
- Add product, order, and payment endpoints.
- Build frontend pages with Tailwind CSS.
- Implement multilingual support and payment integrations.
