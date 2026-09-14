# Format tanlash va hujjatlarni yuborish
# ---------------------------------------------------------------------------
async def choose_format_and_send(update, context):
    query = update.callback_query
    await query.answer()
    fmt = "pdf" if query.data == "fmt_pdf" else "docx"

    lang_key = context.user_data["lang_key"]
    data = context.user_data

    await query.edit_message_text(t(context, "done"))

    # MA’LUMOTNOMA va yaqin qarindoshlar ma’lumotini bitta faylga birlashtiramiz.
    try:
        path = generate("combined", lang_key, data, fmt)
    except Exception as e:
        logger.exception("Bitta hujjat yaratishda xato: %s", e)
        await context.bot.send_message(
            chat_id=query.message.chat_id, text=f"Xatolik yuz berdi: {e}"
        )
        context.user_data.clear()
        return ConversationHandler.END

    with open(path, "rb") as f:
        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=f,
            filename=os.path.basename(path),
            caption="✅ MA’LUMOTNOMA va yaqin qarindoshlar haqidagi ma’lumot",
        )
    os.remove(path)

    photo_path = context.user_data.get("photo_path")
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update, context):
    photo_path = context.user_data.get("photo_path")
    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)
    context.user_data.clear()
    await update.message.reply_text("Bekor qilindi. Qaytadan boshlash uchun /start bosing.")
    return ConversationHandler.END


TEXT_FILTER = filters.TEXT & ~filters.COMMAND


def main():
    if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        raise RuntimeError(
            "BOT_TOKEN oʻrnatilmagan! Muhit o'zgaruvchisi sifatida bering yoki "
            "bot.py faylida toʻgʻridan-toʻgʻri kiriting."
        )

    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANG: [CallbackQueryHandler(choose_lang, pattern="^lang_")],
            CHOOSING_SCRIPT: [CallbackQueryHandler(choose_script, pattern="^script_")],
            FULL_NAME: [MessageHandler(TEXT_FILTER, get_full_name)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
            BIRTH_DATE: [MessageHandler(TEXT_FILTER, get_birth_date)],
            BIRTH_PLACE: [MessageHandler(TEXT_FILTER, get_birth_place)],
            NATIONALITY: [MessageHandler(TEXT_FILTER, get_nationality)],
            EDU_LEVEL: [MessageHandler(TEXT_FILTER, get_edu_level)],
            EDU_DETAIL: [MessageHandler(TEXT_FILTER, get_edu_detail)],
            SPECIALTY: [MessageHandler(TEXT_FILTER, get_specialty)],
            ACAD_DEGREE: [MessageHandler(TEXT_FILTER, get_acad_degree)],
            ACAD_TITLE: [MessageHandler(TEXT_FILTER, get_acad_title)],
            FOREIGN_LANG: [MessageHandler(TEXT_FILTER, get_foreign_lang)],
            MILITARY_TITLE: [MessageHandler(TEXT_FILTER, get_military_title)],
            STATE_AWARDS: [MessageHandler(TEXT_FILTER, get_state_awards)],
            WORK_YEARS: [MessageHandler(TEXT_FILTER, get_work_years)],
            WORK_POSITION: [MessageHandler(TEXT_FILTER, get_work_position)],
            WORK_LOOP: [CallbackQueryHandler(work_loop_decision, pattern="^work_more_")],
            ASK_RELATIVES: [CallbackQueryHandler(ask_relatives_decision, pattern="^rel_(yes|no)$")],
            REL_RELATION: [CallbackQueryHandler(get_rel_relation, pattern="^relation_")],
            REL_NAME: [MessageHandler(TEXT_FILTER, get_rel_name)],
            REL_BIRTH: [MessageHandler(TEXT_FILTER, get_rel_birth)],
            REL_WORK: [MessageHandler(TEXT_FILTER, get_rel_work)],
            REL_ADDRESS: [MessageHandler(TEXT_FILTER, get_rel_address)],
            REL_LOOP: [CallbackQueryHandler(rel_loop_decision, pattern="^rel_more_")],
            CHOOSING_FORMAT: [CallbackQueryHandler(choose_format_and_send, pattern="^fmt_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    logger.info("Bot ishga tushdi...")

    # Render Free Web Service uchun webhook.
    # Python 3.14 da python-telegram-bot run_webhook event-loopni
    # MainThread'da aniq yaratishni talab qilishi mumkin.
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())

    port = int(os.environ.get("PORT", "10000"))
    external_url = os.environ.get("RENDER_EXTERNAL_URL")
    if external_url:
        webhook_url = external_url.rstrip("/") + "/telegram-webhook"
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="telegram-webhook",
            webhook_url=webhook_url,
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # Lokal kompyuterda ishga tushirish uchun polling.
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
