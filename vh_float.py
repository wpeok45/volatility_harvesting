
import asyncio
import sys
import os
import aiohttp
import socket
import array as arr
import json
import math
import decimal
import hashlib
import hmac
import time
import uuid
import datetime
import itertools
import traceback
import statistics
from collections import deque

#   https://bybit-exchange.github.io/docs/v5/ws/connect
#   https://bybit-exchange.github.io/docs/api-explorer/v5/trade/trade

async def Fire_alert(bot_message:str, bot_token:str, bot_chatID:str):
    if bot_token == "" or bot_chatID == "":
        return
    
    msg = bot_message.replace("_", " ")
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f'https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={bot_chatID}&parse_mode=Markdown&text={msg}'
            async with session.get(url) as resp:
                print(f"************************* allert sent")
    except Exception as ex:
        print(f"ERROR: Fire_alert, {repr(traceback.extract_tb(ex.__traceback__))}")
        
class WSClient:
    def __init__(self, loop: asyncio.AbstractEventLoop, stream_url, key, secret):
        self.loop = loop
        self.key = key
        self.secret = secret
        self.stream_url = stream_url
        self.sequence = itertools.cycle(range(1, 100000))
        # aiohttp.resolver.DefaultResolver = aiohttp.resolver.AsyncResolver
        resolver = aiohttp.resolver.AsyncResolver(nameservers=["1.1.1.1", "8.8.8.8"])
        connector=aiohttp.TCPConnector(loop=self.loop, family=socket.AF_INET, limit=100, ttl_dns_cache=30000, resolver=resolver)
        timeout=aiohttp.ClientTimeout(total=5)
        self.session = aiohttp.ClientSession(loop=self.loop, connector=connector, timeout=timeout)
        
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "volharvest/2.0",
            }
        )

    async def _create_auth(self):
        # Generate expires.
        expires = int((time.time() + 100) * 1000)

        # Generate signature.
        signature = str(hmac.new(
            bytes(self.secret, "utf-8"),
            bytes(f"GET/realtime{expires}", "utf-8"), digestmod="sha256"
        ).hexdigest())


        # Authenticate with API.
        # zz ={
        #         "op": "auth",
        #         "args": [self.key, expires, signature]
        #     }
        
        
        # aa = {
        #     "req_id": "10001", # optional
        #     "op": "auth",
        #     "args": [
        #         "api_key",
        #         1662350400000, # expires; is greater than your current timestamp
        #         "signature"
        #     ]
        # }
        return { 'op': 'auth', 'args': [self.key, expires, signature]}  #, 'req_id': '10002'}

    async def _subscription(self, ws):
        sub_msg = {
            "reqId": "sub-001",
            "header": {
                "X-BAPI-TIMESTAMP": str(int(datetime.now().timestamp() * 1000)),
                "X-BAPI-RECV-WINDOW": "8000",
            },
            "op": "order.create",
            "args": [
                {
                    "symbol": "XRPUSDC",
                    "side": "Buy",
                    "orderType": "Market",
                    "qty": "10",
                    "category": "spot"
                }
            ]
        }

        #await ws.send(json.dumps(sub_msg))
        #print("Subscription message sent.")
        return sub_msg

    async def ws_ping_loop(self, ws):
        await asyncio.sleep(5.0)
        # https://bybit-exchange.github.io/docs/v5/ws/connect#how-to-send-the-heartbeat-packet
        while True:
            # ws.send(JSON.stringify({"req_id": "100001", "op": "ping"}));
            try:
                data = {"op": "ping"}
                await ws.send_str(json.dumps(data, ensure_ascii=False), compress=None)
            except Exception as ex:
                print(f"ERROR: ws_ping, {ex}")
                print(f"{repr(traceback.extract_tb(ex.__traceback__))}")
                return
            
            await asyncio.sleep(20.0)
            
    async def start(self, subscribe: list, callback, need_auth=False):
        # https://bybit-exchange.github.io/docs/spot/ws-public/ticker

        while 1:
            await self.initialize()
            print(f"ws start: {self.stream_url}")
            try:
                async with self.session.ws_connect(self.stream_url) as ws:
                    if need_auth:
                        data = await self._create_auth()
                        await ws.send_str(json.dumps(data, ensure_ascii=False), compress=None)
                        await asyncio.sleep(1.0)
            
                    await ws.send_str(json.dumps(subscribe)) #, ensure_ascii=False))
                    
                    await asyncio.sleep(1.0)

                    self.loop.create_task(self.ws_ping_loop(ws))
                    
                    async for msg in ws:
                        match msg.type:
                            case aiohttp.WSMsgType.TEXT:
                                txt = msg.data
                                if not 'ping' in txt:
                                    callback(json.loads(txt))
                            case aiohttp.WSMsgType.BINARY:
                                print("Binary: ", msg.data)
                            case aiohttp.WSMsgType.PING:
                                print("Ping received")
                            case aiohttp.WSMsgType.PONG:
                                print("Pong received")
                            case aiohttp.WSMsgType.CLOSE:
                                await ws.close()
                                print(f"WARNING: ws start, close received, {subscribe}")
                                break
                            case aiohttp.WSMsgType.CLOSED:
                                print(f"WARNING: ws start, closed, {subscribe}")
                                break
                            case aiohttp.WSMsgType.ERROR:
                                print(f"ERROR: ws, Error during receive, {subscribe}, {ws.exception()}")
                                break
                            case _:
                                print(f"WARNING: ws, unknown command: {msg}")

            except Exception as ex:
                print(f"ERROR: ws start, {subscribe}, {ex}")
                print(f"{repr(traceback.extract_tb(ex.__traceback__))}")

            await asyncio.sleep(5.0)


