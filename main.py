from util.aws import readFileFromS3, processVideo

filename = '16850467831781.mp4'

downloadFile = readFileFromS3(filename)

if downloadFile['message'] == 'Success':
    # createImagesFromVideo(filename)
    processVideo('pods', filename, 309, 654, 759 , 1194, False, '1')
else:
    print(downloadFile['message'])
    pass

print('Done')