
# Gold Forecast Pro

## اجرا
```bash
pip install -r requirements.txt
streamlit run app.py
```

## CSV خبر
یک فایل با ستون `text` بساز:
```csv
text
افزایش تنش در خاورمیانه
مذاکرات برای آتش بس
```

## CSV بک‌تست
ستون‌های لازم:
`date,ounce,usd_irr,actual_gold18`

این نسخه «MVP حرفه‌ای» است: داده‌ها را می‌توان دستی/CSV وارد کرد و مدل سناریویی، سیگنال اخبار و بک‌تست پایه دارد.

### برای نسخه Production
- اتصال API بازار
- News API مجاز
- دیتابیس
- مدل ML (LightGBM/XGBoost)
- walk-forward validation
- ثبت پیش‌بینی‌های روزانه و محاسبه خطا
- هشدار تلگرام/ایمیل
