async def process_elected_member(message: Message, state: FSMContext):
    await state.update_data(elected_member=await normalize_input(state, message.text.strip()))
    await ask_work_entry(message, state)


@dp.callback_query(ObyektivkaForm.elected_member, F.data == "skip")
async def skip_elected_member(callback: CallbackQuery, state: FSMContext):
    await state.update_data(elected_member=await skip_default(state))
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_work_entry(callback.message, state)
    await callback.answer()


async def ask_work_entry(message: Message, state: FSMContext):
    await say(
        message, state,
        "Энди МЕҲНАТ ФАОЛИЯТИНГИЗ ҳақида, талаба йилларингиздан бошлаб, "
        "хронологик тартибда киритинг.\n"
        "Бир ёзувни қуйидаги тартибда юборинг:\n"
        "<йиллар> йй. - <лавозим/ташкилот>\n\n"
        "Масалан: 1998-2004 йй. - Тошкент давлат университети талабаси"
    )
    await state.set_state(ObyektivkaForm.work_entry)


@dp.message(ObyektivkaForm.work_entry)
async def process_work_entry(message: Message, state: FSMContext):
    data = await state.get_data()
    work_history = data.get("work_history", [])
    work_history.append(await normalize_input(state, message.text.strip()))
    await state.update_data(work_history=work_history)

    variant = await _variant(state)
    await say(
        message, state,
        "Яна бир иш/лавозим ёзувини қўшасизми?",
        reply_markup=more_or_done_kb(variant),
    )
    await state.set_state(ObyektivkaForm.work_entry_more)


@dp.callback_query(ObyektivkaForm.work_entry_more, F.data == "more")
async def work_entry_more(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await say(callback.message, state, "Яна бир ёзувни киритинг (йиллар йй. - лавозим/ташкилот):")
    await state.set_state(ObyektivkaForm.work_entry)
    await callback.answer()


@dp.callback_query(ObyektivkaForm.work_entry_more, F.data == "done")
async def work_entry_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await ask_relative_relation(callback.message, state, first=True)
    await callback.answer()


# ---------- Yaqin qarindoshlari haqida (2-sahifa uchun) ----------

async def ask_relative_relation(message: Message, state: FSMContext, first: bool = False):
    variant = await _variant(state)
    if first:
        text = (
            "Энди яқин қариндошларингиз (отаси, онаси, турмуш ўртоғи, "
            "фарзандлари, ака-ука, опа-сингиллари ва ҳ.к.) ҳақида маълумот "
            "киритамиз.\n\n"
            "Аввало, қариндошлик даражасини киритинг (масалан: Отаси):"
        )
        await say(message, state, text, reply_markup=skip_kb(variant, "Киритмайман / ўтказиб юбориш"))
    else:
        await say(message, state, "Қариндошлик даражасини киритинг (масалан: Онаси):")
    await state.set_state(ObyektivkaForm.relative_relation)


@dp.callback_query(ObyektivkaForm.relative_relation, F.data == "skip")
async def skip_relatives_entirely(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await generate_and_send(callback.message, state)
    await callback.answer()


@dp.message(ObyektivkaForm.relative_relation)
async def process_relative_relation(message: Message, state: FSMContext):
    await state.update_data(
        current_relative={"relation": await normalize_input(state, message.text.strip())}
    )
    await say(message, state, "Ф.И.Ш.ини (фамилияси, исми ва отасининг исми) тўлиқ киритинг:")
    await state.set_state(ObyektivkaForm.relative_name)


@dp.message(ObyektivkaForm.relative_name)
async def process_relative_name(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_relative", {})
    current["full_name"] = await normalize_input(state, message.text.strip())
    await state.update_data(current_relative=current)
    await say(
        message, state,
        "Туғилган йили ва жойини киритинг.\nМасалан: 1959 йил, Қибрай тумани"
    )
    await state.set_state(ObyektivkaForm.relative_birth)


@dp.message(ObyektivkaForm.relative_birth)
async def process_relative_birth(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_relative", {})
    current["birth_info"] = await normalize_input(state, message.text.strip())
    await state.update_data(current_relative=current)
    await say(
        message, state,
        "Иш жойи ва лавозимини киритинг.\n"
        "Масалан: Тошкент тиббиёт коллежи ўқитувчиси ёки Пенсияда"
    )
    await state.set_state(ObyektivkaForm.relative_job)


@dp.message(ObyektivkaForm.relative_job)
async def process_relative_job(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_relative", {})
    current["job_info"] = await normalize_input(state, message.text.strip())
    await state.update_data(current_relative=current)
    await say(message, state, "Турар жойини (манзилини) киритинг:")
    await state.set_state(ObyektivkaForm.relative_address)


@dp.message(ObyektivkaForm.relative_address)
async def process_relative_address(message: Message, state: FSMContext):
    data = await state.get_data()
    current = data.get("current_relative", {})
    current["address"] = await normalize_input(state, message.text.strip())

    relatives = data.get("relatives", [])
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
