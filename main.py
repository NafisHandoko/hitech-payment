from flask import Flask, render_template, request, jsonify
from midtransclient import Snap, CoreApi
from flask_pymongo import PyMongo
from bson.json_util import dumps

app = Flask(__name__, template_folder='templates', static_folder='static')

app.config["MONGO_URI"] = "mongodb+srv://paaa:pemrogramanpaa123@cluster0.ar1x3.mongodb.net/checkout"
#initializing the client for mongodb
mongo = PyMongo(app)
#creating the customer collection
topup_collection = mongo.db.topup
currency_collection = mongo.db.currency
payment_collection = mongo.db.payment

SERVER_KEY = 'SB-Mid-server-Kt4oVos5rAytBzDRTj2FhdVe'
CLIENT_KEY = 'SB-Mid-client-RI8QHvoIssPOnwk9'

core = CoreApi(
  is_production=False,
  server_key=SERVER_KEY,
  client_key=CLIENT_KEY
)

@app.route('/')
def index():
  print('hello world')
  saldo = currency_collection.find_one({'user_id':'30abc'})['himoney']
  return render_template('topup.html', saldo=saldo)


@app.route('/tes_notif', methods=['POST'])
def tes_notif():
  print('masuk')
  # data = request.form.to_dict(flat=False)
  data = request.json
  print(data)
  return 'Pembayaran Sukses!'


@app.route('/payment', methods=['POST'])
def payment():
  method = payment_collection.find_one({'payment_id':request.json.get('payment_id')})['method']
  # timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  if method=="indomaret":
    # return request.json
    charge_api_response = core.charge({
      "payment_type": "cstore",
      "transaction_details": {
          "gross_amount": request.json.get("gross_amount"),
          "order_id": request.json.get("order_id"),
      },
      "cstore" : {
        "store" : method,
  	    "message" : "Pembayaran Checkout"
  	  }
    })
  elif method=='bri':
    charge_api_response = core.charge({
      "payment_type": "bank_transfer",
      "transaction_details": {
          "gross_amount": request.json.get("gross_amount"),
          "order_id": request.json.get("order_id"),
      },
      "bank_transfer" : {
        "bank" : method,
  	  }
    })
  if charge_api_response['status_code'][0]=='2':status=True
  elif charge_api_response['status_code'][0]=='4' or charge_api_response['status_code'][0]=='5':status=False
  return jsonify({
    "data":charge_api_response,
    "message":charge_api_response['status_message'],
    "status":status
  })

  # return render_template('simple_core_api_checkout_permata.html', permata_va_number=charge_api_response['permata_va_number'], gross_amount=charge_api_response['gross_amount'], order_id=charge_api_response['order_id'])

@app.route('/payment/topup', methods=['POST'])
def payment_topup():
  method = payment_collection.find_one({'payment_id':request.json.get('payment_id')})['method']
  method_type = payment_collection.find_one({'payment_id':request.json.get('payment_id')})['payment_type']
  require_detail = payment_collection.find_one({'payment_id':request.json.get('payment_id')})['require_detail']
  detail_attr = payment_collection.find_one({'payment_id':request.json.get('payment_id')})['detail_attr']
  payment_req_data = {
    "payment_type": method_type,
    "transaction_details": {
      "gross_amount": request.json.get("gross_amount"),
      "order_id": request.json.get("topup_id"),
    }
  }
  if require_detail:
    payment_req_data[method_type] = {
      detail_attr: method,
      "message" : "Pembayaran Topup"
    }
  charge_api_response = core.charge(payment_req_data)
  va_number = charge_api_response.get('va_numbers', '')
  topup = topup_collection.insert_one({
    "topup_id": request.json.get("topup_id"), 
    "amount": int(request.json.get("gross_amount")),
    "payment_code": charge_api_response.get('payment_code', ''),
    "va_number": va_number[0]['va_number'] if type(va_number)==type({}) else "",
    "payment_id": request.json.get("payment_id"),
    "status_id": "0" if charge_api_response['transaction_status']=='failure' else "1" if charge_api_response['transaction_status']=='pending' else "2",
    "user_id": '30abc'
  })
  if charge_api_response['status_code'][0]=='2':status=True
  elif charge_api_response['status_code'][0]=='4' or charge_api_response['status_code'][0]=='5':status=False
  return jsonify({
    "data":charge_api_response,
    "message":charge_api_response['status_message'],
    "status":status
  })
  
@app.route('/payment', methods=['GET'])
def payment_get():
  user = request.args.get('userId')
  data = topup_collection.find({'user_id':user})
  # return dumps(list(resp))
  return dumps({
    'data': list(data)
  })

@app.route('/payment/notif', methods=['POST'])
def notif():
  print(request.json)
  if request.json.get('order_id').split('-')[0]=='topup':
    print('bayar topup')
    topup_collection.update_one({'topup_id': request.json.get('order_id')},{'$set':{'status_id':"0" if request.json.get('transaction_status')=='failure' else "1" if request.json.get('transaction_status')=='pending' else "2"}})
  if topup_collection.find_one({'topup_id':request.json.get('order_id')})['status_id']=="2":
    print('bayar sukses!')
    currency_collection.update_one({'user_id': topup_collection.find_one({'topup_id':request.json.get('order_id')})['user_id']},{'$inc':{'himoney':int(topup_collection.find_one({'topup_id':request.json.get('order_id')})['amount'])}})
  return "Sukses!"

app.run(host='0.0.0.0', port=81)
