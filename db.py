# db.py
import streamlit as st
import gspread
import json
import pandas as pd
from google.oauth2.service_account import Credentials

# --- 設定 ---
# ここにあなたのスプレッドシートのURLを貼ってください
SHEET_URL = "https://docs.google.com/spreadsheets/d/15-4U9We9aKSS9rqDbCgI7QY8Y4fVJvDDvUtcCth8T30/edit?gid=0#gid=0"

# スコープ設定（権限）
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- 接続関数 ---
def get_connection():
    # secrets.toml から鍵情報を読み込む
    key_dict = json.loads(st.secrets["gcp"]["json"])
    creds = Credentials.from_service_account_info(key_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

# --- データ読み込み ---
def load_data_from_sheet(sheet_name):
    try:
        client = get_connection()
        sheet = client.open_by_url(SHEET_URL).worksheet(sheet_name)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return df
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame()
    except Exception as e:
        # シートが空の場合などのエラー対策
        return pd.DataFrame()

# --- データ追加（1行追加） ---
def append_data_to_sheet(sheet_name, data_dict):
    client = get_connection()
    sheet = client.open_by_url(SHEET_URL).worksheet(sheet_name)
    
    # データフレームの列順序を守るため、既存ヘッダーを確認してもよいが
    # 簡易的に値のリストを作って追加する
    # ※初回はヘッダーがないとズレるので、スプレッドシートの1行目に
    # 手動でヘッダー（name, date...）を書いておくのが一番安全です。
    # 今回は「辞書の値」をそのまま追加します。
    
    # 辞書の値をリストに変換
    row = list(data_dict.values())
    sheet.append_row(row)

# --- データ全洗い替え（削除機能用） ---
def overwrite_sheet_data(sheet_name, df):
    client = get_connection()
    sheet = client.open_by_url(SHEET_URL).worksheet(sheet_name)
    sheet.clear() # 全消去
    
    # ヘッダーとデータを書き込み
    # gspreadのupdate機能を使う
    sheet.update([df.columns.values.tolist()] + df.values.tolist())