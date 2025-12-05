import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime, date
import cloudinary
import cloudinary.uploader
import plotly.graph_objects as go
import db

# --- 1. 画面構成設定 ---
st.set_page_config(page_title="選手用入力アプリ", layout="centered")

# --- Cloudinary設定 ---
# cloudinary.config(...) 

# --- 2. 関数群 ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def normalize_to_float(text):
    if not text:
        return 0.0
    try:
        normalized = unicodedata.normalize('NFKC', str(text))
        return float(normalized)
    except ValueError:
        return 0.0

# CSS適用
local_css("style.css")

st.title("🏃‍♂️ コンディション記録")

# --- 3. セッション管理 ---
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'meal_count' not in st.session_state:
    st.session_state.meal_count = 1
if 'exercise_count' not in st.session_state:
    st.session_state.exercise_count = 1
if 'bowel_count' not in st.session_state:
    st.session_state.bowel_count = 1

def add_meal(): st.session_state.meal_count += 1
def add_exercise(): st.session_state.exercise_count += 1
def add_bowel(): st.session_state.bowel_count += 1

# ==========================================
# A. ログイン画面
# ==========================================
if st.session_state.current_user is None:
    st.subheader("👤 選手ログイン")
    name_input = st.text_input("名前を入力してください", placeholder="例：田中 太郎")
    
    if name_input:
        st.info(f"「 **{name_input}** 」さんでよろしいですか？")
        if st.button("はい、この名前で開始します"):
            st.session_state.current_user = name_input
            st.rerun()