class Client:
    def __init__(self, loop: asyncio.AbstractEventLoop, base_url, key, secret) -> None:
        self.loop = loop
        self.key = key
        self.secret = secret
        self.base_url = base_url
        self.sequence = itertools.cycle(range(1, 100000))
        
        # aiohttp.resolver.DefaultResolver = aiohttp.resolver.AsyncResolver
        resolver = aiohttp.resolver.AsyncResolver(nameservers=["1.1.1.1", "8.8.8.8"])
        connector=aiohttp.TCPConnector(loop=self.loop, family=socket.AF_INET, limit=100, ttl_dns_cache=300, resolver=resolver)
        timeout=aiohttp.ClientTimeout(total=5)
        self.session = aiohttp.ClientSession(loop=self.loop, connector=connector, timeout=timeout)
        
    def genSignature(self, payload, time_stamp, recv_window):
        param_str= str(time_stamp) + self.key + recv_window + payload
        hash = hmac.new(bytes(self.secret, "utf-8"), param_str.encode("utf-8"),hashlib.sha256)
        signature = hash.hexdigest()
        return signature
    
    async def HTTP_Request(self, endPoint, method, payload, Info):
        recv_window=str(5000)
        time_stamp=str(int(time.time() * 10 ** 3))
        #time_stamp = str(int(time.time() * 1000))
        signature = self.genSignature(payload, time_stamp, recv_window)
      
        headers = {
        'X-BAPI-API-KEY':self.key,
        'X-BAPI-SIGN': signature,
        'X-BAPI-SIGN-TYPE': '2',
        'X-BAPI-TIMESTAMP': time_stamp,
        'X-BAPI-RECV-WINDOW': recv_window,
        'Content-Type': 'application/json'
    }
        
        if(method=="POST"):
            #async with self.session.post(self.base_url+endPoint, headers=headers, data=json.dumps(payload)) as resp:
            async with self.session.post(self.base_url+endPoint, headers=headers, data=payload) as resp:
                resp_data = await resp.json()
            # print("resp_data: ", resp_data)
            # print(resp.text)
            # print(resp.headers)
            # print(Info)
        else:
            #response = self.session.request(method, self.base_url+endPoint+"?"+payload, headers=headers)
            #print(self.base_url+endPoint+"?"+payload)
            async with self.session.get(self.base_url+endPoint+"?"+payload, headers=headers) as resp:
                resp_data = await resp.json()
        

        return resp_data, resp.status
    
    async def account(self):
        # {'retCode': 0, 'retMsg': 'OK', 'result': {'list': [{'totalEquity': '1896.1162586', 'accountIMRate': '0', 'totalMarginBalance': '1896.07115222', 'totalInitialMargin': '0', 'accountType': 'UNIFIED', 'totalAvailableBalance': '1896.07115222', 'accountMMRate': '0', 'totalPerpUPL': '0', 'totalWalletBalance': '1896.07115222', 'accountLTV': '0', 'totalMaintenanceMargin': '0', 'coin': [{'availableToBorrow': '', 'bonus': '0', 'accruedInterest': '0', 'availableToWithdraw': '0.00000066', 'totalOrderIM': '0', 'equity': '0.00000066', 'totalPositionMM': '0', 'usdValue': '0.04510637', 'unrealisedPnl': '0', 'collateralSwitch': False, 'spotHedgingQty': '0', 'borrowAmount': '0.000000000000000000', 'totalPositionIM': '0', 'walletBalance': '0.00000066', 'cumRealisedPnl': '-0.00003433', 'locked': '0', 'marginCollateral': True, 'coin': 'BTC'}, {'availableToBorrow': '', 'bonus': '0', 'accruedInterest': '0', 'availableToWithdraw': '1897.43540828', 'totalOrderIM': '0', 'equity': '1897.43540828', 'totalPositionMM': '0', 'usdValue': '1896.07115222', 'unrealisedPnl': '0', 'collateralSwitch': True, 'spotHedgingQty': '0', 'borrowAmount': '0.000000000000000000', 'totalPositionIM': '0', 'walletBalance': '1897.43540828', 'cumRealisedPnl': '-2.32815315', 'locked': '0', 'marginCollateral': True, 'coin': 'USDC'}]}]}, 'retExtInfo': {}, 'time': 1717331875175}
        endpoint = "/v5/account/wallet-balance"
        params = "accountType=UNIFIED"
        resp_data, resp_status = await self.HTTP_Request(endpoint, "GET", params, "Account")
        if resp_status != 200:
            print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
            return None
        
        return resp_data

    async def fee_rate(self, symbol):
        # {'retCode': 0, 'retMsg': 'OK', 'result': {'list': [{'symbol': 'ETHUSDT', 'takerFeeRate': '0.00055', 'makerFeeRate': '0.0002'}]}, 'retExtInfo': {}, 'time': 1718750172404}
        # https://api.bybit.com/v5/account/fee-rate?symbol=BTCUSDC
        endpoint = "/v5/account/fee-rate"
        params = f"symbol=BTCUSDC" #BTCUSDC" # ETHUSDT"  #{symbol}"
        resp_data, resp_status = await self.HTTP_Request(endpoint, "GET", params, "Fee-rate")
        if resp_status != 200:
            print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
            return None
        
        return resp_data
        
    async def limit_order(self, symbol:str, side:str, price:float, quantity_size:float):
        quantity = round(quantity_size, 5)  # 0.00047
        # quantity = round(quantity_size * 0.9998 / price, 5)  # 0.00047
        q = str(quantity)
        zeros = "".join(['0'] * (8 - len(q)))
        str_quantity = q + zeros

        endpoint="v5/order/create"
        method="POST"
        orderLinkId=uuid.uuid4().hex

        # params={"category":"spot",
        #         "symbol": symbol,
        #         "side": side,
        #         "orderType": "Limit",
        #         "qty": str_quantity,
        #         "price": str(price),
        #         "timeInForce": "GTC",
        #         "orderLinkId": f"'{orderLinkId}'",
        #         "isLeverage":0,
        #         "orderFilter":"Order"
        # }

        # https://api.bybit.com/v5/market/instruments-info?category=spot&symbol=BTCUSDC
        # {
        #     "retCode":0,
        #     "retMsg":"OK",
        #     "result":
        #         {
        #             "category":"spot",
        #             "list":[
        #                 {
        #                     "symbol":"BTCUSDC",
        #                     "baseCoin":"BTC",
        #                     "quoteCoin":"USDC",
        #                     "innovation":"0",
        #                     "status":"Trading",
        #                     "marginTrading":"both",
        #                     "lotSizeFilter":
        #                         {"basePrecision":"0.000001",
        #                          "quotePrecision":"0.00000001",
        #                          "minOrderQty":"0.000048",
        #                          "maxOrderQty":"71.73956243",
        #                          "minOrderAmt":"1",
        #                          "maxOrderAmt":"4000000"
        #                         },
        #                         "priceFilter":{"tickSize":"0.01"},
        #                         "riskParameters":{"limitParameter":"0.03",
        #                                           "marketParameter":"0.03"
        #                                           }
        #                 }
        #                 ]
        #         },
        #         "retExtInfo":{},
        #         "time":1717340794336
        # }


        #params = '{"category":"linear","symbol": "BTCUSDC","side": "Buy","positionIdx": 0,"orderType": "Limit","qty": "0.001","price": "10000","timeInForce": "GTC","orderLinkId": "' + orderLinkId + '"}'
        
        # DEBUG: params: {"category":"linear","symbol": "BTCUSDC","side": "Buy","positionIdx": 0,"orderType": "Limit","qty": "0.00217","price": "68261","timeInForce": "GTC","orderLinkId": "74844179379a4876985124996c03fd1
        # DEBUG: resp_data: {'retCode': 10001, 'retMsg': 'Qty invalid', 'result': {}, 'retExtInfo': {}, 'time': 1717340529799}
        # DEBUG: params: {"category":"linear","symbol": "BTCUSDC","side": "Buy","positionIdx": 0,"orderType": "Limit","qty": "0.003310","price": "68145","timeInForce": "GTC","orderLinkId": "5e250f12ac4d42718a2e7d502032d01b"}
        
        # GTC Good Till Cancel
        # FOK Fill or Kill (order must be executed)
        # IOC Immediate or Cancel (part of order can be executed)
        params = '{"category":"spot","symbol":"%s","side":"%s","positionIdx":0,"orderType":"Limit","qty":"%s","price":"%s","timeInForce":"GTC","orderLinkId":""' % (symbol, side, str_quantity, str(price))
        
        # Spot Market Buy order, qty is quote currency
        # {"category":"spot","symbol":"BTCUSDT","side":"Buy","orderType":"Market","qty":"200","timeInForce":"IOC","orderLinkId":"spot-test-04","isLeverage":0,"orderFilter":"Order"}

        # {"category":"spot","symbol":"BTCUSDC","side":"Sell","orderType":"Market","qty":"0.101330","timeInForce": "IOC","orderLinkId":"d7413f3607f34de79570e466efe6bc0c","isLeverage":0,"orderFilter":"Order"}
        # {"category":"spot","symbol":"BTCUSDC","side":"Buy","orderType":"Market","qty":"0.100660","timeInForce": "IOC","orderLinkId":"cf25f0ecbc974bc5836b9d26e5b2ead7","isLeverage":0,"orderFilter":"Order"}
        #params = '{"category":"spot","symbol":"%s","side":"%s","orderType":"Market","qty":"%s","timeInForce": "IOC","orderLinkId":"%s","isLeverage":0,"orderFilter":"Order"}' % (symbol, side, str_quantity, orderLinkId)
        params = '{"category":"spot","symbol":"%s","side":"%s","orderType":"Market","qty":"%s","timeInForce":"IOC","orderLinkId":"","isLeverage":0}' % (symbol, side, str_quantity)
        print(f"DEBUG: params: {params}")
        
        resp_data, resp_status = await self.HTTP_Request(endpoint, method, params, "Create")

        if resp_status != 200:
            print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
            return False, -1
        # if resp_data["retCode"] != 0:
        #     print(f"ERROR: resp_data: {resp_data}")
        #     return False, -1
        # DEBUG: resp_data: {'retCode': 170131, 'retMsg': 'Insufficient balance.', 'result': {}, 'retExtInfo': {}, 'time': 1717344232449}
        return True, resp_data["retCode"]

    async def market_order(self, symbol:str, side:str, quantity_size:float):
        str_quantity = str(decimal.Decimal.from_float(quantity_size))
        if len(str_quantity) > 8:
            str_quantity = str_quantity[:8]

        endpoint="v5/order/create"
        method="POST"
        #orderLinkId=uuid.uuid4().hex
        # 
        params = '{"category":"spot","symbol":"%s","side":"%s","orderType":"Market","qty":"%s","timeInForce":"IOC","orderLinkId":"","isLeverage":0}' % (symbol, side, str_quantity)
        print(f"DEBUG: params: {params}")
        
        return await self.HTTP_Request(endpoint, method, params, "Create")
        # resp_data, resp_status = await self.HTTP_Request(endpoint, method, params, "Create")
        # print(resp_data)
        # if resp_status != 200:
        #     print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
        #     return False, -1
        # # if resp_data["retCode"] != 0:
        # #     print(f"ERROR: resp_data: {resp_data}")
        # #     return False, -1
        # # DEBUG: resp_data: {'retCode': 170131, 'retMsg': 'Insufficient balance.', 'result': {}, 'retExtInfo': {}, 'time': 1717344232449}
        # return True, resp_data["retCode"]
    
    async def get_klines(self, symbol, interval=1):
        # {
        #     "retCode":0,
        #     "retMsg":"OK",
        #     "result":
        #         {
        #             "list":[
        #                     {
        #                         "t":1717334640000,
        #                         "s":"BTCUSDC",
        #                         "sn":"BTCUSDC",
        #                         "c":"67709.4",
        #                         "h":"67709.4",
        #                         "l":"67489.28",
        #                         "o":"67489.28",
        #                         "v":"1.252064"
        #                     },
        #                     {"t":1717334700000,"s":"BTCUSDC","sn":"BTCUSDC","c":"67709.4","h":"67709.4","l":"67489.28","o":"67709.4","v":"1.37735"}
        #                 ]
        #         },
        #     "retExtInfo":{},
        #     "time":1717335202430
        # }


        # > t	number	Timestamp(ms)
        # > s	string	Name of the trading pair
        # > sn	string	Alias
        # > c	string	Close price
        # > h	string	High price
        # > l	string	Low price
        # > o	string	Open price
        # > v	string	Trading volume

        # https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDC&interval=15&limit=1000
        
        # https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDC&interval=1&limit=1000  &start=1670601600000&end=1670608800000

        url = "".join([self.base_url, "/v5/market/kline"]) 

        params = {
            "category": "spot",
            "symbol": symbol,
            "interval": interval,
            "limit": 1000
        }

        #try:
            #raise ValueError("123")
        #async with self.session.get("https://api.bybit.com/v5/market/kline?category=spot&symbol=BTCUSDC&interval=1&interval=1&limit=1000") as resp:
        async with self.session.get(url, params=params) as resp:
            data = await resp.json()
            #print(resp.status, data)
            return data
        # except:
        #     exit()

    async def instrument_info(self, symbol):
        # {
        # "retCode":0,
        # "retMsg":"OK",
        # "result":{
            # "category":"spot",
            # "list":[
                # {"symbol":"BTCUSDC",
                # "baseCoin":"BTC",
                # "quoteCoin":"USDC",
                # "innovation":"0",
                # "status":"Trading",
                # "marginTrading":"none",
                # "stTag":"0",
                # "lotSizeFilter":{
                    # "basePrecision":"0.000001",
                    # "quotePrecision":"0.00000001",
                    # "minOrderQty":"0.000198",
                    # "maxOrderQty":"300.030003",
                    # "minOrderAmt":"10","maxOrderAmt":"2000000"
                    # },
                # "priceFilter":{"tickSize":"0.01"},
                # "riskParameters":{"limitParameter":"0.05","marketParameter":"0.05"}}
                # ]
            # },
        # "retExtInfo":{},
        # "time":1734273599757
        # }
        
        # https://api-testnet.bybit.com/v5/market/instruments-info?category=spot&symbol=BTCUSDC
        endpoint = "/v5/market/instruments-info"
        params = f"category=spot&symbol={symbol}"
        resp_data, resp_status = await self.HTTP_Request(endpoint, "GET", params, "instrument_info")
        if resp_status != 200:
            print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
            return None
        
        return resp_data


