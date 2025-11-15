import requests
import os
import hmac
import hashlib
import time


def generate_signature(params, secret_key):
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return hmac.new(secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()


def get_coin_info(symbol):

    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    response = requests.get(url).json()
    tick_size = None
    step_size = None
    for s in response["symbols"]:
        if s["symbol"] == symbol:
            for f in s["filters"]:
                if f["filterType"] == "PRICE_FILTER":
                    tick_size = f["tickSize"]
                if f["filterType"] == "LOT_SIZE":
                    step_size = f["stepSize"]
            
    return tick_size, step_size 

def get_server_time():
    response = requests.get("https://api.binance.com/api/v3/time")
   
    server_time =  response.json()["serverTime"]
    local_time = int(time.time() * 1000)
    time_offset = server_time - local_time 
    return int(time.time() * 1000) + time_offset


def set_leverage(tag, leverage):
    url = "https://fapi.binance.com/fapi/v1/leverage"
    API_KEY = os.environ['binance_api_key']
    SECRET_KEY = os.environ['binance_secret_key'] 

    params = {
        "symbol": tag,

        "leverage": leverage,

        "timestamp": get_server_time()
    }
    params["signature"] = generate_signature(params, SECRET_KEY)
    headers = {"X-MBX-APIKEY": API_KEY}
    requests.post(url, headers=headers, params=params).json()


def set_limit_order(tag, side, quantity, price): #sl이 설정된 주문 넣음
    url = "https://fapi.binance.com/fapi/v1/order"
    API_KEY = os.environ['binance_api_key']
    SECRET_KEY = os.environ['binance_secret_key']
    headers = {
        "accept" : "application/json",
        "X-MBX-APIKEY": API_KEY
    }
    params = {
        "symbol" : tag,
        "side" : side,  # "BUY"  또는 "SELL" 
        "type" : "LIMIT",
        "quantity" : quantity,
        "timestamp" : get_server_time(),
        'timeInForce' : "GTC",
        "price" : price
    }
    
    params["signature"] = generate_signature(params, SECRET_KEY)
    response = requests.post(url, headers=headers, params=params).json()
    return response    


def set_take_profit( tag, side, quantity, price): #TP포지션을 지정가로 넣음
    url = "https://fapi.binance.com/fapi/v1/order"
    API_KEY = os.environ['binance_api_key']
    SECRET_KEY = os.environ['binance_secret_key']
    headers = {"X-MBX-APIKEY": API_KEY}
    close_direction = "SELL" if side == "BUY" else "BUY"

    params = {
        "symbol": tag,
        "side": close_direction,  # 포지션 반대 방향
        "type": "TAKE_PROFIT",  # 지정가 TP 주문
        "quantity": quantity,
        "timestamp": get_server_time(),
        'reduceOnly': True,
        "stopPrice": price,  # 트리거 가격
        "price": price,  # 실행될 지정가
        "timeInForce": "GTC",  # 주문 유지 방식 (Good-Till-Canceled)
    }

    params["signature"] = generate_signature(params, SECRET_KEY)
    req = requests.post(url, headers=headers, params=params).json()
    return req 


def set_stop_loss( tag, side, quantity, price): #SL포지션을 시장가로 넣음
    url = "https://fapi.binance.com/fapi/v1/order"
    API_KEY = os.environ['binance_api_key']
    SECRET_KEY = os.environ['binance_secret_key']
    headers = {
        "accept" : "application/json",
        "X-MBX-APIKEY": API_KEY
    }

    #포지션 정리하는 방향
    close_direction = "SELL" if side == "BUY" else "BUY"


    params = {
        "symbol" : tag,
        "side" : close_direction,  # "BUY"  또는 "SELL" 
        "type" : "STOP_MARKET",
        "quantity" : quantity,
        "timestamp" : get_server_time(),

        'reduceOnly': True,
        "stopPrice" : price
    }
    params["signature"] = generate_signature(params, SECRET_KEY)
    requests.post(url, headers=headers, params=params).json()


def Trading( tag, side, quantity, price): #주문 총괄
    set_leverage( tag, 1)
    set_stop_loss( tag, side, quantity, price)
    set_take_profit( tag, side, quantity, price)


def get_budget(printing = False):
    url = "https://fapi.binance.com/fapi/v3/balance"
    API_KEY = os.environ['binance_api_key']
    SECRET_KEY = os.environ['binance_secret_key']
    headers = {
        "accept" : "application/json",
        "X-MBX-APIKEY": API_KEY
    }
    params = {
        "timestamp" : get_server_time(),
        }
    params["signature"] = generate_signature(params, SECRET_KEY)
    response = requests.get(url, headers=headers, params=params).json()
    try:
        for res in response:
            if res['asset'] == "USDT":
                return round(float(res['availableBalance'])*0.95,2)
    except:
        print(response)

    if printing:
        print(response)
    return 0


def get_trading_log():
    url = "https://fapi/v1/userTrades"
    API_KEY = os.environ['binance_api_key']
    SECRET_KEY = os.environ['binance_secret_key']
    headers = {
        "accept" : "application/json",
        "X-MBX-APIKEY": API_KEY
    }
    params = {
        "timestamp" : get_server_time(),
        }
    params["signature"] = generate_signature(params, SECRET_KEY)
    return requests.get(url, headers=headers, params=params).json()


def get_candle_data(tag, candle_size, length, start_time = None, extra_candle_size = None):
    
    if extra_candle_size != None:
        candle_size = extra_candle_size
    symbol = tag + 'USDT'
    url = "https://fapi.binance.com/fapi/v1/klines"
    headers = {"accept": "application/json"}
    if start_time == None:
        params = {
            "symbol" : symbol,

            "interval" : candle_size,

            "limit" : length
        }
    else:
        start_time = int(start_time)
        params = {
            "symbol" : symbol,

            "interval" : candle_size,

            "limit" : length,

            "startTime" : start_time
        }

    if length < 100:
        weight = 1
    elif length < 500:
        weight = 2
    elif length < 1000:
        weight = 5
    else:
        weight = 10
    
    sleep_time = round(1.5 * weight / (2000 / 60),2)
    time.sleep(sleep_time)
    response = requests.get(url,params=params,headers=headers)
    m_weight = int(response.headers.get("X-MBX-USED-WEIGHT-1M", 0))


    past_prices = response.json()
    if past_prices == None:
        return None
    for i in range(len(past_prices)):
        prices = past_prices[i]
        candle_data = {
            'open' : float(prices[1]), 'high' : float(prices[2]), 'low' : float(prices[3]), 
            'close' : float(prices[4]), 'volume' : float(prices[5]), 'open_time' : float(prices[0])
        }
        past_prices[i] = candle_data

    return past_prices
