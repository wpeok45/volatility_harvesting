# Volatility harvesting (floating percent)

![alt text](pnl.png)

Bybit API spot bot

# Installation
```
pip install -r requirements.txt
```
or 
```
python3 -m pip install -r requirements.txt
```
# Preparation
Change the .env file with your Bybit API and Telegram bot keys (Telegram is optional)

# Run
```
python3 vh_float.py
```
or
```
docker-compose build && docker-compose up -d
```
--------------
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

It's clear that with all these strategies, BTC "just sitting on the shelf", to use retail terminology.
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
