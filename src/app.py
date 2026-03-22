import io
from PIL import Image
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from src.image_op import imagekit, upload_to_imagekit
from bson import ObjectId
from src.db import database
from src.schemas import User, Login
from src.auth import hash, check_hash, get_current_user, create_access_token
from src.operations import serialize_doc


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
            "purchases": [],
            "created_at": datetime.now(tz=timezone.utc)
        })

        token = create_access_token(str(result.inserted_id))

        return RedirectResponse(url="/login", status_code=308)

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
            return RedirectResponse(url="/register", status_code=308)

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
    product_type: str = Form(""),
    price: int = Form(),
    availability: int = Form(),
    sold: int = Form(),
    user_id: str = Depends(get_current_user)
):
    try:
        collection = database["products"]
        contents = await file.read()

        img = Image.open(io.BytesIO(contents)).convert("RGB")
        output = io.BytesIO()

        img.save(output, format="JPEG", quality=90)
        output.seek(0)

        upload_response = await run_in_threadpool(
            upload_to_imagekit,
            output.getvalue(),
            file.filename.replace(".png", ".jpg")
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
            "product_type": product_type,
            "price": price,
            "availability": availability,
            "sold": sold,
            "buyers": []
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

@app.get('/search')
async def load_Product(search: str = Query("")):
    try:
        collection = database["products"]
        result = []

        cursor = collection.find(
            {"$text": {"$search": search}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})])

        async for doc in cursor:
            result.append(serialize_doc(doc))

        return {
            "query": search,
            "count": len(result),
            "results": result
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get('/profile')
async def load_current_profile(user = Depends(get_current_user)):
    try:
        collection = database["user"]
        profile = await collection.find_one({"_id": ObjectId(user)})

        if not profile:
            raise HTTPException(status_code=404, detail="User not found")

        return serialize_doc(profile)

    except HTTPException:
        raise
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Inernal Server Error")

@app.post('/buy/{product_id}')
async def buy_product(
    product_id: str,
    user = Depends(get_current_user)
):
    try:
        product_collection = database["products"]
        user_collection = database["user"]

        product = await product_collection.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(status_code=400, detail="Product not found")

        if product["availability"] <= 0:
            raise HTTPException(status_code=404, detail="Product out of stock")

        await product_collection.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$inc": {
                    "availability": -1,
                    "sold": 1
                },
                "$push": {
                    "buyers": str(user if isinstance(user, str) else user["_id"])
                }
            }
        )

        await user_collection.update_one(
            {"_id": ObjectId(user if isinstance(user, str) else user["_id"])},
            {
                "$push": {
                    "purchases": product_id
                }
            }
        )

        return RedirectResponse(url=f"/payment/{product_id}", status_code=308)

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post('/payment/{product_id}')
async def payment(
    product_id: str,
    user = Depends(get_current_user)
):
    try:
        transaction_collection = database["transaction"]
        product_collection = database["products"]

        product = await product_collection.find_one({
                "_id": ObjectId(product_id)
            })

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        await transaction_collection.insert_one({
            "product_id": product_id,
            "transaction": product["price"],
            "create_at": datetime.now(tz=timezone.utc)
        })

        return {
            "message": "Payment Successful",
            "amount": product['price']
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")