# Creator Toolkit — أدوات نمو حسابك على تيك توك (بدون الاعتماد على «الترويج» المدفوع)

مشروع بايثون بواجهة سطر أوامر يعمل على Kali وTermux، ويستخدم **الواجهات الرسمية فقط** لتيك توك ويوتيوب وإنستغرام.

| الأداة | الأمر |
|---|---|
| مزامنة إحصائيات حسابك | `python -m toolkit sync` |
| تقرير النمو + أفضل فيديوهاتك للترويج | `python -m toolkit report` |
| تسجيل حملات الترويج وحساب تكلفة المتابع/الألف مشاهدة | `python -m toolkit promo add / list` |
| أداء الهاشتاقات | `python -m toolkit hashtags` |
| أفضل ساعات وأيام النشر | `python -m toolkit besttime` |
| جدولة نشر على تيك توك + شورتس + ريلز | `python -m toolkit queue add / list / retry / cancel` |
| تشغيل المجدول | `python -m toolkit run` (أو `run --once` مع cron) |

## التثبيت

```bash
# Termux: pkg install python   |  Kali: sudo apt install python3-pip
pip install -r requirements.txt
cp .env.example .env      # ثم املأ القيم
```

## إعداد كل منصة

### 1) تيك توك
1. أنشئ تطبيقًا في https://developers.tiktok.com وأضف المنتجات: **Login Kit** و**Display API** و**Content Posting API**.
2. سجّل Redirect URI بصيغة https (أي صفحة تملكها، مثل موقع على GitHub Pages أو Vercel؛ لا يهم أن تكون الصفحة فارغة).
3. ضع `TIKTOK_CLIENT_KEY` و`TIKTOK_CLIENT_SECRET` و`TIKTOK_REDIRECT_URI` في `.env`.
4. نفّذ `python -m toolkit auth tiktok`، افتح الرابط ووافق، ثم الصق عنوان الصفحة التي تحوّلك إليها (يحتوي `code=...`).

**قيود مهمة**
- التطبيقات غير المدقَّقة (unaudited) تنشر **بخصوصية SELF_ONLY فقط**. بعد أن تجتاز TikTok تدقيق تطبيقك غيّر `TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE`.
- للتجربة قبل التدقيق: `TIKTOK_MODE=inbox` يرفع الفيديو كمسودة في تطبيق تيك توك وتنشره أنت بضغطة واحدة.
- أرقام حملات «الترويج» (الإنفاق والنتائج) **لا تتوفر عبر API**، لذلك تسجلها بنفسك بأمر `promo add` (10 ثوانٍ لكل حملة).

### 2) يوتيوب شورتس
1. في Google Cloud Console فعّل **YouTube Data API v3** وأنشئ OAuth Client من نوع **Desktop app**، ونزّل الملف باسم `client_secret.json`.
2. `python -m toolkit auth youtube` ثم افتح الرابط المطبوع في المتصفح (على Termux يعمل من نفس الهاتف).
3. مشاريع API غير المدقَّقة تُجبر الفيديوهات على **private**؛ اطلب التدقيق من Google ثم اضبط `YT_PRIVACY=public`.
4. الفيديو يجب أن يكون عموديًا وأقل من 3 دقائق ليُصنَّف Shorts (الأداة تضيف #Shorts تلقائيًا).

### 3) إنستغرام ريلز
1. حساب **Business أو Creator** مرتبط بصفحة فيسبوك، وتطبيق في https://developers.facebook.com.
2. احصل على `IG_USER_ID` وتوكن طويل الأمد (60 يومًا، جدده قبل انتهائه) بصلاحية `instagram_content_publish`.
3. الرفع يتم مباشرة من ملفك (resumable upload) فلا تحتاج رابطًا عامًا. حدّث `IG_API_VERSION` إن أوقفت ميتا النسخة القديمة.

## مثال استخدام يومي

```bash
python -m toolkit sync
python -m toolkit report

# سجّل حملة ترويج دفعت لها (الأرقام من صفحة «تفاصيل الطلب»)
python -m toolkit promo add --spend 1.8 --goal followers --views 3218 --followers 41 --likes 24

# جدولة فيديو على المنصات الثلاث
python -m toolkit queue add --file clip.mp4 --caption "وصف الفيديو #عمان #غناء_صوتي" \
    --at "2026-10-02 20:30" --platforms tiktok,youtube,instagram
python -m toolkit run            # اتركه يعمل، أو: */5 * * * * python -m toolkit run --once
```

إذا فشلت منصة واحدة يُحفظ الخطأ وتُكمل البقية، ثم `queue retry ID` يعيد **المنصة الفاشلة فقط** دون تكرار النشر على الباقي.

## أين تُحفظ البيانات؟
في `~/.creator_toolkit/` (قاعدة SQLite + التوكنات بصلاحية 600). لا تشارك هذا المجلد ولا ملف `.env`.

## Public app pages

GitHub Pages is enabled for this repository:

- Landing page: https://openaziz00-sudo.github.io/creator_toolkit/
- Terms of Service: https://openaziz00-sudo.github.io/creator_toolkit/terms.html
- Privacy Policy: https://openaziz00-sudo.github.io/creator_toolkit/privacy.html
- Integration demo: https://openaziz00-sudo.github.io/creator_toolkit/demo.html

The repository also includes `assets/icon.png` (1024×1024) for developer-portal app registration and `demo.mp4` as a clearly labelled development preview. Before submitting a production review, replace the preview with a recording of the actual TikTok sandbox flow and select only products/scopes demonstrated in that recording.
