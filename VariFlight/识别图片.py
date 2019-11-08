from PIL import Image
import pytesseract


img = Image.open("1.png")
# 模式L”为灰色图像，它的每个像素用8个bit表示，0表示黑，255表示白，其他数字表示不同的灰度。
Img = img.convert('L')

# 自定义灰度界限，大于这个值为黑色，小于这个值为白色
threshold = 200

table = []
for i in range(256):
    if i < threshold:
        table.append(0)
    else:
        table.append(1)

# 图片二值化
photo = Img.point(table, '1')
photo.save("test2.png")
image = Image.open('test2.png')
code = pytesseract.image_to_string(image)
print(code)


import matplotlib.pyplot as plt
import sys, os
from PIL import Image, ImageDraw


# 二值判断,如果确认是噪声,用改点的上面一个点的灰度进行替换
# 该函数也可以改成RGB判断的,具体看需求如何
def getPixel(image, x, y, G, N):
    L = image.getpixel((x, y))
    if L > G:
        L = True
    else:
        L = False

    nearDots = 0
    if L == (image.getpixel((x - 1, y - 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x - 1, y)) > G):
        nearDots += 1
    if L == (image.getpixel((x - 1, y + 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x, y - 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x, y + 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x + 1, y - 1)) > G):
        nearDots += 1
    if L == (image.getpixel((x + 1, y)) > G):
        nearDots += 1
    if L == (image.getpixel((x + 1, y + 1)) > G):
        nearDots += 1

    if nearDots < N:
        return image.getpixel((x, y - 1))
    else:
        return None


# 降噪
# 根据一个点A的RGB值，与周围的8个点的RBG值比较，设定一个值N（0 <N <8），当A的RGB值与周围8个点的RGB相等数小于N时，此点为噪点
# G: Integer 图像二值化阀值
# N: Integer 降噪率 0 <N <8
# Z: Integer 降噪次数
# 输出
#  0：降噪成功
#  1：降噪失败
def clearNoise(image, G, N, Z):
    draw = ImageDraw.Draw(image)

    for i in range(0, Z):
        for x in range(1, image.size[0] - 1):
            for y in range(1, image.size[1] - 1):
                color = getPixel(image, x, y, G, N)
                if color != None:
                    draw.point((x, y), color)


# 测试代码
def main():
    # 打开图片
    img = Image.open("时间.png")

    # 将图片转换成灰度图片
    image = img.convert("L")

    # 去噪,G = 50,N = 3,Z = 8
    clearNoise(image, 50,3, 8)
    plt.subplot(121), plt.imshow(img)
    plt.subplot(122), plt.imshow(image)
    plt.show()
    # 保存图片
    image.save('test3.png')
    image = Image.open('test3.png')
    code = pytesseract.image_to_string(image,lang='eng',config='--psm 10 --oem 3 -c tessedit_char_whitelist=:-,ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').strip()
    print(code)

if __name__ == '__main__':
    main()









