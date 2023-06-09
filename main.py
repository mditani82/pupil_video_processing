from util.aws import readFileFromS3, train
from util.aws_v2 import processVideo

#processVideo(ass_id, videoName, bbox):

from fastapi import FastAPI
from pydantic import BaseModel
import threading
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

origin = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class S3File(BaseModel):
    filename: str
    xmin: str
    ymin: str
    xmax: str
    ymax: str
    ass_id: int

@app.post("/download")
async def download(item: S3File):

    filename = item.filename

    # filename = '1685046783178.mp4'
    # downloadFile = readFileFromS3(filename)
    # if downloadFile['message'] == 'Success':
    
    bbox = item.xmin, item.ymin, item.xmax , item.ymax
    
    processVideo(item.ass_id, videoName, bbox)
    #processVideo(filename, item.xmin, item.ymin, item.xmax , item.ymax, False)
        # processVideo(filename, 309, 654, 759 , 1194, False)
    # return {"message": downloadFile['message']}
    #else:
    #    print(downloadFile['message'])
    return {"message": "Working"}

@app.post("/train")
async def root():
    threading.Thread(target=train).start()
    return {"message": "training started, you'll notified once done."}

@app.get("/model")
async def root():
    return {"message" : "Model"}


# print('Done')
