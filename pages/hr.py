# --- 最上部に login チェック処理を置く ---
import streamlit as st

# ユーザー認証情報（複数ユーザー対応もOK）
USERNAME = "admin"
PASSWORD = "admin12345"

# セッションでログイン状態管理
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 ログイン")
    username = st.text_input("ユーザー名")
    password = st.text_input("パスワード", type="password")
    if st.button("ログイン"):
        if username == USERNAME and password == PASSWORD:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("ユーザー名またはパスワードが違います。")

# --- ✅ ログインしていなければログイン画面を表示して return ---
if not st.session_state.logged_in:
    login()
    st.stop()  # ← これが重要：ログインしてない人にアプリを描画させない

# --- ↓↓↓ ここからが本来のアプリ部分（選択画面やカレンダーなど） ↓↓↓ ---

st.sidebar.success("ログイン中: admin")
if st.sidebar.button("ログアウト"):
    st.session_state.logged_in = False
    st.rerun()

st.title("👨‍💼 人事部ページ")
st.write("✅ あなたはログイン済です。")

main_tab1, main_tab2, main_tab3 = st.tabs(["採用管理", "研修管理", "タスク管理"])

with main_tab1:
    st.subheader("📄 採用管理")
    st.write("ここに応募者一覧などを表示")
    st.write("応募者のステータスを変更したり、面接日程を調整したりします。")
    st.write("応募者の情報はCSVファイルに保存されます。")

    import pandas as pd
    import os

    # データファイルのパス
    DATA_FILE = "data/applicants.csv"

    # 初期化（なければ作成）
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DATA_FILE):
        pd.DataFrame(columns=["名前", "メール", "電話番号", "希望職種", "概要","長所 自己評価","長所 AI分析","短所 自己評価","短所 AI分析","Q&A", "ステータス", "応募日","面接日"]).to_csv(
            DATA_FILE, index=False, encoding="utf-8-sig"
        )

    # タブ切り替え
    sub_tab0,sub_tab1, sub_tab2,sub_tab3 = st.tabs(["📝新規登録","📄 応募者一覧", "✏️ 状況編集","📅カレンダー"])

    import re
    from datetime import datetime

    def extract_by_section(text: str, start_key: str, end_key: str):
        try:
            start_idx = text.index(start_key)
            end_idx = text.index(end_key, start_idx)
            return text[start_idx + len(start_key):end_idx].strip()
        except ValueError:
            return ""

    def extract_ai_sections(text: str):
        # "PLAUD AI分析" が2回以上出てくることを想定
        matches = list(re.finditer(r"PLAUD\s*AI\s*分析", text))

        if len(matches) >= 2:
            start1 = matches[0].end()
            start2 = matches[1].end()

            # 長所AI分析 → 潜在的な懸念まで
            end_match = re.search(r"(潜在的な懸念)", text[start1:])
            end1 = start1 + end_match.start() if end_match else start2
            strength_ai = text[start1:end1].strip()

            # 短所AI分析 → 通常どおり2つ目のPLAUDから Q&A, 面接プロセス, AI提案などまで
            end_match2 = re.search(r"(面接プロセス|Q&A|AI提案|経験 1)", text[start2:])
            end2 = start2 + end_match2.start() if end_match2 else len(text)
            weakness_ai = text[start2:end2].strip()
        else:
            strength_ai = ""
            weakness_ai = ""
        return strength_ai, weakness_ai

    def parse_pdf_text(text: str):
        # 名前
