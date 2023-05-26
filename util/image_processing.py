import os
import cv2

res_height = 1024
directory = f'{os.getcwd()}/downloads'

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