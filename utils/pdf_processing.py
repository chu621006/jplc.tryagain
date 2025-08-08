import pdfplumber
import pandas as pd
import re

def normalize_text(x):
    return "" if x is None else re.sub(r"\s+", " ", str(x)).strip()

def standardize_columns(cols):
    mapping = {}
    for col in cols:
        low = normalize_text(col).lower()
        if any(k in low for k in ["科目", "課程", "名稱", "subject", "course"]):
            mapping[col] = "科目名稱"
        elif "學分" in low or "credit" in low:
            mapping[col] = "學分"
        elif any(k in low for k in ["成績", "gpa", "grade"]):
            mapping[col] = "成績"
        else:
            mapping[col] = normalize_text(col)
    return mapping

def _extract_tables(pdf_file) -> list[pd.DataFrame]:
    dfs = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for tb in tables:
                if not tb or len(tb) < 2:
                    continue
                df = pd.DataFrame(tb[1:], columns=tb[0])
                df.columns = [normalize_text(c) for c in df.columns]
                df = df.rename(columns=standardize_columns(df.columns))
                # ★ 去掉重複欄位（保留第一個），避免 row["科目名稱"] 變 Series
                df = df.loc[:, ~df.columns.duplicated(keep="first")]
                dfs.append(df)
    return dfs

# （其餘程式維持你現有的版本；若有純文字備援就保留）