class Crossunder:
    def __init__(self):
        self.cross = False
    
    def cross_under(self, a:float, b:float):
        if a >= b:
            self.cross = False
            return False
        
        if a < b:
        #if a - b < -1.0:
            if not self.cross:
                self.cross = True
                print(f"cross_under: {a}, {b}")
                return True
        return False


class Crossover:
    def __init__(self):
        self.cross = False
    
    def cross_over(self, a:float, b:float):
        if a <= b:
            self.cross = False
            return False
        
        if a > b:
        #if a - b > 1.0:
            if not self.cross:
                self.cross = True
                print(f"cross_over: {a}, {b}")
                return True
        return False
    

class TradeAnalyse:
    def __init__(self, pair, size=1000) -> None:
        self.info = ""
        self.size = size
        self.prices_m1 = deque(maxlen=30)
        self.prices = deque(maxlen=60*60*5)
        self.diffs = deque(maxlen=3)
        self.diffs_pool = deque(maxlen=60*3)
        self.power_neg = 0.0
        self.power_pos = 0.0
        self.power_max = 0.0
        self.impuls = 0.0
        self.impuls_pos = 0.0
        self.impuls_neg = 0.0
        self.impuls_fmean = 0.0
        # self.impuls_median_pos = 0.0
        self.impuls_median_neg = 0.0
        self.trend = 0.0
        self.trend_percent = 0.0
        self.trend_percent_harmonic = 0.0
        # self.trend_percent_median = 0.0
        self.pair = pair
        self.pair_balance = dict()
        self.native_balance = (0.0, 0.0)
        self.tick = dict()
        self.margin = (0, 0, 0, 0, 0, 0)
        self.trade_profit = 0.0
        self.price_diff = 0.1
        self.rate = 1.0
        self.live_range = 12000.0
        self.traded_price = 0.0
        self.take_on = 0.0
        self.counter_buy = 0
        self.counter_sell = 0
        self.trade_duration = 0.0
        self.sell_timer = 0

        self.m1_timer = 0.0
        self.buy_price_mean = 0.0
        
        self.buy_price = 1.0
        self.buy_list = list()
        self.min_work_range = 300.0
        self.fee = 0.001
        
        self.work_range = 1000.0
        self.work_range_win = deque(maxlen=120)
        self.ma_lenght = float(sys.argv[4])
        self.gap = self.ma_lenght / 4.8
        self.ma_fast = 0.0
        self.ma_fast_m = 0.0
        self.ma_trend = 0.0
        self.ma_trend_prev = 10000000.0
        self.ma_trend_win = deque(maxlen=int(self.ma_lenght))
        self.trend_crossover = Crossover()
        self.trend_crossunder = Crossunder()
        
        # 20%, 89708.3, range: 29179|29178 (min: 60529) 
        # 25%, 75100.0 - 75374.36 = -274.4, range: 23274|19813 (min: 55286)
        # 30%, 69643.99 - 68843.88 =  800.1, range: 17626|17482 (min: 52161)
        # 30%, 66019.47 - 67763.09 = -1743.6, range: 14373(30%) (min: 51646)
        # 35%, 69466.93 - 0.0 = 69466.9, range: 15107|15101 (min: 54365)
        # 50%, 69650.72 - 68843.88 = 806.8, range: 10575|10489 (min: 59161)
        
        # self.range_percent_plus = 0
        # self.range_percent_plus_max = float(sys.argv[6])
        # self.range_percent = float(sys.argv[3])
        
        self.rebalance_at = float(sys.argv[8])
        self.ratio_per_point = 1.0 / float(sys.argv[5])
        self.min_max_ratio = [float(sys.argv[6]), float(sys.argv[7])]
        self.portfolio_ratio = self.min_max_ratio[0]
        self.percent_diff = 0.0
        self.rebalance_bottom = 400 # minimum buy pips
        self.rebalance_top = 3000   # minimum sell pips
        self.bot_token = sys.argv[9]
        self.bot_chatID = sys.argv[10]
        
    def print_setup(self):
        stable_pair = sys.argv[3]
        ma_length = sys.argv[4]
        range = sys.argv[5]
        min_ratio = sys.argv[6]
        max_ratio = sys.argv[7]
        rebalance_at = sys.argv[8]
              
        print(f"---------------Volatility harvesting------------\n"
            f"stable_pair: {stable_pair}\n"
            f"ma_length: {ma_length}\n"
            f"range: {range}\n"
            f"min_ratio: {min_ratio} ({float(min_ratio) * 100.0} %)\n"
            f"max_ratio: {max_ratio} ({float(max_ratio) * 100.0} %)\n"
            f"rebalance_at: {rebalance_at} %, (buy at: {float(rebalance_at) * 0.5} %, sell at: {rebalance_at} %)\n"
            f"tg bot_chatID: {self.bot_chatID}\n"
            f"------------------------------------------------------"
        )
        
    def sma(self, deq: deque, price, temp=False):
        if temp:
            win = list(deq)[1:]
            win.append(price)
            return round(statistics.fmean(win), 2)
        deq.append(price)
        return statistics.fmean(deq)
    
    def ema(self, period, prev_ema, price):
        if prev_ema == 0.0:
            prev = price
        else:
            prev = prev_ema
        return (price - prev_ema) * (2 / (period + 1)) + prev

    def count_impuls(self, price:float):
        if len(self.prices) < 4:
            self.prices.append(price)
            return
        diff = round(price-self.prices[-1], 4)
        self.diffs.append(diff)
        self.impuls = round(sum(self.diffs), 2)
    
    def count_power_s1(self, price:float):
        if len(self.prices) < 4:
            return

        self.diffs_pool.append(price-self.prices[-1])

        if len(self.diffs_pool) < 5:
            return

        positive = list(filter(lambda n: n > 0.0, self.diffs_pool))
        neg_list = list(filter(lambda n: n < 0.0, self.diffs_pool))
        negative = list(map(lambda x: math.fabs(x), neg_list))
        
        self.power_pos = len(positive)
        self.power_neg = len(negative)

        if self.power_pos > 0:
            if self.power_neg > 0:
                self.trend = round(self.power_pos - math.fabs(self.power_neg), 3)
                one_percent = (self.power_pos + math.fabs(self.power_neg)) / 100.0

                self.trend_percent = round(self.power_pos / one_percent, 2)
                #self.power_max = max([math.fabs(self.power_neg), self.power_pos])
            
            self.impuls_pos = statistics.harmonic_mean(positive)
            self.impuls_neg = statistics.harmonic_mean(negative)
            # self.impuls_median_pos = statistics.median(positive)
            # self.impuls_median_neg = statistics.median(negative)
            self.impuls_fmean = round(statistics.fmean(self.diffs_pool), 3)
            # self.impuls_pos = statistics.fmean(positive)
            # self.impuls_neg = statistics.fmean(negative)
            self.trend_percent_harmonic = round(self.impuls_pos / (self.impuls_pos + self.impuls_neg) * 100, 2)
            #self.trend_percent_median = round(self.impuls_median_pos / (self.impuls_median_pos + self.impuls_median_neg) * 100, 2)
                    
    def count_power(self, price:float):
        
        if len(self.prices_m1) < 4:
            self.prices_m1.append(price)
            return

        self.diffs_pool.append(price-self.prices_m1[-1])
        self.prices_m1.append(price)
        
        if len(self.diffs_pool) < 10: #self.diffs_pool.maxlen / 2:
            return

        self.power_pos = len(list(filter(lambda n: n > 0.0, self.diffs_pool)))
        self.power_neg = len(list(filter(lambda n: n < 0.0, self.diffs_pool)))

        if self.power_pos:
            if self.power_neg is not None:
                self.trend = round(self.power_pos - math.fabs(self.power_neg), 3)
                one_percent = (self.power_pos + math.fabs(self.power_neg)) / 100.0

                self.trend_percent = round(self.power_pos / one_percent, 2)
                self.power_max = max([math.fabs(self.power_neg), self.power_pos])

    def count_profit_ok(self, price:float):
        current_btc_val = self.native_balance[0] * price
        total = self.native_balance[0] * price + self.native_balance[1]
        target_btc_val = total * self.portfolio_ratio
        
        self.trade_profit = current_btc_val - target_btc_val
        self.price_diff = price - self.traded_price
        self.percent_diff = self.trade_profit / total * 100.0
        
    def count_portfolio(self, price, ratio):
        ratio += (self.prices[-2] - price) * self.ratio_per_point
        
        if ratio < self.min_max_ratio[0]:
            ratio = self.min_max_ratio[0]
            
        if ratio > self.min_max_ratio[1]:
            ratio = self.min_max_ratio[1]
            
        return ratio

    def count_profit(self, price:float, portfolio_ratio):
        portfolio_ratio = self.count_portfolio(price, portfolio_ratio) 
        current_btc_amount = self.native_balance[0] * price
        total = self.native_balance[0] * price + self.native_balance[1]
        target_btc_val = total * portfolio_ratio
        
        # calculate the difference between the expected and current balance
        trade_profit = current_btc_amount - target_btc_val
        percent_diff = trade_profit / total * 100.0
        
        price_diff = price - self.traded_price
        
        return trade_profit, price_diff, percent_diff, portfolio_ratio

    def monitor(self, price, m1_time, show=False):
        change = False
        if self.m1_timer != m1_time:
            change = True
            self.m1_timer = m1_time
            self.print_setup()

        if not show:
            self.work_range_win.append(price)
            self.ma_trend = round(self.sma(self.ma_trend_win, price), 2) - self.gap
            self.ma_fast_m = round(self.ema(int(self.ma_lenght), self.ma_fast_m, price), 2)
            return
        
        if show:
            self.count_impuls(price)
            self.count_power_s1(price)
            self.prices.append(price)
            
            if change:
                self.work_range_win.append(price)
                self.work_range = int(max(self.work_range_win) - min(self.work_range_win))

                self.ma_trend_prev = self.ma_trend
                self.ma_trend = round(self.sma(self.ma_trend_win, price), 2) - self.gap
                self.ma_fast_m = round(self.ema(int(self.ma_lenght), self.ma_fast_m, price), 2)

            if self.pair_balance and self.traded_price != 0.0:   
                self.trade_profit, self.price_diff, self.percent_diff, self.portfolio_ratio = self.count_profit(price, self.portfolio_ratio)
            
            # rebalance_delta = f"sell {round(abs(self.trade_profit), 2)}" if self.trade_profit > 0.0 else f"buy {round(self.trade_profit, 2)}"
            print(f"{int(price)}, "
                f"impuls:{self.impuls}|{self.impuls_fmean}, "
                f"ratio: {round(self.portfolio_ratio * 100.0, 2)}% ({round(self.percent_diff, 2)}), "
                f"mean: {round(self.buy_price_mean, 1)}, "
                f"pnl: {round(self.native_balance[0]*price - self.native_balance[0]*self.buy_price_mean, 1)} {self.pair[1]}, "
                f"trend: {round(self.ma_trend - self.ma_trend_prev, 1)} (EMA:{round(self.ma_fast_m - self.ma_trend, 1)}), "
                f"price diff: {round(abs(self.price_diff), 2)} > local range: {self.work_range}, "
                f"rebalance: {round(self.trade_profit, 2)} {self.pair[1]}"
                #f"sell at: {self.rebalance_top}"
                )
            

