import os
import sys
import json
import platform
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.process_data import process_data

def get_time_bounds(df):
    earliest = df.loc[df['time_only'].idxmin()]
    latest = df.loc[df['time_only'].idxmax()]
    return earliest, latest

def get_costs(df):
    # 使用IQR方法过滤异常值
    Q1, Q3 = df['txamt'].quantile([0.25, 0.75])
    IQR = Q3 - Q1
    bounds = (Q1 - 1.5 * IQR, Q3 + 1.5 * IQR)
    
    filtered_df = df[(df['txamt'] >= bounds[0]) & (df['txamt'] <= bounds[1])]
    avg_cost = filtered_df['txamt'].mean()
    total_cost = df['txamt'].sum()
    
    return avg_cost, total_cost

def get_top_locations(df):
    return df.groupby('meraddr').size().sort_values(ascending=False).head(3)

def get_top_counters(df):
    counter_counts = {}
    for mername_list in df['mername']:
        for counter in set(mername_list):
            counter_counts[counter] = counter_counts.get(counter, 0) + 1
    
    return pd.Series(counter_counts).sort_values(ascending=False)

def get_max_cost(df):
    return df.loc[df['txamt'].idxmax()]

def analyze_patterns(df):
    def get_meal_type(hour):
        if 5 <= hour < 10: return '早餐'
        elif 10 <= hour < 15: return '午餐'
        elif 15 <= hour < 21: return '晚餐'
        else: return '夜宵'
    
    # 添加月份和用餐类型
    df['month'] = df['txdate'].dt.month
    df['meal_type'] = df['txdate'].dt.hour.map(get_meal_type)
    
    # 计算每月统计数据
    monthly_stats = {}
    time_stds = []
    
    for month in df['month'].unique():
        month_df = df[df['month'] == month]
        time_secs = month_df['txdate'].dt.time.apply(
            lambda x: x.hour * 3600 + x.minute * 60 + x.second
        )
        time_std = time_secs.std()
        time_stds.append(time_std)
        
        monthly_stats[month] = {
            'meals': month_df['meal_type'].value_counts(),
            'std': time_std,
            'data': month_df
        }
    
    # 计算规律性得分
    scores = 100 * (1 - MinMaxScaler().fit_transform([[x] for x in time_stds]))
    for month, score in zip(monthly_stats.keys(), scores):
        monthly_stats[month]['score'] = score[0]
    
    # 生成可视化
    _plot_patterns(monthly_stats)
    
    return monthly_stats

def _plot_patterns(stats):
    # 设置字体
    font = ('Arial Unicode MS' if platform.system() == "Darwin" else
            'Droid Sans Fallback' if platform.system() == "Linux" else
            'SimHei')
    plt.rcParams['font.sans-serif'] = [font]
    plt.rcParams['axes.unicode_minus'] = False
    
    # 找出最规律和最不规律的月份
    months = sorted(stats.items(), key=lambda x: x[1]['score'])
    regular_month, irregular_month = months[-1], months[0]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    for ax, (month, data, color, label) in zip(
        [ax1, ax2],
        [(regular_month[0], regular_month[1], 'green', '最规律'),
         (irregular_month[0], irregular_month[1], 'red', '最不规律')]
    ):
        df = data['data']
        hours = df['txdate'].dt.hour + df['txdate'].dt.minute / 60
        ax.scatter(df['txdate'].dt.day, hours, color=color, alpha=0.6)
        ax.set_title(f'{label}的月份: {month}月\n(规律性: {data["score"]:.1f}/100)')
        ax.set_xlabel('日期')
        ax.set_ylabel('时间 (24小时制)')
        ax.set_yticks(range(0, 24, 2))
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def main():
    data = json.load(open("log.json", "r", encoding='utf-8'))
    df_raw, df = process_data(data)
    get_time_bounds(df)
    get_costs(df)
    get_top_locations(df)
    get_top_counters(df)
    get_max_cost(df)
    analyze_patterns(df)

if __name__ == "__main__":
    main()