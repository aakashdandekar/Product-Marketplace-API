import io
from PIL import Image
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Form, Query
from fastapi.responses import RedirectResponse
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
from src.db import database
from src.schemas import User, Login, Job
from src.auth import hash, check_hash, get_current_user, create_access_token
from typing import Literal

app = FastAPI()

@app.post('/register')
async def register_user(user: User):
    try:
        collection = database["user"]

        exist = await collection.find_one({
            "$or": [
                {"name": user.name},
                {"email": user.email}
            ]
        })

        if exist:
            raise HTTPException(status_code=400, detail="User already exists!")

        password = hash(user.password)

        await collection.insert_one({
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "password": password,
            "field": [],
            "worked_at": [],
            "created_at": datetime.now(timezone.utc)
        })

        return {"message": "User registeration successful"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/login")
async def login_user(login: Login):
    try:
        collection = database["user"]
        user = await collection.find_one({"email": login.email})

        if check_hash(login.password, user["password"]):
            token = create_access_token(user_id=str(user["_id"]))
        else:
            raise HTTPException(status_code=401, detail="Invalid Credential")

        return {"access_token": token}

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post('/update-field')
async def update_field(
    fields: list[str],
    current_user: str = Depends(get_current_user)
):
    try:
        collection = database["user"]
        user = await collection.find_one({"_id": ObjectId(current_user)})

        if len(user.get("field", [])) == 0:
            await collection.update_one(
                {"_id": ObjectId(current_user)},
                {"$push": {"field": {"$each": fields[:4]}}}
            )
        
        if len(user.get("field", [])) == 5:
            raise HTTPException(status_code=400, detail="Maximum Field")

            return {"message": "fields updated successfully"}

        raise HTTPException(status_code=404, detail="User not found")

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post('/add-jobs')
async def add_job(
    job_listing: Job,
    current_user: str = Depends(get_current_user)
):
    try:
        user_collection = database["user"]
        collection = database["jobs"]

        user = await user_collection.find_one({"_id": ObjectId(current_user)})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user["role"] == "recruiter":
            await collection.insert_one({
                "title": job_listing.title,
                "description": job_listing.description,
                "field": job_listing.field,
                "pay": job_listing.pay,
                "currency": job_listing.currency
            })
        else:
            raise HTTPException(status_code=400, detail="Not Authorized")

        return {"Job Listed": job_listing.title}

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get('/')
async def load_jobs(current_user: str = Depends(get_current_user)):
    try:
        jobs = database["jobs"].aggregate([{
            "$sample": {
                "size": 100
            }
        }])
        user_collection = database["user"]
        user = await user_collection.find_one({"_id": ObjectId(current_user)})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_fields = set(user.get("field", []))

        result = []

        async for job in jobs:
            job["_id"] = str(job["_id"])
            if not user_fields:
                result.append(job)
            else:
                job_field = job.get("field", "")
                if job_field in user_fields:
                    result.append(job)

        result = list(result)
        return {
            "count": len(result),
            "jobs": result
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get('/job/{job_id}')
async def get_job(job_id: str):
    try:
        if not ObjectId.is_valid(job_id):
            raise HTTPException(status_code=400, detail="Invalid ID format")

        jobs = database["jobs"]
        job = await jobs.find_one({"_id": ObjectId(job_id)})

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        job["_id"] = str(job["_id"])    

        return {"job": job}

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.delete('/Job-completed/{job_id}')
async def remove_job(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    try:
        user_collection = database["user"]
        user = await user_collection.find_one({"_id": ObjectId(current_user)})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user["role"] != "recruiter":
            raise HTTPException(status_code=400, detail="Not Authorized")

        jobs = database["jobs"]
        result = await jobs.delete_one({"_id": ObjectId(job_id)})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Job not found")

        return {
            "message": "Job deleted successfully",
            "id": job_id
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")