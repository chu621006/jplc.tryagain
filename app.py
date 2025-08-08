# app.py
import streamlit as st
import pandas as pd

# ---- 匯入 DOCX 解析 ----
from utils.docx_processing import process_docx_file

# ---- PDF 解析（可用就載，失敗就自動關掉）----
PDF_ENABLED = True
try:
    from utils.pdf_processing import process_pdf_file
except Exception as e:
    PDF_ENABLED = False
    # 這裡只是提示，不會阻擋 DOCX
    st.warning(f"PDF 解析暫時停用：{e}")

# ---- 學分計算與分類 ----
from utils.grade_analysis import calculate_total_credits


# ---------- Health check：頂層快速回應（供 Uptime/Apps Script ping） ----------
_params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
_health = _params.get("healthz")
if _health == "1" or _health == ["1"]:
    st.write("ok")
    st.stop()  # 頂層一定用 st.stop()，不能用 return


def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # ---- 回饋連結 & 開發者資訊（常駐）----
    st.markdown(
        '<p style="text-align:center;">'
        '感謝您的使用，若您有相關修改建議或發生其他型錯誤，'
        '<a href="https://forms.gle/Bu95Pt74d1oGVCev5" target="_blank">請點此提出</a>'
        '</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align:center;">'
        '開發者：<a href="https://www.instagram.com/chiuuuuu11.7?igsh=MWRlc21zYW55dWZ5Yw==" target="_blank">Chu</a>'
        '</p>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ---- 上傳（支援 DOCX / PDF；PDF 失敗會自動隱藏）----
    types = ["docx", "pdf"] if PDF_ENABLED else ["docx"]
    uploaded = st.file_uploader("請上傳成績單（Word .docx 或 PDF）", type=types)
    if not uploaded:
        st.info("請先上傳檔案。")
        st.stop()

    name = (uploaded.name or "").lower()

    # 解析檔案成 DataFrame 列表
    if name.endswith(".pdf"):
        if not PDF_ENABLED:
            st.error("目前 PDF 解析未啟用，請改上傳 DOCX。")
            st.stop()
        try:
            dfs = process_pdf_file(uploaded)
        except Exception as e:
            st.error(f"PDF 解析失敗：{e}")
            st.stop()

    elif name.endswith(".docx"):
        try:
            dfs = process_docx_file(uploaded)
        except Exception as e:
            st.error(f"DOCX 解析失敗：{e}")
            st.stop()

    else:
        st.error("不支援的檔案格式。")
        st.stop()

    if not dfs:
        st.error("讀不到表格資料，請確認檔案內容（掃描 PDF 可能無法解析）。")
        st.stop()

    # ---- 計算學分 ----
    stats = calculate_total_credits(dfs)

    # ------- 向下相容：舊版 grade_analysis 會回 (total, passed, failed) -------
    if not isinstance(stats, dict):
        try:
            total, passed, failed = stats
            stats = {
                "total": total,
                "required": 0,
                "i_elective": 0,
                "ii_elective": 0,
                "other_elective": 0,
                "passed": passed,
                "failed": failed,
                "passed_required": [],
                "passed_i": [],
                "passed_ii": [],
                "passed_other": [],
            }
        except Exception:
            st.error("學分統計格式不正確，請更新 utils/grade_analysis.py 至最新版。")
            st.stop()

    # ---- 顯示統計 ----
    total = stats["total"]
    required = stats["required"]
    i_elective = stats["i_elective"]
    ii_elective = stats["ii_elective"]
    other_elective = stats["other_elective"]
    elective_total = i_elective + ii_elective + other_elective

    st.markdown("## ✅ 查詢結果")
    st.markdown(f"- **必修學分**：{required:.0f} 學分")
    st.markdown(f"- **一類選修學分**：{i_elective:.0f} 學分")
    st.markdown(f"- **二類選修學分**：{ii_elective:.0f} 學分")
    st.markdown(f"- **總選修學分**：{elective_total:.0f} 學分")
    st.markdown(
        f"<p style='font-size:32px; margin:8px 0;'>📊 **總學分**：<strong>{total:.2f}</strong></p>",
        unsafe_allow_html=True,
    )

    # ---- 分類清單（通過） + 下載按鈕 ----
    st.markdown("### 🧩 分類清單（通過）")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("必修（通過）")
        df_req = pd.DataFrame(stats["passed_required"])
        st.dataframe(df_req if not df_req.empty else pd.DataFrame(columns=["科目名稱","學分","成績"]),
                     use_container_width=True)
        if not df_req.empty:
            st.download_button(
                "下載必修清單 CSV",
                df_req.to_csv(index=False, encoding="utf-8-sig"),
                "必修_通過.csv",
                "text/csv",
            )

    with col2:
        st.subheader("一類選修（通過）")
        df_i = pd.DataFrame(stats["passed_i"])
        st.dataframe(df_i if not df_i.empty else pd.DataFrame(columns=["科目名稱","學分","成績"]),
                     use_container_width=True)
        if not df_i.empty:
            st.download_button(
                "下載一類清單 CSV",
                df_i.to_csv(index=False, encoding="utf-8-sig"),
                "一類選修_通過.csv",
                "text/csv",
            )

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("二類選修（通過）")
        df_ii = pd.DataFrame(stats["passed_ii"])
        st.dataframe(df_ii if not df_ii.empty else pd.DataFrame(columns=["科目名稱","學分","成績"]),
                     use_container_width=True)
        if not df_ii.empty:
            st.download_button(
                "下載二類清單 CSV",
                df_ii.to_csv(index=False, encoding="utf-8-sig"),
                "二類選修_通過.csv",
                "text/csv",
            )

    with col4:
        st.subheader("其他選修（通過）")
        df_other = pd.DataFrame(stats["passed_other"])
        st.dataframe(df_other if not df_other.empty else pd.DataFrame(columns=["科目名稱","學分","成績"]),
                     use_container_width=True)
        if not df_other.empty:
            st.download_button(
                "下載其他選修清單 CSV",
                df_other.to_csv(index=False, encoding="utf-8-sig"),
                "其他選修_通過.csv",
                "text/csv",
            )

    # ---- 全部通過/未通過清單（彙整）----
    st.markdown("### 📚 所有通過課程（彙整）")
    st.dataframe(pd.DataFrame(stats["passed"]), use_container_width=True)

    st.markdown("### ⚠️ 未通過課程")
    st.dataframe(pd.DataFrame(stats["failed"]), use_container_width=True)


if __name__ == "__main__":
    main()
