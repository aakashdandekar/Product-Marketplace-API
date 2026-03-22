# 🛍️ Product Marketplace API

A FastAPI-based backend for a product marketplace with user authentication, image uploads, product search, and purchasing functionality.

---

## Tech Stack

- **Framework:** FastAPI
- **Database:** MongoDB (via Motor — async driver)
- **Authentication:** JWT (python-jose) + bcrypt password hashing
- **Image Storage:** ImageKit
- **Server:** Uvicorn

---

## Project Structure

```
├── main.py           # Entry point — runs the Uvicorn server
└── src/
    ├── app.py        # All route definitions
    ├── auth.py       # JWT creation, password hashing, auth middleware
    ├── db.py         # MongoDB client and database connection
    ├── image_op.py   # ImageKit client and upload helper
    ├── operations.py # MongoDB document serialization utility
    ├── schemas.py    # Pydantic models (User, Product, Login)
    └── __init__.py
```

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd <repo-folder>
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net
DATABASE_NAME=your_database_name
SECRET_KEY=your_jwt_secret_key

PUBLIC_KEY=your_imagekit_public_key
PRIVATE_KEY=your_imagekit_private_key
IMAGEKIT_ENDPOINT=https://ik.imagekit.io/your_imagekit_id
```

### 4. Set up MongoDB text index

Run the following in your MongoDB shell to enable full-text search on products:

```js
db.products.dropIndexes()
db.products.createIndex({ caption: "text", product_type: "text" })
```

### 5. Run the server

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

---

## API Endpoints

### Auth

| Method | Endpoint    | Description                        | Auth Required |
|--------|-------------|------------------------------------|---------------|
| POST   | `/register` | Register a new user                | No            |
| POST   | `/login`    | Log in and receive a JWT token     | No            |

### Products

| Method | Endpoint           | Description                              | Auth Required |
|--------|--------------------|------------------------------------------|---------------|
| POST   | `/upload-product`  | Upload a new product with an image       | Yes           |
| GET    | `/search`          | Full-text search over products           | No            |

### User

| Method | Endpoint   | Description                     | Auth Required |
|--------|------------|---------------------------------|---------------|
| GET    | `/profile` | Get the current user's profile  | Yes           |

### Purchasing

| Method | Endpoint              | Description                           | Auth Required |
|--------|-----------------------|---------------------------------------|---------------|
| POST   | `/buy/{product_id}`   | Purchase a product                    | Yes           |
| POST   | `/payment/{product_id}` | Process payment for a product       | Yes           |

---

## Authentication

The API uses **Bearer token** authentication. After logging in, include the token in the `Authorization` header:

```
Authorization: Bearer <your_token>
```

Tokens expire after **2 hours**.

---

## Image Uploads

Product images are uploaded to [ImageKit](https://imagekit.io). Images are automatically converted to JPEG (quality 90) before upload, regardless of the original format.

---

## Notes

- On registration, users are redirected to `/login` (HTTP 308).
- If a login email is not found, the user is redirected to `/register` (HTTP 308).
- Purchasing a product decrements its `availability` count and records the buyer.
- The `/buy` endpoint redirects to `/payment` to complete the transaction.