# 名前（フルネーム抽出：カッコや改行手前まで）
        name_match = re.search(r"応募者[:：]?\s*(.+?)(（|$)", text)
        name = name_match.group(1).strip() if name_match else ""

        # 応募日
        date_match = re.search(r"日時[:：]?\s*([0-9]{4}-[0-9]{2}-[0-9]{2})", text)
        apply_date = date_match.group(1) if date_match else datetime.today().strftime("%Y-%m-%d")

        # 希望職種
        job = ""
        for line in text.splitlines():
            if "志望" in line:
                job = line.strip().split()[-1]
                break

        # 各セクション
        summary = extract_by_section(text, "候補者の概要", "潜在的な強み")
        strength_self = extract_by_section(text, "潜在的な強み", "PLAUD AI 分析")
        weakness_self = extract_by_section(text, "潜在的な懸念", "PLAUD AI 分析")
        strength_ai, weakness_ai = extract_ai_sections(text)
        qa = extract_by_section(text, "Q&A", "AI提案")

        return {
            "名前": name,
            "メール": "",
            "電話番号": "",
            "希望職種": job,
            "概要": summary,
            "長所 自己評価": strength_self,
            "長所 AI分析": strength_ai,
            "短所 自己評価": weakness_self,
            "短所 AI分析": weakness_ai,
            "Q&A": qa,
            "ステータス": "書類選考中",
            "応募日": apply_date,
            "面接日": ""
        }


    with sub_tab0:  # 新規登録用のタブがあればそちらに、なければ subtab1 の上でもOK
        st.markdown("### 📎 ファイルから応募者情報を登録")

        uploaded_files = st.file_uploader(
            "PDF、Word、CSV、Excel ファイルをアップロードしてください",
            type=["pdf", "docx", "csv", "xlsx"],
            accept_multiple_files=True
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.markdown(f"✅ アップロード済みファイル: `{uploaded_file.name}`")

                file_type = uploaded_file.name.split(".")[-1].lower()

                if file_type == "csv":
                    df_uploaded = pd.read_csv(uploaded_file)
                    st.dataframe(df_uploaded)
                
                elif file_type == "xlsx":
                    df_uploaded = pd.read_excel(uploaded_file)
                    st.dataframe(df_uploaded)

                elif file_type == "pdf":
                    import pdfplumber
                    with pdfplumber.open(uploaded_file) as pdf:
                        text = ""
                        for page in pdf.pages:
                            text += page.extract_text() or ""
                        st.text_area("📄 PDF 抽出テキスト", text, height=200)
                        from datetime import datetime

                        # PDFテキストから情報抽出
                        data = parse_pdf_text(text)

                        # 確認表示（必要なら削除OK）
                        st.markdown("#### 抽出された応募者情報")
                        st.json(data)

                        # 登録ボタン
                        if st.button(f"📩 このPDFから応募者を登録する - {uploaded_file.name}"):
                            df_new = pd.DataFrame([data])
                            df_existing = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
                            df_all = pd.concat([df_existing, df_new], ignore_index=True)
                            df_all.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                            st.success(f"{data['名前']} さんを登録しました！")
                            st.rerun()

                elif file_type == "docx":
                    from docx import Document
                    doc = Document(uploaded_file)
                    text = "\n".join([para.text for para in doc.paragraphs])
                    st.text_area("📄 Word 抽出テキスト", text, height=200)

                else:
                    st.warning("対応していないファイル形式です。")

        st.subheader("📝 応募者を登録する")

        name = st.text_input("名前")
        email = st.text_input("メール")
        phone = st.text_input("電話番号")
        position = st.text_input("希望職種")
        summary = st.text_area("概要")
        strength_self = st.text_area("長所（自己評価）")
        strength_ai = st.text_area("長所（AI分析）")
        weakness_self = st.text_area("短所（自己評価）")
        weakness_ai = st.text_area("短所（AI分析）")
        qa = st.text_area("Q&A")
        status = st.selectbox("ステータス", ["書類選考中", "面接予定", "内定", "不採用"])

        from datetime import datetime
        if st.button("登録"):
            if name.strip() == "":
                st.warning("名前は必須です。")
            else:
                today = datetime.now().strftime("%Y-%m-%d")
                new_row = pd.DataFrame([[name, email, phone, position, summary, strength_self, strength_ai, weakness_self, weakness_ai, qa, status, today, ""]],
                    columns=["名前", "メール", "電話番号", "希望職種", "概要","長所 自己評価","長所 AI分析","短所 自己評価","短所 AI分析","Q&A", "ステータス", "応募日", "面接日"])

                # ファイルがあれば追記、なければ新規作成（保険）
                if os.path.exists(DATA_FILE):
                    new_row.to_csv(DATA_FILE, mode="a", index=False, header=False, encoding="utf-8-sig")
                else:
                    new_row.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")

                st.success(f"{name} さんを登録しました！")
                

    # --- タブ1：一覧表示 ---
    with sub_tab1:
        st.subheader("🔍 応募者検索フィルター")

        df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

        df["応募日_dt"] = pd.to_datetime(df["応募日"], errors="coerce")

        # 検索用UI
        name_query = st.text_input("名前で検索", "")
        job_filter = st.selectbox("希望職種で絞り込み", ["すべて"] + sorted(df["希望職種"].dropna().unique().tolist()))
        status_filter = st.selectbox("ステータスで絞り込み", ["すべて", "書類選考中", "面接予定", "内定", "不採用"])
        min_date = df["応募日_dt"].min()
        if pd.isna(min_date):
            min_date = datetime.today()

        selected_date = st.date_input("応募日がこの日以降", value=min_date)


        # 条件でフィルター
        filtered_df = df.copy()

        if name_query:
            filtered_df = filtered_df[filtered_df["名前"].str.contains(name_query, case=False, na=False)]

        if job_filter != "すべて":
            filtered_df = filtered_df[filtered_df["希望職種"] == job_filter]

        if status_filter != "すべて":
            filtered_df = filtered_df[filtered_df["ステータス"] == status_filter]

        if selected_date:
            filtered_df = filtered_df[pd.to_datetime(filtered_df["応募日"], errors="coerce") >= pd.to_datetime(selected_date)]

        # 結果の表示
        st.write(f"🔎 検索結果：{len(filtered_df)} 件")
        st.dataframe(filtered_df.drop(columns=["応募日_dt"]), use_container_width=True)

        import io

        # CSVをバイト形式でエクスポート
        csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
        csv_bytes = csv.encode('utf-8-sig')

        # ダウンロードボタンの表示
        st.download_button(
            label="📥 絞り込み結果をCSVでダウンロード",
            data=csv_bytes,
            file_name="応募者_フィルター結果.csv",
            mime="text/csv"
        )
        import pandas as pd
        from datetime import datetime, date

        df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

        st.subheader("📅 面接日を登録する")

        if df.empty:
            st.info("応募者がまだいません。")
        else:
            idx = st.selectbox(
                "面接日を登録したい応募者を選択",
                df.index,
                format_func=lambda i: f"{df.at[i, '名前']}（{df.at[i, '希望職種']}）"
            )

            interview_date = st.date_input("面接予定日を選択", value=date.today())

            if st.button("面接日を登録"):
                df.at[idx, "面接日"] = interview_date.strftime("%Y-%m-%d")
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success(f"{df.at[idx, '名前']} さんの面接日を {interview_date} に登録しました。")
                st.rerun()



    # --- タブ2：編集画面 ---
    with sub_tab2:
        st.subheader("✏️ ステータスを編集する")
        df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

        if df.empty:
            st.info("現在、登録されている応募者がいません。")
        else:
            selected_index = st.selectbox(
                "編集したい応募者を選択",
                df.index,
                format_func=lambda i: f"{df.at[i, '名前']}（現在：{df.at[i, 'ステータス']}）"
            )

            new_status = st.selectbox(
                "新しいステータス",
                ["書類選考中", "面接予定", "内定", "不採用"],
                index=["書類選考中", "面接予定", "内定", "不採用"].index(df.at[selected_index, "ステータス"])
            )

            if st.button("ステータスを更新"):
                df.at[selected_index, "ステータス"] = new_status
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success(f"{df.at[selected_index, '名前']} さんのステータスを「{new_status}」に更新しました！")
                st.rerun()
        
        st.divider()
        st.subheader("🗑️ 応募者を削除する")

        df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")

        if df.empty:
            st.info("現在、応募者がいません。")
        else:
            delete_index = st.selectbox(
                "削除したい応募者を選んでください",
                df.index,
                format_func=lambda i: f"{df.at[i, '名前']}（{df.at[i, '希望職種']}）"
            )

            if st.button("この応募者を削除する", type="primary"):
                name = df.at[delete_index, "名前"]
                df = df.drop(delete_index).reset_index(drop=True)
                df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
                st.success(f"{name} さんの応募情報を削除しました。")
                st.rerun()

    import streamlit as st
    import pandas as pd
    from streamlit_calendar import calendar

    with sub_tab3:
    # --- データファイルのパス ---
        DATA_FILE = "data/applicants.csv"

        # --- ファイルの読み込みと整形 ---
        df = pd.read_csv(DATA_FILE, encoding="utf-8-sig")
        df["面接日"] = pd.to_datetime(df["面接日"], errors="coerce")

        # --- カレンダー表示対象の行だけを抽出 ---
        filtered = df[df["面接日"].notna()]

        # --- カラー定義 ---
        color_map = {
            "書類選考中": "blue",
            "面接予定": "orange",
            "内定": "green",
            "不採用": "red"
        }

        # --- カレンダーイベントの作成（最初 or リロード時のみ） ---
        if "calendar_events" not in st.session_state or st.button("🔄 カレンダーを再読み込み"):
            events = []
            for _, row in filtered.iterrows():
                events.append({
                    "id": str(row["名前"]),
                    "title": f"{row['名前']}（{row['ステータス']}）",
                    "start": pd.to_datetime(row["面接日"]).isoformat(),
                    "end": pd.to_datetime(row["面接日"]).isoformat(),
                    "backgroundColor": color_map.get(row["ステータス"], "gray")
                })
            st.session_state["calendar_events"] = events

        # --- カレンダーオプション ---
        calendar_options = {
            "initialView": "dayGridMonth",
            "locale": "ja",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay"
            },
        }

        # --- カレンダーの描画（events が空でも描画する） ---
        st.subheader("📅 面接スケジュール（カレンダー表示）")

        clicked = calendar(
            events=st.session_state.get("calendar_events", []),
            options=calendar_options
        )

        # --- イベントがない場合の警告 ---
        if not st.session_state.get("calendar_events"):
            st.warning("📭 表示できる面接予定がありません。")

        # --- カレンダークリック時の処理 ---
        if clicked and "eventClick" in clicked:
            selected_name = clicked["eventClick"]["event"]["id"]
            st.info(f"🧾 {selected_name} さんの詳細")

            detail = df[df["名前"] == selected_name]
            if not detail.empty:
                st.write(detail.iloc[0].to_frame(name="内容").rename_axis("項目"))


with main_tab2:
    st.subheader("🎓 研修進捗")
    st.write("研修の実施状況など")
    st.write("研修の進捗状況を確認したり、研修を追加したりします。")
    st.write("研修の情報はCSVファイルに保存されます。")

with main_tab3:
    st.subheader("📋 タスク管理")
    st.write("社員ごとのタスク一覧")
    st.write("タスクの進捗状況を確認したり、タスクを追加したりします。")
    st.write("タスクの情報はCSVファイルに保存されます。")