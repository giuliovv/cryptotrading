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
    
def ultimate(prices: pd.Series, low: pd.Series, high: pd.Series, buylevel=30, selllevel=70, days=7, strategy=False, getgains=False, winning=False, commissions=0.005, mingain=0, accelerate=True, firstopportunity=False, stoploss=0) -> pd.Series:
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
    :param float mingain: Minimum gain to sell
    :param bool firstopportunity: If sell first time you have mingain
    :param float stoploss: Maximum percentage loss
    '''
    if prices.index.duplicated().any():
        raise ValueError("There are some duplicate indexes.")
    bp = prices - np.minimum(prices.shift(1), low)
    tr = np.maximum(high, prices.shift(1)) - np.minimum(prices.shift(1), low)
    avg1 = bp.rolling(days).sum()/tr.rolling(days).sum()
    avg2 = bp.rolling(2*days).sum()/tr.rolling(2*days).sum()
    avg3 = bp.rolling(3*days).sum()/tr.rolling(3*days).sum()
    ult = 100 * (4*avg1 + 2*avg2 + avg3)/7
    if mingain == 0 and not firstopportunity and stoploss == 0:
        prices = prices.loc[~ult.isna()]
        ult = ult.dropna()
    if winning or strategy or getgains:
        buy = ult < buylevel
        sell = ult > selllevel
        policy = getpolicy(buy=buy, sell=sell, prices=prices, mingain=mingain, stoploss=stoploss, accelerate=accelerate, firstopportunity=firstopportunity)
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

def bollinger_bands(prices: pd.Series, k=1, period=1000, strategy=False, getgains=False, winning=False, commissions=0.005, accelerate=True, mingain=0, firstopportunity=False, stoploss=0) -> (pd.Series, pd.Series):
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
    :param float mingain: Minimum gain to sell
    :param bool firstopportunity: If sell first time you have mingain
    :param float stoploss: Maximum percentage loss
    '''
    std = prices.rolling(period).std()
    mean = prices.rolling(period).mean()
    upperband = mean + std*k
    lowerband = mean - std*k
    if strategy or getgains or winning:
        sell = prices > upperband
        buy = prices < lowerband
        policy = getpolicy(buy=buy, sell=sell, prices=prices, mingain=mingain, stoploss=stoploss, accelerate=accelerate, firstopportunity=firstopportunity)
    if winning:
        gain = gains(prices=prices, policy=policy, commissions=commissions)
        diff = (prices.iloc[-1]/prices.iloc[0]) - 1
        return gain.sum() - diff * 100
    if strategy:
        return policy
    if getgains:
        return gains(prices=prices, policy=policy, commissions=commissions)
    return lowerband, upperband

def williams(prices: pd.Series, low: pd.Series, high: pd.Series, buylevel=-80, selllevel=-20, days=10, strategy=False, getgains=False, winning=False, commissions=0.005, mingain=0, accelerate=True, firstopportunity=False, stoploss=0) -> pd.Series:
    '''
    Return the Williams %R oscillator

    :param pd.Series prices: Prices of the stock
    :param pd.Series low: Long moving average length
    :param pd.Series high: Short moving average length
    :param int days: Days for moving sum
    :param bool strategy: If strategy should be returned
    :param bool getgains: If gains should be returned
    :param bool winning: If policy gain - no strategy gain should be returned
    :param float commissions: Percentage commissions per transaction
    :param bool accelerate: If uses cython
    :param float mingain: Minimum gain to sell
    :param bool firstopportunity: If sell first time you have mingain
    :param float stoploss: Maximum percentage loss
    '''
    if prices.index.duplicated().any():
        raise ValueError("There are some duplicate indexes.")
    high_N = high.rolling(days).max()
    low_N = low.rolling(days).min()
    R = -100*(high_N - prices)/(high_N - low_N)
    if winning or strategy or getgains:
        buy = R > buylevel
        sell = R < selllevel
        policy = getpolicy(buy=buy, sell=sell, prices=prices, mingain=mingain, stoploss=stoploss, accelerate=accelerate, firstopportunity=firstopportunity)
    else:
        return R
    if winning:
        gain = gains(prices=prices, policy=policy, commissions=commissions)
        diff = (prices.iloc[-1]/prices.iloc[0]) - 1
        return gain.sum() - diff * 100
    if strategy:
        return policy
    if getgains:
        return gains(prices=prices, policy=policy, commissions=commissions)

