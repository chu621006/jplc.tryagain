import re
import pandas as pd

# ...（你的 normalize 與字典/分類函式維持不變）...

def _pick(row: pd.Series, col: str, default=""):
    """
    安全從 row 取一個欄位值：
    - 若是純量，直接回傳
    - 若是 Series（同名欄位造成），取第一個非空值
    - 若全是空或沒有該欄位，回 default
    """
    if col in row.index:
        v = row[col]
        if isinstance(v, pd.Series):
            v = v.dropna()
            if len(v) > 0:
                return v.astype(str).iloc[0]
            return default
        return v if pd.notna(v) else default
    return default

def calculate_total_credits(df_list: list[pd.DataFrame]) -> dict:
    total_credits = required_credits = i_credits = ii_credits = other_credits = 0.0
    passed_all, failed_all = [], []
    passed_req, passed_i, passed_ii, passed_other = [], [], [], []

    for df in df_list:
        name_col   = "科目名稱" if "科目名稱" in df.columns else ( "課程名稱" if "課程名稱" in df.columns else df.columns[0] )
        credit_col = "學分"     if "學分"     in df.columns else ( "credit"   if "credit"   in df.columns else df.columns[-2] )
        grade_col  = "成績"     if "成績"     in df.columns else ( "GPA"      if "GPA"      in df.columns else df.columns[-1] )

        for _, row in df.iterrows():
            name = _pick(row, name_col, "")
            raw_credit = _pick(row, credit_col, 0)
            gpa = _pick(row, grade_col, "")

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
