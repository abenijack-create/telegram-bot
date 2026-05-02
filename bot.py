import os
import random
import zipfile
import string
from PIL import Image, ImageEnhance

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIG ----------------
TOKEN = "8759996316:AAH_phFX8PaLWVMnJl6op-i9ToPXgSGqlL4"

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

user_state = {}

# ---------------- MENU ----------------
async def setup_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Start new session"),
    ])

# ---------------- RANDOM NAMES ----------------
def rand_str(n=10):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(n))

def file_name(user_id, content_id):
    return f"user{user_id}_{content_id}_{rand_str(8)}"

def zip_name():
    return f"All_Content_{rand_str(6)}.zip"

# ---------------- IMAGE ENGINE (NO ROTATION) ----------------
def make_variants(image_path, count, user_id, content_id):
    img = Image.open(image_path).convert("RGB")
    w, h = img.size

    results = []

    for _ in range(count):

        # RANDOM CROP (main variation source)
        scale = random.uniform(0.85, 1.0)
        cw, ch = int(w * scale), int(h * scale)

        x = random.randint(0, w - cw)
        y = random.randint(0, h - ch)

        v = img.crop((x, y, x + cw, y + ch))

        # LIGHT CAMERA-LIKE VARIATION
        v = ImageEnhance.Brightness(v).enhance(random.uniform(0.97, 1.05))
        v = ImageEnhance.Contrast(v).enhance(random.uniform(0.97, 1.08))
        v = ImageEnhance.Color(v).enhance(random.uniform(0.97, 1.10))

        # FLIP (optional variation)
        if random.random() < 0.5:
            v = v.transpose(Image.FLIP_LEFT_RIGHT)

        name = file_name(user_id, content_id) + ".jpg"
        path = f"{OUTPUT_DIR}/{name}"

        v.save(path, quality=92)
        results.append(path)

    return results

# ---------------- ZIP ----------------
def create_zip(files):
    zname = zip_name()
    zpath = f"{OUTPUT_DIR}/{zname}"

    with zipfile.ZipFile(zpath, "w") as z:
        for f in files:
            z.write(f, os.path.basename(f))

    return zpath, zname

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_state.pop(user_id, None)

    keyboard = [
        [
            InlineKeyboardButton("5", callback_data="5"),
            InlineKeyboardButton("10", callback_data="10"),
            InlineKeyboardButton("20", callback_data="20"),
        ],
        [
            InlineKeyboardButton("30", callback_data="30"),
            InlineKeyboardButton("40", callback_data="40"),
            InlineKeyboardButton("50", callback_data="50"),
        ],
    ]

    await update.message.reply_text(
        "📸 OFM Content Spoofer\n\nChoose number of outputs:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

# ---------------- COUNT ----------------
async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id
    count = int(q.data)

    user_state[user_id] = {"count": count}

    await q.message.reply_text("📤 Upload your image now.")

# ---------------- PHOTO ----------------
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_state:
        await update.message.reply_text("Use /start first.")
        return

    count = user_state[user_id]["count"]

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    content_id = photo.file_id[:20].replace("/", "").replace("=", "")

    input_path = f"{OUTPUT_DIR}/input_{user_id}_{content_id}.jpg"
    await file.download_to_drive(input_path)

    await update.message.reply_text("⏳ Processing...")

    variants = make_variants(input_path, count, user_id, content_id)

    zip_path, zname = create_zip(variants)

    await update.message.reply_document(
        document=open(zip_path, "rb"),
        filename=zname
    )

    await update.message.reply_text("✅ Done. Your files are ready.")

# ---------------- RUN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(choose, pattern="^(5|10|20|30|40|50)$"))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.post_init = setup_commands

print("🚀 Bot running (no rotation)...")
app.run_polling()