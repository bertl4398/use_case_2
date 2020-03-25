import io
import secrets

from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware

from minio import Minio
from minio.error import (ResponseError, BucketAlreadyOwnedByYou,
                         BucketAlreadyExists)

from typing import List
from pydantic import BaseModel


class Data(BaseModel):
    hr: List[int] = []


minioClient = Minio('minio:9000',
                    access_key='minio',
                    secret_key='minio1234',
                    secure=False)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBasic()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(
        credentials.username, "stanleyjobson")
    correct_password = secrets.compare_digest(
        credentials.password, "swordfish")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.post("/upload/video")
async def create_upload_video(file: UploadFile = File(...),
                              username: str = Depends(get_current_username)):
    contents = await file.read()
    contents_length = len(contents)
    await file.seek(0)

    # Make a bucket with the make_bucket API call.
    try:
        minioClient.make_bucket(username)
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass
    except ResponseError as err:
        raise

    # Put an object 'pumaserver_debug.log' with contents from 'pumaserver_debug.log'.
    try:
        minioClient.put_object(
            username, 'video.mp4', file.file, contents_length)
    except ResponseError as err:
        print(err)

    return {"message": "success"}


@app.post("/upload/data")
async def create_upload_data(data: Data,
                             username: str = Depends(get_current_username)):
    output = io.BytesIO()
    output_len = output.write(bytes(data.hr))
    output.seek(0)

    # Make a bucket with the make_bucket API call.
    try:
        minioClient.make_bucket(username)
    except BucketAlreadyOwnedByYou as err:
        pass
    except BucketAlreadyExists as err:
        pass
    except ResponseError as err:
        raise

    # Put an object 'debug.log' with contents from 'debug.log'.
    try:
        minioClient.put_object(username, 'heartrate.dat', output, output_len)
    except ResponseError as err:
        print(err)
    return {"message": "success"}
