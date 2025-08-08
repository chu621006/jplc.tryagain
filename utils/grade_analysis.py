# utils/grade_analysis.py
import re
import pandas as pd

def _normalize_name(name: str) -> str:
    s = str(name or "")
    s = re.sub(r'（.*?）|\(.*?\)|〈.*?〉|【.*?】', '', s)
    s = re.sub(r'上學期|下學期', '', s)
    s = re.sub(r'[：:、，,。．\.\-/／—–\s]+', '', s)
    return s.strip()

def is_passing_gpa(gpa: str) -> bool:
    return bool(re.search(r'抵免|通過|[ABC][\+\-]?|C-', str(gpa)))

_REQ_LIST = [
    "綜合日語","專題研究","多元文化導論","表象文化概論",
    "語言溝通概論","社會文化概論","日語語法",
    "中文：文學欣賞與實用","大一英文","大二英文",
    "AI思維與程式設計","全民國防教育","大一體育","大二體育"
]
_I_LIST = [
    "日語語音學演練","日語討論與表達","日語新聞聽解","日劇聽解",
    "專題論證寫作","學習方法論","日語戲劇實踐","類義表現",
    "台日社會語言分析","多元文化社會與語言","華日語言對比分析",
    "中日語言對比分析","辭典學日語","日語分科教學法",
    "日本資訊傳播導論","媒體素養論","歷史與敘事","台日區域專題",
    "不可思議的日本","台日報導製作","台日報導實踐","台日報導寫作",
    "日本古代中世史","日本史","日本近世近代史",
    "台日交流實踐-農食育中的語言實踐","社會與企業"
]
_II_LIST = [
    "華日翻譯","翻譯-中翻日","日語口譯入門","日語口譯實務",
    "職場日語","商務日語","日本上古中古表象文化論","日本古典表象文化論",
    "日本中世近世表象文化論","日語專書導讀","日語精讀與專書探討",
    "日本近代表象文化論","日本現代表象文化論","日本殖民時期台灣日語文學",
    "現代台灣日語文學","文化與敘事","越境文化論","跨文化敘事",
    "日本國際關係","行走·探索·思考-台灣裡的東亞"
]
_REQ_SET = {_normalize_name(x) for x in _REQ_LIST}
_I_SET   = {_normalize_name(x) for x in _I_LIST}
_II_SET  = {_normalize_name(x) for x in _II_LIST}

def categorize_course(name: str) -> str:
    raw = str(name or "").strip()
    base = _normalize_name(raw)
    # 先比明確字典
    if any(base.startswith(tok) for tok in _REQ_SET): return "Required"
    if any(base.startswith(tok) for tok in _I_SET):   return "I"
    if any(base.startswith(tok) for tok in _II_SET):  return "II"
    # 再判斷通識：前綴 + 分隔符
    if re.match(r'^\s*(人文|社會|自然)\s*[:：／/\-－]', raw): return "Required"
    return "Other"

def calculate_total_credits(df_list: list[pd.DataFrame]) -> dict:
    total=req=i_cr=ii_cr=other=0.0
    passed_all, failed_all = [], []
    passed_req, passed_i, passed_ii, passed_other = [], [], [], []

    for df in df_list:
        name_col   = "科目名稱" if "科目名稱" in df.columns else ( "課程名稱" if "課程名稱" in df.columns else df.columns[0] )
        credit_col = "學分"     if "學分"     in df.columns else ( "credit" if "credit" in df.columns else df.columns[-2] )
        grade_col  = "成績"     if "成績"     in df.columns else ( "GPA"    if "GPA"    in df.columns else df.columns[-1] )

        for _, row in df.iterrows():
            name = row.get(name_col, "")
            try: credit = float(row.get(credit_col, 0) or 0)
            except Exception: credit = 0.0
            gpa  = row.get(grade_col, "")

            if is_passing_gpa(gpa):
                item = {"科目名稱": name, "學分": credit, "成績": gpa}
                passed_all.append(item); total += credit
                cat = categorize_course(name)
                if   cat=="Required": req   += credit; passed_req.append(item)
                elif cat=="I":        i_cr += credit; passed_i.append(item)
                elif cat=="II":       ii_cr+= credit; passed_ii.append(item)
                else:                 other+= credit; passed_other.append(item)
            else:
                failed_all.append({"科目名稱": name, "學分": credit, "成績": gpa})

    return {
        "total": total, "required": req,
        "i_elective": i_cr, "ii_elective": ii_cr, "other_elective": other,
        "passed": passed_all, "failed": failed_all,
        "passed_required": passed_req, "passed_i": passed_i,
        "passed_ii": passed_ii, "passed_other": passed_other
    }
