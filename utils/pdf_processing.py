import pdfplumber
import pandas as pd
import re

# -------- 共用：清理字串 & 欄位標準化 --------
def normalize_text(x):
    """清理字串：合併多重空格、去頭去尾"""
    return "" if x is None else re.sub(r"\s+", " ", str(x)).strip()

def standardize_columns(cols):
    """
    將原始欄位名稱映射成：科目名稱 / 學分 / 成績（其餘保留）
    """
    mapping = {}
    for col in cols:
        low = normalize_text(col).lower()
        if any(k in low for k in ["科目", "課程", "名稱", "subject", "course"]):
            mapping[col] = "科目名稱"
        elif ("學分" in low) or ("credit" in low):
            mapping[col] = "學分"
        elif any(k in low for k in ["成績", "gpa", "grade"]):
            mapping[col] = "成績"
        else:
            mapping[col] = normalize_text(col)
    return mapping

# -------- 1) 表格解析（優先） --------
def _extract_tables(pdf_file) -> list[pd.DataFrame]:
    dfs = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for tb in tables:
                if not tb or len(tb) < 2:
                    continue
                df = pd.DataFrame(tb[1:], columns=tb[0])
                # 清欄名
                df.columns = [normalize_text(c) for c in df.columns]
                # 標準化欄名
                df = df.rename(columns=standardize_columns(df.columns))
                if len(df.columns) >= 2:
                    dfs.append(df)
    return dfs

# -------- 2) 純文字解析（備援） --------
# 針對東海成績單常見的行格式：
# 111 上 0272 綜合日語（一）Ｃ 3 B+
# 113 下 0307 台日交流實踐--農食育中的語言實踐 3 A-
_LINE_RE = re.compile(
    r"""
    ^\s*
    (?P<year>\d{3})\s*        # 學年度（111/112/113）
    (?P<term>[上下])\s+       # 學期 上/下
    (?P<code>\S+)\s+          # 選課代號
    (?P<name>.+?)\s+          # 科目名稱（貪婪到學分前）
    (?P<credit>\d+)\s+        # 學分（整數）
    (?P<grade>(?:[A-E][\+\-]?|通過|抵免|未通過))\s*$  # 成績
    """,
    re.VERBOSE
)

def _extract_text_rows(pdf_file) -> list[pd.DataFrame]:
    rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for raw in text.splitlines():
                line = normalize_text(raw)
                m = _LINE_RE.match(line)
                if m:
                    rows.append({
                        "學年度": f"{m.group('year')} {m.group('term')}",
                        "科目名稱": m.group("name"),
                        "學分": m.group("credit"),
                        "成績": m.group("grade"),
                    })
    if not rows:
        return []
    df = pd.DataFrame(rows, columns=["學年度", "科目名稱", "學分", "成績"])
    return [df]

# -------- 對外主函式 --------
def process_pdf_file(file) -> list[pd.DataFrame]:
    """
    回傳 DataFrame list（每頁/每表一個），欄位保證盡量有：
    - 科目名稱 / 學分 / 成績
    """
    # 先表格，表格抓不到再走純文字
    dfs = _extract_tables(file)
    if dfs:
        return dfs
    return _extract_text_rows(file)
