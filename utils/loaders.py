import os, os.path

import pandas as pd
from requests.auth import HTTPBasicAuth
from tqdm.auto import tqdm

import requests
import time
import datetime

from apikeys import key

def get_data(currency_pair, end=None, step=60, limit=1000):
    '''
   Get bitstamp historic data

   :param str currency_pair: Currency pair (ex btcusd)
   :param str end: Final date
   :param int step: Seconds step, 60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 259200
   :param int limit: How many steps
   '''
    if end:
        end = int(time.mktime(datetime.datetime.strptime(end, "%d/%m/%Y %H %M %S").timetuple()))
    else:
        end = int(datetime.datetime.now().timestamp())
    url = f"https://www.bitstamp.net/api/v2/ohlc/{currency_pair}/?step={step}&limit={limit}&end={end}"
    headers = {"Accept": "application/json"}
    auth = HTTPBasicAuth('apikey', key.apikey)

    return requests.get(url, headers=headers , auth=auth)

def check_availability(currency_pair):
    '''
   Return first and last available dates on dataset for currency_pair and dataset if available

   :param str currency_pair: Currency pair (ex btcusd)
   :raise ValueError: if currency_pair not in database
   '''
    path = f"bitstamp/{currency_pair}.pkl"
    if not os.path.isfile(path):
        raise ValueError("Currency pair not found in the database")
    df = pd.read_pickle(path)
    return df.index[0], df.index[-1], df

def populate_dataset(currency_pair, step=60, limit=1000, n_requests=100):
    '''
   Populate dataset for currency_pair

   :param str currency_pair: Currency pair (ex btcusd)
   :param int step: Seconds step, 60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400, 259200
   :param int limit: How many steps
   :param int n_requests: How many requests, max 8000 per 10 minutes
   '''
    if not os.path.isdir('bitstamp'):
        if os.path.isdir('../bitstamp'):
            os.chdir("..")
        else:
            raise FileNotFoundError("Can't find bitstamp folder, you are in the wrong folder.") 
    try:
        start, _, old_df = check_availability(currency_pair)
    except ValueError:
        print("Currency pair not found in the database, creating new dataset...")
        start = datetime.datetime.strptime("15/02/2021", "%d/%m/%Y")
        old_df = pd.DataFrame([])
    datas = [get_data(
        currency_pair=currency_pair,
        step=step, 
        limit=limit, 
        end=(start - datetime.timedelta(seconds=step*limit)*i).strftime("%d/%m/%Y %H %M %S")) 
            for i in tqdm(range(n_requests))]
    df = pd.concat([pd.DataFrame(data.json()["data"]["ohlc"]) for data in reversed(datas)]).astype(float)
    df.timestamp = df.timestamp.astype(int)
    df.index = pd.to_datetime(df.timestamp, unit='s')
    df_complete = pd.concat([df, old_df])
    df_complete.to_pickle(f"bitstamp/{currency_pair}.pkl")