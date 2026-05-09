import os
import asyncio
import logging
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.request import HTTPXRequest

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменной окружения
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
IMAGES_DIR = "images"

if not TOKEN:
    logger.error("❌ Токен не найден!")
    exit(1)

# ВОПРОСЫ
QUESTIONS = [
    {"text": "Вы чаще пишете быстро, лишь бы было понятно, или выводите каждую букву?", "options": ["Быстро, главное понятно", "Вывожу каждую букву"], "types": ["СХ", "ФМ"]},
    {"text": "Вы сильнее нажимаете на ручку, когда пишете, или почти не давите?", "options": ["Сильно давлю", "Почти не давлю"], "types": ["ХМ", "СФ"]},
    {"text": "Обычно ваши буквы стоят прямо, наклонены вперёд или назад?", "options": ["Стоят прямо", "Наклонены вперед", "Наклонены назад"], "types": ["Ф", "СХ", "МФ"]},
    {"text": "А у вас бывает, что к концу слова буквы становятся мельче и неразборчивее?", "options": ["Да, часто", "Редко", "Нет, всегда одинаково"], "types": ["ХС", "Ф", "ФМ"]},
    {"text": "На что больше похожи ваши заглавные буквы: на печатные или на прописные?", "options": ["На печатные", "На прописные", "Смесь того и другого"], "types": ["МФ", "СХ", "С"]},
    {"text": "Вы чаще пишете крупно или мелко?", "options": ["Крупно", "Мелко", "Средне"], "types": ["ХС", "МФ", "СФ"]},
    {"text": "Если вы очень торопитесь, почерк становится просто непонятным или всё равно можно разобрать?", "options": ["Становится непонятным", "Все равно можно разобрать", "Кое-как, но можно"], "types": ["Х", "ФМ", "С"]},
    {"text": "Вы когда-нибудь специально меняли почерк? Или он всегда был сам собой?", "options": ["Да менял(а) специально", "Нет всегда был сам собой", "Менялся сам без моего желания"], "types": ["МФ", "ХС", "М"]},
    {"text": "От чего, по-вашему, может зависеть Ваш почерк в определенный момент?", "options": ["От предмета", "От настроения", "От скорости", "От состояния здоровья"], "types": ["ФМ", "СХ", "Х", "М"]},
    {"text": "Что может влиять на Ваш почерк в определенный момент?", "options": ["Освещение", "Шум вокруг", "Бумага", "Находящиеся рядом люди"], "types": ["МФ", "МХ", "ФМ", "МС"]},
    {"text": "Зависит ли Ваш почерк от Вашего отношения к тому, что Вы пишите?", "options": ["Да", "Нет"], "types": ["МС", "ФХ"]},
    {"text": "Какого размера Ваш почерк?", "options": ["Крупный", "Средний", "Мелкий"], "types": ["ХС", "СФ", "МФ"]},
    {"text": "Выберите утверждение, которое больше Вам подходит:", "options": ["Коммуникабельный человек", "Скромный", "Умею находить компромиссы"], "types": ["СХ", "ФМ", "ФС"]},
    {"text": "Какой у Вас почерк?", "options": ["Ровный и идеально организованный", "Крупный, но неорганизованный", "Мелкий и организованный", "Мелкий и очень плохо организованный"], "types": ["ФМ", "ХС", "Ф", "М"]},
    {"text": "Выберите утверждение, которое больше Вам подходит:", "options": ["Активен и сосредоточен", "Импульсивен", "Разумно использую силы", "Нерешителен и робок"], "types": ["СХ", "Х", "Ф", "М"]},
    {"text": "Выберите утверждение, которое больше Вам подходит:", "options": ["Спокойный флегматик", "Мягкая реакция", "Эмоциональная напряженность", "Эгоистичен"], "types": ["Ф", "СФ", "Х", "М"]},
    {"text": "Считаете ли Вы, что по почерку можно определить характер человека?", "options": ["Да", "Нет"], "types": ["МФ", "СХ"]},
    {"text": "Выберите наиболее подходящий вариант:", "options": ["Буквы соединены между собой", "Буквы без соединений"], "types": ["СХ", "МФ"]},
    {"text": "Какое у Вас расположение строк?", "options": ["Поднимаются вверх", "Опускаются вниз", "Прямые", "Неровные"], "types": ["СХ", "МФ", "Ф", "Х"]},
    {"text": "Какие у Вас поля?", "options": ["Узкие", "Широкие"], "types": ["ХС", "МФ"]},
]

