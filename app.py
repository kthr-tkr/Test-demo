import streamlit as st

st.set_page_config(page_title="企業DXシステム", layout="wide")
st.title("🏢 企業DXシステム（メインページ）")

st.markdown("部署を選択してください：")

st.page_link("pages/hr.py", label="👨‍💼 人事部", icon="🧑‍💼")
# 将来ここに他部署を追加
