
import os, math, re
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(page_title="Gold Forecast Pro", page_icon="🪙", layout="wide")

# ---------- Helpers ----------
def gold18(ounce, usd_irr):
    return ounce * usd_irr / 31.1034768 * 0.75

def fmt_rial(x):
    return f"{x:,.0f} ریال"

def fmt_toman(x):
    return f"{x/10:,.0f} تومان"

def news_score(text):
    positive = ["جنگ","حمله","تحریم","تنش","بحران","نااطمینانی","درگیری","موشک",
                "war","attack","sanction","tension","crisis","uncertainty","conflict","missile"]
    negative = ["آتش بس","صلح","مذاکره","توافق","کاهش تنش","پایان جنگ",
                "ceasefire","peace","talks","deal","de-escalation"]
    t = str(text).lower()
    p = sum(t.count(x.lower()) for x in positive)
    n = sum(t.count(x.lower()) for x in negative)
    return 0 if p+n == 0 else max(-1, min(1, (p-n)/(p+n)))

def model(base_oz, base_usd, target_oz, target_usd, sentiment, premium):
    raw = gold18(target_oz, target_usd)
    # News has a bounded influence; it is not allowed to dominate fundamentals.
    news_adj = 1 + sentiment * 0.08
    return raw * news_adj * (1 + premium)

# ---------- Header ----------
st.title("🪙 Gold Forecast Pro — ایران")
st.caption("داشبورد تحلیلی طلای ۱۸ عیار؛ بازار، دلار، اونس و اخبار را در یک مدل سناریویی ترکیب می‌کند.")

with st.sidebar:
    st.header("ورودی بازار")
    ounce = st.number_input("اونس جهانی (USD)", 500.0, 10000.0, 4380.0, 10.0)
    usd = st.number_input("دلار آزاد (ریال)", 100000.0, 10000000.0, 2279000.0, 10000.0)
    current = st.number_input("طلای ۱۸ عیار فعلی (ریال/گرم)", 10000000.0, 1000000000.0, 233600000.0, 1000000.0)
    premium = st.slider("پریمیوم/حباب داخلی", -0.15, 0.25, 0.0, 0.005)

st.markdown("### وضعیت بنیادی فعلی")
fundamental = gold18(ounce, usd)
a,b,c,d = st.columns(4)
a.metric("ارزش بنیادی", fmt_rial(fundamental))
b.metric("قیمت بازار", fmt_rial(current))
c.metric("اختلاف", f"{(current/fundamental-1)*100:+.1f}%")
d.metric("دلار", fmt_toman(usd))

# ---------- News ----------
st.markdown("### 📰 موتور اخبار")
tab1, tab2 = st.tabs(["ورود دستی خبرها", "CSV خبرها"])

with tab1:
    news_text = st.text_area("خبرها را وارد کن؛ هر خبر در یک خط", height=180,
        placeholder="مثال: افزایش تنش در خاورمیانه...\nمثال: مذاکرات برای آتش‌بس...")
    if news_text.strip():
        items = [x.strip() for x in news_text.splitlines() if x.strip()]
        scores = [news_score(x) for x in items]
        avg = float(np.mean(scores))
        label = "صعودی" if avg > .15 else "نزولی" if avg < -.15 else "خنثی"
        st.metric("سیگنال اخبار", f"{label} ({avg:+.2f})")
        nd = pd.DataFrame({"خبر": items, "امتیاز": scores})
        st.dataframe(nd, use_container_width=True, hide_index=True)
    else:
        avg = 0.0

with tab2:
    uploaded = st.file_uploader("CSV با ستون text", type=["csv"])
    if uploaded:
        ndf = pd.read_csv(uploaded)
        if "text" not in ndf.columns:
            st.error("فایل باید ستونی به نام text داشته باشد.")
        else:
            ndf["score"] = ndf["text"].map(news_score)
            avg = float(ndf["score"].mean())
            st.dataframe(ndf, use_container_width=True, hide_index=True)