# РЕЗУЛЬТАТЫ
RESULTS = {
    "С": {
        "title": "✨Сангвиник✨\n\n",
        "text": "Вы — душа компании. Быстро загораетесь идеями, но остываете, когда дело доходит до рутины. Вам сложно усидеть на месте, а почерк выдает вашу эмоциональную спонтанность. Вы не переносите монотонность...\n\n📍Вот пару советов для вашего почерка\n\n· Попробуйте писать чуть медленнее...\n· Добавьте структуру...\n· Идеальная работа...",
        "photo": "sangvinic.jpg"
    },
    "М": {
        "title": "✨Меланхолик✨\n\n",
        "text": "Вы — человек глубокой рефлексии. Ваш почерк выдает перфекциониста...\n\n📍Вот пару советов для вашего почерка\n\n· Попробуйте иногда писать крупнее...\n· Если заметили, что строка поползла вниз...\n· Идеальная работа...",
        "photo": "melanholic.jpg"
    },
    "Ф": {
        "title": "✨Флегматик✨\n\n",
        "text": "Вы — человек системы и ритма. Ваш почерк почти не меняется...\n\n📍Вот пару советов для вашего почерка\n\n· Не бойтесь иногда «разболтать» почерк...\n· Если окружающим кажется, что вы слишком скупы...\n· Идеальная работа...",
        "photo": "flegmatic.jpg"
    },
    "Х": {
        "title": "✨Холерик✨\n\n",
        "text": "Вы — человек порыва. Ваш почерк выдает нетерпение...\n\n📍Вот пару советов для вашего почерка\n\n· Купите ручку с толстым корпусом...\n· Попробуйте писать печатными буквами...\n· Идеальная работа...",
        "photo": "holeric.jpg"
    }
}

user_scores = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_photo_path = os.path.join(IMAGES_DIR, "start_photo.jpg")
    welcome_text = (
        "📝 *Тест: Какой у вас характер по почерку*\n\n"
        "«Все мы учились в школе писать одинаково. Но потом каждый сбился на свою тропу. "
        "Эти отклонения от прописи — не ошибки, а следы темперамента. "
        "Острые углы выдадут раздражение, широкие петли — открытость, а смазанные штрихи — спешку. "
        "Давайте расшифруем ваш автограф души»🪄"
    )
    
    keyboard = [[InlineKeyboardButton("🎯 Начать тест", callback_data="start_test")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if os.path.exists(start_photo_path):
        with open(start_photo_path, "rb") as photo:
            await update.message.reply_photo(
                photo=InputFile(photo),
                caption=welcome_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def start_test_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    user_id = query.from_user.id
    user_scores[user_id] = []
    context.user_data["question_index"] = 0
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q_index = context.user_data.get("question_index", 0)
    if q_index >= len(QUESTIONS):
        await show_result(update, context)
        return
    
    q = QUESTIONS[q_index]
    photo_path = os.path.join(IMAGES_DIR, f"photo{q_index+1}.jpg")
    
    keyboard = [[InlineKeyboardButton(opt, callback_data=str(i))] for i, opt in enumerate(q["options"])]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"❓ *Вопрос {q_index+1} из {len(QUESTIONS)}*\n\n{q['text']}"
    
    if os.path.exists(photo_path):
        with open(photo_path, "rb") as f:
            if update.callback_query:
                await update.callback_query.message.reply_photo(photo=InputFile(f), caption=text, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await update.message.reply_photo(photo=InputFile(f), caption=text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        if update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    q_index = context.user_data.get("question_index", 0)
    if q_index >= len(QUESTIONS):
        return
    
    selected_idx = int(query.data)
    selected_types = QUESTIONS[q_index]["types"][selected_idx]
    
    if user_id not in user_scores:
        user_scores[user_id] = []
    for letter in selected_types:
        if letter in ["Х", "С", "Ф", "М"]:
            user_scores[user_id].append(letter)
    
    context.user_data["question_index"] = q_index + 1
    await ask_question(update, context)

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    scores = user_scores.get(user_id, [])
    
    if not scores:
        await update.callback_query.message.reply_text("Не удалось определить темперамент. Попробуйте /start")
        return
    
    counter = Counter(scores)
    result_type = counter.most_common(1)[0][0]
    result_data = RESULTS.get(result_type)
    
    if result_data:
        result_text = result_data["title"] + result_data["text"]
        result_photo_path = os.path.join(IMAGES_DIR, result_data["photo"])
        
        if os.path.exists(result_photo_path):
            with open(result_photo_path, "rb") as photo:
                await update.callback_query.message.reply_photo(photo=InputFile(photo), caption=result_text, parse_mode="Markdown")
        else:
            await update.callback_query.message.reply_text(result_text, parse_mode="Markdown")
    else:
        await update.callback_query.message.reply_text(f"Ваш тип: {result_type}")
    
    await update.callback_query.message.reply_text("✨ Чтобы пройти тест заново, отправь /start", parse_mode="Markdown")
    
    if user_id in user_scores:
        del user_scores[user_id]
    context.user_data.clear()

def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0, write_timeout=30.0)
    app = Application.builder().token(TOKEN).request(request).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start_test_callback, pattern="start_test"))
    app.add_handler(CallbackQueryHandler(handle_answer))
    
    logger.info("✅ Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()