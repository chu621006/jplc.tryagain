import streamlit as st
import pandas as pd
from utils.docx_processing import process_docx_file

PDF_ENABLED = True
try:
    from utils.pdf_processing import process_pdf_file
except Exception as e:
    PDF_ENABLED = False
    st.warning(f"PDF 解析暫時停用：{e}")

from utils.grade_analysis import calculate_total_credits

# ---------- Health check：頂層快速回應 ----------
params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
h = params.get("healthz")
if h == "1" or h == ["1"]:
    st.write("ok")
    st.stop()  # 頂層要用 st.stop()，不能用 return


def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # 回饋連結 & 開發者資訊（常駐顯示）
    st.markdown(
        '<p style="text-align:center;">'
        '感謝您的使用，若您有相關修改建議或發生其他類型錯誤，'
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

# 上傳（支援 DOCX / PDF）
types = ["docx", "pdf"] if PDF_ENABLED else ["docx"]
uploaded = st.file_uploader("請上傳成績單（Word .docx 或 PDF）", type=types)
if not uploaded:
    st.info("請先上傳檔案。")
    st.stop()

name = (uploaded.name or "").lower()

if name.endswith(".pdf"):
    if not PDF_ENABLED:
        st.error("目前 PDF 解析未啟用，請改上傳 DOCX。")
        st.stop()  # ← 這行一定要縮排在 if 區塊裡
    try:
        dfs = process_pdf_file(uploaded)
    except Exception as e:
        st.error(f"PDF 解析失敗：{e}")
        st.stop()

elif name.endswith(".docx"):
    dfs = process_docx_file(uploaded)

else:
    st.error("不支援的檔案格式。")
    st.stop()


    # 計算學分
    stats = calculate_total_credits(dfs)

    # ---- 向下相容：舊版 grade_analysis 會回 (total, passed, failed) ----
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
            return

    # 顯示統計
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

    # 分類清單（通過）
    st.markdown("### 🧩 分類清單（通過）")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("必修（通過）")
        st.dataframe(pd.DataFrame(stats["passed_required"]), use_container_width=True)
    with col2:
        st.subheader("一類選修（通過）")
        st.dataframe(pd.DataFrame(stats["passed_i"]), use_container_width=True)
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("二類選修（通過）")
        st.dataframe(pd.DataFrame(stats["passed_ii"]), use_container_width=True)
    with col4:
        st.subheader("其他選修（通過）")
        st.dataframe(pd.DataFrame(stats["passed_other"]), use_container_width=True)

    st.markdown("### 📚 所有通過課程（彙整）")
    st.dataframe(pd.DataFrame(stats["passed"]), use_container_width=True)

    st.markdown("### ⚠️ 未通過課程")
    st.dataframe(pd.DataFrame(stats["failed"]), use_container_width=True)


if __name__ == "__main__":
    main()



