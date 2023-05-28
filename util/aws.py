import boto3
import os
import cv2
import shutil
from sklearn.model_selection import train_test_split
import ruamel.yaml
from ultralytics import YOLO
from pathlib import Path

bucketName = 'pupilengine'
directory = f'{os.getcwd()}/downloads'
imagesDataDirectory  = f'{os.getcwd()}/data/images/' 
labelsDataDirectory =  f'{os.getcwd()}/data/labels/' 
# res_height = 1024

def readFileFromS3(filename: str):

    #check if downloads folder exist
    if not os.path.isdir(directory):
        os.mkdir(directory)

    file_with_path = f'{directory}/{filename}'

    #check if file is available
    if os.path.isfile(file_with_path):
        for subdir, dirs, files in os.walk(imagesDataDirectory):
            if not subdir == imagesDataDirectory:
                # temp = subdir.replace(imagesDataDirectory[:-7],'')
                if filename in subdir:
                    return { 'message': 'Video already processed'}
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

def processVideo(filename: str, xmin, ymin, xmax, ymax, drawPOI):
    
    #check if video Directory Exist
    videoDirectory = f'{directory}/{filename[:-4]}'

    #delete Data Folder <----------this should be removed.
    # if  os.path.isdir(videoDirectory):
    #     shutil.rmtree(videoDirectory)


    # Clean content of Directory if exist
    # if  os.path.isdir(imagesDataDirectory[:-8]):
    #     shutil.rmtree(imagesDataDirectory[:-8])
    
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
        if not generateTxTfiles(img, bbox, filename, index, videoDirectory):
            break

       # write image file
        if not saveImage(filename, index, img, videoDirectory):
            break
                    
        index += 1

        if index == 10:
            break

    splitTrainTest(videoDirectory, filename)
    modifyYamlFile(filename)
    # train()

def generateTxTfiles(img, bbox, filename, index, videoDirectory):


    labelIndex = 0
    try:
        path = Path('data/dataset.yaml')
        yaml = ruamel.yaml.YAML(typ='safe')
        data = yaml.load(path)
        labelIndex = len(data['names'])
    except:
        labelIndex = 0


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

def splitTrainTest(videoDirectory, filename):

    foldersValidation(videoDirectory, filename)
    
    # getting list of images
    dir_list = os.listdir(videoDirectory)

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

    test_dir = videoDirectory + f'/images/test_{filename}'
    train_dir = videoDirectory + f'/images/train_{filename}'

    test_dir_labels = videoDirectory + f'/labels/test_{filename}'
    train_dir_labels = videoDirectory + f'/labels/train_{filename}'

    batch_move_files(train_names, videoDirectory, train_dir_labels, 'txt')
    batch_move_files(test_names, videoDirectory, test_dir_labels, 'txt')

    batch_move_files(train_names, videoDirectory, train_dir, 'jpg')
    batch_move_files(test_names, videoDirectory, test_dir, 'jpg')

    shutil.move(train_dir, f'{imagesDataDirectory}/train_{filename}') 
    shutil.move(test_dir, f'{imagesDataDirectory}/test_{filename}') 

    shutil.move(train_dir_labels, f'{labelsDataDirectory}/train_{filename}') 
    shutil.move(test_dir_labels, f'{labelsDataDirectory}/test_{filename}') 

    # Clean content of Directory if exist
    # if  os.path.isdir(videoDirectory):
    #     shutil.rmtree(videoDirectory)

def foldersValidation(videoPath, filename):

    if not os.path.exists(videoPath + f'/labels/test_{filename}'):
        os.makedirs(videoPath + f'/labels/test_{filename}')

    if not os.path.exists(videoPath + f'/labels/train_{filename}'):
        os.makedirs(videoPath + f'/labels/train_{filename}')

    if not os.path.exists(videoPath + f'/images/test_{filename}'):
        os.makedirs(videoPath + f'/images/test_{filename}')

    if not os.path.exists(videoPath + f'/images/train_{filename}'):
        os.makedirs(videoPath + f'/images/train_{filename}')

def modifyYamlFile(filename):

    trainFiles = []
    for subdir, dirs, files in os.walk(imagesDataDirectory):
        if not subdir == imagesDataDirectory:
            temp = subdir.replace(imagesDataDirectory[:-7],'')
            if 'train' in temp:
                trainFiles.append(temp)
    
    valFiles = []
    for subdir, dirs, files in os.walk(imagesDataDirectory):
        if not subdir == imagesDataDirectory:

            temp = subdir.replace(imagesDataDirectory[:-7],'')
            if 'test' in temp:
                valFiles.append(temp)

    # Names Dictionary
    names = {}
    try:
        path = Path('data/dataset.yaml')
        yaml = ruamel.yaml.YAML(typ='safe')
        data = yaml.load(path)
        len(data['names'])
        names = data['names']
        names[len(data['names'])] = filename
    except:
        names[0] = filename

    inp = """\
    path:
    train:
        Smith
    val:
        Alice
    test:
    names:
    """
    code = ruamel.yaml.load(inp, ruamel.yaml.RoundTripLoader)
    
    code['path'] = imagesDataDirectory[:-7]
    code['train'] = trainFiles
    code['val'] = valFiles
    code['names'] = names

    yaml = ruamel.yaml.YAML()

    with open(r'data/dataset.yaml', 'w') as file:
        yaml.indent(offset=2)
        yaml.dump(code, file)

def train():
    ROOT_DIR = "/Users/moeitani/Desktop/yolo/gentxttracking/data"
    model = YOLO("yolov8n.yaml")
    results = model.train(data=os.path.join(ROOT_DIR, "dataset.yaml"), epochs=2)
    path = model.export(format="onnx")
    # print(path)
    
    # transfer file to s3
    s3 = boto3.client('s3')
    with open(path, "rb") as f:
        s3.upload_fileobj(f, bucketName, 'best.onnx')