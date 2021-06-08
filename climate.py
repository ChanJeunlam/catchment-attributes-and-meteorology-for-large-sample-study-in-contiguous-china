from itertools import groupby
import pandas as pd
import numpy as np
from tqdm import tqdm
from utils import absolute_file_paths
import datetime


def split_a_list_at_zeros(L):
    return [list(g) for k, g in groupby(L, key=lambda x: x != 0) if k]


def p_mean(data: str):
    return float(data.mean())


def high_prec_freq(data: str):
    num_high_pre_days = len(data[data > data.mean() * 5].dropna())
    return num_high_pre_days / len(data) * 365


def high_prec_dur(data: str):
    data = np.array(data)
    tmp_data = data.copy()
    tmp_data[tmp_data < data.mean() * 5] = 0
    tmp = [len(x) for x in split_a_list_at_zeros(tmp_data)]
    if len(tmp) > 0:
        return np.mean(tmp)
    else:
        return None


def high_prec_timing(data: str):
    months = [x.month for x in data[data > data.mean() * 5].dropna().index]
    seasons = [month2season(x) for x in months]
    seasons, counts = np.unique(seasons, return_counts=True)
    if len(counts) > 0:
        return [x for _, x in sorted(zip(counts, seasons))][-1]
    else:
        return None


def month2season(month):
    """DJF=Dec-Feb, MAM=Mar-May,. JJA=Jun-Aug, SON=Sep-Nov"""
    if month in [3, 4, 5]:
        return 'mam'
    elif month in [6, 7, 8]:
        return 'jja'
    elif month in [9, 10, 11]:
        return 'son'
    elif month in [12, 1, 2]:
        return 'djf'


def low_prec_freq(data: str):
    num_low_pre_days = len(data[data < 1].dropna())
    return num_low_pre_days / len(data) * 365


def low_prec_dur(data: str):
    data = np.array(data)
    tmp_data = data.copy()
    tmp_data[data < 1] = 1  # 降雨小于 1mm 的日子标记为 1
    tmp_data[data > 1] = 0  # 降雨大于 1mm 的日子 标记为 0
    tmp = [len(x) for x in split_a_list_at_zeros(tmp_data)]
    if len(tmp) > 0:
        return np.mean(tmp)  # 在 0 处分开，得到 1的序列
    else:
        return None


def low_prec_timing(data: str):
    months = [x.month for x in data[data < 1].dropna().index]
    seasons = [month2season(x) for x in months]
    seasons, counts = np.unique(seasons, return_counts=True)
    return [x for _, x in sorted(zip(counts, seasons))][-1]


def frac_snow_daily(df):
    return len(df.loc[df['平均气温'] < 0].loc[df['20-20时累计降水量'] > 0]) / len(df)


def p_seasonality(pre: np.array, tem: np.array):
    ''' seasonality and timing of precipitation, positive [negative] values indicate
    that precipitation peaks in summer [winter]

    Parameters
    ----------
    pre 逐日降雨数据
    tem 逐日温度数据

    Returns
    -------
    float
        p_seasonality
    '''

    res = []
    for year in range(2009, 2019):
        tmp_pre = pre.loc[datetime.datetime(year, 5, 1):datetime.datetime(year + 1, 5, 1)]
        sp = np.argmax(tmp_pre)
        tmp_tem = tem.loc[datetime.datetime(year, 5, 1):datetime.datetime(year + 1, 5, 1)]
        st = np.argmax(tmp_tem)
        res.append(np.cos(2 * np.pi / 365 * (sp - st)))
    return np.mean(res)


if __name__ == '__main__':

    forcing_dir = './forcing_time_series'
    output_dir = './output'

    files = [x for x in absolute_file_paths(forcing_dir) if 'forcing.xlsx' in x][:10]

    res = {}
    for file in tqdm(files):
        name = file.split('\\')[-2]
        df = pd.read_excel(file).rename(columns={'Unnamed: 0': 'date'}).set_index('date')
        df = df.loc[datetime.datetime(2000, 1, 1):datetime.datetime(2019, 12, 31)]
        pre = df[['20-20时累计降水量']]
        tem = df[['平均气温']]

        res[name] = {'p_mean': p_mean(pre), 'high_prec_freq': high_prec_freq(pre),
                     'high_prec_dur': high_prec_dur(pre), 'high_prec_timing': high_prec_timing(pre),
                     'low_prec_freq': low_prec_freq(pre), 'low_prec_dur': low_prec_dur(pre),
                     'low_prec_timing': low_prec_timing(pre), 'frac_snow_daily': frac_snow_daily(df),
                     'p_seasonality': p_seasonality(pre, tem)}
    pd.DataFrame(res).T.to_excel(f'{output_dir}/climate.xlsx')