class Trader:
    def __init__(self, loop: asyncio.AbstractEventLoop, key, secret) -> None:
        self.loop = loop
        self.key = key
        self.secret = secret
        self.client = Client(self.loop, base_url="https://api.bybit.com/", key=key, secret=secret)
        self.pair = ['BTC', sys.argv[3]]
        self.symbol = ''.join(self.pair)
        self.margin = 0.0
        self.last_price = 0.0
        self.ta = TradeAnalyse(self.pair, size=60000)
        self.trade_lock = asyncio.Lock()
        self.print_balance_timer = 1.0  #time.time()
        self.max_percent_buy = 0.0
        self.max_percent_sell = 0.0
        self.minOrderQty = 0.000198
        self.minOrderAmt = 10.0
        
    async def initialize(self):
        self.client.session = aiohttp.ClientSession()
        self.client.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "volharvest/1.0",
            }
        )

        prices = []
        m1 = dict()
        
        # https://bybit-exchange.github.io/docs/v5/market/kline
        # > list[0]: startTime	string	Start time of the candle (ms)
        # > list[1]: openPrice	string	Open price
        # > list[2]: highPrice	string	Highest price
        # > list[3]: lowPrice	string	Lowest price
        # > list[4]: closePrice	string	Close price. Is the last traded price when the candle is not closed
        # > list[5]: volume	string	Trade volume. Unit of contract: pieces of contract. Unit of spot: quantity of coins
        # > list[6]: turnover	string	Turnover. Unit of figure: quantity of quota coin
        
        # {"retCode":0,
        #     "retMsg":"OK",
        #     "result":{
        #         "category":"spot",
        #         "symbol":"BTCUSDC",
        #         "list":[
        #             ["1730117460000","68564.29","68564.29","68557.51","68557.51","0.27609","18929.80573142"],
        #             ["1730117400000","68608.97","68612.17","68564.29","68564.29","13.616608","933896.91701808"]
        #         ]
        #     }
        # }
        
        while True:
            try:
                m1 = await self.client.get_klines(symbol=self.symbol, interval="1")
                break
            except Exception as ex:
                    print(f"ERROR: tr.initialize, {ex}")
                    print(f"{repr(traceback.extract_tb(ex.__traceback__))}")
                    await asyncio.sleep(4.0)
                    
        if m1["retCode"] != 0:
            return

        data = m1["result"]["list"]
        data.sort(key=lambda x: x[0])
        prices = list(map(lambda d: float(d[4]) , data))
       
        for p in prices:
            self.ta.monitor(p, 1.0, show=False)

        await self.Get_instrument_info(prices[-1])
        self.load_history()
    
    async def Get_instrument_info(self, price: float):
        data = await self.client.instrument_info(symbol=self.symbol)
        #print(data["result"]["list"][0]["lotSizeFilter"])
        self.minOrderQty = float(data["result"]["list"][0]["lotSizeFilter"]["minOrderQty"])
        self.minOrderAmt = float(data["result"]["list"][0]["lotSizeFilter"]["minOrderAmt"])

        print(f"INFO: minOrderQty: {decimal.Decimal.from_float(self.minOrderQty)}({round(self.minOrderQty * price, 2)} {self.pair[1]}), minOrderAmt: {self.minOrderAmt}")    
            
    def load_history(self):
        header = arr.array('L', [])
        data_s1 = arr.array('d', [])
        try:
            with open("data_s1.dat", 'rb') as f:
                header.fromfile(f, 1)
                data_s1.fromfile(f, header[0])

                counter = 0
                for pr in data_s1:
                    if counter > 0:
                        self.ta.diffs_pool.append(pr-self.ta.prices[-1])
                    self.ta.prices.append(pr)
                    counter += 1
            print(f"INFO: load prices, size: {len(self.ta.prices)}, last: {self.ta.prices[-1]}")
        except Exception as ex:
                print(f"ERROR: tr.initialize, {ex}")
                print(f"{repr(traceback.extract_tb(ex.__traceback__))}")
                
    async def account_balance_loop(self):

        while True:
            await self.get_account_balance()
            await asyncio.sleep(22.0)
        
    async def get_account_balance(self):
        """
        {'retCode': 0,
         'retMsg': 'OK', 
         'result': 
         {
             'list': 
                [
                    {
                        'totalEquity': '1896.1162586', 
                        'accountIMRate': '0', 
                        'totalMarginBalance': '1896.07115222', 
                        'totalInitialMargin': '0', 
                        'accountType': 'UNIFIED', 
                        'totalAvailableBalance': '1896.07115222', 
                        'accountMMRate': '0', 
                        'totalPerpUPL': '0', 
                        'totalWalletBalance': '1896.07115222', 
                        'accountLTV': '0', 
                        'totalMaintenanceMargin': '0', 
                        'coin': [
                            {
                                'availableToBorrow': '', 
                                'bonus': '0', 
                                'accruedInterest': '0', 
                                'availableToWithdraw': '0.00000066', 
                                'totalOrderIM': '0', 
                                'equity': '0.00000066', 
                                'totalPositionMM': '0', 
                                'usdValue': '0.04510637', 
                                'unrealisedPnl': '0', 
                                'collateralSwitch': False, 
                                'spotHedgingQty': '0', 
                                'borrowAmount': '0.000000000000000000', 
                                'totalPositionIM': '0', 
                                'walletBalance': '0.00000066', 
                                'cumRealisedPnl': '-0.00003433', 
                                'locked': '0', 
                                'marginCollateral': True, 
                                'coin': 'BTC'
                            }, 
                            {'availableToBorrow': '', 'bonus': '0', 'accruedInterest': '0', 'availableToWithdraw': '1897.43540828', 'totalOrderIM': '0', 'equity': '1897.43540828', 'totalPositionMM': '0', 'usdValue': '1896.07115222', 'unrealisedPnl': '0', 'collateralSwitch': True, 'spotHedgingQty': '0', 'borrowAmount': '0.000000000000000000', 'totalPositionIM': '0', 'walletBalance': '1897.43540828', 'cumRealisedPnl': '-2.32815315', 'locked': '0', 'marginCollateral': True, 'coin': 'USDC'}]}]}, 
                            'retExtInfo': {}, 
                            'time': 1717331875175
                            }
        """
        
        # {'retCode': 0, 'retMsg': 'OK', 'result': {'list': [
        #     {
        #         'totalEquity': '1895.97464863', 'accountIMRate': '0', 'totalMarginBalance': '1674.286611', 'totalInitialMargin': '0', 
        #         'accountType': 'UNIFIED', 'totalAvailableBalance': '1674.286611', 'accountMMRate': '0', 'totalPerpUPL': '0', 'totalWalletBalance': '1674.286611', 
        #         'accountLTV': '0', 'totalMaintenanceMargin': '0', 
        #         'coin': [
        #             {'availableToBorrow': '', 'bonus': '0', 'accruedInterest': '0', 'availableToWithdraw': '0.0032594', 'totalOrderIM': '0', 'equity': '0.0032594', 'totalPositionMM': '0', 'usdValue': '221.68803762', 'unrealisedPnl': '0', 'collateralSwitch': False, 'spotHedgingQty': '0', 'borrowAmount': '0.000000000000000000', 'totalPositionIM': '0', 'walletBalance': '0.0032594', 'cumRealisedPnl': '-0.00003759', 'locked': '0', 'marginCollateral': True, 'coin': 'BTC'}, 
        #             {'availableToBorrow': '', 'bonus': '0', 'accruedInterest': '0', 'availableToWithdraw': '1675.51476332', 'totalOrderIM': '0', 'equity': '1675.51476332', 'totalPositionMM': '0', 'usdValue': '1674.286611', 'unrealisedPnl': '0', 'collateralSwitch': True, 'spotHedgingQty': '0', 'borrowAmount': '0.000000000000000000', 'totalPositionIM': '0', 'walletBalance': '1675.51476332', 'cumRealisedPnl': '-2.32815315', 'locked': '0', 'marginCollateral': True, 'coin': 'USDC'}
        #             ]}
        #             ]},'retExtInfo': {}, 'time': 1717342385844}
    
    #{'BTC': 0.0, 'USDC': 1675.51476332}, totall:1675.51476332
        try:
            msg = await self.client.account()
        except Exception as ex:
            print(f"ERROR: get_account_balance, {ex}")
            print(f"{repr(traceback.extract_tb(ex.__traceback__))}")
            return

        if 'result' not in msg:
            return
        if 'list' not in msg['result']:
            return
        if 'coin' not in msg['result']['list'][0]:
            return
        
        data = msg['result']['list'][0]["coin"]
        self.get_pair_balance(data)

    async def ws_ticker(self):
        ticker = WSClient(self.loop, stream_url="wss://stream.bybit.com/v5/public/spot", key=self.key, secret=self.secret)
        
        # subscribtion = {"op": "subscribe", "args": [f"tickers.{self.symbol}", "kline.1.BTCUSDC"]}   
        subscribtion = {"op": "subscribe", "args": [f"kline.1.{self.symbol}"]}   
        await ticker.start(subscribtion, self.ticker_handler, need_auth=False)

    async def ws_user_data(self):
        ticker = WSClient(self.loop, stream_url="wss://stream.bybit.com/v5/private", key=self.key, secret=self.secret)
        #channels = f"tickers.{self.symbol}"#["user.balance", f"user.order.{self.symbol}"] #f"user.trade.{self.symbol}"
        channels = {"op": "subscribe", "args": ["wallet", "order"]}
        await ticker.start(channels, self.message_handler, need_auth=True)
        
    def get_pair_balance(self, data):
        """
        wallet = {
            'id': '198581153_wallet_1717323241371', 
            'topic': 'wallet', 
            'creationTime': 1717323241370, 
            'data': [
                        {
                            'accountIMRate': '0', 
                            'accountMMRate': '0', 
                            'totalEquity': '1886.65298697', 
                            'totalWalletBalance': '267.27422175', 
                            'totalMarginBalance': '267.27422175', 
                            'totalAvailableBalance': '200.48519696', 
                            'totalPerpUPL': '0', 
                            'totalInitialMargin': '0', 
                            'totalMaintenanceMargin': '0', 
                            'coin': [
                                        {'coin': 'USDC', 
                                        'equity': '0', 
                                        'usdValue': '0', 
                                        'walletBalance': '0', 
                                        'availableToWithdraw': '0', 
                                        'availableToBorrow': '', 
                                        'borrowAmount': '0', 
                                        'accruedInterest': '0', 
                                        'totalOrderIM': '0', 
                                        'totalPositionIM': '0', 
                                        'totalPositionMM': '0', 
                                        'unrealisedPnl': '0', 
                                        'cumRealisedPnl': '0', 
                                        'bonus': '0', 
                                        'collateralSwitch': True, 
                                        'marginCollateral': True, 
                                        'locked': '0', 
                                        'spotHedgingQty': '0'
                                        }, 
                                        {
                                            'coin': 'USDC', 
                                            'equity': '267.46572722', 
                                            'usdValue': '267.27422175', 
                                            'walletBalance': '267.46572722', 
                                            'availableToWithdraw': '200.41772084', 
                                            'availableToBorrow': '', 
                                            'borrowAmount': '0', 
                                            'accruedInterest': '0', 
                                            'totalOrderIM': '0', 
                                            'totalPositionIM': '0', 
                                            'totalPositionMM': '0', 
                                            'unrealisedPnl': '0', 
                                            'cumRealisedPnl': '-0.47257094', 
                                            'bonus': '0', 
                                            'collateralSwitch': True, 
                                            'marginCollateral': True, 
                                            'locked': '66.83688', 
                                            'spotHedgingQty': '0'
                                        }
                                    ], 
                            'accountLTV': '0', 
                            'accountType': 'UNIFIED'
                        }
                    ]
                }

        wallet_filled_buy = 
        {
            'id': '198581153_wallet_1717323248961', 
            'topic': 'wallet', 
            'creationTime': 1717323248961, 
            'data': [
                        {
                            'accountIMRate': '0', 
                            'accountMMRate': '0', 
                            'totalEquity': '1886.59224122', 
                            'totalWalletBalance': '200.48640073', 
                            'totalMarginBalance': '200.48640073', 
                            'totalAvailableBalance': '200.48640073', 
                            'totalPerpUPL': '0', 
                            'totalInitialMargin': '0', 
                            'totalMaintenanceMargin': '0', 
                            'coin': [
                                    {
                                        'coin': 'BTC', 
                                        'equity': '0.02499098', 
                                        'usdValue': '1686.10584048', 
                                        'walletBalance': '0.02499098', 
                                        'availableToWithdraw': '0.02499098', 
                                        'availableToBorrow': '', 
                                        'borrowAmount': '0', 
                                        'accruedInterest': '0', 
                                        'totalOrderIM': '0', 
                                        'totalPositionIM': '0', 
                                        'totalPositionMM': '0', 
                                        'unrealisedPnl': '0', 
                                        'cumRealisedPnl': '-0.00003201', 
                                        'bonus': '0',
                                        'collateralSwitch': False, 
                                        'marginCollateral': True, 
                                        'locked': '0', 
                                        'spotHedgingQty': '0'
                                    },
                                    {
                                        'coin': 'USDC', 
                                        'equity': '200.62884722', 
                                        'usdValue': '200.48640073', 
                                        'walletBalance': '200.62884722', 
                                        'availableToWithdraw': '200.62884722', 
                                        'availableToBorrow': '', 
                                        'borrowAmount': '0', 
                                        'accruedInterest': '0', 
                                        'totalOrderIM': '0', 
                                        'totalPositionIM': '0', 
                                        'totalPositionMM': '0', 
                                        'unrealisedPnl': '0', 
                                        'cumRealisedPnl': '-0.47257094', 
                                        'bonus': '0', 
                                        'collateralSwitch': True, 
                                        'marginCollateral': True, 
                                        'locked': '0', 
                                        'spotHedgingQty': '0'
                                    }
                                ], 
                            'accountLTV': '0', 
                            'accountType': 'UNIFIED'
                        }
                    ]
        }
       """

        # 'coin': [
        #             {'availableToBorrow': '', 'bonus': '0', 'accruedInterest': '0', 'availableToWithdraw': '0.0032594', 'totalOrderIM': '0', 'equity': '0.0032594', 'totalPositionMM': '0', 'usdValue': '221.68803762', 'unrealisedPnl': '0', 'collateralSwitch': False, 'spotHedgingQty': '0', 'borrowAmount': '0.000000000000000000', 'totalPositionIM': '0', 'walletBalance': '0.0032594', 'cumRealisedPnl': '-0.00003759', 'locked': '0', 'marginCollateral': True, 'coin': 'BTC'}, 
        #             {'availableToBorrow': '', 'bonus': '0', 'accruedInterest': '0', 'availableToWithdraw': '1675.51476332', 'totalOrderIM': '0', 'equity': '1675.51476332', 'totalPositionMM': '0', 'usdValue': '1674.286611', 'unrealisedPnl': '0', 'collateralSwitch': True, 'spotHedgingQty': '0', 'borrowAmount': '0.000000000000000000', 'totalPositionIM': '0', 'walletBalance': '1675.51476332', 'cumRealisedPnl': '-2.32815315', 'locked': '0', 'marginCollateral': True, 'coin': 'USDC'}
        #         ]
        
        p0 =  next(filter(lambda x: x['coin'] == self.pair[0], data), None)
        p1 =  next(filter(lambda x: x['coin'] == self.pair[1], data), None)

        native = [self.ta.native_balance[0], self.ta.native_balance[1]]

        if p0:
            native[0] = float(p0['equity'])
        if p1:
            native[1] = float(p1['equity'])

        self.ta.native_balance = (native[0], native[1])
        self.ta.pair_balance[self.pair[0]] = native[0] * self.last_price
        self.ta.pair_balance[self.pair[1]] = native[1]

        total = sum(self.ta.pair_balance.values())
        ratio = round(self.ta.pair_balance[self.pair[0]] / total * 100.0, 2)
        
        print(f"    {self.pair[0]}: {round(self.ta.pair_balance[self.pair[0]], 2)} ({ratio} %), "
              f"{self.pair[1]}: {round(self.ta.pair_balance[self.pair[1]], 2)} ({round(100.0 - ratio, 2)} %), "
              f"total:{round(total, 2)}"
              )

    def message_handler(self, msg):
        # print(f"message_handler: {msg}")

        # {'success': True, 'ret_msg': '', 'op': 'auth', 'conn_id': 'cmjop6gf2tdtup418330-13evcq'}
        # {'success': True, 'ret_msg': '', 'op': 'subscribe', 'conn_id': 'cmjop6gf2tdtup418330-13evcq'}

        # {'topic': 'order', 
        #  'id': '198581153_22009_30594798538', 
        #  'creationTime': 1717320865878, 
        #  'data': [
        #      {'category': 'spot', 
        #       'symbol': 'BTCUSDC', 
        #       'orderId': '1699405026566695680', 
        #       'orderLinkId': '1717320865460', 
        #       'blockTradeId': '', 
        #       'side': 'Sell', 
        #       'positionIdx': 0, 
        #       'orderStatus': 'Filled', 
        #       'cancelType': 'UNKNOWN', 
        #       'rejectReason': 'EC_NoError', 
        #       'timeInForce': 'GTC', 
        #       'isLeverage': '0', 
        #       'price': '67610.00', 
        #       'qty': '0.006989', 
        #       'avgPrice': '67616.39', 
        #       'leavesQty': '0.000000', 
        #       'leavesValue': '0.00000000', 
        #       'cumExecQty': '0.006989', 
        #       'cumExecValue': '472.57094971', 
        #       'cumExecFee': '0.47257094971', 
        #       'orderType': 'Limit', 
        #       'stopOrderType': '', 
        #       'orderIv': '', 
        #       'triggerPrice': '0.00', 
        #       'takeProfit': '0.00', 
        #       'stopLoss': '0.00', 
        #       'triggerBy': '', 
        #       'tpTriggerBy': '', 
        #       'slTriggerBy': '', 
        #       'triggerDirection': 0, 
        #       'placeType': '', 
        #       'lastPriceOnCreated': '67616.04', 
        #       'closeOnTrigger': False, 
        #       'reduceOnly': False, 
        #       'smpGroup': 0, 
        #       'smpType': 'None', 
        #       'smpOrderId': '', 
        #       'slLimitPrice': '0.00', 
        #       'tpLimitPrice': '0.00', 
        #       'marketUnit': '', 
        #       'createdTime': '1717320865876', 
        #       'updatedTime': '1717320865877', 
        #       'feeCurrency': 'USDC'
        #       }
        #     ]
        # }

        

        if 'topic' in msg:
            match msg['topic']:
                case 'wallet':

                    if "data" not in msg:
                        return
        
                    data = msg['data'][0]["coin"]
                    self.get_pair_balance(data)

                case 'order':
                    # message_handler: {'topic': 'order', 'id': '198581153_22009_30595842447', 'creationTime': 1717321732525, 'data': [{'category': 'spot', 'symbol': 'BTCUSDC', 'orderId': '1699412296520264448', 'orderLinkId': '1717321732099', 'blockTradeId': '', 'side': 'Buy', 'positionIdx': 0, 'orderStatus': 'Filled', 'cancelType': 'UNKNOWN', 'rejectReason': 'EC_NoError', 'timeInForce': 'GTC', 'isLeverage': '0', 'price': '67456.00', 'qty': '0.003038', 'avgPrice': '67449.99', 'leavesQty': '0.000000', 'leavesValue': '0.01825838', 'cumExecQty': '0.003038', 'cumExecValue': '204.91306962', 'cumExecFee': '0.000003038', 'orderType': 'Limit', 'stopOrderType': '', 'orderIv': '', 'triggerPrice': '0.00', 'takeProfit': '0.00', 'stopLoss': '0.00', 'triggerBy': '', 'tpTriggerBy': '', 'slTriggerBy': '', 'triggerDirection': 0, 'placeType': '', 'lastPriceOnCreated': '67449.98', 'closeOnTrigger': False, 'reduceOnly': False, 'smpGroup': 0, 'smpType': 'None', 'smpOrderId': '', 'slLimitPrice': '0.00', 'tpLimitPrice': '0.00', 'marketUnit': '', 'createdTime': '1717321732522', 'updatedTime': '1717321732524', 'feeCurrency': 'BTC'}]}
                    data = msg['data'][0]
                    
                    if not 'avgPrice' in data:
                        return

                    if data['avgPrice'] == '':
                        return
                    
                    self.manage_trades(data)
                    
                    price = float(data['avgPrice'])
                    qtty = float(data['qty'])
                    print(f"MESSAGE: ------------- {data['side']}, ",
                          f"type:{data['orderType']}, ",
                          f"Current status:{data['orderStatus']}, ",
                          f"price:{price}, q:{qtty} {self.pair[1]}",
                    )
                    
                    
                case _:
                    pass

        # if "executionReport" in json.dumps(msg):
        #     self.order[msg['S']] = msg

        #     price = round(float(msg['p']), 2)
        #     qtty = (float(msg['q']), float(msg['q']) * float(msg['p']))

    def manage_trades(self, data):
        # DEBUG: params: {"category":"spot","symbol":"BTCUSDC","side":"Buy","orderType":"Market","qty":"6746.0355445","timeInForce":"IOC","orderLinkId":"","isLeverage":0}
        # {'avgPrice': '56897.08',
        # 'blockTradeId': '',
        # 'cancelType': 'UNKNOWN',
        # 'category': 'spot',
        # 'closeOnTrigger': False,
        # 'createdTime': '1720446320000',
        # 'cumExecFee': '0',
        # 'cumExecQty': '0.118565',
        # 'cumExecValue': '6746.00233705',
        # 'feeCurrency': 'BTC',
        # 'isLeverage': '0',
        # 'lastPriceOnCreated': '56888.84',
        # 'leavesQty': '0.000000',
        # 'leavesValue': '0.03320745',
        # 'marketUnit': 'quoteCoin',
        # 'orderId': '1725623236034915072',
        # 'orderIv': '',
        # 'orderLinkId': '1725623236034915073',
        # 'orderStatus': 'PartiallyFilledCanceled',
        # 'orderType': 'Market',
        # 'placeType': '',
        # 'positionIdx': 0,
        # 'price': '0',
        # 'qty': '6746.03554450',
        # 'reduceOnly': False,
        # 'rejectReason': 'EC_CancelForNoFullFill',
        # 'side': 'Buy',
        # 'slLimitPrice': '0.00',
        # 'slTriggerBy': '',
        # 'smpGroup': 0,
        # 'smpOrderId': '',
        # 'smpType': 'None',
        # 'stopLoss': '0.00',
        # 'stopOrderType': '',
        # 'symbol': 'BTCUSDC',
        # 'takeProfit': '0.00',
        # 'timeInForce': 'IOC',
        # 'tpLimitPrice': '0.00',
        # 'tpTriggerBy': '',
        # 'triggerBy': '',
        # 'triggerDirection': 0,
        # 'triggerPrice': '0.00',
        # 'updatedTime': '1720446320002'}

        if not 'Filled' in data['orderStatus']:
            return
        
        # if data['rejectReason'] != 'EC_NoError':
        #     return

        if data['side'] == 'Buy':
            if data['symbol'].startswith(self.pair[0]):
                price = float(data['avgPrice'])
                qtty = float(data['qty'])
                btc = qtty / price
                str_quantity = str(decimal.Decimal.from_float(btc))
                if len(str_quantity) > 8:
                    str_quantity = str_quantity[:8]
                    btc = float(str_quantity)
                    
                self.ta.traded_price = price
                
                if self.ta.buy_price_mean == 0.0:
                    self.ta.buy_price_mean = price
                else:
                    
                    # btc / usd
                    # 0.052948 / 5511.85556068
                    
                    # (5000 + 2500) / (0,051282051 + 0,027027027)
                    # (7500+ 1250) / 0,092594792
                    # (0.01280579 * 62293.2 + 10.0) / (0.01280579 + 10.0 / 61728.56)
                    # prices:[62300.34, 61728.56], weights: [0.01280579, 0.00016199956713715662]
                    # MESSAGE: ------------- Buy,  type:Market,  Current status:Filled,  price:61728.56, q:10.0 USDC
                    # {'BTC': 800.389376219, 'USDC': 4642.12859809} (14.71 %, 85.28999999999999 %), total:5442.517974309

                    # str_btc = str(qtty / price)
                    
                    # if len(str_btc) > 8:
                    #     btc = str_btc[:8]
                    
                    
                    #print(f"str_btc: {str_btc}, btc: {btc}")
                    
                    # weights = [self.ta.native_balance[0], btc]
                    # prices = [self.ta.buy_price_mean, price]
                    # print(f"prices:{prices}, weights: {weights}")
                    

                    print(f"({self.ta.native_balance[0]} * {self.ta.buy_price_mean} + {qtty}) / ({self.ta.native_balance[0]} + {qtty} / {price})")

                    self.ta.buy_price_mean = round((self.ta.native_balance[0] * self.ta.buy_price_mean + qtty) / (self.ta.native_balance[0] + btc), 2)
                    self.loop.create_task(Fire_alert(bot_message=f"B: {self.ta.traded_price}, -{round(qtty, 2)}, mean: {self.ta.buy_price_mean}",
                                      bot_token=self.ta.bot_token,
                                      bot_chatID=self.ta.bot_chatID
                                      ))
                self.save_states()
                
                # MESSAGE: ------------- Buy,  type:Market,  Current status:Filled,  price:94507.54, q:5.0 USDT
                # btc = str(qtty / price)
                # if len(btc) > 8:
                #     btc = btc[:8]

                # self.ta.buy_list.append([price, btc])
                # self.ta.buy_list.sort(key=lambda x: x[0], reverse=True)
                
                # with open("buy_list.json", 'w') as f:
                #     json.dump(self.ta.buy_list, f, indent=4)

                
        if data['side'] == 'Sell':
            if data['symbol'].startswith(self.pair[0]):
                price = float(data['avgPrice'])
                qtty = float(data['qty'])

                
                # (0.01280579 * 62293.2 - 10.0) / (0.01280579 - 10.0 / 61728.56)
                #  (0.001231 * 89561 - 0.000124*102174.12) / (0.001231 - 0.000124) 
                
                self.ta.buy_price_mean = round((self.ta.native_balance[0] * self.ta.buy_price_mean - qtty* price) / (self.ta.native_balance[0] - qtty), 2)
                self.ta.traded_price = price
                self.save_states()
                self.loop.create_task(Fire_alert(bot_message=f"S: {self.ta.traded_price}, {round(qtty* price, 2)}, mean: {self.ta.buy_price_mean}",
                                      bot_token=self.ta.bot_token,
                                      bot_chatID=self.ta.bot_chatID
                                      ))
                
                self.loop.create_task(self.wait_for_change_balance(price))

    async def wait_for_change_balance(self, price:float):
        await asyncio.sleep(3.0)
        if self.ta.native_balance[0] * price  < 11.0:
            self.ta.traded_price = price
            self.ta.buy_price_mean = 0.0
            self.save_states()
        
    def ticker_handler(self, msg):
       
        #{'type': 'snapshot', 'topic': 'kline.1.BTCUSDC', 'data': [{'start': 1717334160000, 'end': 1717334219999, 'interval': '1', 'open': '67945.49', 'close': '67919.1', 'high': '67945.49', 'low': '67909.18', 'volume': '4.949795', 'turnover': '336220.15102034', 'confirm': False, 'timestamp': 1717334192215}], 'ts': 1717334192215}
        #if "kline.1.BTCUSDC" in msg
        if 'topic' in msg:
            if msg['topic'] == f"kline.1.{self.symbol}":
                if 'data' in msg:
                    d = msg['data'][0]
                    # if self.ta.m1_timer != d["end"]:
                    #     self.ta.m1_timer = d["end"]

                    self.last_price = float(d["close"])
                    self.ta.monitor(self.last_price, d["end"],  show=True)
        else:
            print(f"WARNING: ticker_handler, msg: {msg}")
        # if msg['topic'] == f"tickers.{self.symbol}":
        #     if 'data' in msg:
        #         if 'symbol' in msg['data']:
        #             if msg['data']['symbol'] == self.symbol:
        #                 self.last_price = float(msg['data']["lastPrice"])
        #                 self.ta.monitor(self.last_price, show=True)

    def save_states(self):
        data = dict()
        data['traded_price'] = self.ta.traded_price
        data['buy_price_mean'] = self.ta.buy_price_mean
        data['portfolio_ratio'] = self.ta.portfolio_ratio
        data['trend_crossover'] = self.ta.trend_crossover.cross
        data['trend_crossunder'] = self.ta.trend_crossunder.cross

        with open("states.json", 'w') as f:
            json.dump(data, f, indent=4)

    def init_new_states(self):
        current_btc_amount = self.ta.native_balance[0] * self.last_price
        total = current_btc_amount + self.ta.native_balance[1]
        self.ta.portfolio_ratio = current_btc_amount / total
        
        self.ta.traded_price = self.last_price
        self.ta.buy_price_mean = 0.0
        self.ta.trend_crossover.cross = False
        self.ta.trend_crossunder.cross = False
        
        print(f"traded_price:{self.ta.traded_price}\n"
              f"buy_price_mean:{self.ta.buy_price_mean}\n"
              f"trend_crossover:{self.ta.trend_crossover.cross}\n"
              f"trend_crossunder:{self.ta.trend_crossunder.cross}\n"
              f"portfolio_ratio:{self.ta.portfolio_ratio}"
              )
        
    def load_states(self):
        try:
            with open("states.json", 'r') as f:
                data = json.load(f)
                self.ta.traded_price = data['traded_price']
                self.ta.buy_price_mean = data['buy_price_mean']
                self.ta.portfolio_ratio = data['portfolio_ratio']
                self.ta.trend_crossover.cross = data['trend_crossover']
                self.ta.trend_crossunder.cross = data['trend_crossunder']
                print(f"Load states.json: {data}")

        except Exception as ex:
            self.init_new_states()
            print(f"{ex.with_traceback(None)}")

    async def do_buy(self, qtty):
        counter = 0
        while counter < 20:
            counter += 1
            try:
                resp_data, resp_status = await self.client.market_order(symbol=self.symbol, side='Buy', quantity_size=qtty)
                print(resp_data)
                if resp_status != 200:
                    print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
                    break
                if resp_data["retCode"] != 0:
                    await asyncio.sleep(2.0)
                    if self.ta.pair_balance[self.pair[0]] < 7.0:
                        break
                    # {'retCode': 170131, 'retMsg': 'Insufficient balance.', 'result': {}, 'retExtInfo': {}, 'time': 1718698611944}
                    if resp_data["retCode"] == 170131:
                        qtty *= 0.99
                    else:
                        break
                else:
                    break
            except Exception as e:
                print(f"ERROR: do_buy, {e.with_traceback(__tb = sys.exc_info()[2])}")
                await asyncio.sleep(1.1)

    async def do_sell(self, qtty):
        counter = 0
        while counter < 20:
            counter += 1
            try:
                resp_data, resp_status = await self.client.market_order(symbol=self.symbol, side='Sell', quantity_size=qtty)
                print(resp_data)
                if resp_status != 200:
                    print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
                    break
                if resp_data["retCode"] != 0:
                    await asyncio.sleep(2.0)
                    if self.ta.pair_balance[self.pair[0]] < 7.0:
                        break
                    # {'retCode': 170131, 'retMsg': 'Insufficient balance.', 'result': {}, 'retExtInfo': {}, 'time': 1718698611944}
                    if resp_data["retCode"] == 170131:
                        qtty *= 0.99
                    else:
                        break
                else:
                    break
            except Exception as e:
                print(f"ERROR: do_sell(), {e.with_traceback(__tb = sys.exc_info()[2])}")
                await asyncio.sleep(1.1)

    async def buy_signal(self):
        qty = math.fabs(self.ta.trade_profit)
        # if qty < 16.0 or self.ta.native_balance[1] < 16.0:
        if qty < self.minOrderAmt or self.ta.native_balance[1] < self.minOrderAmt:
            print(f"Ma cross: BUY, low qtty:{qty}, minOrderAmt: {self.minOrderAmt}")
            return False
      
        if qty > self.ta.native_balance[1]:
            qty = self.ta.native_balance[1]
        
        await self.do_buy(qty)
        return True

    async def sell_signal(self):
        qty = self.ta.trade_profit / self.last_price
        if qty < self.minOrderQty:
            print(f"Ma cross: SELL, low qtty:{qty * self.last_price}, minOrderQty: {self.minOrderQty}")
            return False

        await self.do_sell(qty)
        return True

    async def save_history_loop(self):

        while True:
            data_s1 = arr.array('d', self.ta.prices)
            header: arr.array = arr.array('L', [len(data_s1)])
            with open("data_s1.dat", 'wb') as f:
                header.tofile(f)
                data_s1.tofile(f)

            await asyncio.sleep(30.0)

    async def trade_loop(self):
        while self.last_price == 0.0:
            await asyncio.sleep(0.3)
            
        self.load_states()
        
        await asyncio.sleep(1.0)
        await self.get_account_balance()
        await asyncio.sleep(1.0)

        print(f"###################   Waiting for MA signal   ###################")

        await asyncio.sleep(7.0)

        price_change = self.last_price


        while True:
            await asyncio.sleep(0.3)

            if self.ta.ma_trend == 0.0 or self.ta.ma_fast_m == 0.0:
                continue
            
            trend = self.ta.ma_trend - self.ta.ma_trend_prev

            if abs(price_change - self.last_price) > 30.0:
                price_change = self.last_price
                self.save_states()
            

            try:
                if self.ta.trend_crossover.cross_over(self.ta.ma_fast_m, self.ta.ma_trend):
                    self.save_states()
                    
                    # don't BUY while trend going down
                    if trend < -1.0:
                        continue
                    
                    if abs(self.ta.percent_diff) < self.ta.rebalance_at * 0.5:
                        continue

                    if self.ta.trade_profit < 0.0:
                        if abs(self.ta.price_diff) > self.ta.work_range: # * 0.5:
                            if await self.buy_signal():
                                await asyncio.sleep(5.0)

                if self.ta.trend_crossunder.cross_under(self.ta.ma_fast_m, self.ta.ma_trend):
                    self.save_states()
                    
                    # don't SELL while trend going up
                    if trend > 0.0:
                        continue
                    
                    if abs(self.ta.percent_diff) < self.ta.rebalance_at:
                        continue
                    
                    if self.ta.trade_profit > 0.0:
                        if abs(self.ta.price_diff) > self.ta.work_range:
                            if await self.sell_signal():
                                await asyncio.sleep(5.0)

            except Exception as ex:
                print(f"ERROR: trade_loop, {ex}")
                print(f"{repr(traceback.extract_tb(ex.__traceback__))}")
            
if __name__ == "__main__":
    main_loop = asyncio.new_event_loop()
    
    tr = Trader(loop=main_loop, key=sys.argv[1], secret=sys.argv[2])

    main_loop.run_until_complete(tr.initialize())
   
    main_loop.create_task(tr.ws_ticker())

    time.sleep(1.0)
    main_loop.create_task(tr.ws_user_data())
    main_loop.create_task(tr.account_balance_loop())
    main_loop.create_task(tr.save_history_loop())
    main_loop.run_until_complete(tr.trade_loop())
