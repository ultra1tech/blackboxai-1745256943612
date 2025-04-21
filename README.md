# GlobalMarket - E-commerce Marketplace Platform

A global marketplace platform connecting buyers and sellers worldwide, built with FastAPI and modern web technologies.

## Features

- User Authentication (Buyers & Sellers)
- Product Management
- Order Processing
- Reviews & Ratings
- Wishlist Management
- Analytics Dashboard
- Multi-language Support
- Secure Payments Integration
- Global Shipping Options

## Tech Stack

### Backend
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- MySQL (Database)
- JWT Authentication
- Pydantic (Data validation)

### Frontend
- HTML5
- Tailwind CSS
- JavaScript (ES6+)
- Chart.js (Analytics)

## Setup Instructions

### Prerequisites
- Python 3.8+
- MySQL Server
- Node.js (for serving frontend)

### Backend Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the backend directory with:
```
DATABASE_URL=mysql+mysqlconnector://root:root@localhost:3306/marketplace
SECRET_KEY=your-secret-key-keep-it-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

4. Initialize the database:
```bash
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
```

### Frontend Setup

1. Install a simple HTTP server:
```bash
npm install -g http-server
```

2. Serve the frontend files:
```bash
cd frontend
python3 -m http.server 8000
```

## Running the Application

1. Start the backend server:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

2. Access the application:
- Frontend: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## API Endpoints

### Authentication
- POST /register - Register new user
- POST /token - Login and get access token

### Products
- GET /api/products - List products
- POST /api/products - Create product (sellers only)
- GET /api/products/{id} - Get product details
- PUT /api/products/{id} - Update product
- DELETE /api/products/{id} - Delete product

### Orders
- POST /api/orders - Create order
- GET /api/orders - List orders
- GET /api/orders/{id} - Get order details
- PUT /api/orders/{id}/status - Update order status

### Reviews
- POST /api/reviews - Create review
- GET /api/reviews/product/{id} - Get product reviews
- GET /api/reviews/seller/{id} - Get seller reviews

### Users
- GET /api/users/me - Get current user
- PUT /api/users/profile - Update profile
- GET /api/users/dashboard/stats - Get dashboard statistics

### Categories
- GET /api/categories - List categories
- POST /api/categories - Create category (admin only)
- GET /api/categories/{id}/products - Get category products

### Wishlist
- POST /api/wishlists - Add to wishlist
- GET /api/wishlists - Get wishlist items
- DELETE /api/wishlists/{id} - Remove from wishlist

## Testing

Run the test suite:
```bash
cd backend
pytest
```

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens for authentication
- CORS middleware configured
- Input validation using Pydantic
- SQL injection prevention with SQLAlchemy
- XSS prevention with proper content encoding
- CSRF protection
- Rate limiting on sensitive endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
