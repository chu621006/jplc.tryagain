# utils/grade_analysis.py
import re
import pandas as pd

# ---------- 文字正規化 ----------
def _normalize_name(name: str) -> str:
    """移除各種括號內容／學期字樣／標點與空白，做 startswith 比對用"""
    s = str(name or "")
    s = re.sub(r'（.*?）|\(.*?\)|〈.*?〉|【.*?】', '', s)  # 括號與內容
    s = re.sub(r'上學期|下學期', '', s)
    s = re.sub(r'[：:、，,。．\.\-/／—–\s]+', '', s)      # 標點與空白
    return s.strip()

# ---------- 成績是否通過 ----------
def is_passing_gpa(gpa: str) -> bool:
    """C- 以上、通過、抵免都算通過"""
    return bool(re.search(r'抵免|通過|[ABC][\+\-]?|C-', str(gpa)))

# ---------- 課名字典 ----------
# 必修（含通識、AI、英文、體育等；以及你們列的系上必修）
_REQ_LIST = [
    "綜合日語", "專題研究", "多元文化導論", "表象文化概論",
    "語言溝通概論", "社會文化概論", "日語語法",
    "中文：文學欣賞與實用", "大一英文", "大二英文",
    "AI思維與程式設計", "全民國防教育", "大一體育", "大二體育",
]

# 一類選修（含你補充的舊名／同義名；社會與企業在此）
_I_LIST = [
    "日語語音學演練", "日語討論與表達", "日語新聞聽解", "日劇聽解",
    "專題論證寫作", "學習方法論", "日語戲劇實踐", "類義表現",
    "台日社會語言分析", "多元文化社會與語言", "華日語言對比分析",
    "中日語言對比分析", "辭典學日語", "日語分科教學法",
    "日本資訊傳播導論", "媒體素養論", "歷史與敘事", "台日區域專題",
    "不可思議的日本", "台日報導製作", "台日報導實踐", "台日報導寫作",
    "日本古代中世史", "日本史", "日本近世近代史",
    "台日交流實踐-農食育中的語言實踐",
    "社會與企業",  # ← 這科容易被誤判成通識，放在 I 類優先匹配
]

# 二類選修
_II_LIST = [
    "華日翻譯", "翻譯-中翻日", "日語口譯入門", "日語口譯實務",
    "職場日語", "商務日語",
    "日本上古中古表象文化論", "日本古典表象文化論", "日本中世近世表象文化論",
    "日語專書導讀", "日語精讀與專書探討",
    "日本近代表象文化論", "日本現代表象文化論",
    "日本殖民時期台灣日語文學", "現代台灣日語文學",
    "文化與敘事", "越境文化論", "跨文化敘事",
    "日本國際關係", "行走·探索·思考-台灣裡的東亞",
]

_REQ_SET = {_normalize_name(x) for x in _REQ_LIST}
_I_SET   = {_normalize_name(x) for x in _I_LIST}
_II_SET  = {_normalize_name(x) for x in _II_LIST}

# ---------- 安全取值/選欄 ----------
def _pick(row: pd.Series, col: str, default=""):
    """
    從 row 取欄位值，確保回傳純量：
    - 若為 Series（同名欄位造成），取第一個非空
    - 若不存在或為 NaN，回 default
    """
    if col is None or col not in row.index:
        return default
    v = row[col]
    if isinstance(v, pd.Series):
        v = v.dropna()
        if len(v) > 0:
            return v.astype(str).iloc[0]
        return default
    return v if pd.notna(v) else default

def _find_col(df: pd.DataFrame, prefer_keywords: list[str], fallback_index: int | None = None):
    """
    在 df.columns 中尋找包含 prefer_keywords 的欄位（不分大小寫）。
    找不到就用 fallback_index（若給且存在）；仍找不到回 None。
    """
    cols = list(df.columns)
    lowered = [str(c).strip().lower() for c in cols]

    for i, low in enumerate(lowered):
        if any(k in low for k in prefer_keywords):
            return cols[i]

    if fallback_index is not None and -len(cols) <= fallback_index < len(cols):
        return cols[fallback_index]

    return None

# ---------- 課程分類 ----------
def categorize_course(name: str) -> str:
    raw = str(name or "").strip()
    base = _normalize_name(raw)

    # 1) 先比對明確字典（避免被通識前綴吃掉，例如「社會與企業」）
    if any(base.startswith(tok) for tok in _REQ_SET):
        return "Required"
    if any(base.startswith(tok) for tok in _I_SET):
        return "I"
    if any(base.startswith(tok) for tok in _II_SET):
        return "II"

    # 2) 再判斷通識：必須是「人文/社會/自然 + 分隔符」
    if re.match(r'^\s*(人文|社會|自然)\s*[:：／/\-－]', raw):
        return "Required"

    return "Other"

# ---------- 主計算 ----------
def calculate_total_credits(df_list: list[pd.DataFrame]) -> dict:
    total_credits = required_credits = i_credits = ii_credits = other_credits = 0.0
    passed_all, failed_all = [], []
    passed_req, passed_i, passed_ii, passed_other = [], [], [], []

    for df in df_list:
        if df is None or df.empty or len(df.columns) == 0:
            continue

        # 安全挑欄位（找不到學分/成績時為 None，不會爆）
        name_col   = _find_col(df, ["科目", "課程", "名稱", "subject", "course"], fallback_index=0)
        credit_col = _find_col(df, ["學分", "credit"], fallback_index=None)
        grade_col  = _find_col(df, ["成績", "gpa", "grade"], fallback_index=None)

        for _, row in df.iterrows():
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
        "total":          total_credits,
        "required":       required_credits,
        "i_elective":     i_credits,
        "ii_elective":    ii_credits,
        "other_elective": other_credits,
        "passed":         passed_all,
        "failed":         failed_all,
        "passed_required": passed_req,
        "passed_i":        passed_i,
        "passed_ii":       passed_ii,
        "passed_other":    passed_other,
    }
