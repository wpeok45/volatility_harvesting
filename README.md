# Volatility Harvesting (Floating Percent)

![alt text](pnl.png)

A Bybit API spot trading bot implementing volatility harvesting strategy with dynamic portfolio rebalancing.

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Or using Python 3 explicitly:

```bash
python3 -m pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env_example .env
   ```

2. Edit `.env` file and configure the following parameters:
   - `API_KEY` - Your Bybit API Key ([Get it here](https://www.bybit.com/app/user/api-management))
   - `SECRET_KEY` - Your Bybit API Secret
   - `STABLE_PAIR` - Stablecoin to use (default: USDT)
   - `MA_LENGTH` - Moving Average period for trading signals (default: 24 minutes)
   - `RANGE` - Price range for portfolio ratio calculation (default: 50000 pips)
   - `MIN_RATIO` - Minimum crypto allocation (default: 0.01 = 1%)
   - `MAX_RATIO` - Maximum crypto allocation (default: 0.99 = 99%)
   - `REBALANCE_TOP` - Sell trigger percentage (default: 3.0%)
   - `REBALANCE_BOTTOM` - Buy trigger percentage (default: 3.0%)
   - `REBALANCE_ISDYNAMIC` - Enable Fibonacci scaling (default: true)
   - `AMPLITUDE_TIME_FRAME` - Time window for amplitude calculation (in seconds)
   - `FEE` - Trading fee percentage (default: 0.1%)
   - `TGBOT_TOKEN` - Telegram bot token for notifications (optional)
   - `TGBOT_CHATID` - Telegram chat ID for notifications (optional)

3. Ensure you have sufficient balance in your Bybit spot account

## Running the Bot

### Using Python directly:

```bash
python3 vh_float3.py
```

### Using Docker:

Build and run the container in detached mode:

```bash
docker compose build
docker compose up -d
```

View logs:

```bash
docker compose logs -f
```

Stop the bot:

```bash
docker compose down
```

## Monitoring

- Console output shows real-time trading activity
- `trading.log` file contains detailed trading history (automatically rotated at 10MB, keeps 5 backups)
- Telegram notifications (if configured) provide trade alerts

--------------

## Strategy Overview

Volatility harvesting is actually not a complicated strategy, but it requires a re-evaluation of the way we view price movements in the market.

It is based on two conditions:
1. The probability of the price moving up or down over n time is always equal to a "coin toss," or 50/50.
    - We deliberately ignore all other conditions, considering them external (such as political events, news, etc.)
    - The market volume of BTC and the number of participants is so huge that any external influence will inevitably be balanced out.
2. Extreme price fluctuations (for example $60k, $16k, $100k) occur within a reasonable time frame.
    - This means periods of decline and rise do not last for decades.

Bitcoin fits these conditions well. Next, let's look at the strategies included in Volatility harvesting.
### HODL
What if we bought BTC with $1 for every price point from $10k to $60k as it rises?
We would pay $50,000 at an average price of $35k and would be in good profit. This is a standard HODL strategy.
As the price drops to $16k, the portfolio will suffer losses.
### DCA
What if we make a small adjustment to HODL and sell each purchased BTC ($1) if its price increases by a certain percent?
This would be a standard DCA (Dollar Cost Averaging) strategy.
### VA
Now, let's try buying more than BTC ($1) and selling less than BTC ($1) as the price decreases, and vice versa — buying less and selling more as the price increases. This will be similar to the DVA or VA strategy.

It should be noted that DCA and DVA are considered investment strategies. Simply put, it is a way to enter the market by accumulating BTC in the portfolio at specific periods or price change ranges (for example, "by grid").
### Volatility harvesting
We just make sure the portfolio is always 50% / 50%.
We rebalance when the ratio in the portfolio changes. For example, if the asset price increases and the ratio becomes 60% / 40%, we sell the asset by 10%, thereby restoring the balance to 50% / 50%.

It's clear that with all these strategies, BTC is just sitting on the shelf, to use retail terminology.
Our goal is to sell everything we bought, with profit and as quickly and efficiently as possible, as in swing trading.
We will not consider strategies that rely on the "survivorship bias," such as trend-based ones.
But ideally, everything should work "by itself," without tedious technical analysis and news reading.
We need a universal formula that fully complies with mathematical probabilities.

 ### Portfolio balancing formula with zero risk:
```
if BTC price = $0.01 then portfolio balance ratio = 100% (BTC) / 0% (USDT)
if BTC price = ATH then portfolio balance ratio = 0% (BTC) / 100% (USDT)
```
If you want to take more risk for higher profits, you can limit the range by half:
```
if BTC price = ATH/2 $ then portfolio balance ratio = 100% (BTC) / 0% (USDT)
if BTC price = ATH then portfolio balance ratio = 0% (BTC) / 100% (USDT)
```

### Volatility harvesting with floating ratio
```
Initial portfolio state: BTC = 0.0, STABLE_PAIR = 1000.0 USD
TOTAL_AMOUNT = 1000 USD
BTC price = ATH (100000 USD)
RATIO = 0.0
RANGE = 100000

Value of each price pip:
    TOTAL_AMOUNT / RANGE = 0.01 USD
    If the price drops by 1000 pips, we buy 1000 * ~0.01 = 10 USD

RATIO_PER_PIP = 1.0 / RANGE = 0.00001
Each tick will change the portfolio ratio as RATIO +(-) RATIO_PER_PIP
Suppose the price dropped by 500 pips:
RATIO += 500 * 0.00001 = 0.005
Now the portfolio balance will be BTC = 0.5%, STABLE_PAIR = 99.5%
```
At ATH we have 0% / 100%, and as the price falls, the left percentage increases and the right decreases.

When to rebalance the portfolio:
- Sell BTC when the percent changes by at least 2% (if fee = 0.1)
- Sell or buy on price reversals, for example, when EMA24 and MA24 cross
- To avoid false reversals, check the local price range, e.g., for 2 hours



It is hard to imagine a formula more universal than this.
It seems that effective traders and large funds follow it in the vast majority of cases.
Even intraday traders on short ranges most likely intuitively adhere to this formula.

This is not financial advice. Use at your own risk.
