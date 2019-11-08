# New_VariFlight
这是新版的非常准航班使用接口
此接口难点是怎么将航班出发时间、值机柜台、登机口以及到达时间、行李转盘、到达口进行合理的排序，它们的信息一般都在后台传送到前端显示样式的图片中
步骤如下:
    1. 首先判断是否有登机信息（包含三个）和出机信息（包含三个）,有信息的必然有图片链接，获取图片链接之后再去识别图片信息
    2. 使用正则在源码中获取可能的登机和下机图片链接顺序【2，1，3】，通过可能的顺序列表在前面识别出来的文本中取出第一个数字-1的索引值
    3. 判断索引值是否位时间文本，如果是时间文本，则该顺序正确，否则不正确，再根据这个顺序取出对应的值即为最终的值
    
注：
  在使用pytesseract识别图片过程中，需要增加lang和config参数
  如：code = pytesseract.image_to_string(image,lang='eng',config='--psm 10 --oem 3 -c tessedit_char_whitelist=:,-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
  
参数说明: config->需要识别的类型 ，whitelist可以增加任何自己想识别的字符
code = pytesseract.image_to_string(image,lang='eng',config='--psm 10 --oem 3 -c tessedit_char_whitelist=:,-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').strip()
Page segmentation modes:
  0    Orientation and script detection (OSD) only.
  1    Automatic page segmentation with OSD.
  2    Automatic page segmentation, but no OSD, or OCR.
  3    Fully automatic page segmentation, but no OSD. (Default)
  4    Assume a single column of text of variable sizes.
  5    Assume a single uniform block of vertically aligned text.
  6    Assume a single uniform block of text.
  7    Treat the image as a single text line.
  8    Treat the image as a single word.
  9    Treat the image as a single word in a circle.
 10    Treat the image as a single character.
 11    Sparse text. Find as much text as possible in no particular order.
 12    Sparse text with OSD.
 13    Raw line. Treat the image as a single text line,
                        bypassing hacks that are Tesseract-specific.
