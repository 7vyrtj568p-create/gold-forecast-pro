import os
import requests
import streamlit as st

st.set_page_config(
    page_title="Gold Forecast Pro — ایران",
    page_icon="🪙",
    layout="wide"
)

API_URL = "https://api.oanor.com/irr-api/v1/gold"


def fmt_rial(value):
    return f"{value:,.0f} ریال"


def fmt_toman(value):
    return f"{value / 10:,.0f} تومان"


def get_api_key():
    try:
        return st.secrets["OANOR_API_KEY"]
    except Exception:
        return os.getenv("OANOR_API_KEY", "")


def fetch_market_data():
    api_key = get_api_key()

    if not api_key:
        raise RuntimeError(
            "کلید OANOR_API_KEY در Streamlit Secrets پیدا نشد."
        )

    headers = {
        "x-oanor-key": api_key,
        "Accept": "application/json",
    }

    response = requests.get(
        API_URL,
        headers=headers,
        timeout=20
    )

    if response.status_code == 401:
        raise RuntimeError("کلید API نامعتبر یا منقضی است.")

    if response.status_code == 429:
        raise RuntimeError(
            "سقف درخواست API پر شده است. کمی بعد دوباره امتحان کنید."
        )

    response.raise_for_status()

    return response.json()


def find_number(data, possible_keys):
    """
    پیدا کردن عدد در پاسخ API حتی اگر ساختار JSON تو در تو باشد.
    """

    if isinstance(data, dict):

        # اول کلیدهای مورد انتظار را بررسی می‌کنیم
        for key in possible_keys:
            if key in data:
                value = data[key]

                if isinstance(value, (int, float)):
                    return float(value)

                if isinstance(value, str):
                    try:
                        return float(
                            value.replace(",", "").replace(" ", "")
                        )
                    except Exception:
                        pass

        # سپس داخل آبجکت‌های تو در تو می‌گردیم
        for value in data.values():
            result = find_number(value, possible_keys)

            if result is not None:
                return result

    elif isinstance(data, list):

        for item in data:
            result = find_number(item, possible_keys)

            if result is not None:
                return result

    return None


def calculate_gold18(ounce_usd, usd_irr):
    """
    تبدیل اونس جهانی و دلار به ارزش بنیادی طلای ۱۸ عیار
    """

    return (
        ounce_usd
        * usd_irr
        / 31.1034768
        * 0.75
    )


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🪙 Gold Forecast Pro — ایران")

st.caption(
    "داشبورد زنده تحلیل طلای ۱۸ عیار ایران "
    "با استفاده از داده بازار"
)


# ---------------------------------------------------------
# REFRESH
# ---------------------------------------------------------

if st.button("🔄 بروزرسانی قیمت‌ها", type="primary"):
    st.cache_data.clear()
    st.rerun()


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

try:

    market = fetch_market_data()

    # نام‌های احتمالی فیلدها
    ounce = find_number(
        market,
        [
            "ounce",
            "gold_ounce",
            "global_ounce",
            "xau_usd",
            "xau",
            "ons",
            "oz"
        ]
    )

    gold18 = find_number(
        market,
        [
            "gold18",
            "gold_18",
            "gold_18k",
            "gram18",
            "18k",
            "gold_gram_18"
        ]
    )

    gold24 = find_number(
        market,
        [
            "gold24",
            "gold_24",
            "gold_24k",
            "gram24",
            "24k",
            "gold_gram_24"
        ]
    )


    # -----------------------------------------------------
    # دلار
    # -----------------------------------------------------

    usd = None

    try:

        currency_url = (
            "https://api.oanor.com/irr-api/v1/currencies"
        )

        headers = {
            "x-oanor-key": get_api_key(),
            "Accept": "application/json",
        }

        currency_response = requests.get(
            currency_url,
            headers=headers,
            timeout=20
        )

        if currency_response.ok:

            currencies = currency_response.json()

            usd = find_number(
                currencies,
                [
                    "USD",
                    "usd",
                    "usd_irr",
                    "usd_rate",
                    "dollar",
                    "dollar_rate",
                    "USDT"
                ]
            )

    except Exception:
        usd = None


    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        if ounce is not None:
            st.metric(
                "🌍 اونس جهانی",
                f"${ounce:,.2f}"
            )
        else:
            st.metric(
                "🌍 اونس جهانی",
                "دریافت نشد"
            )


    with col2:

        if usd is not None:
            st.metric(
                "💵 دلار",
                fmt_rial(usd)
            )
        else:
            st.metric(
                "💵 دلار",
                "دریافت نشد"
            )


    with col3:

        if gold18 is not None:
            st.metric(
                "🟡 طلای ۱۸ عیار",
                fmt_rial(gold18)
            )
        else:
            st.metric(
                "🟡 طلای ۱۸ عیار",
                "دریافت نشد"
            )


    # -----------------------------------------------------
    # FUNDAMENTAL VALUE
    # -----------------------------------------------------

    st.divider()

    st.header("📊 وضعیت بنیادی طلا")


    if ounce is not None and usd is not None:

        fundamental = calculate_gold18(
            ounce,
            usd
        )

        st.metric(
            "ارزش بنیادی طلای ۱۸ عیار",
            fmt_rial(fundamental),
            fmt_toman(fundamental)
        )


        if gold18 is not None and fundamental > 0:

            difference = (
                gold18 / fundamental
            ) - 1

            st.write(
                f"فاصله قیمت بازار از ارزش بنیادی: "
                f"**{difference:+.2%}**"
            )

            if difference > 0:

                st.info(
                    "قیمت بازار بالاتر از ارزش محاسباتی بنیادی است."
                )

            elif difference < 0:

                st.info(
                    "قیمت بازار پایین‌تر از ارزش محاسباتی بنیادی است."
                )

            else:

                st.info(
                    "قیمت بازار تقریباً برابر ارزش بنیادی است."
                )

    else:

        st.warning(
            "برای محاسبه ارزش بنیادی، "
            "اونس و دلار باید از API دریافت شوند."
        )


    # -----------------------------------------------------
    # GOLD 24
    # -----------------------------------------------------

    if gold24 is not None:

        st.subheader("طلای ۲۴ عیار")

        st.write(
            fmt_rial(gold24)
        )


    # -----------------------------------------------------
    # RAW DATA
    # -----------------------------------------------------

    with st.expander("🔎 مشاهده داده خام API"):

        st.json(market)


except Exception as error:

    st.error(
        f"خطا در دریافت اطلاعات بازار: {error}"
    )

    st.info(
        "بررسی کنید OANOR_API_KEY در "
        "Streamlit → Settings → Secrets "
        "ذخیره شده باشد."
    )


# ---------------------------------------------------------
# NEWS
# ---------------------------------------------------------

st.divider()

st.header("📰 موتور اخبار")

st.info(
    "اتصال خودکار اخبار در مرحله بعد اضافه می‌شود. "
    "پس از تأیید عملکرد داده‌های بازار، "
    "منابع خبری معتبر و تحلیل اثر اخبار را اضافه می‌کنیم."
)


# ---------------------------------------------------------
# DISCLAIMER
# ---------------------------------------------------------

st.caption(
    "این ابزار برای تحلیل و سناریوسازی است و "
    "قیمت آینده را تضمین نمی‌کند."
)
