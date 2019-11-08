#-*- coding:utf-8 -*-
import io
import re
from urllib.parse import urljoin

import requests
from PIL import Image
from lxml import etree
from pytesseract import pytesseract


class Flight_Info(object):
    def __init__(self,flight_num,date):
        self.flight_num = flight_num
        self.date = date
        self.index_url = f"http://www.variflight.com/flight/fnum/{self.flight_num}.html?AE71649A58c77&fdate={self.date}"
        self.session = requests.session()
        self.session.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'}
        self.Info_List = []


    #获取航班信息详情页的url
    def flight_info_url_list(self):
        response = self.session.get(self.index_url)
        e = etree.HTML(response.text)
        seach_result = e.xpath('//*[@class="searchlist_innerli"]')

        #如果有航班信息，获取详情页链接
        if seach_result:
            name = e.xpath('//*[@class="tit"]/h1/@title')[0].strip()
            log = "{0}航班存在信息...".format(name)
            #print(log)
            mylist = e.xpath('//*[@id="list"]/li')

            for selector in mylist:
                detailpage_link = selector.xpath('a[@class="searchlist_innerli"]/@href')[0]
                detailpage_link = urljoin(response.url, detailpage_link)
                self.parse_flight_info(detailpage_link)
        else:
            log = "此航班不存在信息"
            self.Info_List.append(log)

        return self.Info_List

    def parse_flight_info(self,detail_url):
        resp = self.session.get(detail_url)
        e = etree.HTML(resp.text)
        item = {}

        #出行日期
        item['Date'] = self.date[:4] + '-' + self.date[4:6] + '-' + self.date[-2:]

        #航班号、航空公司
        flight_Company_No = e.xpath('//div[@class="detail_main"]/div[1]/span[1]/b/text()')[0]
        item["FlightNo"] = flight_Company_No.split(' ')[1].strip()
        item["FlightCompany"] = flight_Company_No.split(' ')[0].strip()

        #出发地、航站楼
        Dep_Terminal = e.xpath('//div[@class="detail_main"]/div[5]/div[1]/h2/text()')[1]
        item["FlightDepAirport"] = re.findall(r'[\u4e00-\u9fa5]+', Dep_Terminal)[0]
        item["FlightHTerminal"] = re.findall(r'T\d?\w', Dep_Terminal)[0] if re.findall(r'T\d?\w', Dep_Terminal) else ''

        # 计划起飞(日期、星期、计划起飞时间)
        Plan_Deptime = e.xpath('//div[@class="detail_main"]/div[5]/div[1]/span/text()')[0].strip()
        Plan_Deptime = Plan_Deptime.split(' ')[1]
        item["Flight_DepWeekPlan"] = Plan_Deptime[:2]
        item["FlightDeptimePlan"]= Plan_Deptime[-5:]

        #出发天气(天气图标、温度、PM、是否延误)
        DepWeather_Icon_Link = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[1]/img/@src')[0]
        DepWeather_Icon_Link = urljoin(resp.url,DepWeather_Icon_Link )

        Dep_Tem_Wea = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[1]/p[1]/text()')[0]
        Dep_Temp = Dep_Tem_Wea.split(' ')[0].replace('\t','')
        Dep_Wea = Dep_Tem_Wea.split(' ')[1].replace('\t','')

        PM = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[1]/p[2]/text()')[0]
        Dep_Delay = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[1]/p[3]/text()')[0]

        item['DepWeather_Icon_Link'] = DepWeather_Icon_Link
        item['Dep_Temp'] = Dep_Temp
        item['Dep_Wea'] = Dep_Wea
        item['Dep_PM '] = PM
        item['Dep_Delay'] = Dep_Delay

        # 实际或预计起飞、值机柜台、登机口图片url并识别图片内容
        #由于三个链接是随机交换的，因此需要找到对应的顺序
        #判断是实际起飞还是预计起飞
        Dep_txt = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[2]/p[1]/text()')[0]
        item["Dep_txt"] = Dep_txt
        #获取可变图片链接
        dep_context_list = []

        Dep_p1_link = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[2]/p[2]/img/@src')
        if Dep_p1_link:
            Dep_p1_link= urljoin(resp.url,Dep_p1_link[0])
            context1 = self.get_pic_context(Dep_p1_link)
        else:
            context1 =e.xpath('//ul[@class="f_common rand_ul_dep"]/li[2]/p[2]/text()')[0].strip()

        Dep_p2_link = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[3]/p[2]/img/@src')
        if Dep_p2_link:
            Dep_p2_link = urljoin(resp.url, Dep_p2_link[0])
            context2 = self.get_pic_context(Dep_p2_link)
        else:
            context2 =e.xpath('//ul[@class="f_common rand_ul_dep"]/li[3]/p[2]/text()')[0].strip()

        Dep_p3_link = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[4]/p[2]/img/@src')
        if Dep_p3_link:
            Dep_p3_link = Dep_p3_link[0]
            Dep_p3_link = urljoin(resp.url, Dep_p3_link)
            context3= self.get_pic_context(Dep_p3_link)
        else:
            context3 = e.xpath('//ul[@class="f_common rand_ul_dep"]/li[4]/p[2]/text()')[0].strip().strip()

        dep_context_list.append(context1)
        dep_context_list.append(context2)
        dep_context_list.append(context3)
        #print(context1,context2,context3)

        #通过正则表达式去js获取正确的图片顺序
        # func('rand_ul_dep', 2, 1, 3);
        # func('rand_ul_arr', 2, 3, 1);
        rand_ul_dep = re.findall(r"func\('rand_ul_dep',(.*?)\);",resp.text)[0]  #[' 1,3,2']
        rand_ul_dep = [int(i) for i in rand_ul_dep.split(',')]
        #print(rand_ul_dep)
        #通过随机顺序获取对应文本的值
        FlightDeptime = dep_context_list[rand_ul_dep[0]-1]  #实际（预计）起飞时间
        Check_In_Counters = dep_context_list[rand_ul_dep[1]-1]
        Departure_Gate = dep_context_list[rand_ul_dep[2]-1]
        new_dep_context_list = []
        new_dep_context_list.append(FlightDeptime)
        new_dep_context_list.append(Check_In_Counters)
        new_dep_context_list.append(Departure_Gate)
        if ':' in FlightDeptime:        #如果第一个是时间，只取一次值
            item["FlightDeptime"] = FlightDeptime
            item["Check_In_Counters"] = Check_In_Counters   #值机柜台
            item["Departure_Gate"] = Departure_Gate      #登机口
        else:                           #如果第一个不是时间，就再取一次值
            item["FlightDeptime"] = new_dep_context_list[rand_ul_dep[0]-1]
            item["Check_In_Counters"] = new_dep_context_list[rand_ul_dep[1]-1]
            item["Departure_Gate"] = new_dep_context_list[rand_ul_dep[2]-1]
        print(item["FlightDeptime"],item["Check_In_Counters"],item["Departure_Gate"])
        #到达地、出机口
        Arr_Terminal = e.xpath('//div[@class="detail_main"]/div[@class="fly_mian"][2]/div[1]/h2/text()')[1]
        item["FlightArrAirport"] = re.findall(r'[\u4e00-\u9fa5]+',Arr_Terminal)[0]
        item["FlightTerminal"] = re.findall(r'T\d?\w',Arr_Terminal)[0] if re.findall(r'T\d?\w',Arr_Terminal) else ''

        # 计划到达(日期、星期、计划到达时间)
        Plan_Arrtime = e.xpath('//div[@class="detail_main"]/div[6]/div[1]/span/text()')[0].strip()
        Plan_Arrtime = Plan_Arrtime.split(' ')[1]
        item["Flight_ArrWeekPlan"] = Plan_Arrtime[:2]
        item["FlightArrtimePlan"] = Plan_Arrtime[-5:]

        # 到达天气(天气图标、温度、PM、是否延误)
        ArrWeather_Icon_Link = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[1]/img/@src')[0]
        ArrWeather_Icon_Link = urljoin(resp.url, ArrWeather_Icon_Link)

        Arr_Tem_Wea = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[1]/p[1]/text()')[0]
        Arr_Temp = Arr_Tem_Wea.split('\t')[0]+'C'
        Arr_Wea = Arr_Tem_Wea.split('\t')[-1].replace('C','')

        PM = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[1]/p[2]/text()')[0]
        Arr_Delay = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[1]/p[3]/text()')[0]

        item['ArrWeather_Icon_Link'] = ArrWeather_Icon_Link
        item['Arr_Temp'] = Arr_Temp
        item['Arr_Wea'] =Arr_Wea
        item['ArrPM '] = PM
        item['Arr_Delay'] = Arr_Delay

        # 实际或预计到达、值机柜台、登机口图片url并识别图片内容
        # 由于三个链接是随机交换的，因此需要找到对应的顺序
        # 判断是实际到达还是预计到达
        Arr_txt = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[2]/p[1]/text()')[0]
        item["Arr_txt"] = Arr_txt

        # 获取可变图片链接
        arr_context_list = []

        Arr_p1_link = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[2]/p[2]/img/@src')
        if Arr_p1_link:
            Arr_p1_link = urljoin(resp.url, Arr_p1_link[0])
            context1 = self.get_pic_context(Arr_p1_link)
        else:
            context1 = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[2]/p[2]/text()')[0].strip()

        Arr_p2_link = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[3]/p[2]/img/@src')
        if Arr_p2_link:
            Arr_p2_link = urljoin(resp.url, Arr_p2_link[0])
            context2 = self.get_pic_context(Arr_p2_link)
        else:
            context2 = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[3]/p[2]/text()')[0].strip()

        Arr_p3_link = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[4]/p[2]/img/@src')
        if Arr_p3_link:
            Arr_p3_link = urljoin(resp.url, Arr_p3_link[0])
            context3 = self.get_pic_context(Arr_p3_link)
        else:
            context3 = e.xpath('//ul[@class="f_common rand_ul_arr"]/li[4]/p[2]/text()')[0].strip()

        arr_context_list.append(context1)
        arr_context_list.append(context2)
        arr_context_list.append(context3)
        #print(context1,context2,context3)

        # 通过正则表达式去js获取正确的图片顺序
        # func('rand_ul_dep', 2, 1, 3);
        # func('rand_ul_arr', 2, 3, 1);
        rand_ul_arr = re.findall(r"func\('rand_ul_arr',(.*?)\);", resp.text)[0]  # [' 1,3,2']
        rand_ul_arr = [int(i) for i in rand_ul_arr.split(',')]
        #print(rand_ul_arr)
        # 通过随机顺序获取对应文本的值,如果第一个取出来是时间，证明取值正确；如果第一个取出来的不是时间，那么取值就是错误的顺序，就再取值一次就是正确的顺序
        FlightArrtime= arr_context_list[rand_ul_arr[0] - 1]  # 实际（预计）到达时间
        Carousel= arr_context_list[rand_ul_arr[1] - 1]  # 行李转盘
        ArrivalPort = arr_context_list[rand_ul_arr[2] - 1]  # 到达口

        new_arr_context_list = []
        new_arr_context_list.append(FlightArrtime)
        new_arr_context_list.append(Carousel)
        new_arr_context_list.append(ArrivalPort)

        if ':' in FlightArrtime:    #判断第一个取出来的值是不是时间
            item["FlightArrtime"] = FlightArrtime
            item["Carousel"] = Carousel
            item["ArrivalPort"] = ArrivalPort
        else:
            item["FlightArrtime"] =new_arr_context_list[rand_ul_arr[0] - 1]
            item["Carousel"] =new_arr_context_list[rand_ul_arr[1] - 1]
            item["ArrivalPort"] =new_arr_context_list[rand_ul_arr[2] - 1]
        print(item["FlightArrtime"],item["Carousel"],item["ArrivalPort"])

        # 机型
        item["generic"] = e.xpath('//div[@class="p_info"]/ul/li[1]/span/text()')[0]

        # 机龄
        item["FlightYear"] = e.xpath('//div[@class="p_info"]/ul/li[2]/span/text()')[0]

        # 准点率
        OntimeRate_link = e.xpath('//div[@class="p_info"]/ul/li[3]/span/img/@src')[0]
        OntimeRate_link = urljoin(resp.url, OntimeRate_link)
        item["OntimeRate"] = self.get_pic_context(OntimeRate_link)

        # 里程
        item["distance"] = e.xpath('//div[@class="p_ti"]/span[1]/text()')[0]

        # 飞行时间
        item["FlightDuration"] = e.xpath('//div[@class="p_ti"]/span[2]/text()')[0]

        # 飞机状态
        item["FlightState"] = e.xpath('//div[@class="state"]/div/text()')[0]
        #print(item)
        self.Info_List.append(item)



    def get_pic_context(self,p):
        response = self.session.get(p)
        image = Image.open(io.BytesIO(response.content))
        code = pytesseract.image_to_string(image,lang='eng',config='--psm 6 --oem 3 -c tessedit_char_whitelist=:,-ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').strip()
        if code:
            context = code
        else:
            context = "未识别"
        return context




if __name__ =="__main__":
    #3U5013   CA173  CA163
    info = Flight_Info(flight_num='CA172',date='20191108')
    Info_List = info.flight_info_url_list()
    # print(Info_List)





