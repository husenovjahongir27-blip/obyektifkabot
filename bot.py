    relatives.append(current)
    await state.update_data(relatives=relatives, current_relative={})

    variant = await _variant(state)
    await say(
        message, state,
        "Яна бир қариндош қўшасизми?",
        reply_markup=more_or_done_kb(variant),
    )
    await state.set_state(ObyektivkaForm.relative_more)


@dp.callback_query(ObyektivkaForm.relative_more, F.data == "more")
async def relative_more(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_relative_relation(callback.message, state, first=False)
    await callback.answer()


@dp.callback_query(ObyektivkaForm.relative_more, F.data == "done")
async def relative_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await generate_and_send(callback.message, state)
    await callback.answer()


# ---------- Hujjatni yaratish va yuborish ----------

async def generate_and_send(message: Message, state: FSMContext, bot: Bot | None = None):
    data = await state.get_data()
    await say(message, state, "Ҳужжат тайёрланмоқда, бироз кутинг...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        safe_name = "".join(
            c for c in data.get("full_name", "malumotnoma") if c.isalnum() or c in " _-"
        ).strip()
        safe_name = safe_name.replace(" ", "_") or "malumotnoma"

        photo_path = None
        photo_file_id = data.get("photo_file_id")
        if photo_file_id:
            bot_instance = bot or message.bot
            photo_path = os.path.join(tmp_dir, "photo.jpg")
            await bot_instance.download(photo_file_id, destination=photo_path)

        docx_path = os.path.join(tmp_dir, f"{safe_name}.docx")
        generate_malumotnoma_docx(data, docx_path, photo_path=photo_path,
                                    lang_variant=_lang_variant(data))

        with open(docx_path, "rb") as f:
            docx_bytes = f.read()
        try:
            await db.log_document(
                message.chat.id, data.get("full_name", "-"), "docx",
                os.path.basename(docx_path), docx_bytes,
            )
        except Exception:
            logging.exception("DB xatosi: log_document (docx)")

        await message.answer_document(FSInputFile(docx_path))

        pdf_path = convert_docx_to_pdf(docx_path, tmp_dir)
        if pdf_path:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            try:
                await db.log_document(
                    message.chat.id, data.get("full_name", "-"), "pdf",
                    os.path.basename(pdf_path), pdf_bytes,
                )
            except Exception:
                logging.exception("DB xatosi: log_document (pdf)")
            await message.answer_document(FSInputFile(pdf_path))
        else:
            await say(
                message, state,
                "PDF версиясини тайёрлаб бўлмади (серверда LibreOffice топилмади), "
                "лекин Word (.docx) файли тайёр.",
            )

    await say(
        message, state,
        "Маълумотнома тайёр! Юқоридаги файл(лар)ни очиб юклаб олишингиз мумкин. "
        "Янгисини яратиш учун \"🟢 Yangi ob'ektivka\" тугмасини босинг.",
        reply_markup=main_menu_kb(),
    )
    await state.clear()


async def _health(request):
    return web.Response(text="OK")


async def start_web_server():
    """Render 'Web Service' $PORT ni tinglashni talab qiladi — aks holda
    deploy 'Timed Out' bo'lib, eski jarayon bilan yangisi bir vaqtda
    ishga tushib, Telegram 'Conflict' xatosiga olib keladi. Shu sabab
    polling bilan bir qatorda mayda HTTP server ham ishga tushiriladi."""
    app = web.Application()
    app.router.add_get("/", _health)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Health-check HTTP server {port}-portda ishga tushdi")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN топилмади. Лойиҳа папкасида .env файл яратинг ва "
            "ичига BOT_TOKEN=... деб ёзинг (токенни @BotFather дан олинг)."
        )

    try:
        await db.init_db()
    except Exception:
        logging.exception("DB xatosi: init_db")

    bot = Bot(token=BOT_TOKEN)
    # Agar avval botga webhook o'rnatilgan bo'lsa, uni o'chirish shart —
    # aks holda getUpdates (polling) bilan "Conflict" xatosi chiqadi.
    await bot.delete_webhook(drop_pending_updates=True)
    await start_web_server()
    await dp.start_polling(bot)

