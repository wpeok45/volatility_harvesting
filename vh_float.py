import asyncio
import sys
import os
import socket
import array as arr
import json
import math
import cmath
import decimal
import hashlib
import hmac
import time
import datetime
import traceback
import statistics
import dotenv
from pathlib import Path
from collections import deque
import aiohttp

dotenv.load_dotenv(override=True)

API_KEY = os.getenv("API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
STABLE_PAIR = os.getenv("STABLE_PAIR", "USDT")
# trading signals length for MA, EMA
MA_LENGTH = float(os.getenv("MA_LENGTH", 24.0))
# range = 50% of ATH, ratio_per_point = 1.0 / RANGE (each price tick changes portfolio ratio like ratio +(-) ratio_per_point)
RANGE = float(os.getenv("RANGE", 50.0))
# minimum portfolio bitcoin to stablecoin ratio 1% / 99%
MIN_RATIO = float(os.getenv("MIN_RATIO", 0.01))
# maximum portfolio bitcoin to stablecoin ratio 99% /1%
MAX_RATIO = float(os.getenv("MAX_RATIO", 0.99))
# % rebalance(SELL)
REBALANCE_TOP = float(os.getenv("REBALANCE_TOP", 3.0))
# % rebalance(BUY)
REBALANCE_BOTTOM = float(os.getenv("REBALANCE_BOTTOM", 3.0))
REBALANCE_ISDYNAMIC = os.getenv("REBALANCE_ISDYNAMIC", "false").lower() in (
    "true",
    "1",
    "yes",
    "y",
)
# secundes, time frame for amplitude calculation
AMPLITUDE_TIME_FRAME = int(os.getenv("AMPLITUDE_TIME_FRAME", 120))
# trading fee in percent, default 0.1%
FEE = float(os.getenv("FEE", 0.1))
TGBOT_TOKEN = os.getenv("TGBOT_TOKEN", "")
TGBOT_CHATID = os.getenv("TGBOT_CHATID", "")


async def Fire_alert(bot_message: str, bot_token: str, bot_chatID: str):
    if bot_token == "" or bot_chatID == "":
        return

    msg = bot_message.replace("_", " ")

    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={bot_chatID}&parse_mode=Markdown&text={msg}"
            async with session.get(url) as resp:
                print("************************* allert sent")
    except Exception as ex:
        print(f"ERROR: Fire_alert, {repr(traceback.extract_tb(ex.__traceback__))}")


def log(data: str, log_file: str = "trading.log"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, mode="a", encoding="UTF-8") as f:
        print(f"[{timestamp}] {data}", file=f)


def rotate_log_file(log_file: str, max_files: int = 5, max_size_mb: float = 10.0):
    """Rotate log file if it exceeds max size.

    Args:
        log_file: Path to log file
        max_files: Maximum number of rotated files to keep
        max_size_mb: Maximum file size in MB before rotation
    """
    log_path = Path(log_file)

    # Check if file exists and size
    if not log_path.exists():
        return

    file_size_mb = log_path.stat().st_size / (1024 * 1024)

    if file_size_mb < max_size_mb:
        return

    # Rotate existing backup files
    for i in range(max_files - 1, 0, -1):
        old_file = Path(f"{log_file}.{i}")
        new_file = Path(f"{log_file}.{i + 1}")

        if old_file.exists():
            if i + 1 >= max_files:
                # Delete oldest file
                old_file.unlink()
            else:
                # Rename to next number
                old_file.rename(new_file)

    # Rename current log to .1
    if log_path.exists():
        log_path.rename(f"{log_file}.1")

    print(f"LOG ROTATED: {log_file} ({file_size_mb:.2f} MB)")


class WSClient:
    def __init__(self, loop: asyncio.AbstractEventLoop, stream_url, key, secret):
        self.loop = loop
        self.key = key
        self.secret = secret
        self.stream_url = stream_url
        resolver = aiohttp.resolver.AsyncResolver(nameservers=["1.1.1.1", "8.8.8.8"])
        connector = aiohttp.TCPConnector(
            loop=self.loop,
            family=socket.AF_INET,
            limit=100,
            ttl_dns_cache=30000,
            resolver=resolver,
        )
        timeout = aiohttp.ClientTimeout(total=5)
        self.session = aiohttp.ClientSession(
            loop=self.loop, connector=connector, timeout=timeout
        )

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "volharvest/2.0",
            },
        )

    async def _create_auth(self):
        # Generate expires.
        expires = int((time.time() + 100) * 1000)

        # Generate signature.
        signature = str(
            hmac.new(
                bytes(self.secret, "utf-8"),
                bytes(f"GET/realtime{expires}", "utf-8"),
                digestmod="sha256",
            ).hexdigest(),
        )

        return {
            "op": "auth",
            "args": [self.key, expires, signature],
        }  # , 'req_id': '10002'}

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
                    "category": "spot",
                },
            ],
        }

        return sub_msg

    async def ws_ping_loop(self, ws):
        await asyncio.sleep(5.0)

        while True:
            try:
                data = {"op": "ping"}
                await ws.send_str(json.dumps(data, ensure_ascii=False), compress=None)
            except Exception as ex:
                print(f"ERROR: ws_ping, {ex}")
                print(f"{repr(traceback.extract_tb(ex.__traceback__))}")
                return

            await asyncio.sleep(20.0)

    async def start(self, subscribe: list, callback, need_auth=False):

        while 1:
            await self.initialize()
            print(f"ws start: {self.stream_url}")
            try:
                async with self.session.ws_connect(self.stream_url) as ws:
                    if need_auth:
                        data = await self._create_auth()
                        await ws.send_str(
                            json.dumps(data, ensure_ascii=False), compress=None
                        )
                        await asyncio.sleep(1.0)

                    await ws.send_str(json.dumps(subscribe))  # , ensure_ascii=False))

                    await asyncio.sleep(1.0)

                    self.loop.create_task(self.ws_ping_loop(ws))

                    async for msg in ws:
                        match msg.type:
                            case aiohttp.WSMsgType.TEXT:
                                txt = msg.data
                                if "ping" not in txt:
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
                                print(
                                    f"ERROR: ws, Error during receive, {subscribe}, {ws.exception()}"
                                )
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
        timeout = aiohttp.ClientTimeout(total=5)
        self.session = aiohttp.ClientSession(loop=self.loop, timeout=timeout)

    def genSignature(self, payload, time_stamp, recv_window):
        param_str = str(time_stamp) + self.key + recv_window + payload
        hash = hmac.new(
            bytes(self.secret, "utf-8"), param_str.encode("utf-8"), hashlib.sha256
        )
        signature = hash.hexdigest()
        return signature

    async def HTTP_Request(self, endPoint, method, payload, Info):
        recv_window = str(5000)
        time_stamp = str(int(time.time() * 10**3))
        signature = self.genSignature(payload, time_stamp, recv_window)

        headers = {
            "X-BAPI-API-KEY": self.key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": time_stamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json",
        }

        if method == "POST":
            async with self.session.post(
                self.base_url + endPoint, headers=headers, data=payload
            ) as resp:
                resp_data = await resp.json()
        else:
            async with self.session.get(
                self.base_url + endPoint + "?" + payload, headers=headers
            ) as resp:
                resp_data = await resp.json()

        return resp_data, resp.status

    async def account(self):
        endpoint = "/v5/account/wallet-balance"
        params = "accountType=UNIFIED"
        resp_data, resp_status = await self.HTTP_Request(
            endpoint, "GET", params, "Account"
        )
        if resp_status != 200:
            print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
            return None

        return resp_data

    async def fee_rate(self, symbol):
        endpoint = "/v5/account/fee-rate"
        params = f"symbol={symbol}"
        resp_data, resp_status = await self.HTTP_Request(
            endpoint, "GET", params, "Fee-rate"
        )
        if resp_status != 200:
            print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
            return None

        return resp_data

    async def limit_order(
        self, symbol: str, side: str, price: float, quantity_size: float
    ):
        quantity = round(quantity_size, 5)
        q = str(quantity)
        zeros = "".join(["0"] * (8 - len(q)))
        str_quantity = q + zeros

        endpoint = "v5/order/create"
        method = "POST"
        # orderLinkId=uuid.uuid4().hex

        params = (
            '{"category":"spot","symbol":"%s","side":"%s","orderType":"Market","qty":"%s","timeInForce":"IOC","orderLinkId":"","isLeverage":0}'
            % (symbol, side, str_quantity)
        )
        print(f"DEBUG: params: {params}")

        resp_data, resp_status = await self.HTTP_Request(
            endpoint, method, params, "Create"
        )

        if resp_status != 200:
            print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
            return False, -1

        return True, resp_data["retCode"]

    async def market_order(self, symbol: str, side: str, quantity_size: float):
        str_quantity = str(decimal.Decimal.from_float(quantity_size))
        if len(str_quantity) > 8:
            str_quantity = str_quantity[:8]

        endpoint = "v5/order/create"
        method = "POST"
        # orderLinkId=uuid.uuid4().hex

        params = (
            '{"category":"spot","symbol":"%s","side":"%s","orderType":"Market","qty":"%s","timeInForce":"IOC","orderLinkId":"","isLeverage":0}'
            % (symbol, side, str_quantity)
        )
        print(f"DEBUG: params: {params}")

        return await self.HTTP_Request(endpoint, method, params, "Create")

    async def get_klines(self, symbol, interval=1):
        url = "".join([self.base_url, "/v5/market/kline"])

        params = {
            "category": "spot",
            "symbol": symbol,
            "interval": interval,
            "limit": 1000,
        }

        async with self.session.get(url, params=params) as resp:
            data = await resp.json()
            # print(resp.status, data)
            return data
        # except:
        #     exit()

    async def instrument_info(self, symbol):
        endpoint = "/v5/market/instruments-info"
        params = f"category=spot&symbol={symbol}"
        resp_data, resp_status = await self.HTTP_Request(
            endpoint, "GET", params, "instrument_info"
        )
        if resp_status != 200:
            print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
            return None

        return resp_data