def momentum(prices: pd.Series, period=10, strategy=False, getgains=False, winning=False, commissions=0.005) -> pd.Series:
    '''
    Return the Momentum

    :param pd.Series prices: Prices of the stock
    :param int period: Days for moving average
    :param bool strategy: If strategy should be returned
    :param bool getgains: If gains should be returned
    :param bool winning: If policy gain - no strategy gain should be returned
    :param float commissions: Percentage commissions per transaction
    '''
    if prices.index.duplicated().any():
        raise ValueError("There are some duplicate indexes.")
    momentum = prices.rolling(period).mean().pct_change()
    if winning or strategy or getgains:
        buy = momentum > 0
        sell = momentum < 0
        buy_ = buy.shift(1) != buy
        sell_ = sell.shift(1) != sell
        sell_.loc[:buy_[buy_].iloc[0].index] = 0
        policy = buy_ | sell_
    else:
        return momentum
    if winning:
        gain = gains(prices=prices, policy=policy, commissions=commissions)
        diff = (prices.iloc[-1]/prices.iloc[0]) - 1
        return gain.sum() - diff * 100
    if strategy:
        return policy
    if getgains:
        return gains(prices=prices, policy=policy, commissions=commissions)

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
    buy = prices[policy].iloc[::2]
    sell = prices[policy].iloc[1::2]
    buy = buy.iloc[:sell.size].values
    gains = (sell/buy) - 1
    return (gains - commissions*2)*budget

def getpolicy(buy: pd.Series, sell: pd.Series, prices: pd.Series, mingain=0, stoploss=0, accelerate=True, firstopportunity=False) -> pd.Series:
    """
    Return the policy given all the moments sell or buy is True

    :param pd.Series buy: When the buy pricinple is respected
    :param pd.Series sell: When the sell pricinple is respected
    :param float mingain: Minimum gain to sell
    :param float stoploss: Maximum percentage loss
    :param bool accelerate: If use cython
    :param bool firstopportunity: If sell first time you have mingain, MUST USE ACCELERATE
    """
    if firstopportunity and not accelerate:
        print("Changing accelerate to True to use firstopportunity.")
        accelerate = True
    buys = buy.shift(1) != buy
    sells = sell.shift(1) != sell
    policy = pd.Series(np.zeros(buy.size), index=buy.index)
    if accelerate:
        buys.reset_index(drop=True, inplace=True)
        sells.reset_index(drop=True, inplace=True)
        index = buys[buys | sells].index.to_numpy()
        if mingain == 0 and stoploss == 0:
            policy_ = ultimate_cycle.ultimate_cycle(policy.to_numpy(), buys.to_numpy(), sells.to_numpy(), index)
        elif not firstopportunity and stoploss == 0:
            policy_ = ultimate_cycle.cycle_checkgain(policy.to_numpy(), buys.to_numpy(), sells.to_numpy(), index, prices.to_numpy(), mingain)
        else:
            policy_ = ultimate_cycle.cycle_absolutegain(policy.to_numpy(dtype=bool), buys.to_numpy(dtype=bool), buys[buys].index.to_numpy(dtype=np.int32), prices.to_numpy(dtype=np.float32), mingain, stoploss)
        policy = pd.Series(policy_, index=policy.index)
    else:
        token = 1
        buy_price = 0
        for idx in tqdm(buys[buys | sells].index):
            if token and buys.loc[idx]:
                policy.loc[idx] = 1
                token = 0
                buy_price = prices.loc[idx]
            elif not token and sells.loc[idx] and mingain*(prices.loc[idx]/buy_price) >= mingain*(1 + mingain):
                policy.loc[idx] = 1
                token = 1
    return policy == 1