import numpy as np
import pandas as pd

def macd(prices: pd.Series, long: int, short: int, strategy=False, getgains=False, winning=False, commissions=0.005) -> pd.Series:
    '''
    Return the MACD

    :param pd.Series prices: Prices of the stock
    :param int long: Long moving average length
    :param int short: Short moving average length
    :param bool strategy: If strategy should be returned
    :param bool getgains: If gains should be returned
    :param bool winning: If policy gain - no strategy gain should be returned
    :param float commissions: Percentage commissions per transaction
    '''
    if prices.index.duplicated().any():
        raise ValueError("There are some duplicate indexes.")
    macdvalues = prices.rolling(short).mean() - prices.rolling(long).mean()
    if winning:
        positive = macdvalues > 0
        policy = positive.shift(1) != positive
        if positive.iloc[0]:
            policy.iloc[0] = 1
        gain = gains(prices=prices, policy=policy, commissions=commissions)
        diff = (prices.iloc[-1]/prices.iloc[0]) - 1
        return gain.sum() - diff * 100
    if strategy:
        positive = macdvalues > 0
        return positive.shift(1) != positive
    if getgains:
        positive = macdvalues > 0
        policy = positive.shift(1) != positive
        if positive.iloc[0]:
            policy.iloc[0] = 1
        return gains(prices=prices, policy=policy, commissions=commissions)
    return macdvalues
    
def ultimate(prices: pd.Series, low: pd.Series, high: pd.Series, days=7, strategy=False, getgains=False, winning=False, commissions=0.005) -> pd.Series:
    '''
    Return the Ultimate oscillator

    :param pd.Series prices: Prices of the stock
    :param pd.Series low: Long moving average length
    :param pd.Series high: Short moving average length
    :param int days: Days for moving sum
    :param bool strategy: If strategy should be returned
    :param bool getgains: If gains should be returned
    :param bool winning: If policy gain - no strategy gain should be returned
    :param float commissions: Percentage commissions per transaction
    '''
    if prices.index.duplicated().any():
        raise ValueError("There are some duplicate indexes.")
    bp = prices - np.minimum(prices.shift(1), low)
    tr = np.maximum(high, prices.shift(1)) - np.minimum(prices.shift(1), low)
    avg1 = bp.rolling(days).sum()/tr.rolling(days).sum()
    avg2 = bp.rolling(2*days).sum()/tr.rolling(2*days).sum()
    avg3 = bp.rolling(3*days).sum()/tr.rolling(3*days).sum()
    ult = 100 * (4*avg1 + 2*avg2 + avg3)/7
    ult = ult.dropna()
    if winning or strategy or getgains:
        buy = ult > 70
        buys = buy.shift(1) != buy
        sell = ult < 30
        sells = sell.shift(1) != sell
        policy = pd.Series(np.zeros(ult.size), index=ult.index)
        token = 1
        for idx in buys[buys | sells].index:
            if token and buys.loc[idx].all():
                policy.loc[idx] = 1
                token = 0
            elif not token and sells.loc[idx].all():
                policy.loc[idx] = 1
                token = 1
        policy = policy == 1
    else:
        return ult
    if winning:
        gain = gains(prices=prices, policy=policy, commissions=commissions)
        diff = (prices.iloc[-1]/prices.iloc[0]) - 1
        return gain.sum() - diff * 100
    if strategy:
        return policy
    if getgains:
        return gains(prices=prices, policy=policy, commissions=commissions)

def gains(prices: pd.Series, policy: pd.Series, budget=100, commissions=0.005) -> pd.Series:
    '''
    Return the gains

    :param pd.Series prices: Prices of the stock
    :param pd.Series policy: True when buy or sell
    :param float budget: My budget
    :param float commissions: Percentage commissions per transaction
    '''
    prices = prices.loc[policy.index]
    gains = (prices[policy].shift(-1)/prices[policy]) - 1
    return (gains - commissions*2)*budget
