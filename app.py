import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import datetime
from tkinter import simpledialog

# --- 設定 ---
DATA_FILE = 'daily_data.csv'
USER_FILE = 'user_profile.csv'

# --- データ保存機能 (CSV) ---
def save_daily_record(data):
    file_exists = os.path.isfile(DATA_FILE)
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['日付', '体重', '体脂肪率', '睡眠時間', '排便', '便の状態', '運動時間', '運動内容', '食事メモ'])
        writer.writerow(data)
    messagebox.showinfo("成功", "データが保存されました！")

def save_user_profile(name, dob, height):
    with open(USER_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['名前', '生年月日', '身長'])
        writer.writerow([name, dob, height])
    messagebox.showinfo("完了", "プロフィールを登録しました")

# --- アプリ画面の構築 ---
class NutritionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("栄養管理アプリ (Python 3.14版)")
        self.geometry("500x700")

        # タブを作る
        tab_control = ttk.Notebook(self)
        self.tab1 = ttk.Frame(tab_control)
        self.tab2 = ttk.Frame(tab_control)
        self.tab3 = ttk.Frame(tab_control)
        
        tab_control.add(self.tab1, text='毎日の入力')
        tab_control.add(self.tab2, text='食事記録')
        tab_control.add(self.tab3, text='設定/分析')
        tab_control.pack(expand=1, fill="both")

        self.create_daily_input_tab()
        self.create_meal_tab()
        self.create_settings_tab()

    def create_daily_input_tab(self):
        frame = ttk.Frame(self.tab1, padding=20)
        frame.pack(fill="both", expand=True)

        # 日付
        ttk.Label(frame, text="【コンディション入力】", font=("", 14, "bold")).pack(pady=10)
        
        # 体重
        ttk.Label(frame, text="体重 (kg):").pack(anchor="w")
        self.weight_entry = ttk.Entry(frame)
        self.weight_entry.pack(fill="x", pady=5)

        # 体脂肪
        ttk.Label(frame, text="体脂肪率 (%):").pack(anchor="w")
        self.fat_entry = ttk.Entry(frame)
        self.fat_entry.pack(fill="x", pady=5)

        # 睡眠
        ttk.Label(frame, text="睡眠時間 (時間):").pack(anchor="w")
        self.sleep_combo = ttk.Combobox(frame, values=[str(x/2) for x in range(0, 49)])
        self.sleep_combo.current(14) # 7.0時間
        self.sleep_combo.pack(fill="x", pady=5)

        # 排便
        ttk.Label(frame, text="排便状況:").pack(anchor="w")
        self.bowel_frame = ttk.Frame(frame)
        self.bowel_frame.pack(fill="x", pady=5)
        self.bowel_var = tk.StringVar(value="あり")
        ttk.Radiobutton(self.bowel_frame, text="あり", variable=self.bowel_var, value="あり").pack(side="left")
        ttk.Radiobutton(self.bowel_frame, text="なし", variable=self.bowel_var, value="なし").pack(side="left")

        # 運動
        ttk.Label(frame, text="運動時間 (分):").pack(anchor="w")
        self.ex_time_entry = ttk.Entry(frame)
        self.ex_time_entry.pack(fill="x", pady=5)
        
        ttk.Label(frame, text="運動内容:").pack(anchor="w")
        self.ex_content = tk.Text(frame, height=3)
        self.ex_content.pack(fill="x", pady=5)

        # 保存ボタン
        btn = ttk.Button(frame, text="記録を保存する", command=self.submit_daily)
        btn.pack(pady=20, fill="x")

    def submit_daily(self):
        date = datetime.date.today()
        weight = self.weight_entry.get()
        fat = self.fat_entry.get()
        sleep = self.sleep_combo.get()
        bowel = self.bowel_var.get()
        bowel_detail = "普通" # 簡易化
        ex_time = self.ex_time_entry.get()
        ex_text = self.ex_content.get("1.0", "end-1c")

        save_daily_record([date, weight, fat, sleep, bowel, bowel_detail, ex_time, ex_text, ""])

    def create_meal_tab(self):
        frame = ttk.Frame(self.tab2, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="【食事記録】", font=("", 14, "bold")).pack(pady=10)
        
        ttk.Label(frame, text="タイミング:").pack(anchor="w")
        self.meal_type = ttk.Combobox(frame, values=["朝食", "昼食", "夕食", "間食"])
        self.meal_type.current(0)
        self.meal_type.pack(fill="x", pady=5)

        ttk.Label(frame, text="メニュー内容:").pack(anchor="w")
        self.meal_desc = tk.Text(frame, height=5)
        self.meal_desc.pack(fill="x", pady=5)

        # 簡易保存ボタン
        btn = ttk.Button(frame, text="食事を保存", command=lambda: messagebox.showinfo("OK", "食事を記録しました（仮）"))
        btn.pack(pady=20, fill="x")

    def create_settings_tab(self):
        frame = ttk.Frame(self.tab3, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="ユーザー設定", font=("", 14)).pack()
        
        ttk.Label(frame, text="名前:").pack(anchor="w")
        self.name_entry = ttk.Entry(frame)
        self.name_entry.pack(fill="x")

        ttk.Button(frame, text="設定保存", command=lambda: save_user_profile(self.name_entry.get(), "", "")).pack(pady=10)

        # 分析用（簡易表示）
        ttk.Label(frame, text="▼ 保存されたデータ（最新5件）").pack(pady=20, anchor="w")
        self.log_text = tk.Text(frame, height=10)
        self.log_text.pack(fill="x")
        
        # データ読み込みボタン
        ttk.Button(frame, text="データを更新して表示", command=self.load_logs).pack(fill="x")

    def load_logs(self):
        self.log_text.delete("1.0", "end")
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                text = f.read()
                self.log_text.insert("1.0", text)
        else:
            self.log_text.insert("1.0", "データがまだありません")

if __name__ == "__main__":
    app = NutritionApp()
    app.mainloop()
