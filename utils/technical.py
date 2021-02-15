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
    macdvalues = prices.rolling(short).mean() - prices.rolling(long).mean()
    if winning:
        positive = macdvalues > 0
        policy = positive.shift(1) != positive
        gain = gains(prices=prices, policy=policy, commissions=commissions)
        diff = (prices.iloc[-1]/prices.iloc[0]) - 1
        return gain.sum() - diff * 100
    if strategy:
        positive = macdvalues > 0
        return positive.shift(1) != positive
    if getgains:
        positive = macdvalues > 0
        policy = positive.shift(1) != positive
        return gains(prices=prices, policy=policy, commissions=commissions)
    return macdvalues
    

def gains(prices: pd.Series, policy: pd.Series, budget=100, commissions=0.005) -> pd.Series:
    '''
    Return the gains

    :param pd.Series prices: Prices of the stock
    :param pd.Series policy: True when buy or sell
    :param float budget: My budget
    :param float commissions: Percentage commissions per transaction
    '''
    gains = (prices[policy].shift(-1)/prices[policy]) - 1
    return (gains - commissions*2)*budget
