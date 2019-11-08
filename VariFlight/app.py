from flask import Flask, request, jsonify
from gevent.pywsgi import WSGIServer

from flight_spyder import Flight_Info
app = Flask(__name__)


@app.route('/api/flight_info',methods = ["GET","POST"])
def api():
    if request.method == 'GET':
        flight_num = request.args.get('flight_num')
        date = request.args.get('date')
        info = Flight_Info(flight_num='CA172', date='20191108')
        data = info.flight_info_url_list()

        resp = jsonify({'code': 1, 'result': data})
        resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == '__main__':
    app.config["JSON_AS_ASCII"] = False
    # app.run(debug=True,host= '0.0.0.0',port=5000)
    WSGIServer(('0.0.0.0', 5000), app).serve_forever()
