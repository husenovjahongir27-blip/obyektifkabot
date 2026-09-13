# MA'LUMOTNOMA Telegram Bot

Kadrlar bo'limi standartidagi **MA'LUMOTNOMA** (F.I.Sh., tug'ilgan yili/joyi, ma'lumoti,
mehnat faoliyati va h.k.) hamda ixtiyoriy ravishda **yaqin qarindoshlari to'g'risida
ma'lumot** (jadval) hujjatlarini tayyorlab beruvchi Telegram bot.

## Imkoniyatlari
- Til: **O'zbekcha (Lotin / Kirill)** yoki **Ruscha**
- To'liq MA'LUMOTNOMA maydonlari: F.I.Sh., tug'ilgan yili, tug'ilgan joyi, millati,
  ma'lumoti, o'quv yurti, mutaxassisligi, ilmiy daraja/unvon, chet tillari,
  harbiy unvon, davlat mukofotlari
- **Mehnat faoliyati** — istalgancha band qo'shish mumkin (yillar + lavozim)
- **Yaqin qarindoshlari to'g'risida ma'lumot** — ixtiyoriy, jadval ko'rinishida
  (Otasi/Onasi/Akasi/Opasi va h.k., istalgancha kishi qo'shiladi)
- Chiqish formati: **PDF** yoki **DOCX (Word)**
- Ikkala hujjat ham namunadagi kabi — sarlavha, ikki ustunli maydonlar, jadval

## O'rnatish

### 1. Bot yaratish
[@BotFather](https://t.me/BotFather) orqali `/newbot` bilan bot yarating va
tokenni saqlab qo'ying.

### 2. Muhitni tayyorlash
```bash
cd obyektifka_bot
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Shriftlar
`fonts/DejaVuSans.ttf` va `fonts/DejaVuSans-Bold.ttf` fayllari **loyihaga allaqachon
qo'shilgan** — PDF darhol ishlaydi (lotin va kirill harflari to'g'ri chiqadi).
Agar boshqa shrift bilan almashtirmoqchi bo'lsangiz, xuddi shu nomlar bilan
`fonts/` papkasiga qo'ying.

### 4. Tokenni kiritish
```bash
export BOT_TOKEN="123456789:AA...sizning_tokeningiz"
```
Yoki `bot.py` faylidagi `BOT_TOKEN` qatoriga yozing (kod bilan hech kimga
ulashmang).

### 5. GitHub va hostingga joylash

### GitHub
1. GitHub'da yangi **Private** yoki **Public** repository yarating.
2. Shu loyiha fayllarini repository'ga yuklang.
3. **BOT_TOKEN ni GitHub kodiga yozmang**. Tokenni faqat hostingdagi Environment Variable/Secret sifatida kiriting.

### Render orqali 24/7 ishga tushirish
1. Render'da GitHub repository'ni ulang.
2. Service turini **Background Worker** qilib tanlang.
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. Environment Variable qo'shing: `BOT_TOKEN` = BotFather bergan token.
6. Deploy qiling. Loglarda `Bot ishga tushdi...` chiqsa, Telegram'da `/start` yuboring.

> Eslatma: Telegram bot polling ishlatayotgani uchun doimiy ishlaydigan worker/server kerak. Oddiy GitHub repository botni o'zi 24/7 ishga tushirib bermaydi.

## 6. Ishga tushirish
```bash
python bot.py
```

Serverda doimiy ishlashi uchun `systemd`, `pm2`, `screen`/`tmux` yoki Docker
orqali fon jarayoni sifatida ishga tushiring.

## Suhbat oqimi
1. Til va (agar o'zbekcha bo'lsa) alifbo tanlanadi
2. Shaxsiy maydonlar ketma-ket so'raladi (F.I.Sh. dan davlat mukofotlarigacha)
3. **Mehnat faoliyati**: yillar → lavozim, so'ng "Yana qo'shamizmi?" — istalgancha
   band qo'shish mumkin
4. **Qarindoshlar** (ixtiyoriy): "Ha" desa — qarindoshlik turi (tugma orqali) →
   F.I.Sh. → tug'ilgan yili/joyi → ish joyi/lavozimi → turar joyi, so'ng
   "Yana qo'shamizmi?"
5. Format tanlanadi (PDF/DOCX) va tayyor fayl(lar) yuboriladi — agar qarindosh
   qo'shilgan bo'lsa, ikkinchi fayl alohida yuboriladi

## Loyiha tuzilishi
```
obyektifka_bot/
├── bot.py            # Telegram bot logikasi (ConversationHandler)
├── generator.py       # PDF/DOCX fayl yaratish (docx jadvallar, reportlab platypus)
├── labels.py           # Uch tildagi (uz-latin, uz-kirill, ru) yorliqlar va savollar
├── fonts/              # PDF uchun shriftlar (DejaVuSans, tayyor holda qo'shilgan)
├── output/             # Vaqtinchalik yaratilgan fayllar (yuborilgach o'chiriladi)
├── requirements.txt
└── README.md
```

## Hujjat ko'rinishini o'zgartirish
- Maydon nomlari / savollarni o'zgartirish uchun `labels.py` dagi `LABELS` va
  `PROMPTS` lug'atlarini tahrirlang.
- Jadval kengliklari, shrift o'lchamlari, chegaralar (borders) kabi vizual
  detallar `generator.py` da — funksiyalar yaxshi izohlangan.
- Qarindoshlik turlari ro'yxatini (`Otasi`, `Onasi`, ...) `labels.py` dagi
  `RELATION_OPTIONS` orqali boshqarasiz.

## Eslatma
- Kiritilgan ma'lumotlar hech qayerda saqlanmaydi — fayl yuborilgach `output/`
  papkasidan darhol o'chiriladi.
- Bu shablon rasmiy blank emas, balki tarkibi va formati namunaga mos matnli
  hujjat. Rasmiy tashkilot rekvizitlari (shtamp, MFO va h.k.) kerak bo'lsa,
  `generator.py` ga qo'shimcha qilish mumkin.
