# Obyektivka (Ma'lumotnoma) Telegram Bot

Foydalanuvchidan ma'lumot yig'ib, rasmiy **MA'LUMOTNOMA** namunasiga (2025-yilgi
shakl) mos tarzda tayyor obyektivka hujjatini `.docx` va `.pdf` formatlarida
generatsiya qiluvchi Telegram bot.

> **Muhim:** bot faqat "obyektivka to'ldiruvchi" (asosiy shaxs) haqidagi bo'limni
> to'ldiradi. Namunadagi "yaqin qarindoshlari haqida" bo'limi (alohida sahifadagi
> jadval) ushbu botga kiritilmagan.
>
> Barcha band nomlari (label) namuna faylidan dasturiy nusxa ko'chirish orqali
> olingan (`labels.py`) — imlo xatolarining oldini olish uchun.

## Til va yozuv tanlash

Bot ishga tushganda foydalanuvchidan avval hujjat tili so'raladi:

- **O'zbekcha** tanlansa — keyin yozuv turi so'raladi: **Kirilcha** yoki **Lotincha**.
  Foydalanuvchi javoblarni istagan yozuvda kiritishi mumkin (aralash holda ham) —
  bot ularni tanlangan yozuvga avtomatik moslab (`uz_translit.py` orqali) saqlaydi.
- **Ruscha** tanlansa — hujjat band nomlari ruscha chiqadi, lekin foydalanuvchi
  javoblarni o'zi ruscha kiritishi kerak (avtomatik tarjima amalga oshirilmaydi,
  faqat lotin/kirill orasidagi yozuv konvertatsiyasi qo'llab-quvvatlanadi).

Avtomatik lotin/kirill konvertatsiyasi juda yaxshi natija beradi, lekin 100%
kafolatlanmaydi (ayniqsa noodatiy familiyalarda) — shuning uchun bot foydalanuvchini
tayyor hujjatni tekshirib chiqishga chaqiradi.

## O'rnatish

1. Kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

2. PDF konvertatsiyasi uchun serveringizda **LibreOffice** o'rnatilgan bo'lishi kerak:
   ```bash
   sudo apt-get update && sudo apt-get install -y libreoffice
   ```
   (LibreOffice bo'lmasa ham bot ishlayveradi, faqat foydalanuvchiga faqat `.docx`
   fayl yuboriladi, `.pdf` yuborilmaydi.)

3. Loyiha papkasida `.env` fayl yarating va botingiz tokenini kiriting
   (tokenni [@BotFather](https://t.me/BotFather) dan olasiz):
   ```
   BOT_TOKEN=1234567890:AAExampleTokenHere
   ```

## Ishga tushirish

```bash
python bot.py
```

## Ishlash tartibi

1. Foydalanuvchi `/start` bosadi.
2. **Surat** — 3x4 profil surati so'raladi (ixtiyoriy; bo'lmasa namunadagi kabi
   izohli bo'sh joy qoldiriladi).
3. Bot namunadagi barcha bandlar bo'yicha ketma-ket so'raydi: F.I.Sh., hozirgi
   lavozim va sana, tug'ilgan yili/joyi, millati, partiyaviyligi, ma'lumoti,
   tamomlagan OTM, mutaxassisligi, ilmiy darajasi/unvoni, chet tillari, harbiy
   unvoni, davlat/idoraviy mukofotlar, saylanadigan organlarga a'zoligi.
   Ixtiyoriy bandlarda "Yo'q / o'tkazib yuborish" tugmasi bor.
4. **Mehnat faoliyati** — foydalanuvchi talaba yillaridan boshlab bir nechta
   yozuvni ketma-ket kiritadi ("➕ Yana qo'shish" / "✅ Tugatish" tugmalari orqali).
5. Izoh (ixtiyoriy).
6. Bot barcha ma'lumotlar asosida `.docx` va `.pdf` fayllarni yaratib, foydalanuvchiga
   yuboradi.

Jarayonni istalgan vaqtda `/cancel` bilan bekor qilish mumkin.

## Fayllar tuzilishi

- `bot.py` — asosiy bot fayli (barcha handlerlar)
- `states.py` — suhbat bosqichlari (FSM states)
- `doc_generator.py` — `.docx` yaratish va `.pdf` ga aylantirish logikasi
  (namunaga mos jadval tuzilishi, shrift, sahifa chegaralari)
- `labels.py` — namuna fayldan dasturiy nusxa ko'chirilgan aniq Kirill
  band nomlari (imlo xatosi bo'lmasligi uchun)
- `requirements.txt` — kerakli kutubxonalar

## Kengaytirish g'oyalari

- "Yaqin qarindoshlari haqida" bo'limini alohida modul sifatida qo'shish.
- Ma'lumotlarni bazaga saqlash (masalan, SQLite) — foydalanuvchi keyinroq
  qayta tahrirlashi uchun.
