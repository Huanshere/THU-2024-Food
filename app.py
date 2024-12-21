import json
import os
import streamlit as st
from dotenv import load_dotenv

from utils.analyze_data import (
    analyze_patterns,
    get_costs,
    get_max_cost,
    get_time_bounds,
    get_top_counters,
    get_top_locations,
)
from utils.get_eat_record import get_record
from utils.process_data import process_data
from utils.prompts import get_eat_habbit_prompt
from utils.ask_gpt import ask_gpt

st.set_page_config(
    page_title="清华食堂消费年度总结",
    page_icon="🍜",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Get TEST_MODE from environment variables
TEST_MODE = os.getenv('TEST_MODE', 'true').lower() == 'true'

# 添加自定义 CSS 样式
def load_css():
    with open('utils/styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def create_stat_card(title, value, location, date, comment, emoji=""):
    return f"""
        <div class='stat-card'>
            <div class='stat-label'>{title} {emoji}</div>
            <div class='stat-value'>{value}</div>
            <div class='stat-label'>地点: {location}</div>
            <div class='stat-label'>{'时间' if ':' in date else '日期'}: {date}</div>
            <div class='stat-label'>{comment}</div>
        </div>
    """

def main():
    load_css()
    st.title("🏫 清华食堂消费年度总结")
    
    # 更新欢迎页面文案
    st.markdown("""
    ### 👋 准备好开启你的美食冒险了吗？
    
    这是一个专门为清华吃货们打造的 2024 年度美食档案！让我们一起来揭秘你的饕餮传说～
    """)

    # 更新用户输入区域文案
    with st.form("user_input"):
        st.subheader("🔑 请出示你的美食探员证件")
        idserial = st.text_input("学号")
        servicehall = st.text_input("Cookie中的servicehall")
        submitted = st.form_submit_button("开启美食档案 🚀")

        if TEST_MODE:
            idserial = "2024012345"
            servicehall = "1234567890"
            submitted = True

        # After the form submission check
        if submitted:
            if not idserial or not servicehall:
                st.error("⚠️ 请填写完整信息！")
                return

            # First spinner for data fetching
            with st.spinner("正在获取数据，请稍候..."):
                try:
                    data = get_record(servicehall, idserial) if not TEST_MODE else json.load(open("log.json", "r", encoding='utf-8'))
                    df_raw, df = process_data(data)
                    username = df['username'].iloc[0]
                    st.success("✅ 数据获取成功")
                except Exception as e:
                    st.error(f"❌ 数据获取失败，请检查学号和Cookie是否正确")
                    return

    if submitted:
        # Create expander after successful data fetch
        with st.expander(f"📊 {username}的美食探险日记", expanded=True):
            # Second spinner for report generation
            with st.spinner("正在生成报告，请稍候..."):
                try:
                    # 1. 消费统计卡片
                    st.subheader("💰 年度资金报告")
                    col1, col2 = st.columns(2)
                    
                    avg_cost, total_cost = get_costs(df)
                    with col1:
                        cups = int(total_cost // 13)
                        st.markdown("""
                            <div class='stat-card card-blue'>
                                <div class='stat-label'>2024 一共吃了</div>
                                <div class='stat-value'>¥{total_cost:.2f}</div>
                                <div class='stat-label'>相当于 {cups} 杯生椰拿铁 🥥</div>
                            </div>
                        """.format(total_cost=total_cost, cups=cups), unsafe_allow_html=True)
                    
                    with col2:
                        cups = float(round(avg_cost / 13, 1))
                        st.markdown("""
                            <div class='stat-card card-green'>
                                <div class='stat-label'>平均每顿饭钱</div>
                                <div class='stat-value'>¥{avg_cost:.2f}</div>
                                <div class='stat-label'>相当于 {cups} 杯生椰拿铁 🥥</div>
                            </div>
                        """.format(avg_cost=avg_cost, cups=cups), unsafe_allow_html=True)

                    # 2. 最常光顾食堂展示
                    st.subheader("🏆 你的主力探店地")
                    top_3_canteens = get_top_locations(df)
                    cols = st.columns(3)  # 创建3列
                    
                    for idx, ((location, visits), col) in enumerate(zip(top_3_canteens.items(), cols), 1):
                        color_class = f"card-{'purple' if idx == 1 else 'orange' if idx == 2 else 'red'}"
                        with col:
                            st.markdown(f"""
                                <div class='stat-card {color_class}'>
                                    <div class='stat-label'>第 {idx} 名</div>
                                    <div class='stat-value'>{location}</div>
                                    <div class='stat-label'>一共吃了 {visits} 顿</div>
                                </div>
                            """, unsafe_allow_html=True)
                    st.markdown("", unsafe_allow_html=True)

                    # 3. 最喜爱的窗口
                    st.subheader("🎯 你的心头好")
                    counter_visits = get_top_counters(df)
                    top_5_counters = counter_visits.head()
                    cols = st.columns(5)
                    
                    for idx, ((counter, visits), col) in enumerate(zip(top_5_counters.items(), cols), 1):
                        with col:
                            st.markdown(f"""
                                <div class='stat-card'>
                                    <div class='stat-label'>第 {idx} 名</div>
                                    <div class='stat-value'>{counter.replace('园_', '')}</div>
                                    <div class='stat-label'>吃了 {visits} 次</div>
                                </div>
                            """, unsafe_allow_html=True)
                    st.markdown("", unsafe_allow_html=True)

                    # 4. 最逆天的记录
                    st.subheader("🌟 探险里程碑")
                    earliest, latest = get_time_bounds(df)
                    most_expensive = get_max_cost(df)
                    
                    earliest_prompt = get_eat_habbit_prompt(username, earliest)
                    latest_prompt = get_eat_habbit_prompt(username, latest)
                    most_expensive_prompt = get_eat_habbit_prompt(username, most_expensive)
                    
                    earliest_comment = ask_gpt(earliest_prompt)
                    latest_comment = ask_gpt(latest_prompt)
                    most_expensive_comment = ask_gpt(most_expensive_prompt)

                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(
                            create_stat_card(
                                "清晨觅食冠军", 
                                earliest['txdate'].strftime('%H:%M'),
                                earliest['meraddr'],
                                earliest['txdate'].strftime('%Y-%m-%d'),
                                earliest_comment,
                                "☀️"
                            ),
                            unsafe_allow_html=True
                        )
                    
                    with col2:
                        st.markdown(
                            create_stat_card(
                                "夜宵王者",
                                latest['txdate'].strftime('%H:%M'),
                                latest['meraddr'],
                                latest['txdate'].strftime('%Y-%m-%d'),
                                latest_comment,
                                "🌙"
                            ),
                            unsafe_allow_html=True
                        )

                    with col3:
                        st.markdown(
                            create_stat_card(
                                "土豪餐王",
                                f"¥{most_expensive['txamt']:.2f}",
                                most_expensive['meraddr'],
                                most_expensive['txdate'].strftime('%Y-%m-%d %H:%M'),
                                most_expensive_comment,
                                "💫"
                            ),
                            unsafe_allow_html=True
                        )
                    st.markdown("", unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ 生成报告时出现错误: {str(e)}")
                    return

if __name__ == "__main__":
    main()