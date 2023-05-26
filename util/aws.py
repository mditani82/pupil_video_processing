import glob
import boto3
import os
import cv2
import shutil
from sklearn.model_selection import train_test_split

bucketName = 'pupilengine'
directory = f'{os.getcwd()}/downloads'
imagesDataDirectory  = f'{os.getcwd()}/data/images' 
labelsDataDirectory = f'{os.getcwd()}/data/labels' 
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

        if index == 10:
            break

    splitTrainTest(videoDirectory, filename, labelIndex)

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

def splitTrainTest(videoPath, filename, labelIndex):

    foldersValidation(videoPath, filename, labelIndex)
    
    # getting list of images
    dir_list = os.listdir(videoPath)

    # replacing the extension
    images = []
    for name in dir_list:
        if name[-3:] == 'jpg':
            images.append(name)

    # splitting the dataset
    train_names, test_names = train_test_split(images, test_size=0.3, shuffle=True)

    def batch_move_files(file_list, source_path, destination_path, ext):
        for file in file_list:
            _name = file[:-3] + ext
            shutil.move(os.path.join(source_path, _name), destination_path)
        return

    test_dir = videoPath + f'/images/test_{labelIndex}'
    train_dir = videoPath + f'/images/train_{labelIndex}'

    batch_move_files(train_names, videoPath, train_dir, 'jpg')
    batch_move_files(test_names, videoPath, test_dir, 'jpg')

    test_dir_labels = videoPath + f'/labels/test_{labelIndex}'
    train_dir_labels = videoPath + f'/labels/train_{labelIndex}'

    batch_move_files(train_names, videoPath, train_dir_labels, 'txt')
    batch_move_files(test_names, videoPath, test_dir_labels, 'txt')

    shutil.move(train_dir, imagesDataDirectory) 
    shutil.move(test_dir, imagesDataDirectory) 

    shutil.move(train_dir_labels, labelsDataDirectory) 
    shutil.move(test_dir_labels, labelsDataDirectory) 

def foldersValidation(videoPath, filename, labelIndex):

    if not os.path.exists(videoPath + f'/labels/test_{labelIndex}'):
        os.makedirs(videoPath + f'/labels/test_{labelIndex}')

    if not os.path.exists(videoPath + f'/labels/train_{labelIndex}'):
        os.makedirs(videoPath + f'/labels/train_{labelIndex}')

    if not os.path.exists(videoPath):
        os.makedirs(videoPath)

    if not os.path.exists(videoPath + f'/images/test_{labelIndex}'):
        os.makedirs(videoPath + f'/images/test_{labelIndex}')

    if not os.path.exists(videoPath + f'/images/train_{labelIndex}'):
        os.makedirs(videoPath + f'/images/train_{labelIndex}')

    pass

def modifyYamlFile():
    pass