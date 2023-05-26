import boto3
import os
import cv2

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

def createImagesFromVideo(filename: str):

    file_with_path = f'{directory}/{filename}'

    if not os.path.isfile(file_with_path):
        return { 'message': 'Error'}

    video_directory = f'{directory}/{filename[:-4]}'
    if not os.path.isdir(video_directory):
        os.mkdir(video_directory)                 

    vid = cv2.VideoCapture(file_with_path)
    

    index = 0
    while(True):

        ret, frame = vid.read()
        if not ret: 
            break
        vid_img_name = f'{filename[:-4]}_{str(index)}.jpg'
        name = f'{video_directory}/{vid_img_name}'
        image = image_resize(frame, height = res_height)
        cv2.imwrite(name, image)
                    
        index += 1

def image_resize(image, width = None, height = None, inter = cv2.INTER_AREA):
        # initialize the dimensions of the image to be resized and
        # grab the image size
        dim = None
        (h, w) = image.shape[:2]

        # if both the width and height are None, then return the
        # original image
        if width is None and height is None:
            return image

        # check to see if the width is None
        if width is None:
            # calculate the ratio of the height and construct the
            # dimensions
            r = height / float(h)
            dim = (int(w * r), height)

        # otherwise, the height is None
        else:
            # calculate the ratio of the width and construct the
            # dimensions
            r = width / float(w)
            dim = (width, int(h * r))

        # resize the image
        resized = cv2.resize(image, dim, interpolation = inter)

        # return the resized image
        return resized

def generateTxTFiles(name: str, filename: str, xmin, ymin, xmax, ymax):
    
    video_directory = f'{directory}/{filename[:-4]}'
    if not os.path.isdir(video_directory):
        os.mkdir(video_directory)   

    print(video_directory)
    print(f'{directory}/{filename}')
    
    cap = cv2.VideoCapture(f'{directory}/{filename}')
    tracker = cv2.TrackerMIL_create()
    success, img = cap.read()
    # bbox = xmin, ymin, xmax, ymax
    bbox = 88, 132, 142, 277
    tracker.init(img, bbox)

    index = 0
    while True:
        timer = cv2.getTickCount()
        success, img = cap.read()

        sccess, bbox = tracker.update(img)

        print(bbox)

        # write txt file

        # save image file

        
        
        vid_img_name = f'{filename[:-4]}_{str(index)}.jpg'
        name = f'{video_directory}/{vid_img_name}'

        print(vid_img_name)
        print(name)

        cv2.imwrite(name, img)
                    
        index += 1