class Crossunder:
    def __init__(self):
        self.cross = False

    def cross_under(self, a: float, b: float):
        if a >= b:
            self.cross = False
            return False

        if a < b:
            # if a - b < -1.0:
            if not self.cross:
                self.cross = True
                return True
        return False


class Crossover:
    def __init__(self):
        self.cross = False

    def cross_over(self, a: float, b: float):
        if a <= b:
            self.cross = False
            return False

        if a > b:
            # if a - b > 1.0:
            if not self.cross:
                self.cross = True
                return True
        return False


class DynamicOrderScale:
    """Manages dynamic scaling of buy/sell order percentages based on consecutive trades.

    Supports both Fibonacci and linear scaling strategies.
    """

    # Fibonacci sequence cache (class-level constant)
    FIBONACCI_SEQUENCE = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610]

    def __init__(
        self,
        min_buy_percent: float,
        min_sell_percent: float,
        use_fibonacci: bool = True,
    ) -> None:
        """Initialize order scaler.

        Args:
            min_buy_percent: Minimum buy percentage
            min_sell_percent: Minimum sell percentage
            use_fibonacci: Use Fibonacci sequence for scaling (default: True)
        """
        self.enabled = False
        self.min_buy_percent = min_buy_percent
        self.min_sell_percent = min_sell_percent
        self.use_fibonacci = use_fibonacci
        self._buy_counter = 1
        self._sell_counter = 1

    @property
    def buy_counter(self) -> int:
        """Current buy counter."""
        return self._buy_counter

    @buy_counter.setter
    def buy_counter(self, value: int) -> None:
        """Set buy counter with validation."""
        if value < 1:
            self._buy_counter = 1
        elif value > len(self.FIBONACCI_SEQUENCE):
            self._buy_counter = len(self.FIBONACCI_SEQUENCE)
        else:
            self._buy_counter = value

    @property
    def sell_counter(self) -> int:
        """Current sell counter."""
        return self._sell_counter

    @sell_counter.setter
    def sell_counter(self, value: int) -> None:
        """Set sell counter with validation."""
        if value < 1:
            self._sell_counter = 1
        elif value > len(self.FIBONACCI_SEQUENCE):
            self._sell_counter = len(self.FIBONACCI_SEQUENCE)
        else:
            self._sell_counter = value

    def _get_multiplier(self, counter: int) -> float:
        """Get scaling multiplier for given counter.

        Args:
            counter: Counter value (1-indexed)

        Returns:
            Multiplier value from Fibonacci or linear sequence
        """
        if not self.use_fibonacci:
            return counter

        # Convert 1-indexed to 0-indexed for array access
        index = counter - 1

        # Safely get Fibonacci value
        if index >= len(self.FIBONACCI_SEQUENCE):
            return self.FIBONACCI_SEQUENCE[-1]

        return self.FIBONACCI_SEQUENCE[index]

    def increment_buy(self) -> None:
        """Increase buy scale, decrease sell scale."""
        self._buy_counter = min(self._buy_counter + 1, len(self.FIBONACCI_SEQUENCE))
        self._sell_counter = max(self._sell_counter - 1, 1)

    def increment_sell(self) -> None:
        """Increase sell scale, decrease buy scale."""
        self._sell_counter = min(self._sell_counter + 1, len(self.FIBONACCI_SEQUENCE))
        self._buy_counter = max(self._buy_counter - 1, 1)

    def get_buy_percent(self) -> float:
        """Calculate current buy percentage based on counter.

        Returns:
            Scaled buy percentage
        """
        if not self.enabled:
            return self.min_buy_percent

        multiplier = self._get_multiplier(self._buy_counter)
        return self.min_buy_percent * multiplier

    def get_sell_percent(self) -> float:
        """Calculate current sell percentage based on counter.

        Returns:
            Scaled sell percentage
        """
        if not self.enabled:
            return self.min_sell_percent

        multiplier = self._get_multiplier(self._sell_counter)
        return self.min_sell_percent * multiplier

    def reset(self) -> None:
        """Reset counters to initial state."""
        self._buy_counter = 1
        self._sell_counter = 1

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"DynamicOrderScale("
            f"enabled={self.enabled}, "
            f"buy={self.buy_counter}, "
            f"sell={self.sell_counter}, "
            f"fibonacci={self.use_fibonacci})"
        )


