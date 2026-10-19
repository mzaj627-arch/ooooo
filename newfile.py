import telebot
import subprocess
import os
import zipfile
import tempfile
import shutil
import requests
import re
import logging
from telebot import types
import time
import json
from flask import Flask
from threading import Thread

# --- إعدادات سيرفر Flask لمنع توقف البوت في Render ---
app = Flask('')

@app.route('/')
def home():
    return "🔥 Jarrah Hosting Bot is Alive and Running 24/7!"

def run_flask():
    # قراءة المنفذ الديناميكي الخاص بـ Render تلقائياً
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- التوكن الجديد والمحدث ---
TOKEN = '8946951685:AAG4GnnQXtfaox3QT-_K0PncnZa_fFGsPRk'
ADMIN_ID = 8871479815
channel = '@dhndpu'

# 🔑 المفتاح السري الخاص بك
SECRET_ADMIN_KEY = 'jarrah2026'

bot = telebot.TeleBot(TOKEN)
uploaded_files_dir = 'uploaded_bots'
db_file = 'database.json'
bot_scripts = {}

if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)

# --- نظام قاعدة البيانات المحلية ---
def load_db():
    if os.path.exists(db_file):
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db(data):
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_data(user_id):
    db = load_db()
    str_id = str(user_id)
    if str_id not in db:
        db[str_id] = {
            'points': 0,
            'last_login': '',
            'is_vip': (user_id == ADMIN_ID)
        }
        save_db(db)
    return db[str_id]

