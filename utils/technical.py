import numpy as np
import pandas as pd
from tqdm.auto import tqdm

from utils import ultimate_cycle

# OSCILLATORS

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
    
def ultimate(prices: pd.Series, low: pd.Series, high: pd.Series, buylevel=30, selllevel=70, days=7, strategy=False, getgains=False, winning=False, commissions=0.005, accelerate=True) -> pd.Series:
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
    :param bool accelerate: If uses cython
    '''
    if prices.index.duplicated().any():
        raise ValueError("There are some duplicate indexes.")
    bp = prices - np.minimum(prices.shift(1), low)
    tr = np.maximum(high, prices.shift(1)) - np.minimum(prices.shift(1), low)
    avg1 = bp.rolling(days).sum()/tr.rolling(days).sum()
    avg2 = bp.rolling(2*days).sum()/tr.rolling(2*days).sum()
    avg3 = bp.rolling(3*days).sum()/tr.rolling(3*days).sum()
    ult = 100 * (4*avg1 + 2*avg2 + avg3)/7
    if winning or strategy or getgains:
        buy = ult < buylevel
        sell = ult > selllevel
        policy = getpolicy(buy=buy, sell=sell, accelerate=accelerate)
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

def bollinger_bands(prices: pd.Series, k=1, period=1000, strategy=False, getgains=False, winning=False, commissions=0.005, accelerate=True) -> pd.Series:
    '''
    Return the Bollinger bands

    :param pd.Series prices: Prices of the stock
    :param int k: How many standard deviations out
    :param int period: Period for moving average 
    :param bool strategy: If strategy should be returned
    :param bool getgains: If gains should be returned
    :param bool winning: If policy gain - no strategy gain should be returned
    :param float commissions: Percentage commissions per transaction
    :param bool accelerate: If uses cython
    '''
    std = prices.rolling(period).std()
    mean = prices.rolling(period).mean()
    upperband = mean + std*k
    lowerband = mean - std*k
    if strategy or getgains or winning:
        sell = prices > upperband
        buy = prices < lowerband
        policy = getpolicy(buy=buy, sell=sell, accelerate=accelerate)
    if winning:
        gain = gains(prices=prices, policy=policy, commissions=commissions)
        diff = (prices.iloc[-1]/prices.iloc[0]) - 1
        return gain.sum() - diff * 100
    if strategy:
        return policy
    if getgains:
        return gains(prices=prices, policy=policy, commissions=commissions)
    return lowerband, upperband

# UTILS

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

def getpolicy(buy: pd.Series, sell: pd.Series, accelerate=True) -> pd.Series:
    """
    Return the policy given all the moments sell or buy is True

    :param pd.Series buy: When the buy pricinple is respected
    :param pd.Series sell: When the sell pricinple is respected
    :param bool accelerate: If use cython
    """
    buys = buy.shift(1) != buy
    sells = sell.shift(1) != sell
    policy = pd.Series(np.zeros(buy.size), index=buy.index)
    if accelerate:
        index = buys[buys | sells].reset_index(drop=True).index.to_numpy()
        policy_ = ultimate_cycle.ultimate_cycle(policy.to_numpy(), buys.to_numpy(), sells.to_numpy(), index)
        policy = pd.Series(policy_, index=policy.index)
    else:
        token = 1
        for idx in tqdm(buys[buys | sells].index):
            if token and buys.loc[idx]:
                policy.loc[idx] = 1
                token = 0
            elif not token and sells.loc[idx]:
                policy.loc[idx] = 1
                token = 1
    return policy == 1