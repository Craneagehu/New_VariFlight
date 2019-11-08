import requests



index_url= 'http://www.variflight.com/flight/fnum/sc1155.html?AE71649A58c77&fdate=20191105'
url= 'http://www.variflight.com/schedule/CKG-PEK-SC1155.html?AE71649A58c77=&fdate=20191103'


session = requests.session()
resp = session.get(index_url)
# print(resp.text)
# print(session.cookies)

resp2 = session.get(url)
print(resp2.text)
print(session.cookies)