# ---------- Forecast ----------
st.markdown("### 📈 پیش‌بینی سناریویی")
st.caption("این بخش سناریو می‌سازد؛ برای پیش‌بینی آماری واقعی، باید تاریخچه چندساله قیمت و خبر به مدل آموزش داده شود.")

scenarios = {
    "نزولی": (4200, 2150000),
    "پایه": (4400, 2300000),
    "صعودی": (4800, 2700000),
}
rows = []
for name,(oz,du) in scenarios.items():
    value = model(ounce, usd, oz, du, avg, premium)
    rows.append([name, oz, du, value, (value/current-1)*100])

fdf = pd.DataFrame(rows, columns=["سناریو","اونس هدف","دلار هدف (ریال)","طلای ۱۸ (ریال/گرم)","تغییر نسبت به امروز"])
st.dataframe(fdf.style.format({
    "اونس هدف":"{:.0f}",
    "دلار هدف (ریال)":"{:,.0f}",
    "طلای ۱۸ (ریال/گرم)":"{:,.0f}",
    "تغییر نسبت به امروز":"{:+.1f}%"
}), use_container_width=True, hide_index=True)

# ---------- Custom forecast ----------
st.markdown("### 🎯 پیش‌بینی سفارشی")
x,y,z = st.columns(3)
with x:
    target_oz = st.number_input("اونس هدف", 1000.0, 10000.0, 4600.0, 25.0)
with y:
    target_usd = st.number_input("دلار هدف (ریال)", 100000.0, 20000000.0, 2600000.0, 10000.0)
with z:
    horizon = st.selectbox("افق", ["۷ روز","۳۰ روز","۶۰ روز","۹۰ روز"])

custom = model(ounce, usd, target_oz, target_usd, avg, premium)
cc1,cc2,cc3 = st.columns(3)
cc1.metric("طلای ۱۸ عیار", fmt_rial(custom))
cc2.metric("به تومان", fmt_toman(custom))
cc3.metric("تغییر", f"{(custom/current-1)*100:+.1f}%")

# ---------- Backtest upload ----------
st.markdown("### 🧪 Backtest / ارزیابی مدل")
hist = st.file_uploader("CSV اختیاری: date, ounce, usd_irr, actual_gold18", type=["csv"], key="hist")
if hist:
    h = pd.read_csv(hist)
    required = {"date","ounce","usd_irr","actual_gold18"}
    if not required.issubset(h.columns):
        st.error("ستون‌های لازم: date, ounce, usd_irr, actual_gold18")
    else:
        h["predicted"] = gold18(h["ounce"], h["usd_irr"])
        h["error_pct"] = (h["predicted"]/h["actual_gold18"]-1)*100
        mae = h["error_pct"].abs().mean()
        rmse = math.sqrt(np.mean(h["error_pct"]**2))
        q1,q2 = st.columns(2)
        q1.metric("MAE درصدی", f"{mae:.2f}%")
        q2.metric("RMSE درصدی", f"{rmse:.2f}%")
        st.line_chart(h.set_index("date")[["actual_gold18","predicted"]])

# ---------- Architecture ----------
with st.expander("⚙️ اتصال خودکار داده‌ها در نسخه تولیدی"):
    st.markdown("""
برای نسخه آنلاین واقعی، این داشبورد باید به APIهای مجاز متصل شود:
- XAU/USD و USD/IRR
- طلای ۱۸ عیار ایران
- اخبار دارای مجوز (مثلاً Reuters/LSEG یا سایر تأمین‌کنندگان مجاز)
- ذخیره تاریخچه در PostgreSQL
- زمان‌بندی دریافت داده با worker
- مدل ML با walk-forward validation

کلیدهای API را داخل کد قرار نده؛ از environment variables یا secrets استفاده کن.
""")

st.warning("خروجی این برنامه برآورد سناریویی است و توصیه خرید یا فروش نیست. در شوک‌های جنگی، خطای مدل می‌تواند به‌طور محسوسی افزایش یابد.")
