import boto3
import os
import cv2
import xml.etree.cElementTree as ET
from PIL import Image
import math
import xml.dom.minidom
import shutil
from sklearn.model_selection import train_test_split
from pathlib import Path
import ruamel.yaml

bucketName = 'pupilengine'
downloadsFolder = f'{os.getcwd()}/downloads'
annotationsFolder = f'{os.getcwd()}/annotations'

result = ''
res_height = 1024

convertXML= False
convertTXT= True

baseDataDirectory = f'{os.getcwd()}/data/dataset.yaml' 
imagesDataDirectory  = f'{os.getcwd()}/data/images/' 
labelsDataDirectory =  f'{os.getcwd()}/data/labels/' 

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

# download files from s3
def downloadFile(filename):

    if not os.path.isdir(downloadsFolder):
        os.mkdir(downloadsFolder)
    
    if not os.path.isdir(annotationsFolder):
        os.mkdir(annotationsFolder)

    file_with_path = f'{downloadsFolder}/{filename[:-4]}'
    print("file_with_path: ", file_with_path)

    #check if file exist in folder
    if os.path.isfile(f'{downloadsFolder}/{filename}'):
        print("File Already Exists")
    else:
        print('Filename: ' + filename)
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucketName)

        # print(file_with_path)

        if bucket.creation_date:
            try:
                obj = s3.Object(bucketName, filename)
                obj.download_file(f'{downloadsFolder}/{filename}')
                result =  { 'message': 'Success'}
                # print(result)
                # convertVideoToFrames(filename)
            except:
                result =  { 'message': 'File Not Found' }
                # print(result)
        else:
            result =  { 'message': 'Bucket Not Found' }
            print(result)

# generate images and xmls per video
def convertVideoToFrames(filename, ass_id, bbox):

    vid = cv2.VideoCapture(f'{downloadsFolder}/{filename}')

    index = 0
    while(True):

        ret, frame = vid.read()
        if not ret: 
            break

        img_name = f'{annotationsFolder}/{filename[:-4]}_{index}.jpg'
        xml_name = f'{annotationsFolder}/{filename[:-4]}_{index}.xml'
        txt_name = f'{annotationsFolder}/{filename[:-4]}_{index}.txt'

        image = image_resize(frame, height = res_height)
        cv2.imwrite(img_name, image)

        if convertXML: genXmlFiles(filename, img_name, xml_name, ass_id, bbox)
        if convertTXT: genTxtFiles(txt_name, ass_id, bbox)
                    
        index += 1

def genTxtFiles(txt_name, ass_id, bbox):

    # labelIndex = 0
    # try:
    #     path = Path('data/dataset.yaml')
    #     yaml = ruamel.yaml.YAML(typ='safe')
    #     data = yaml.load(path)
    #     labelIndex = len(data['names'])
    # except:
    #     labelIndex = 0


    if os.path.isfile(f'{baseDataDirectory}'):
        
        try:
            path = Path('data/dataset.yaml')
            yaml = ruamel.yaml.YAML(typ='safe')
            data = yaml.load(path)
            len(data['names'])
            names = data['names']
            # print(names)
            name_values = names.values()
            if  str(ass_id) in name_values:
                # print('Label alreay available')


                key_list = list(names.keys())
                val_list = list(names.values())
                position = val_list.index(str(ass_id))

                labelIndex = key_list[position]


                # return
            else:
                # print('Label added')
                names[len(data['names'])] = str(ass_id)
                labelIndex = len(data['names']) -1
        except:
            names[0] = str(ass_id)
    else:
        # print("File Already processed")
        labelIndex = 0
    


    #rounding to 6 digits after decimal point
    txtXmin = str(bbox[0])
    txtYmin = str(bbox[1])
    txtXmax = str(bbox[2])
    txtYmax = str(bbox[3])

    lineEntry = f"{labelIndex} {txtXmin} {txtYmin} {txtXmax} {txtYmax}"

    with open(txt_name, 'w') as fTxt:
        fTxt.write(lineEntry)
    pass

