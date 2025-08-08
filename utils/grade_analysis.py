# 放在檔案前面那些 import/normalize 後面，加這個幫手
def _find_col(df: pd.DataFrame, prefer_keywords: list[str], fallback_index: int | None = None):
    """
    在 df.columns 中尋找包含指定關鍵字的欄位（不分大小寫）。
    找不到就用 fallback_index（若給且存在）；再找不到就回 None。
    """
    cols = list(df.columns)
    lowered = [str(c).strip().lower() for c in cols]

    for i, low in enumerate(lowered):
        if any(k in low for k in prefer_keywords):
            return cols[i]

    if fallback_index is not None:
        # 允許只有 1 欄的情況；安全地回傳最後一欄或 None
        if -len(cols) <= fallback_index < len(cols):
            return cols[fallback_index]

    return None


# 這段整個覆蓋你原本的 calculate_total_credits
def calculate_total_credits(df_list: list[pd.DataFrame]) -> dict:
    total_credits = required_credits = i_credits = ii_credits = other_credits = 0.0
    passed_all, failed_all = [], []
    passed_req, passed_i, passed_ii, passed_other = [], [], [], []

    for df in df_list:
        if df is None or df.empty or len(df.columns) == 0:
            continue

        # 1) 安全選欄位（找不到就給 None；名稱至少給第一欄）
        name_col = _find_col(
            df, ["科目", "課程", "名稱", "subject", "course"], fallback_index=0
        )
        credit_col = _find_col(df, ["學分", "credit"], fallback_index=None)
        grade_col = _find_col(df, ["成績", "gpa", "grade"], fallback_index=None)

        # 2) 逐列處理
        for _, row in df.iterrows():
            # 取值時確保是純量；Series 取第一個非空；None 用預設
            name = _pick(row, name_col, "") if name_col is not None else ""
            raw_credit = _pick(row, credit_col, 0) if credit_col is not None else 0
            gpa = _pick(row, grade_col, "") if grade_col is not None else ""

            try:
                credit = float(raw_credit)
            except Exception:
                credit = 0.0

            if is_passing_gpa(gpa):
                item = {"科目名稱": name, "學分": credit, "成績": gpa}
                passed_all.append(item)
                total_credits += credit

                cat = categorize_course(name)
                if cat == "Required":
                    required_credits += credit; passed_req.append(item)
                elif cat == "I":
                    i_credits += credit; passed_i.append(item)
                elif cat == "II":
                    ii_credits += credit; passed_ii.append(item)
                else:
                    other_credits += credit; passed_other.append(item)
            else:
                failed_all.append({"科目名稱": name, "學分": credit, "成績": gpa})

    return {
        "total": total_credits,
        "required": required_credits,
        "i_elective": i_credits,
        "ii_elective": ii_credits,
        "other_elective": other_credits,
        "passed": passed_all,
        "failed": failed_all,
        "passed_required": passed_req,
        "passed_i": passed_i,
        "passed_ii": passed_ii,
        "passed_other": passed_other,
    }