# ==========================================
# B. メイン画面
# ==========================================
else:
    user_name = st.session_state.current_user
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"お疲れ様です、**{user_name}** さん")
    with col2:
        if st.button("ログアウト"):
            st.session_state.current_user = None
            st.session_state.meal_count = 1
            st.session_state.exercise_count = 1
            st.session_state.bowel_count = 1
            st.rerun()

    # スプレッドシートからユーザー一覧を取得
    users_df = db.load_data_from_sheet('users')
    
    # --- B-1. 初回登録 ---
    is_registered = False
    if not users_df.empty:
        if user_name in users_df['name'].values:
            is_registered = True

    if not is_registered:
        st.warning("初回登録が必要です。")
        with st.form("reg_form"):
            dob = st.date_input("生年月日", min_value=date(1990, 1, 1))
            height_str = st.text_input("身長 (cm)", placeholder="例: 175.5")
            
            if st.form_submit_button("登録して開始"):
                height_val = normalize_to_float(height_str)
                if height_val > 0:
                    new_user_data = {
                        'name': user_name,
                        'dob': str(dob),
                        'height': height_val
                    }
                    db.append_data_to_sheet('users', new_user_data)
                    st.rerun()
                else:
                    st.error("身長を正しく入力してください")

    # --- B-2. 日々の入力 ---
    else:
        tab_input, tab_review = st.tabs(["📝 今日の入力", "📊 自分の記録"])
        
        with tab_input:
            input_date = st.date_input("日付", date.today())
            str_date = str(input_date)
            
            st.write("---")
            st.subheader("📊 体調入力")
            
            c1, c2 = st.columns(2)
            with c1:
                weight_str = st.text_input("体重 (kg)", placeholder="例: 65.5", key="weight_input")
            with c2:
                fat_str = st.text_input("体脂肪率 (%)", placeholder="例: 12.3", key="fat_input")
            
            sleep_options = [x * 0.5 for x in range(0, 49)]
            sleep = st.selectbox("睡眠時間 (h)", sleep_options, index=14, key="sleep_input")

            # --- 排便記録 ---
            st.write("---")
            st.subheader("🚻 排便記録")
            had_bowel = st.radio("今日は排便がありましたか？", ["あり", "なし"], horizontal=True, index=1, key="had_bowel_check")
            
            bowel_data_list = []
            if had_bowel == "あり":
                st.caption("回数分だけ追加できます")
                for i in range(st.session_state.bowel_count):
                    st.markdown(f"**排便 {i+1}**")
                    bc1, bc2, bc3 = st.columns(3)
                    with bc1:
                        b_time = st.time_input("時間", value=datetime.now().time(), key=f"bowel_time_{i}")
                    with bc2:
                        b_amount = st.selectbox("量", ["普通", "少ない", "多い"], key=f"bowel_amount_{i}")
                    with bc3:
                        b_hardness = st.selectbox("硬さ", ["普通", "柔らかい", "下痢", "硬い"], key=f"bowel_hardness_{i}")
                    
                    bowel_data_list.append({'time': str(b_time), 'amount': b_amount, 'hardness': b_hardness})
                st.button("＋ 排便枠を追加", on_click=add_bowel)

            # --- 運動記録 ---
            st.write("---")
            st.subheader("🏃‍♂️ 運動記録")
            exercise_data_list = []
            exercise_time_options = [f"{x}分" for x in range(0, 190, 10)]

            for i in range(st.session_state.exercise_count):
                st.markdown(f"**運動 {i+1}**")
                ec1, ec2 = st.columns([1, 2])
                with ec1:
                    ex_time = st.selectbox("時間", exercise_time_options, index=3, key=f"ex_time_{i}") 
                with ec2:
                    ex_content = st.text_input("運動内容", placeholder="例：ジョグ、ベンチプレスなど", key=f"ex_content_{i}")
                
                if ex_content:
                    exercise_data_list.append({'time': ex_time, 'content': ex_content})
            st.button("＋ 運動枠を追加", on_click=add_exercise)

            # --- 食事記録 ---
            st.write("---")
            st.subheader("🍽️ 食事記録")
            meal_data_list = []
            for i in range(st.session_state.meal_count):
                st.markdown(f"**食事 {i+1}**")
                mc1, mc2 = st.columns([1, 1])
                with mc1:
                    m_type = st.selectbox("種類", ["朝食", "昼食", "夕食", "間食"], key=f"meal_type_{i}")
                with mc2:
                    m_time = st.time_input("時間", value=datetime.now().time(), key=f"meal_time_{i}")
                m_img = st.file_uploader("写真", type=['png', 'jpg'], key=f"meal_img_{i}")
                m_menu = st.text_area("メニュー", height=68, key=f"meal_menu_{i}")
                
                meal_data_list.append({'type': m_type, 'time': str(m_time), 'menu': m_menu, 'image_file': m_img})
                st.divider()
            st.button("＋ 食事枠を追加", on_click=add_meal)

            # --- 保存ボタン ---
            if st.button("✅ 今日の記録をすべて保存する", type="primary", use_container_width=True):
                weight_val = normalize_to_float(weight_str)
                fat_val = normalize_to_float(fat_str)
                
                if weight_val > 0:
                    # 【修正箇所】メッセージをシンプルに変更
                    with st.spinner("保存中..."):
                        # 1. コンディション保存 (上書きロジック)
                        daily_df = db.load_data_from_sheet('daily')
                        if not daily_df.empty:
                            daily_df = daily_df[~((daily_df['name'] == user_name) & (daily_df['date'] == str_date))]
                        
                        new_row = pd.DataFrame([{
                            'name': user_name, 'date': str_date, 
                            'weight': weight_val, 'body_fat': fat_val, 'sleep': sleep
                        }])
                        updated_daily_df = pd.concat([daily_df, new_row], ignore_index=True)
                        db.overwrite_sheet_data('daily', updated_daily_df)
                        
                        # 2. 排便データの保存
                        if had_bowel == "あり" and bowel_data_list:
                            for b in bowel_data_list:
                                db.append_data_to_sheet('bowel', {
                                    'name': user_name, 'date': str_date,
                                    'time': b['time'], 'amount': b['amount'], 'hardness': b['hardness']
                                })

                        # 3. 運動データの保存
                        if exercise_data_list:
                            for ex in exercise_data_list:
                                db.append_data_to_sheet('exercise', {
                                    'name': user_name, 'date': str_date,
                                    'time': ex['time'], 'content': ex['content']
                                })

                        # 4. 食事保存
                        if any(m['menu'] or m['image_file'] for m in meal_data_list):
                            for meal in meal_data_list:
                                if not meal['menu'] and not meal['image_file']:
                                    continue
                                image_url = ""
                                if meal['image_file']:
                                    try:
                                        res = cloudinary.uploader.upload(meal['image_file'])
                                        image_url = res['secure_url']
                                    except:
                                        pass
                                
                                db.append_data_to_sheet('meal', {
                                    'name': user_name, 'date': str_date,
                                    'type': meal['type'], 'time': meal['time'],
                                    'menu': meal['menu'], 'image_url': image_url
                                })
                    
                    # 【修正箇所】メッセージをシンプルに変更
                    st.toast("保存完了", icon="✅")
                else:
                    st.error("体重を正しく入力してください")

        # --- 振り返りタブ ---
        with tab_review:
            st.subheader("📊 コンディション分析")
            daily_df = db.load_data_from_sheet('daily')
            
            if not daily_df.empty:
                my_data = daily_df[daily_df['name'] == user_name].copy()
                if not my_data.empty:
                    my_data['date'] = pd.to_datetime(my_data['date'])
                    my_data = my_data.sort_values('date')
                    my_data = my_data.drop_duplicates(subset=['date'], keep='last')
                    
                    my_data['weight'] = pd.to_numeric(my_data['weight'], errors='coerce')
                    my_data['body_fat'] = pd.to_numeric(my_data['body_fat'], errors='coerce')
                    
                    latest = my_data.iloc[-1]
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("現在の体重", f"{latest['weight']} kg")
                    with col2:
                        st.metric("体脂肪率", f"{latest['body_fat']} %")
                    
                    # Plotlyグラフ
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=my_data['date'], y=my_data['weight'], mode='lines+markers', name='体重 (kg)', line=dict(color='#007bff', width=2)))
                    fig.add_trace(go.Scatter(x=my_data['date'], y=my_data['body_fat'], mode='lines+markers', name='体脂肪率 (%)', line=dict(color='#28a745', width=2, dash='dot')))

                    max_val = 100
                    if not my_data['weight'].dropna().empty:
                        max_val = max(my_data['weight'].max(), my_data['body_fat'].max()) * 1.1

                    fig.update_layout(
                        height=350, margin=dict(l=20, r=20, t=20, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        yaxis=dict(range=[0, max_val], fixedrange=True, title="値"),
                        xaxis=dict(fixedrange=True, tickformat="%Y-%m-%d", dtick="D1"),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                    # 履歴表示
                    st.divider()
                    c_ex, c_bowel = st.columns(2)
                    with c_ex:
                        st.write("🏃‍♂️ 最近の運動")
                        ex_df = db.load_data_from_sheet('exercise')
                        if not ex_df.empty:
                            my_ex = ex_df[ex_df['name'] == user_name].tail(3)
                            for _, row in my_ex.iterrows():
                                st.success(f"{row['date']} : {row['content']}")
                    with c_bowel:
                        st.write("🚻 最近の排便")
                        bowel_df = db.load_data_from_sheet('bowel')
                        if not bowel_df.empty:
                            my_bowel = bowel_df[bowel_df['name'] == user_name].tail(3)
                            for _, row in my_bowel.iterrows():
                                st.info(f"{row['date']} : {row['amount']} / {row['hardness']}")
                else:
                    st.info("データなし")
            else:
                st.info("データなし")