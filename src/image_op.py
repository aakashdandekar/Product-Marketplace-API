import requests
import os
import base64
from dotenv import load_dotenv
from imagekitio import ImageKit

load_dotenv()

imagekit = ImageKit(
    public_key=os.getenv("PUBLIC_KEY"),
    private_key=os.getenv("PRIVATE_KEY"),
    url_endpoint=os.getenv("IMAGEKIT_ENDPOINT")
)

def upload_to_imagekit(file_bytes, filename):
    url = "https://upload.imagekit.io/api/v1/files/upload"
    files = {'file': (filename, file_bytes)}
    data = {'fileName': filename}

    auth = (os.getenv("PRIVATE_KEY"), "")
            
    response = requests.post(
        url,
        files=files,
        data=data,
        auth=auth
    )
            
    if response.status_code != 200:
        raise Exception(f"ImageKit API Error: {response.text}")
                
    return response.json()