def genXmlFiles(imageName, img_name, xml_name, ass_id, bbox):

    xmin, ymin, xmax, ymax = bbox

    # fileNameWithAddress = f'{ass_id}/{imageName[:-3]}.jpg'

    # print(img_name)
    # print("--------------")

    # im=Image.open(f'{videoDirectory}/{filename[:-4]}_{str(index)}.jpg' )
    im=Image.open(img_name)
    width= int(im.size[0])
    height= int(im.size[1])

    root = ET.Element("annotation")
    doc = ET.SubElement(root, "folder").text = str(annotationsFolder)
    # ET.SubElement(root, "filename",).text = f'{filename[:-4]}_{str(index)}.jpg'
    ET.SubElement(root, "filename",).text = f'{str(imageName[:-4])}.jpg'

    ET.SubElement(root, "path").text = str(img_name)
    
    source = ET.SubElement(root, "source")
    
    ET.SubElement(source, "database",).text = 'Unknown'

    size = ET.SubElement(root, "size")
    ET.SubElement(size, "width",).text = str(width)
    ET.SubElement(size, "height",).text = str(height)
    ET.SubElement(size, "depth",).text = '3'
    ET.SubElement(root, "segmented",).text = '0'

    # the below should be in a loop
    object = ET.SubElement(root, "object")
    # ET.SubElement(object, "name",).text = getLable(lineEntries[0]) 
    ET.SubElement(object, "name",).text = str(ass_id)
    ET.SubElement(object, "pose",).text = 'Unspecified'
    ET.SubElement(object, "truncated",).text = '0'
    ET.SubElement(object, "difficult",).text = '0'

    xmax = float(xmax) * float(width) 
    xmin = float(xmin) * float(width) 
    ymax = float(ymax) * float(height) 
    ymin = float(ymin) * float(height) 

    # print(xmin, ymin, ymax, ymax)

    bndbox = ET.SubElement(object, "bndbox")
    ET.SubElement(bndbox, "xmin",).text = str(math.ceil(xmin))
    ET.SubElement(bndbox, "ymin",).text = str(math.ceil(ymin))
    ET.SubElement(bndbox, "xmax",).text = str(math.ceil(xmax))
    ET.SubElement(bndbox, "ymax",).text = str(math.ceil(ymax))


    dom = xml.dom.minidom.parseString(ET.tostring(root))
    xml_string = dom.toprettyxml()

    with open(xml_name, 'w') as xfile:
        xfile.write(xml_string)
        xfile.close()
    pass

def foldersValidation(videoPath, filename):

    if not os.path.exists(videoPath + f'/labels/test_{filename}'):
        os.makedirs(videoPath + f'/labels/test_{filename}')

    if not os.path.exists(videoPath + f'/labels/train_{filename}'):
        os.makedirs(videoPath + f'/labels/train_{filename}')

    if not os.path.exists(videoPath + f'/images/test_{filename}'):
        os.makedirs(videoPath + f'/images/test_{filename}')

    if not os.path.exists(videoPath + f'/images/train_{filename}'):
        os.makedirs(videoPath + f'/images/train_{filename}')

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

    if not os.path.exists(test_dir):
        return {'Already available'}
    
    try:
        if convertXML:
            batch_move_files(train_names, videoDirectory, train_dir_labels, 'xml')
            batch_move_files(test_names, videoDirectory, test_dir_labels, 'xml')
        
        if convertTXT:
            batch_move_files(train_names, videoDirectory, train_dir_labels, 'txt')
            batch_move_files(test_names, videoDirectory, test_dir_labels, 'txt')
    except:
        print('error in batch move files xml ot txt')

    try:    
        batch_move_files(train_names, videoDirectory, train_dir, 'jpg')
        batch_move_files(test_names, videoDirectory, test_dir, 'jpg')
    except:
        print('error in batch move files images')

    try:
        shutil.move(train_dir, f'{imagesDataDirectory}/train_{filename}') 
        shutil.move(test_dir, f'{imagesDataDirectory}/test_{filename}') 

        shutil.move(train_dir_labels, f'{labelsDataDirectory}/train_{filename}') 
        shutil.move(test_dir_labels, f'{labelsDataDirectory}/test_{filename}') 
    except:
        print('error in move')

    # Clean content of Directory if exist
    # if  os.path.isdir(videoDirectory):
    #     shutil.rmtree(videoDirectory)

def modifyYamlFile(filename, ass_id):

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
        # print(names)
        name_values = names.values()
        if  str(ass_id) in name_values:
            print('Label alreay available')
            # return
        else:
            print('Label added')
            names[len(data['names'])] = str(ass_id)
    except:
        names[0] = str(ass_id)

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


# ass_id_db = 11
# _lableIndex = 1
# videoList=['202306041854061887273.mp4']
# videoList=['202306050828331681552.mp4']
# videoList=['202306041941353055496.mp4']
# videoNameFromS3='202306050828331681552.mp4'
# videoNameFromS3='202306041941353055496.mp4'
# videoNameFromS3='202306050829275932168.mp4'
# bbox_db = 0.22572815533980584, 0.31330749354005166, 0.7742718446601942, 0.6866925064599483


def processVideo(ass_id, videoName, bbox):
    
    downloadFile(videoName)

    print('Check', f'{imagesDataDirectory}test_{videoName}')
    if os.path.exists(f'{imagesDataDirectory}test_{videoName}'):
        print("File Already processed")
    else:
        convertVideoToFrames(videoName, ass_id, bbox)
        splitTrainTest(annotationsFolder, videoName)
        modifyYamlFile(videoName, ass_id)

# processVideo(ass_id_db, videoNameFromS3, bbox_db)
