# 🛍️ Product Marketplace API

A FastAPI-based REST API for a product marketplace, featuring user authentication, image uploads via ImageKit, full-text product search, and purchasing functionality powered by MongoDB.

---

## 🚀 Features

- **User Authentication** — Register and login with JWT-based auth and bcrypt password hashing
- **Product Listings** — Upload products with images; images are auto-converted to JPEG before storage
- **Full-Text Search** — Search products by caption and type using MongoDB text indexes
- **Purchase Flow** — Buy products with availability tracking; records buyer per purchase
- **Image Storage** — Seamless integration with [ImageKit](https://imagekit.io) for cloud image hosting
- **User Profile Fields** — Update up to 5 custom fields on a user profile
- **Job Listings** — Recruiters can post, view, and delete job listings
- **Role-Based Access** — Certain actions (e.g. deleting jobs) are restricted to users with the `recruiter` role

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Server | Uvicorn |
| Database | MongoDB (async via Motor) |
| Authentication | JWT (`python-jose`) + bcrypt (`passlib`) |
| Image Storage | ImageKit (`imagekitio`) |
| Image Processing | Pillow |
| Validation | Pydantic + `email-validator` |

---

## 📁 Project Structure

```
Product-Marketplace-API/
├── main.py                  # Entry point — starts the Uvicorn server
├── requirements.txt         # Python dependencies
├── database_commands.md     # MongoDB index setup reference
└── src/
    ├── app.py               # All API route definitions
    ├── auth.py              # JWT creation, password hashing, auth middleware
    ├── db.py                # MongoDB client and database connection
    ├── image_op.py          # ImageKit client and image upload helper
    ├── operations.py        # MongoDB document serialization utility
    ├── schemas.py           # Pydantic models (User, Product, Login)
    └── __init__.py
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.9+
- MongoDB (local or Atlas)
- [ImageKit](https://imagekit.io) account

### 1. Clone the repository

```bash
git clone https://github.com/aakashdandekar/Product-Marketplace-API.git
cd Product-Marketplace-API
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=mongodb://localhost:27017/
DATABASE_NAME=your_database_name
SECRET_KEY=your_jwt_secret_key

PUBLIC_KEY=your_imagekit_public_key
PRIVATE_KEY=your_imagekit_private_key
IMAGEKIT_ENDPOINT=https://ik.imagekit.io/your_imagekit_id
```

### 4. Set up MongoDB text index

Run the following in your MongoDB shell to enable full-text product search:

```js
db.products.dropIndexes()
db.products.createIndex({ caption: "text", product_type: "text" })
```

### 5. Start the server

```bash
python3 main.py
```

The API will be available at: **`http://localhost:8000`**

Interactive API docs (Swagger UI): **`http://localhost:8000/docs`**

---

## 📡 API Reference

### Authentication

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/register` | Register a new user | No |
| `POST` | `/login` | Log in and receive a JWT token | No |

### Products

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/upload-product` | Upload a new product with an image | Yes |
| `GET` | `/search` | Full-text search over products | No |

### User

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/profile` | Get the authenticated user's profile | Yes |

### Purchasing

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/buy/{product_id}` | Initiate a product purchase | Yes |
| `POST` | `/payment/{product_id}` | Process payment for a product | Yes |

### User Fields

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/update-field` | Add custom fields to the user profile (max 5) | Yes |

### Jobs

| Method | Endpoint | Description | Auth Required | Role Required |
|---|---|---|---|---|
| `POST` | `/add-jobs` | Post a new job listing | Yes | Recruiter |
| `GET` | `/jobs` | List all available job listings | Yes | Any |
| `GET` | `/job/{job_id}` | Get details of a specific job by ID | No | — |
| `DELETE` | `/Job-completed/{job_id}` | Remove a completed or closed job | Yes | Recruiter |

---

## 🔐 Authentication

This API uses **Bearer token** (JWT) authentication. After a successful login, include the token in all authenticated requests:

```
Authorization: Bearer <your_token>
```

> Tokens expire after **2 hours**.

---

## 🖼️ Image Uploads

Product images are stored on [ImageKit](https://imagekit.io). Before upload, all images are automatically converted to **JPEG at 90% quality** regardless of the original format, keeping storage efficient.

---

## 📦 Dependencies

```
fastapi==0.110.0
uvicorn[standard]==0.29.0
motor==3.3.2
pymongo==4.6.1
dnspython==2.6.1
python-jose==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-multipart==0.0.9
email-validator==2.1.1
python-dotenv==1.0.1
imagekitio==3.0.1
requests==2.31.0
urllib3==1.26.18
pillow
```

---

## 📝 Notes

- On registration, users are automatically redirected to `/login` (HTTP 308).
- If a login email is not found in the database, the user is redirected to `/register` (HTTP 308).
- The `/buy/{product_id}` endpoint redirects to `/payment/{product_id}` to complete the transaction.
- Purchasing a product decrements its `availability` count and records the buyer's user ID.
- `/update-field` appends up to **5 custom fields** to the user's profile; attempting to add more returns a `400 Maximum Field` error.
- `/Job-completed/{job_id}` is restricted to users with the `recruiter` role; others receive a `400 Not Authorized` error.
- `/job/{job_id}` validates the ObjectId format and returns `400 Invalid ID format` if malformed.

---

## 📄 License

This project is licensed under the [Apache-2.0 License](LICENSE).
