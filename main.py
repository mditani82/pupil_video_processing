from util.aws import readFileFromS3, createImagesFromVideo, generateTxTFiles

filename = '1685046783178.mp4'

downloadFile = readFileFromS3(filename)

if downloadFile['message'] == 'Success':
    # createImagesFromVideo(filename)
    generateTxTFiles('pods', filename, '0', '0', '0', '0')
else:
    print(downloadFile['message'])
    pass

print('Done')