import streamlit as st
import pandas as pd

from utils.docx_processing import process_docx_file
from utils.pdf_processing import process_pdf_file
from utils.grade_analysis import calculate_total_credits

def main():
    st.set_page_config(page_title="成績單學分計算工具", layout="wide")
    st.title("📄 成績單學分計算工具")

    # 常駐的回饋/開發者（略）

    # 上傳：同時支援 DOCX / PDF（PDF 為測試版）
    uploaded = st.file_uploader("請上傳成績單（Word .docx 或 PDF）", type=["docx", "pdf"])
    if not uploaded:
        st.info("請先上傳檔案。")
        return

    name = (uploaded.name or "").lower()
    if name.endswith(".docx"):
        dfs = process_docx_file(uploaded)
    elif name.endswith(".pdf"):
        dfs = process_pdf_file(uploaded)  # ← 新增
    else:
        st.error("不支援的檔案格式。")
        return

    if not dfs:
        st.error("讀不到表格資料，請確認檔案內容（掃描PDF可能無法解析）。")
        return

    stats = calculate_total_credits(dfs)

# 向下相容：舊版會回 (total, passed, failed)
if not isinstance(stats, dict):
    try:
        total, passed, failed = stats
        stats = {
            "total": total, "required": 0, "i_elective": 0,
            "ii_elective": 0, "other_elective": 0,
            "passed": passed, "failed": failed,
            "passed_required": [], "passed_i": [], "passed_ii": [], "passed_other": []
        }
    except Exception:
        st.error("學分統計格式不正確，請更新 utils/grade_analysis.py 至最新版。")
        return

    # --- 結果（與你現在版面一致） ---
    total           = stats["total"]
    required        = stats["required"]
    i_elective      = stats["i_elective"]
    ii_elective     = stats["ii_elective"]
    other_elective  = stats["other_elective"]
    elective_total  = i_elective + ii_elective + other_elective

    st.markdown("## ✅ 查詢結果")
    st.markdown(f"- **必修學分**：{required:.0f} 學分")
    st.markdown(f"- **一類選修學分**：{i_elective:.0f} 學分")
    st.markdown(f"- **二類選修學分**：{ii_elective:.0f} 學分")
    st.markdown(f"- **總選修學分**：{elective_total:.0f} 學分")
    st.markdown(
        f"<p style='font-size:32px; margin:8px 0;'>📊 **總學分**：<strong>{total:.2f}</strong></p>",
        unsafe_allow_html=True
    )

    # 分類清單（你前一版已加，這裡簡版示例）
    st.markdown("### 📚 所有通過課程（彙整）")
    st.dataframe(pd.DataFrame(stats["passed"]), use_container_width=True)
    st.markdown("### ⚠️ 未通過課程")
    st.dataframe(pd.DataFrame(stats["failed"]), use_container_width=True)

if __name__ == "__main__":
    main()

