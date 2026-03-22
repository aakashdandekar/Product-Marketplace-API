from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Form
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from src.image_op import imagekit, upload_to_imagekit
from bson import ObjectId
from src.db import database
from src.schemas import User, Login
from src.auth import hash, check_hash, get_current_user, create_access_token


app = FastAPI()

@app.post('/register')
async def register_user(user: User):
    try:
        collection = database["user"]

        exist = await collection.find_one({
            "$or": [
                {"email": user.email},
                {"name": user.name}
            ]
        })

        if exist:
            raise HTTPException(status_code=400, detail="User already exists!")

        password = hash(password=user.password)

        result = await collection.insert_one({
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "password": password,
            "created_at": datetime.now(tz=timezone.utc)
        })

        token = create_access_token(str(result.inserted_id))

        return {
            "message": "User registered successfully",
            "access_token": token
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post('/login')
async def login_user(login: Login):
    try:
        collection = database["user"]
        db_user = await collection.find_one({
            "email": login.email
        })

        if not db_user:
            raise HTTPException(status_code=401, detail="User not found")

        if check_hash(login.password, db_user["password"]):
            token = create_access_token(str(db_user["_id"]))
        else:
            raise HTTPException(status_code=401, detail="Invalid Credentials")

        return {"access_token": token}

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/upload-product")
async def upload_product(
    file: UploadFile = File(...),
    caption: str = Form(""),
    price: int = Form(),
    availability: int = Form(),
    sold: int = Form(),
    user_id: str = Depends(get_current_user)
):
    try:
        collection = database["products"]
        contents = await file.read()

        upload_response = await run_in_threadpool(
            upload_to_imagekit,
            contents,
            file.filename
        )

        file_id = upload_response.get("fileId")
        img_url = upload_response.get("url")
        
        if not file_id or not img_url:
            raise HTTPException(status_code=500, detail="Invalid response from ImageKit")

        result = await collection.insert_one({
            "image_id": file_id,
            "user_id": ObjectId(user_id),
            "post_url": img_url,
            "caption": caption,
            "price": price,
            "availability": availability,
            "sold": sold
        })

        return {
            "id": str(result.inserted_id),
            "image_url": img_url
        }
    
    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

"""
@app.get('/')
async def load_feed(user=Depends(get_current_user)):
    try:
        collection = database["products"]


    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
"""