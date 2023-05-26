import glob
import boto3
import os
import cv2
import shutil
from sklearn.model_selection import train_test_split

bucketName = 'pupilengine'
directory = f'{os.getcwd()}/downloads'
res_height = 1024

def readFileFromS3(filename: str):
    file_with_path = f'{directory}/{filename}'

    if os.path.isfile(file_with_path):
        return { 'message': 'Success'}

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketName)

    if bucket.creation_date:
        try:
            obj = s3.Object(bucketName, filename)
            obj.download_file(file_with_path)
            return { 'message': 'Success'}
        except:
             return { 'message': 'File Not Found' }
    else:
        return { 'message': 'Bucket Not Found' }

# def createImagesFromVideo(filename: str):

#     file_with_path = f'{directory}/{filename}'

#     if not os.path.isfile(file_with_path):
#         return { 'message': 'Error'}

#     video_directory = f'{directory}/{filename[:-4]}'
#     if not os.path.isdir(video_directory):
#         os.mkdir(video_directory)                 

#     vid = cv2.VideoCapture(file_with_path)
    

#     index = 0
#     while(True):

#         ret, frame = vid.read()
#         if not ret: 
#             break
#         vid_img_name = f'{filename[:-4]}_{str(index)}.jpg'
#         name = f'{video_directory}/{vid_img_name}'
#         image = image_resize(frame, height = res_height)
#         cv2.imwrite(name, image)
                    
#         index += 1

# def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
#         # initialize the dimensions of the image to be resized and
#         # grab the image size
#         dim = None
#         (h, w) = image.shape[:2]

#         # if both the width and height are None, then return the
#         # original image
#         if width is None and height is None:
#             return image

#         # check to see if the width is None
#         if width is None:
#             # calculate the ratio of the height and construct the
#             # dimensions
#             r = height / float(h)
#             dim = (int(w * r), height)

#         # otherwise, the height is None
#         else:
#             # calculate the ratio of the width and construct the
#             # dimensions
#             r = width / float(w)
#             dim = (width, int(h * r))

#         # resize the image
#         resized = cv2.resize(image, dim, interpolation = inter)

#         # return the resized image
#         return resized

def processVideo(name: str, filename: str, xmin, ymin, xmax, ymax, drawPOI, labelIndex):
    
    #check if video Directory Exist
    videoDirectory = f'{directory}/{filename[:-4]}'
    
    # Clean content of Directory if exist
    if  os.path.isdir(videoDirectory):
        shutil.rmtree(videoDirectory)
    
    # Create Directory if not exist
    if not os.path.isdir(videoDirectory):
        os.mkdir(videoDirectory)

    cap = cv2.VideoCapture(f'{directory}/{filename}')
    tracker = cv2.TrackerMIL_create()
    success, img = cap.read()

    bbox = xmin, ymin, xmax - xmin, ymax - ymin
    # bbox = 309, 654, 759 - 309, 1194 - 654

    tracker.init(img, bbox)

    index = 0
    while True:

        timer = cv2.getTickCount()
        success, img = cap.read()
        sccess, bbox = tracker.update(img)

        if drawPOI == True:
            if success:
                drawBox(img, bbox)
            else:
                cv2.putText(img, "Lost", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)

        # write txt file
        if not generateTxTfiles(img, bbox, labelIndex, filename, index, videoDirectory):
            break

       # write image file
        if not saveImage(filename, index, img, videoDirectory):
            break
                    
        index += 1

        # if index == 10:
        #     break

    splitTrainTest(videoDirectory)

def generateTxTfiles(img, bbox, labelIndex, filename, index, videoDirectory):

    try:
        imgWidth = img.shape[1]
        imgHeight = img.shape[0]
        #rounding to 6 digits after decimal point
        txtXmin = str(round(float(bbox[0])/float(imgWidth),6))
        txtYmin = str(round(float(bbox[1])/float(imgHeight),6))
        txtXmax = str(round(float(bbox[2])/float(imgWidth),6))
        txtYmax = str(round(float(bbox[3])/float(imgHeight),6))

        lineEntry = f"{labelIndex} {txtXmin} {txtYmin} {txtXmax} {txtYmax}"

        vidTxtName = f'{filename[:-4]}_{str(index)}.txt'
        name = f'{videoDirectory}/{vidTxtName}'
        with open(f"{name}", 'w') as fTxt:
            fTxt.write(lineEntry)
        return True
    except:
        return False

def saveImage(filename, index, img, videoDirectory):
    vidImgName = f'{filename[:-4]}_{str(index)}.jpg'
    name = f'{videoDirectory}/{vidImgName}'
    try:
        cv2.imwrite(name, img)  
        return True
    except:
        return False
    
def drawBox(img, bbox):
        x, y, w, h = int(bbox[0]),  int(bbox[1]),  int(bbox[2]),  int(bbox[3])
        cv2.rectangle(img, (x,y), ((x+w), (y+w)), (255,0,255), 3,1)
        cv2.putText(img, "Tracking", (75, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

def splitTrainTest(videoPath):
    
    # getting list of images
    dir_list = os.listdir(videoPath)

    # replacing the extension
    images = []
    for name in dir_list:
        if name[-3:] == 'jpg':
            images.append(name)

    # splitting the dataset
    train_names, test_names = train_test_split(images, test_size=0.3)

    def batch_move_files(file_list, source_path, destination_path):
        for file in file_list:
            image = file[:-3] + 'jpg'
            label = file[:-3] + 'txt'
            shutil.move(os.path.join(source_path, image), destination_path)
            shutil.move(os.path.join(source_path, label), destination_path)
        return

    if not os.path.exists(videoPath):
        os.makedirs(videoPath)

    if not os.path.exists(videoPath + '/images/test'):
        os.makedirs(videoPath + '/images/test')

    if not os.path.exists(videoPath + '/images/train'):
        os.makedirs(videoPath + '/images/train')

    test_dir = videoPath + '/images/test'
    train_dir = videoPath + '/images/train'

    batch_move_files(train_names, videoPath, train_dir)
    batch_move_files(test_names, videoPath, test_dir)
