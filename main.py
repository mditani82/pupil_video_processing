from util.aws import readFileFromS3, processVideo, train

from fastapi import FastAPI
from pydantic import BaseModel
import threading


app = FastAPI()

class S3File(BaseModel):
    filename: str
    xmin: int
    ymin: int
    xmax: int
    ymax: int

@app.post("/download")
async def download(item: S3File):

    filename = item.filename

    # filename = '1685046783178.mp4'
    downloadFile = readFileFromS3(filename)
    if downloadFile['message'] == 'Success':
        processVideo(filename, item.xmin, item.ymin, item.xmax , item.ymax, False)
        # processVideo(filename, 309, 654, 759 , 1194, False)
        return {"message": downloadFile['message']}
    else:
        print(downloadFile['message'])
        return {"message": downloadFile['message']}

@app.post("/train")
async def root():
    threading.Thread(target=train).start()
    return {"message": "training started, you'll notified once done."}

@app.get("/model")
async def root():
    return {"message" : "Model"}


# print('Done')