# --- التحقق من الاشتراك الإجباري ---
def check_subscription(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        member_status = bot.get_chat_member(channel, user_id).status
        return member_status in ['member', 'administrator', 'creator']
    except Exception as e:
        logging.error(f"Subscription Check Error: {e}")
        return False

def ask_for_subscription(chat_id):
    markup = types.InlineKeyboardMarkup()
    join_button = types.InlineKeyboardButton('📢 اشترك في القناة', url='https://t.me/dhndpu')
    markup.add(join_button)
    bot.send_message(chat_id, f"📢 عذراً يا غالي، يجب عليك الاشتراك في القناة أولاً لتتمكن من استخدام البوت:\n{channel}", reply_markup=markup)

# --- الواجهة الرئيسية للبوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if not check_subscription(user_id):
        ask_for_subscription(message.chat.id)
        return

    user = get_user_data(user_id)
    points = user['points']
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    upload_button = types.InlineKeyboardButton('🚀 رفع استضافة جديدة', callback_data='upload')
    daily_button = types.InlineKeyboardButton('🎁 هدية النقطة اليومية', callback_data='daily_bonus')
    profile_button = types.InlineKeyboardButton('👤 حسابي ونقاطي', callback_data='profile')
    speed_button = types.InlineKeyboardButton('⚡ فحص السرعة', callback_data='speed')
    dev_button = types.InlineKeyboardButton('👑 المطور جراح', url='https://t.me/adoatt1')
    
    markup.add(upload_button)
    markup.add(daily_button, profile_button)
    markup.add(speed_button, dev_button)
    
    welcome_text = (
        f"🌟 **أهلاً بك في أقوى بوت استضافة متكامل!**\n"
        f"👑 **المطور:** جراح (@adoatt1)\n\n"
        f"📌 يدعم جميع أنواع الاستضافات والمشاريع:\n"
        f"🔹 Python (.py)\n"
        f"🔹 Node.js (.js)\n"
        f"🔹 PHP (.php)\n"
        f"🔹 الملفات المضغوطة (.zip)\n\n"
        f"💎 نقاطك الحالية: `{points}` نقطة\n"
        f"💡 تكلفة الرفع **10 نقاط** (أو تجميعها يومياً / الشراء بـ **50 نجمة** ⭐️)."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup, parse_mode='Markdown')

# --- أمر المفتاح السري المطور ---
@bot.message_handler(commands=['key'])
def secret_key_handler(message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "⚠️ الاستخدام الصحيح:\n`/key مفتاحك_السري`", parse_mode='Markdown')
        return
    
    if args[1] == SECRET_ADMIN_KEY:
        db = load_db()
        str_id = str(user_id)
        if str_id not in db:
            get_user_data(user_id)
            db = load_db()
        db[str_id]['is_vip'] = True
        db[str_id]['points'] = 99999
        save_db(db)
        bot.reply_to(message, "🎉 **تم تفعيل صلاحيات VIP والارتقاء إلى وضع المطور المطلق بنجاح!** 🚀", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ المفتاح السري غير صحيح!")

# --- النقطة اليومية ---
@bot.callback_query_handler(func=lambda call: call.data == 'daily_bonus')
def daily_bonus_callback(call):
    user_id = call.from_user.id
    today = time.strftime('%Y-%m-%d')
    user = get_user_data(user_id)
    
    if user['last_login'] == today:
        bot.answer_callback_query(call.id, "⚠️ استلمت نقطتك اليومية مسبقاً، اعد المحاولة غداً!", show_alert=True)
    else:
        user['points'] += 1
        user['last_login'] = today
        db = load_db()
        db[str(user_id)] = user
        save_db(db)
        bot.answer_callback_query(call.id, "✅ تم إضافة نقطة يومية لحسابك!", show_alert=True)

# --- معلومات الملف الشخصي ---
@bot.callback_query_handler(func=lambda call: call.data == 'profile')
def profile_callback(call):
    user_id = call.from_user.id
    user = get_user_data(user_id)
    vip_status = "نشط 👑 (VIP)" if user['is_vip'] else "عادي 👤"
    
    text = (
        f"👤 **معلومات حسابك:**\n"
        f"🆔 معرفك: `{user_id}`\n"
        f"💎 النقاط: `{user['points']}`\n"
        f"⭐ نوع الحساب: {vip_status}\n"
        f"🛠️ المطور: جراح"
    )
    bot.send_message(call.message.chat.id, text, parse_mode='Markdown')

# --- فحص سرعة استجابة البوت ---
@bot.callback_query_handler(func=lambda call: call.data == 'speed')
def bot_speed_info(call):
    try:
        start_time = time.time()
        res = requests.get(f'https://api.telegram.org/bot{TOKEN}/getMe')
        latency = time.time() - start_time
        if res.ok:
            bot.send_message(call.message.chat.id, f"⚡ سرعة استجابة السيرفر: `{latency:.2f}` ثانية.", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ خطأ: {e}")

# --- طلب رفع استضافة ---
@bot.callback_query_handler(func=lambda call: call.data == 'upload')
def ask_to_upload_file(call):
    user_id = call.from_user.id
    user = get_user_data(user_id)
    
    if user['is_vip'] or user['points'] >= 10:
        bot.send_message(call.message.chat.id, "📥 **أرسل الآن ملف الاستضافة الخاص بك:**\n(يدعم: `.py`, `.js`, `.php`, أو `.zip`).", parse_mode='Markdown')
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        stars_btn = types.InlineKeyboardButton('⭐️ شراء بـ 50 نجمة للرفع الفوري', callback_data='pay_stars')
        daily_btn = types.InlineKeyboardButton('🎁 النقطة اليومية', callback_data='daily_bonus')
        markup.add(stars_btn, daily_btn)
        
        bot.send_message(
            call.message.chat.id, 
            f"❌ نقاطك غير كافية (`{user['points']}`/10).\nيمكنك الشراء بـ 50 نجمة للرفع المباشر:", 
            reply_markup=markup, 
            parse_mode='Markdown'
        )

# --- نظام النجوم Telegram Stars (50 XTR) ---
@bot.callback_query_handler(func=lambda call: call.data == 'pay_stars')
def pay_with_stars(call):
    chat_id = call.message.chat.id
    try:
        bot.send_invoice(
            chat_id=chat_id,
            title="شراء رصيد استضافة",
            description="رفع مشروع استضافة فوري دون انتظار تجميع النقاط (50 نجمة)",
            invoice_payload="instant_upload_boost",
            provider_token="",
            currency="XTR",
            prices=[types.LabeledPrice(label="رفع استضافة", amount=50)],
            start_parameter="buy-hosting"
        )
    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ في الفاتورة: {e}")

@bot.pre_checkout_query_handler(func=lambda query: True)
def pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def successful_payment(message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    user['is_vip'] = True
    db = load_db()
    db[str(user_id)] = user
    save_db(db)
    bot.send_message(message.chat.id, "🎉 **تمت عملية الشراء بنجاح!** يمكنك الآن إرسال ملف الاستضافة لترفيعه فوراً.", parse_mode='Markdown')

# --- استقبال المستندات وتشغيل الاستضافة ---
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id

    if not check_subscription(user_id):
        ask_for_subscription(message.chat.id)
        return

    user = get_user_data(user_id)
    if not user['is_vip']:
        if user['points'] < 10:
            bot.reply_to(message, "❌ رصيدك أقل من 10 نقاط!")
            return
        else:
            user['points'] -= 10
            db = load_db()
            db[str(user_id)] = user
            save_db(db)

    try:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name

        if file_name.endswith('.zip'):
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_folder_path = os.path.join(temp_dir, file_name.split('.')[0])
                zip_path = os.path.join(temp_dir, file_name)
                with open(zip_path, 'wb') as new_file:
                    new_file.write(downloaded_file)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(zip_folder_path)

                final_folder_path = os.path.join(uploaded_files_dir, f"{user_id}_{file_name.split('.')[0]}")
                if os.path.exists(final_folder_path):
                    shutil.rmtree(final_folder_path)
                shutil.copytree(zip_folder_path, final_folder_path)

                run_universal_hosting(final_folder_path, message.chat.id, file_name, message)

        else:
            if not (file_name.endswith('.py') or file_name.endswith('.js') or file_name.endswith('.php')):
                bot.reply_to(message, "⚠️ يدعم الملفات التالية فقط: `.py`, `.js`, `.php`, `.zip`.")
                return

            script_path = os.path.join(uploaded_files_dir, f"{user_id}_{file_name}")
            with open(script_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            run_single_script(script_path, message.chat.id, file_name, message)

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ في الملف: {e}")

# --- معالجة وتشغيل المجلدات والملفات ---
def run_universal_hosting(folder_path, chat_id, file_name, original_message):
    try:
        bot.send_message(chat_id, "🔄 جاري تثبيت المكتبات وتجهيز البيئة...")
        
        req_path = os.path.join(folder_path, 'requirements.txt')
        if os.path.exists(req_path):
            subprocess.check_call(['pip', 'install', '-r', req_path])
            
        pkg_path = os.path.join(folder_path, 'package.json')
        if os.path.exists(pkg_path):
            subprocess.check_call(['npm', 'install'], cwd=folder_path)

        main_file = None
        for f in ['bot.py', 'main.py', 'run.py', 'index.js', 'app.py']:
            if os.path.exists(os.path.join(folder_path, f)):
                main_file = f
                break
        
        if main_file:
            main_path = os.path.join(folder_path, main_file)
            execute_process(main_path, chat_id, file_name, original_message, folder_path)
        else:
            bot.send_message(chat_id, "❓ يرجى كتابة اسم ملف التشغيل الرئيسي داخل المجلد (مثال: main.py):")
            bot_scripts[chat_id] = {'folder_path': folder_path}
            bot.register_next_step_handler(original_message, get_custom_file_to_run)

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ أثناء الإعداد: {e}")

def run_single_script(script_path, chat_id, file_name, original_message):
    execute_process(script_path, chat_id, file_name, original_message, os.path.dirname(script_path))

def execute_process(path, chat_id, file_name, original_message, folder_path):
    try:
        bot.send_message(chat_id, f"🚀 جاري إطلاق تشغيل الاستضافة `{file_name}`...", parse_mode='Markdown')
        
        if path.endswith('.py'):
            process = subprocess.Popen(['python3', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif path.endswith('.js'):
            process = subprocess.Popen(['node', path], cwd=folder_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif path.endswith('.php'):
            process = subprocess.Popen(['php', '-S', '0.0.0.0:8000', '-t', folder_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            process = subprocess.Popen(['python3', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        bot_scripts[chat_id] = {'process': process, 'folder_path': folder_path}

        user_info = f"@{original_message.from_user.username}" if original_message.from_user.username else str(original_message.from_user.id)
        caption = f"📤 قام `{user_info}` برفع استضافة جديدة بنجاح."
        try:
            bot.send_document(ADMIN_ID, open(path, 'rb'), caption=caption, parse_mode='Markdown')
        except:
            pass

        markup = types.InlineKeyboardMarkup(row_width=2)
        stop_btn = types.InlineKeyboardButton("🔴 إيقاف الاستضافة", callback_data=f'stop_{chat_id}')
        del_btn = types.InlineKeyboardButton("🗑️ حذف الملفات", callback_data=f'delete_{chat_id}')
        markup.add(stop_btn, del_btn)
        
        bot.send_message(chat_id, "✅ **تم تشغيل الاستضافة بنجاح 24/7!**", reply_markup=markup, parse_mode='Markdown')

    except Exception as e:
        bot.send_message(chat_id, f"❌ خطأ أثناء التشغيل: {e}")

def get_custom_file_to_run(message):
    try:
        chat_id = message.chat.id
        folder_path = bot_scripts.get(chat_id, {}).get('folder_path')
        if not folder_path:
            bot.send_message(chat_id, "⚠️ انتهت الجلسة، أعد رفع الملف.")
            return
            
        custom_file_path = os.path.join(folder_path, message.text)
        if os.path.exists(custom_file_path):
            execute_process(custom_file_path, chat_id, message.text, message, folder_path)
        else:
            bot.send_message(chat_id, "❌ الملف غير موجود داخل المجلد!")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")

# --- أزرار التحكم ---
@bot.callback_query_handler(func=lambda call: call.data.startswith('stop_') or call.data.startswith('delete_'))
def control_callbacks(call):
    chat_id = call.message.chat.id
    if 'stop' in call.data:
        if chat_id in bot_scripts and bot_scripts[chat_id].get('process'):
            bot_scripts[chat_id]['process'].terminate()
            bot.answer_callback_query(call.id, "🔴 تم إيقاف الاستضافة.", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "⚠️ لا توجد استضافة تعمل حالياً.", show_alert=True)
            
    elif 'delete' in call.data:
        folder_path = bot_scripts.get(chat_id, {}).get('folder_path')
        if folder_path and os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            bot.answer_callback_query(call.id, "🗑️ تم حذف الملفات نهائياً.", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "⚠️ الملفات غير موجودة.", show_alert=True)

# --- نقطة البدء التشغيلية ---
if __name__ == '__main__':
    keep_alive()  # تشغيل سيرفر الحفظ في الخلفية
    
    # إلغاء أي Webhook قديم لتفادي التوقف نهائياً
    try:
        bot.remove_webhook()
    except Exception as e:
        print(f"Webhook clean log: {e}")
        
    print("🚀 Bot running perfectly under developer Jarrah supervision...")
    bot.infinity_polling(skip_pending=True)
