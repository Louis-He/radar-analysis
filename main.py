from PIL import Image, ImageSequence
import time
from urllib import request

URL = "https://dd.weather.gc.ca/radar/PRECIPET/GIF/WKR/"
UTCoffset = 4

# convert image to radar precipitation level
def convertRGBtoPrepLevel(_width, _height, radarpix):
    prepLevelMatrix = [None] * _height
    for i in range(len(prepLevelMatrix)):
        prepLevelMatrix[i] = [0] * _width

    for h in range(_height):
        for w in range(_width):
            r, g, b = radarpix[w, h]

            if([r, g, b] == [153, 204, 255]): # bottom
                prepLevelMatrix[h][w] = 1
            elif([r, g, b] == [0, 153, 255]):
                prepLevelMatrix[h][w] = 2
            elif ([r, g, b] == [0, 255, 102]): # bottom green
                prepLevelMatrix[h][w] = 3
            elif ([r, g, b] == [0, 204, 0]):
                prepLevelMatrix[h][w] = 4
            elif ([r, g, b] == [0, 153, 0]):
                prepLevelMatrix[h][w] = 5
            elif ([r, g, b] == [0, 102, 0]):
                prepLevelMatrix[h][w] = 6
            elif ([r, g, b] == [255, 255, 51]): # bottom yellow
                prepLevelMatrix[h][w] = 7
            elif ([r, g, b] == [255, 204, 0]):
                prepLevelMatrix[h][w] = 8
            elif ([r, g, b] == [255, 153, 0]):
                prepLevelMatrix[h][w] = 9
            elif ([r, g, b] == [255, 102, 0]): # bottom orange
                prepLevelMatrix[h][w] = 10
            elif ([r, g, b] == [255, 0, 0]): # red
                prepLevelMatrix[h][w] = 11
            elif ([r, g, b] == [255, 2, 153]): # pink
                prepLevelMatrix[h][w] = 12
            elif ([r, g, b] == [153, 51, 204]): # purple
                prepLevelMatrix[h][w] = 13
            elif ([r, g, b] == [102, 0, 153]): # top level
                prepLevelMatrix[h][w] = 14

    return (prepLevelMatrix)

# number to string
def coreAreaReminder(coreAvg):
    if coreAvg == 0:
        return "无明显降水"
    elif coreAvg < 1:
        return "部分地区有弱降水"
    elif coreAvg < 2:
        return "有弱降水"
    elif coreAvg < 5:
        return "有中等强度降水"
    elif coreAvg < 7:
        return "有高强度降水"
    else:
        return "雨量较大，注意防范"

# analyze according to radar level
def analyzeRadar(_width, _height, radarLevel):
    grids = splitGrid(_width, _height, radarLevel)
    coreArea = analyzeCoreToronto(_width, _height, radarLevel)
    print(analyzeSmallZone(_width, _height, grids))
    print(coreArea)
    print(coreAreaReminder(coreArea))

def analyzeSmallZone(_width, _height, grids):
    sum = 0
    count = 0
    for h in range(17, 20):
        for w in range(16, 19):
            sum += grids[h][w]
            count += 1
    average = sum / count
    return average

def analyzeCoreToronto(_width, _height, radarLevel):
    sum = 0
    count = 0
    for h in range(int(_height * 0.54), int(_height * 0.58)): # up and down axis
        for w in range(int(_width * 0.51), int(_width * 0.54)): # left and right axis
            sum += radarLevel[h][w]
            count += 1

    return sum / count

def splitGrid(_width, _height, radarLevel):
    prepLevelMatrix = [None] * 33
    for i in range(len(prepLevelMatrix)):
        prepLevelMatrix[i] = [0] * 33

    heightlow = 0
    heightHigh = 0.03

    for i in range(33):
        widthlow = 0
        widthHigh = 0.03
        for j in range(33):
            sum = 0
            count = 0
            for h in range(int(_height * heightlow), int(_height * heightHigh)):
                for w in range(int(_width * widthlow), int(_width * widthHigh)):
                    sum += radarLevel[h][w]
                    count += 1
            prepLevelMatrix[i][j] = sum / count
            widthlow += 0.03
            widthHigh += 0.03
        heightHigh += 0.03
        heightlow += 0.03

    return prepLevelMatrix

# time related calculation
def latestPossiblePic(timeStamp):
    minute = int(time.strftime("%M", time.localtime(timeStamp)))
    newminute = 0

    if(minute < 10):
        newminute = 0
    elif(minute < 20):
        newminute = 10
    elif (minute < 30):
        newminute = 20
    elif (minute < 40):
        newminute = 30
    elif (minute < 50):
        newminute = 40
    elif (minute < 60):
        newminute = 50

    timeDelta = minute - newminute
    timeStamp = timeStamp - timeDelta * 60

    return timeStamp

# download previous 30 mins radar images
def downloadPrepRes():
    nowTime = time.time() + UTCoffset * 60 * 60
    nowTime = latestPossiblePic(nowTime)
    nowTimeStr = time.strftime("%Y%m%d%H%M_WKR_PRECIPET_RAIN.gif", time.localtime(nowTime))

    try:
        request.urlretrieve(URL + nowTimeStr, "test.gif")
    except:
        nowTime = nowTime - 10 * 60

    nowTimeSingle = nowTime
    for i in range(4):
        nowTimeSingleStr = time.strftime("%Y%m%d%H%M_WKR_PRECIPET_RAIN.gif", time.localtime(nowTimeSingle))
        request.urlretrieve(URL + nowTimeSingleStr, str(i) + ".gif")

        nowTimeSingle = nowTimeSingle - 10 * 60

def analyzePic(src):
    # https://dd.weather.gc.ca/radar/PRECIPET/GIF/WKR/201906041800_WKR_PRECIPET_RAIN.gif
    im = Image.open(src)
    it = ImageSequence.Iterator(im)

    radarImg = it[0]
    width = radarImg.size[0]
    height = radarImg.size[1]
    radarImg = radarImg.crop((width * 0.01, height * 0.035, width * 0.82, height * 0.99))

    width = radarImg.size[0]
    height = radarImg.size[1]
    radarImg = radarImg.convert('RGB')
    radarPix = radarImg.load()

    radarLevel = convertRGBtoPrepLevel(width, height, radarPix)
    analyzeRadar(width, height, radarLevel)

    for h in range(int(height * 0.51), int(height * 0.60)): # up and down axis
        for w in range(int(width * 0.48), int(width * 0.57)): # left and right axis
            radarPix[w, h] = (255, 126, 0)

    for h in range(int(height * 0.54), int(height * 0.58)): # up and down axis
        for w in range(int(width * 0.51), int(width * 0.54)): # left and right axis
            radarPix[w, h] = (255, 0, 0)

    radarImg.save("test.png")

downloadPrepRes()
analyzePic("3.gif")
analyzePic("2.gif")
analyzePic("1.gif")
analyzePic("0.gif")