class TradeAnalyse:
    def __init__(self, pair, log_file: str = "trading.log") -> None:
        self.prices = deque(maxlen=60 * 60 * 24)
        self.diffs = deque(maxlen=3)
        self.diffs_pool = deque(maxlen=int(60 * 15))
        self.min_impuls = 0.0
        self.power_pos = 0
        self.power_neg = 0
        self.impuls = 0.0
        self.impuls_harmonic = 0.0
        self.impuls_percent = 0.0
        self.impuls_harmonic_percent = 0.0
        self.pair = pair
        self.pair_balance = dict()
        self.native_balance = (0.0, 0.0)
        self.trade_profit = 0.0
        self.price_diff = 0.1
        self.traded_price = 0.0
        self.m1_timer = 0.0
        self.buy_price_mean = 0.0
        self.local_range = 1000.0
        self.local_range_win = deque(maxlen=AMPLITUDE_TIME_FRAME)
        self.ma_length = MA_LENGTH
        self.gap = self.ma_length / 4.8
        self.ma_fast = 0.0
        self.ma_fast_m = 0.0
        self.ma_trend = 0.0
        self.ma_trend_prev = 10000000.0
        self.ma_trend_win = deque(maxlen=int(self.ma_length))
        self.trend_crossover = Crossover()
        self.trend_crossunder = Crossunder()
        self.rebalance_top = REBALANCE_TOP
        self.rebalance_bottom = REBALANCE_BOTTOM
        self.min_profitable_percent = REBALANCE_TOP
        self.order_scale = DynamicOrderScale(self.rebalance_bottom, self.rebalance_top)
        self.order_scale.enabled = REBALANCE_ISDYNAMIC
        self.fee = FEE / 100.0  # 0.1% = 0.001
        self.ATH = 999000.0
        self.working_range = self.ATH / 100.0 * RANGE
        self.ratio_per_point = 1.0 / self.working_range
        self.min_max_ratio = [MIN_RATIO, MAX_RATIO]
        self.log_file = log_file
        self.real_ratio = 0.0
        self.portfolio_ratio = self.min_max_ratio[0]
        self.percent_diff = 0.0
        self.bot_token = TGBOT_TOKEN
        self.bot_chatID = TGBOT_CHATID

    def fft(self, x):
        N = len(x)
        if N <= 1:
            return x
        even = self.fft(x[0::2])
        odd = self.fft(x[1::2])
        T = [cmath.exp(-2j * cmath.pi * k / N) * odd[k] for k in range(N // 2)]
        return [even[k] + T[k] for k in range(N // 2)] + [
            even[k] - T[k] for k in range(N // 2)
        ]

    def calculate_avg_amplitude(self, data):
        spectrum = self.fft(data)
        amplitudes = [abs(x) for x in spectrum[1:]]

        half = len(amplitudes) // 2
        positive_amplitudes = amplitudes[:half]

        average_amplitude = sum(positive_amplitudes) / len(positive_amplitudes)

        return average_amplitude

    def get_profitable_range(self, price: float):
        # 1000 / 118000 = 0,008474576               fee = 1.0
        # 0,008474576 * 118010 = 1000,08471376     fee = 1.0
        # 1000,08471376 − 1000 = 0,08471376
        # (2,0 ÷ 0,08471376) * 10 = 236,894521293 pips

        # 118237 / 1001.940338
        # 118000 / 999.932
        # 1001.940338 − 999.932 = 2,008338

        fee_amount = 1000.0 * self.fee * 2.0
        val = 1000.0 / price
        val_up_one = val * (price + 1.0)
        val_one_pip = val_up_one - 1000.0
        return fee_amount / val_one_pip

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

    def append_diff(self, price: float):
        impuls = price - self.prices[-1]
        if impuls != 0.0:
            self.diffs_pool.append(impuls)

    def count_power_s1(self, price: float):
        if len(self.prices) < 4:
            return
        self.append_diff(price)

        if len(self.diffs_pool) < 4:
            return

        abs_diffs_pool = list(map(lambda x: math.fabs(x), self.diffs_pool))
        abs_diffs_pool.sort(reverse=True)
        pos = len(abs_diffs_pool) // 10

        self.min_impuls = abs_diffs_pool[pos]

        positive = list(filter(lambda n: n > self.min_impuls, self.diffs_pool))
        neg_list = list(filter(lambda n: n < -self.min_impuls, self.diffs_pool))
        negative = list(map(lambda x: math.fabs(x), neg_list))

        self.power_pos = len(positive)
        self.power_neg = len(negative)

        if self.power_pos > 1:
            if self.power_neg > 1:
                self.impuls = self.power_pos - self.power_neg
                self.impuls_percent = round(
                    self.power_pos / (self.power_pos + self.power_neg) * 100 - 50.0, 2
                )

                impuls_pos = statistics.harmonic_mean(positive)
                impuls_neg = statistics.harmonic_mean(negative)

                self.impuls_harmonic = round(impuls_pos - impuls_neg, 2)

                self.impuls_harmonic_percent = round(
                    impuls_pos / (impuls_pos + impuls_neg) * 100 - 50.0, 2
                )

    def change_portfolio_ratio(self, price, ratio):
        if self.ATH == 999000.0:
            return 1.0

        if price > self.ATH:
            self.ATH = price

        self.working_range = self.ATH / 100.0 * RANGE
        self.ratio_per_point = 1.0 / self.working_range

        ratio += (self.prices[-2] - price) * self.ratio_per_point

        if ratio < self.min_max_ratio[0]:
            ratio = self.min_max_ratio[0]

        if ratio > self.min_max_ratio[1]:
            ratio = self.min_max_ratio[1]

        return ratio

    def calculate_profit(self, price: float):
        current_btc_amount = self.native_balance[0] * price
        total = current_btc_amount + self.native_balance[1]
        target_btc_amount = total * self.portfolio_ratio

        # calculate the difference between the expected and current balance
        self.trade_profit = current_btc_amount - target_btc_amount
        self.percent_diff = self.trade_profit / total * 100.0
        self.price_diff = price - self.traded_price

    def print_setup(self, price: float):
        if self.ATH == 999000.0:
            return
        # if self.trade_profit == 0.0:
        #     return

        min_profitable_range = self.get_profitable_range(price)
        one_percent_pips = self.working_range / 100.0
        self.min_profitable_percent = min_profitable_range / one_percent_pips

        if self.rebalance_top < self.min_profitable_percent:
            self.order_scale.min_sell_percent = self.rebalance_top

        if self.rebalance_bottom < self.min_profitable_percent:
            self.order_scale.min_buy_percent = self.rebalance_bottom

        self.rebalance_top = self.order_scale.get_sell_percent()
        self.rebalance_bottom = self.order_scale.get_buy_percent()

        sell_pips = round(one_percent_pips * self.rebalance_top, 2)
        buy_pips = round(one_percent_pips * self.rebalance_bottom, 2)

        total = self.native_balance[0] * price + self.native_balance[1]
        price_for_pips = total / self.working_range

        one_percent_amnt = round(price_for_pips * one_percent_pips, 2)
        sell_amnt = round(price_for_pips * sell_pips, 2)
        buy_amnt = round(price_for_pips * buy_pips, 2)

        sell_value = sell_amnt / price
        sell_amnt_old = sell_value * (price - sell_pips)

        sell_fee = sell_amnt * self.fee
        revenue = round(sell_amnt - sell_amnt_old - sell_fee * 2.0, 3)

        # real_value = abs(self.trade_profit / price)
        # real_amnt_old = real_value * (price - self.price_diff)
        # real_fee = abs(self.trade_profit * self.fee)
        # real_revenue = round(abs(self.trade_profit) - real_amnt_old - real_fee * 2.0, 2)

        real_value = self.trade_profit / price
        real_amnt_old = real_value * (price - self.price_diff)
        real_fee = self.trade_profit * (self.fee * 2.0)
        real_revenue = round(self.trade_profit - real_amnt_old - real_fee * 2.0, 3)

        data = (
            f"---------------Volatility harvesting------------\n"
            f"tg bot_chatID: {self.bot_chatID}\n"
            f"stable_pair: {STABLE_PAIR}\n"
            f"ATH: {self.ATH}\n"
            f"ma_length: {MA_LENGTH}\n"
            f"range: {RANGE}% ({int(self.working_range)}) pips, lower price limit: {int(price - self.native_balance[1] / price_for_pips)} {self.pair[1]}\n"
            f"ratio per pip: {self.ratio_per_point:.8f}\n"
            f"pip cost: {round(price_for_pips, 2)} {self.pair[1]}\n"
            f"min_ratio: {MIN_RATIO} ({float(MIN_RATIO) * 100.0}%)\n"
            f"max_ratio: {MAX_RATIO} ({float(MAX_RATIO) * 100.0}%)\n"
            f"amplitude {self.local_range_win.maxlen / 60} h: {self.local_range} pips\n"
            f"rebalance params:\n"
            f"  1%: {round(one_percent_pips, 2)} pips ({one_percent_amnt} {self.pair[1]})\n"
            f"  min profitable pips: {round(min_profitable_range, 1)} ({round(self.min_profitable_percent, 2)}%)\n"
            f"  is dynamic rebalance: {self.order_scale.enabled}\n"
            f"  buy at: -{round(self.rebalance_bottom, 2)}% (-{buy_pips} pips or -{buy_amnt} {self.pair[1]})\n"
            f"  sell at: {round(self.rebalance_top, 2)}% ({sell_pips} pips or {sell_amnt} {self.pair[1]})\n"
            f"  min revenue: {revenue} {self.pair[1]}\n"
            f"  fee: {round(sell_fee * 2, 3)} {self.pair[1]}\n"
            f"now:\n"
            f"  spread: {round(self.price_diff, 2)} pips, {round(self.percent_diff, 2)} %, {round(self.trade_profit, 2)} {self.pair[1]}\n"
            f"  fee:{round(real_fee, 3)} {self.pair[1]} (buy+sell)\n"
        )

        if self.price_diff > 0.0:
            data += f"  revenue: {real_revenue} {self.pair[1]}\n"

        data += f"------------------------------------------------------"

        print(data)

    def monitor(self, price, m1_time, show=False):
        change = False
        if self.m1_timer != m1_time:
            change = True
            self.m1_timer = m1_time

        self.count_power_s1(price)
        self.prices.append(price)

        if not show:
            self.local_range_win.append(price)
            self.ma_trend = round(self.sma(self.ma_trend_win, price), 2) - self.gap
            self.ma_fast_m = round(
                self.ema(int(self.ma_length), self.ma_fast_m, price), 2
            )
            return

        if show:
            self.portfolio_ratio = self.change_portfolio_ratio(
                price, self.portfolio_ratio
            )

            if change:
                rotate_log_file(self.log_file, max_files=5, max_size_mb=10.0)
                self.local_range_win.append(price)
                self.local_range = int(
                    max(self.local_range_win) - min(self.local_range_win)
                )

                self.ma_trend_prev = self.ma_trend
                self.ma_trend = round(self.sma(self.ma_trend_win, price), 2) - self.gap
                self.ma_fast_m = round(
                    self.ema(int(self.ma_length), self.ma_fast_m, price), 2
                )

            if self.pair_balance and self.traded_price != 0.0 and self.ATH != 999000.0:
                self.calculate_profit(price)
                if change:
                    self.print_setup(price)

            data = (
                f"{int(price)}, "
                f"impuls {self.diffs_pool.maxlen/60}m: {self.impuls}|{self.impuls_harmonic} ({self.impuls_percent}%|{self.impuls_harmonic_percent}%), "
                f"spot cost: {round(self.buy_price_mean, 1)}, "
                f"pnl: {round(self.native_balance[0]*price - self.native_balance[0]*self.buy_price_mean, 1)} {self.pair[1]}, "
                f"trend: {round(self.ma_trend - self.ma_trend_prev, 1)}, EMA:{round(self.ma_fast_m - self.ma_trend, 1)}, "
                f"spread: {round(abs(self.price_diff), 2)} > local range: {self.local_range}, "
                f"target ratio: {round(self.portfolio_ratio * 100.0, 2)}%, "
                f"rebalance: {round(self.percent_diff, 2)}% ({round(self.trade_profit, 2)} {self.pair[1]})"
            )

            print(data)
            log(data, self.log_file)


class Trader:
    def __init__(
        self, loop: asyncio.AbstractEventLoop, key, secret, data_dir: str = "data"
    ) -> None:
        self.loop = loop  # asyncio.get_running_loop()
        self.key = key
        self.secret = secret
        self.client = None
        self.pair = ["BTC", STABLE_PAIR]
        self.symbol = "".join(self.pair)
        self.last_price = 0.0
        self.minOrderQty = 0.000198
        self.minOrderAmt = 10.0
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # File paths for data storage
        self.log_file = str(self.data_dir / "trading.log")
        self.data_file = str(self.data_dir / "data_s1.dat")
        self.state_file = str(self.data_dir / f"{self.symbol}.json")

        # Initialize TradeAnalyse with log file
        self.ta = TradeAnalyse(self.pair, log_file=self.log_file)

    async def init_data(self):
        self.client = Client(
            loop=self.loop,
            base_url="https://api.bybit.com/",
            key=self.key,
            secret=self.secret,
        )
        self.client.session = aiohttp.ClientSession()
        self.client.session.headers.update(
            {
                "Content-Type": "application/json",
                "User-Agent": "volharvest/1.0",
            },
        )

        prices = []
        m1 = dict()

        while True:
            try:
                m720 = await self.client.get_klines(symbol=self.symbol, interval="720")
                # {
                #     "retCode":0,
                #     "retMsg":"OK",
                #     "result":{
                #         "category":"spot",
                #         "symbol":"BTCUSDT",
                #         "list":[
                #             ["1747785600000","106855.3","107731.9","106187.8","107518.1","3057.888486","327543867.4335117"],
                #             }

                m1 = await self.client.get_klines(symbol=self.symbol, interval="1")
                break
            except Exception as ex:
                print(f"ERROR: tr.initialize, {ex}")
                print(f"{repr(traceback.extract_tb(ex.__traceback__))}")
                await asyncio.sleep(4.0)

        if m1["retCode"] != 0:
            return

        # get ATH price for m720
        data = m720["result"]["list"]
        prices = list(map(lambda d: float(d[4]), data))
        self.ta.ATH = max(prices)

        # get 1m history
        data = m1["result"]["list"]
        data.sort(key=lambda x: x[0])
        prices = list(map(lambda d: float(d[4]), data))

        for p in prices:
            self.ta.monitor(p, 1.0, show=False)

        await self.Get_instrument_info(prices[-1])
        self.load_history()

    async def Get_instrument_info(self, price: float):
        data = await self.client.instrument_info(symbol=self.symbol)
        self.minOrderQty = float(
            data["result"]["list"][0]["lotSizeFilter"]["minOrderQty"]
        )
        self.minOrderAmt = float(
            data["result"]["list"][0]["lotSizeFilter"]["minOrderAmt"]
        )

        print(
            f"INFO: minOrderQty: {decimal.Decimal.from_float(self.minOrderQty)}({round(self.minOrderQty * price, 2)} {self.pair[1]}), minOrderAmt: {self.minOrderAmt}"
        )

    def load_history(self):
        header = arr.array("L", [])
        data_s1 = arr.array("d", [])
        try:
            with open(self.data_file, "rb") as f:
                header.fromfile(f, 1)
                data_s1.fromfile(f, header[0])

                counter = 0
                for pr in data_s1:
                    if counter > 0:
                        # self.ta.diffs_pool.append(pr - self.ta.prices[-1])
                        self.ta.append_diff(pr)
                    self.ta.prices.append(pr)
                    counter += 1
            print(
                f"INFO: load prices, size: {len(self.ta.prices)}, last: {self.ta.prices[-1]}"
            )
        except Exception as ex:
            print(f"ERROR: tr.initialize, {ex}")
            print(f"{repr(traceback.extract_tb(ex.__traceback__))}")

    async def account_balance_loop(self):

        while True:
            await self.get_account_balance()
            await asyncio.sleep(22.0)

    async def get_account_balance(self):
        try:
            msg = await self.client.account()
        except Exception as ex:
            print(f"ERROR: get_account_balance, {ex}")
            print(f"{repr(traceback.extract_tb(ex.__traceback__))}")
            return

        if "result" not in msg:
            return
        if "list" not in msg["result"]:
            return
        if "coin" not in msg["result"]["list"][0]:
            return

        data = msg["result"]["list"][0]["coin"]
        self.get_pair_balance(data)

    async def ws_ticker(self):
        ticker = WSClient(
            self.loop,
            stream_url="wss://stream.bybit.com/v5/public/spot",
            key=self.key,
            secret=self.secret,
        )
        subscribtion = {"op": "subscribe", "args": [f"kline.1.{self.symbol}"]}
        await ticker.start(subscribtion, self.ticker_handler, need_auth=False)

    async def ws_user_data(self):
        ticker = WSClient(
            self.loop,
            stream_url="wss://stream.bybit.com/v5/private",
            key=self.key,
            secret=self.secret,
        )
        channels = {"op": "subscribe", "args": ["wallet", "order"]}
        await ticker.start(channels, self.message_handler, need_auth=True)

    def get_pair_balance(self, data):
        p0 = next(filter(lambda x: x["coin"] == self.pair[0], data), None)
        p1 = next(filter(lambda x: x["coin"] == self.pair[1], data), None)

        native = [self.ta.native_balance[0], self.ta.native_balance[1]]

        if p0:
            native[0] = float(p0["equity"])
        if p1:
            native[1] = float(p1["equity"])

        self.ta.native_balance = (native[0], native[1])
        self.ta.pair_balance[self.pair[0]] = native[0] * self.last_price
        self.ta.pair_balance[self.pair[1]] = native[1]

        total = sum(self.ta.pair_balance.values())
        self.ta.real_ratio = round(
            self.ta.pair_balance[self.pair[0]] / total * 100.0, 2
        )

        print(
            f"            Balance: {self.pair[0]}: {round(self.ta.pair_balance[self.pair[0]], 2)} ({self.ta.real_ratio} %), "
            f"{self.pair[1]}: {round(self.ta.pair_balance[self.pair[1]], 2)} ({round(100.0 - self.ta.real_ratio, 2)} %), "
            f"total:{round(total, 2)}",
        )

    def message_handler(self, msg):
        if "topic" in msg:
            match msg["topic"]:
                case "wallet":

                    if "data" not in msg:
                        return

                    data = msg["data"][0]["coin"]
                    self.get_pair_balance(data)

                case "order":
                    data = msg["data"][0]

                    if "avgPrice" not in data:
                        return

                    if data["avgPrice"] == "":
                        return

                    self.manage_trades(data)

                    price = float(data["avgPrice"])
                    qtty = float(data["qty"])
                    if data["side"] == "Sell":
                        qtty *= price

                    out = (
                        f"MESSAGE: ------------- {data['side']}, "
                        f"type:{data['orderType']}, "
                        f"Current status:{data['orderStatus']}, "
                        f"price:{price}, q:{qtty} {self.pair[1]}"
                    )

                    print(out)
                    log(out, self.log_file)
                case _:
                    pass

    def manage_trades(self, data):
        if "Filled" not in data["orderStatus"]:
            return

        if data["side"] == "Buy":
            if data["symbol"].startswith(self.pair[0]):
                price = float(data["avgPrice"])
                qtty = float(data["qty"])
                btc = qtty / price
                str_quantity = str(decimal.Decimal.from_float(btc))
                if len(str_quantity) > 8:
                    str_quantity = str_quantity[:8]
                    btc = float(str_quantity)

                self.ta.traded_price = price
                self.ta.order_scale.increment_buy()

                if self.ta.buy_price_mean == 0.0:
                    self.ta.buy_price_mean = price
                else:
                    # print(
                    #     f"({self.ta.native_balance[0]} * {self.ta.buy_price_mean} + {qtty}) / ({self.ta.native_balance[0]} + {qtty} / {price})"
                    # )

                    self.ta.buy_price_mean = round(
                        (self.ta.native_balance[0] * self.ta.buy_price_mean + qtty)
                        / (self.ta.native_balance[0] + btc),
                        2,
                    )
                    self.loop.create_task(
                        Fire_alert(
                            bot_message=f"B: {self.ta.traded_price}, -{round(qtty, 2)}, mean: {self.ta.buy_price_mean}",
                            bot_token=self.ta.bot_token,
                            bot_chatID=self.ta.bot_chatID,
                        ),
                    )
                self.save_states()

        if data["side"] == "Sell":
            if data["symbol"].startswith(self.pair[0]):
                price = float(data["avgPrice"])
                qtty = float(data["qty"])

                self.ta.buy_price_mean = round(
                    (self.ta.native_balance[0] * self.ta.buy_price_mean - qtty * price)
                    / (self.ta.native_balance[0] - qtty),
                    2,
                )
                self.ta.traded_price = price
                self.ta.order_scale.increment_sell()

                self.save_states()
                self.loop.create_task(
                    Fire_alert(
                        bot_message=f"S: {self.ta.traded_price}, {round(qtty* price, 2)}, mean: {self.ta.buy_price_mean}",
                        bot_token=self.ta.bot_token,
                        bot_chatID=self.ta.bot_chatID,
                    ),
                )

                self.loop.create_task(self.wait_for_change_balance(price))

    async def wait_for_change_balance(self, price: float):
        await asyncio.sleep(3.0)
        if self.ta.native_balance[0] * price < 11.0:
            self.ta.traded_price = price
            self.ta.buy_price_mean = 0.0
            self.save_states()

    def ticker_handler(self, msg):
        if "topic" in msg:
            if msg["topic"] == f"kline.1.{self.symbol}":
                if "data" in msg:
                    d = msg["data"][0]
                    self.last_price = float(d["close"])
                    self.ta.monitor(self.last_price, d["end"], show=True)
        else:
            print(f"WARNING: ticker_handler, msg: {msg}")

    def save_states(self):
        data = dict()
        data["traded_price"] = self.ta.traded_price
        data["buy_price_mean"] = self.ta.buy_price_mean
        data["portfolio_ratio"] = self.ta.portfolio_ratio
        data["trend_crossover"] = self.ta.trend_crossover.cross
        data["trend_crossunder"] = self.ta.trend_crossunder.cross
        data["buy_counter"] = self.ta.order_scale.buy_counter
        data["sell_counter"] = self.ta.order_scale.sell_counter

        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=4)

    def init_new_states(self):
        current_btc_amount = self.ta.native_balance[0] * self.last_price
        total = current_btc_amount + self.ta.native_balance[1]
        self.ta.portfolio_ratio = current_btc_amount / total

        self.ta.traded_price = self.last_price
        self.ta.buy_price_mean = 0.0
        self.ta.trend_crossover.cross = False
        self.ta.trend_crossunder.cross = False

        print(
            f"traded_price:{self.ta.traded_price}\n"
            f"buy_price_mean:{self.ta.buy_price_mean}\n"
            f"trend_crossover:{self.ta.trend_crossover.cross}\n"
            f"trend_crossunder:{self.ta.trend_crossunder.cross}\n"
            f"portfolio_ratio:{self.ta.portfolio_ratio}",
        )

    def load_states(self):
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
                self.ta.traded_price = data["traded_price"]
                self.ta.buy_price_mean = data["buy_price_mean"]
                self.ta.portfolio_ratio = data["portfolio_ratio"]
                self.ta.trend_crossover.cross = data["trend_crossover"]
                self.ta.trend_crossunder.cross = data["trend_crossunder"]
                self.ta.order_scale._buy_counter = data["buy_counter"]
                self.ta.order_scale._sell_counter = data["sell_counter"]
                print(f"Load {self.state_file}: {data}")

        except Exception as ex:
            self.init_new_states()
            print(f"{ex.with_traceback(None)}")

    async def do_buy(self, qtty):
        counter = 0
        while counter < 20:
            counter += 1
            try:
                resp_data, resp_status = await self.client.market_order(
                    symbol=self.symbol, side="Buy", quantity_size=qtty
                )
                print(resp_data)
                if resp_status != 200:
                    print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
                    break
                if resp_data["retCode"] != 0:
                    await asyncio.sleep(2.0)
                    if self.ta.pair_balance[self.pair[0]] < 7.0:
                        break

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
                resp_data, resp_status = await self.client.market_order(
                    symbol=self.symbol, side="Sell", quantity_size=qtty
                )
                print(resp_data)
                if resp_status != 200:
                    print(f"ERROR: {resp_data} \n\n resp_status: {resp_status}")
                    break
                if resp_data["retCode"] != 0:
                    await asyncio.sleep(2.0)
                    if self.ta.pair_balance[self.pair[0]] < 7.0:
                        break
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
            print(
                f"Ma cross: SELL, low qtty:{qty * self.last_price}, minOrderQty: {self.minOrderQty}"
            )
            return False

        await self.do_sell(qty)
        return True

    async def sell_all(self):
        qty = self.ta.native_balance[0]
        if qty < self.minOrderQty:
            print(
                f"Ma cross: SELL, low qtty:{qty * self.last_price}, minOrderQty: {self.minOrderQty}"
            )
            return False

        await self.do_sell(qty)
        return True

    async def save_history_loop(self):
        while True:
            data_s1 = arr.array("d", self.ta.prices)
            header: arr.array = arr.array("L", [len(data_s1)])
            with open(self.data_file, "wb") as f:
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

        print("###################   Waiting for MA signal   ###################")

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
                if self.ta.trend_crossover.cross_over(
                    self.ta.ma_fast_m, self.ta.ma_trend
                ):
                    self.save_states()

                    # don't BUY while trend going down
                    if trend < 1.0:
                        continue

                    if abs(self.ta.percent_diff) < self.ta.rebalance_bottom:
                        continue

                    if self.ta.trade_profit < 0.0:
                        if abs(self.ta.price_diff) > self.ta.local_range:
                            if await self.buy_signal():
                                await asyncio.sleep(5.0)

                if self.ta.trend_crossunder.cross_under(
                    self.ta.ma_fast_m, self.ta.ma_trend
                ):
                    self.save_states()

                    # don't SELL while trend going up
                    if trend > -1.0:
                        continue

                    ### To do: add option to sell all at min ratio
                    # if self.ta.portfolio_ratio - 0.05 < self.ta.min_max_ratio[0]:
                    #     if await self.sell_all():
                    #         await asyncio.sleep(5.0)

                    if abs(self.ta.percent_diff) < self.ta.rebalance_top:
                        continue

                    if self.ta.trade_profit > 0.0:
                        if abs(self.ta.price_diff) > self.ta.local_range:
                            if await self.sell_signal():
                                await asyncio.sleep(5.0)

            except Exception as ex:
                print(f"ERROR: trade_loop, {ex}")
                print(f"{repr(traceback.extract_tb(ex.__traceback__))}")


if __name__ == "__main__":
    main_loop = asyncio.new_event_loop()

    tr = Trader(loop=main_loop, key=API_KEY, secret=SECRET_KEY)

    main_loop.run_until_complete(tr.init_data())
    main_loop.create_task(tr.ws_ticker())

    time.sleep(1.0)
    main_loop.create_task(tr.ws_user_data())
    main_loop.create_task(tr.account_balance_loop())
    main_loop.create_task(tr.save_history_loop())
    main_loop.run_until_complete(tr.trade_loop())
