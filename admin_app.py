import streamlit as st
import pandas as pd
import os
import plotly.graph_objects as go
import db # db.pyを読み込み

# --- 1. 画面構成設定 ---
st.set_page_config(page_title="管理者ダッシュボード", layout="wide")

# --- 2. 関数群 ---
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"{file_name} が見つかりません")

def show_sidebar_toggle():
    st.markdown("""
        <style>
        header {visibility: visible !important;}
        header .stAppHeader {background-color: transparent;}
        </style>
    """, unsafe_allow_html=True)

# CSS適用
local_css("style.css")
show_sidebar_toggle()

st.title("📈 チーム管理ダッシュボード")

# --- 3. ログイン処理 ---
if 'admin_login' not in st.session_state:
    st.session_state.admin_login = False

if not st.session_state.admin_login:
    pwd = st.text_input("管理者パスワードを入力してください", type="password")
    if pwd:
        if pwd == "admin123":
            st.session_state.admin_login = True
            st.rerun()
        else:
            st.error("パスワードが違います")
else:
    # ログイン後
    col_header, col_logout = st.columns([8, 1])
    with col_header:
        st.success("ログイン中")
    with col_logout:
        if st.button("ログアウト"):
            st.session_state.admin_login = False
            st.rerun()

    # DBからユーザー一覧読み込み
    users_df = db.load_data_from_sheet('users')

    if users_df.empty:
        st.warning("登録されている選手がいません")
        st.stop()

    # --- サイドバー：メニュー ---
    st.sidebar.title("メニュー")
    mode = st.sidebar.radio("表示モードを選択", ["📊 個別分析", "📅 日毎一覧", "🗑️ 選手管理（削除）"])

    # DBから全データ読み込み
    daily_df = db.load_data_from_sheet('daily')
    meal_df = db.load_data_from_sheet('meal')
    ex_df = db.load_data_from_sheet('exercise')
    bowel_df = db.load_data_from_sheet('bowel')

    # ==========================================
    # モードA: 個別分析
    # ==========================================
    if mode == "📊 個別分析":
        st.subheader("👤 選手ごとの詳細分析")
        
        selected_user = st.selectbox("データを見たい選手を選択してください", users_df['name'].unique())
        st.divider()
        st.header(f"{selected_user} 選手の詳細データ")
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 コンディション推移", "🏃‍♂️ 運動履歴", "🍽️ 食事履歴", "🚻 排便履歴"])
        
        with tab1:
            if not daily_df.empty:
                user_daily = daily_df[daily_df['name'] == selected_user].copy()
                if not user_daily.empty:
                    user_daily['date'] = pd.to_datetime(user_daily['date'])
                    user_daily = user_daily.sort_values('date')
                    user_daily = user_daily.drop_duplicates(subset=['date'], keep='last')
                    
                    user_daily['weight'] = pd.to_numeric(user_daily['weight'], errors='coerce')
                    user_daily['body_fat'] = pd.to_numeric(user_daily['body_fat'], errors='coerce')

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=user_daily['date'], y=user_daily['weight'], mode='lines+markers', name='体重 (kg)', line=dict(color='#007bff', width=2)))
                    fig.add_trace(go.Scatter(x=user_daily['date'], y=user_daily['body_fat'], mode='lines+markers', name='体脂肪率 (%)', line=dict(color='#28a745', width=2, dash='dot')))

                    max_val = 100
                    if not user_daily['weight'].dropna().empty:
                        max_val = max(user_daily['weight'].max(), user_daily['body_fat'].max()) * 1.1

                    fig.update_layout(
                        height=400, margin=dict(l=20, r=20, t=20, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        yaxis=dict(range=[0, max_val], fixedrange=True, title="値"),
                        xaxis=dict(fixedrange=True, tickformat="%Y-%m-%d", dtick="D1"),
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                    with st.expander("詳細データを見る"):
                        st.dataframe(user_daily, use_container_width=True)
                else:
                    st.warning("記録がありません")
            else:
                st.info("データがありません")

        with tab2:
            if not ex_df.empty:
                user_ex = ex_df[ex_df['name'] == selected_user].copy()
                if not user_ex.empty:
                    user_ex['date'] = pd.to_datetime(user_ex['date'])
                    user_ex = user_ex.sort_values(['date'], ascending=False)
                    for i, row in user_ex.iterrows():
                        date_str = row['date'].strftime('%Y-%m-%d')
                        time_str = str(row['time'])[:5] if pd.notnull(row.get('time')) else ""
                        st.success(f"**{date_str}** | ⏱ {time_str} | {row['content']}")
                else:
                    st.warning("記録がありません")
            else:
                st.info("データがありません")

        with tab3:
            if not meal_df.empty:
                user_meal = meal_df[meal_df['name'] == selected_user].copy()
                if not user_meal.empty:
                    user_meal['date'] = pd.to_datetime(user_meal['date'])
                    user_meal = user_meal.sort_values(['date'], ascending=False)
                    for i, row in user_meal.iterrows():
                        date_str = row['date'].strftime('%Y-%m-%d')
                        time_display = str(row['time'])[:5] if pd.notnull(row.get('time')) else ""
                        with st.container():
                            c1, c2 = st.columns([2, 1])
                            with c1:
                                st.info(f"📅 **{date_str} {time_display}** ({row['type']})\n\n{row['menu']}")
                            with c2:
                                # 【修正箇所】URLが http で始まる場合のみ画像を表示する（空文字対策）
                                img_url = row.get('image_url')
                                if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                                    st.image(img_url, use_container_width=True)
                            st.divider()
                else:
                    st.warning("記録がありません")
            else:
                st.info("データがありません")

        with tab4:
            if not bowel_df.empty:
                user_bowel = bowel_df[bowel_df['name'] == selected_user].copy()
                if not user_bowel.empty:
                    user_bowel['date'] = pd.to_datetime(user_bowel['date'])
                    user_bowel = user_bowel.sort_values(['date'], ascending=False)
                    for i, row in user_bowel.iterrows():
                        date_str = row['date'].strftime('%Y-%m-%d')
                        time_str = str(row['time'])[:5] if pd.notnull(row.get('time')) else ""
                        c1, c2, c3 = st.columns([2, 1, 1])
                        c1.write(f"📅 {date_str} {time_str}")
                        c2.write(f"量: {row['amount']} / 硬さ: {row['hardness']}")
                        if row['hardness'] == "下痢":
                            c3.warning("⚠️")
                        st.divider()
                else:
                    st.warning("記録がありません")
            else:
                st.info("データがありません")

    # ==========================================
    # モードB: 日毎一覧
    # ==========================================
    elif mode == "📅 日毎一覧":
        st.subheader("📅 日毎データ一覧")
        from datetime import date
        target_date = st.date_input("確認したい日付を選択", date.today())
        target_date_str = str(target_date)

        d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs(["📊 体調一覧", "🏃‍♂️ 運動一覧", "🍽️ 食事一覧", "🚻 排便一覧"])

        with d_tab1:
            if not daily_df.empty:
                day_daily = daily_df[daily_df['date'] == target_date_str].copy()
                if not day_daily.empty:
                    day_daily = day_daily.drop_duplicates(subset=['name'], keep='last')
                    display_df = day_daily[['name', 'weight', 'body_fat', 'sleep']].copy()
                    display_df.columns = ['名前', '体重(kg)', '体脂肪率(%)', '睡眠(h)']
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                else:
                    st.info(f"{target_date} の記録はありません")
            else:
                st.info("データなし")

        with d_tab2:
            if not ex_df.empty:
                day_ex = ex_df[ex_df['date'] == target_date_str].copy()
                if not day_ex.empty:
                    display_ex = day_ex[['name', 'time', 'content']].copy()
                    display_ex['time'] = display_ex['time'].astype(str).str[:5]
                    display_ex.columns = ['名前', '時間', '運動内容']
                    st.dataframe(display_ex, use_container_width=True, hide_index=True)
                else:
                    st.info("記録なし")
            else:
                st.info("データなし")

        with d_tab3:
            if not meal_df.empty:
                day_meal = meal_df[meal_df['date'] == target_date_str].copy()
                if not day_meal.empty:
                    for i, row in day_meal.iterrows():
                        time_str = str(row['time'])[:5] if pd.notnull(row.get('time')) else ""
                        with st.container():
                            c_txt, c_img = st.columns([3, 1])
                            with c_txt:
                                st.markdown(f"**{row['name']}** | {time_str} ({row['type']})")
                                st.info(row['menu'])
                            with c_img:
                                # 【修正箇所】URLチェックを追加
                                img_url = row.get('image_url')
                                if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                                    st.image(img_url, use_container_width=True)
                            st.divider()
                else:
                    st.info("記録なし")
            else:
                st.info("データなし")

        with d_tab4:
            if not bowel_df.empty:
                day_bowel = bowel_df[bowel_df['date'] == target_date_str].copy()
                if not day_bowel.empty:
                    display_bowel = day_bowel[['name', 'time', 'amount', 'hardness']].copy()
                    display_bowel['time'] = display_bowel['time'].astype(str).str[:5]
                    display_bowel.columns = ['名前', '時間', '量', '硬さ']
                    st.dataframe(display_bowel, use_container_width=True, hide_index=True)
                else:
                    st.info("記録なし")
            else:
                st.info("データなし")

    # ==========================================
    # モードC: 選手管理（削除）
    # ==========================================
    elif mode == "🗑️ 選手管理（削除）":
        st.subheader("🗑️ 選手データの完全削除")
        delete_target = st.selectbox("削除する選手を選択", users_df['name'].unique())
        
        st.write("---")
        st.markdown(f"### 👤 {delete_target} さんのデータ概要")
        
        user_info = users_df[users_df['name'] == delete_target].iloc[0]
        
        d_cnt = len(daily_df[daily_df['name'] == delete_target]) if not daily_df.empty else 0
        m_cnt = len(meal_df[meal_df['name'] == delete_target]) if not meal_df.empty else 0
        e_cnt = len(ex_df[ex_df['name'] == delete_target]) if not ex_df.empty else 0
        b_cnt = len(bowel_df[bowel_df['name'] == delete_target]) if not bowel_df.empty else 0

        col_prof, col_stats = st.columns(2)
        with col_prof:
            st.info("**基本プロフィール**")
            st.write(f"**生年月日:** {user_info['dob']}")
            st.write(f"**身長:** {user_info['height']} cm")
        with col_stats:
            st.error("**削除される記録**")
            st.write(f"📊 コンディション: {d_cnt} 件")
            st.write(f"🍽️ 食事: {m_cnt} 件")
            st.write(f"🏃‍♂️ 運動: {e_cnt} 件")
            st.write(f"🚻 排便: {b_cnt} 件")

        st.write("---")
        agree = st.checkbox(f"はい、{delete_target} のデータを完全に削除することに同意します")
        
        if st.button("🚫 データを削除する", type="primary", disabled=not agree):
            with st.spinner("スプレッドシートからデータを削除中..."):
                sheet_names = ['users', 'daily', 'meal', 'exercise', 'bowel']
                for sheet in sheet_names:
                    df = db.load_data_from_sheet(sheet)
                    if not df.empty and 'name' in df.columns:
                        df_new = df[df['name'] != delete_target]
                        db.overwrite_sheet_data(sheet, df_new)
            
            st.success(f"✅ {delete_target} さんのデータを削除しました。")
            st.rerun()