#Library Import
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes,ConversationHandler
from anthropic import Anthropic
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
import os


#configuration Setup
load_dotenv()

# Clients
ai_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

chat_histories = {}
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

# 🔢 ConversationHandler এর স্টেপগুলোর স্টেট (States)
PRODUCT, QUANTITY, ADDRESS, PHONE, CONFIRM = range(5)

# Products info
STORE_INFO = """
Saif's Kids Store Products:
১. Bangladesh Map Puzzle — ৪৫০ টাকা, বয়স ৫-১২ বছর
২. Magic Drawing Board — ৩৫০ টাকা, বয়স ৩-১০ বছর
৩. Flash Cards — ২৫০ টাকা, বয়স ৩-৬ বছর
Delivery: ঢাকায় ১-২ দিন, বাইরে ৩-৫ দিন
Order: Facebook page এ message করুন

রিটার্ন পলিসি:
পণ্য পাওয়ার ৭ দিনের মধ্যে return করা যাবে।
পণ্য অবশ্যই অব্যবহৃত এবং original packaging এ থাকতে হবে।

ওয়ারেন্টি পলিসি:
সব পণ্যে ৩০ দিনের ওয়ারেন্টি আছে।
পণ্য নষ্ট হলে বিনামূল্যে replace করা হবে।

পেমেন্ট পদ্ধতি:
bKash, Nagad, রকেট এবং ক্যাশ অন ডেলিভারি।
"""
# ==================== 🛒 ORDER SYSTEM (CONVERSATION) ====================
# 🎬 ১. অর্ডার শুরু (/order)
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # প্রোডাক্ট সিলেক্ট করার জন্য কীবোর্ড বাটন
    reply_keyboard = [['Bangladesh Map Puzzle', 'Magic Drawing Board', 'Flash Cards']]
    
    await update.message.reply_text(
        "🛒 আপনি সরাসরি বটের মাধ্যমেই অর্ডার করতে যাচ্ছেন।\n\n"
        "**ধাপ ১:** নিচের বাটন থেকে কোন Product-টি নিতে চান সিলেক্ট করুন (অথবা টাইপ করুন):",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return PRODUCT

# 📦 ২. প্রোডাক্ট রিসিভ এবং পরিমাণ জিজ্ঞাসা
async def order_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_product'] = update.message.text
    
    # পরিমাণ সিলেক্ট করার বাটন
    reply_keyboard = [['১ টি', '২ টি', '৩ টি']]
    
    await update.message.reply_text(
        f"✅ প্রোডাক্ট: {update.message.text}\n\n"
        f"**ধাপ ২:** আপনি কতটি (Quantity) নিতে চান সিলেক্ট করুন বা লিখে জানান:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return QUANTITY

# 🔢 ৩. পরিমাণ রিসিভ এবং ঠিকানা জিজ্ঞাসা
async def order_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_qty'] = update.message.text
    
    await update.message.reply_text(
        "**ধাপ ৩:** আপনার সম্পূর্ণ ঠিকানা (Full Address) লিখে দিন:\n"
        "উদাহরণ: হাউস# ১২, রোড# ৫, ধানমন্ডি, ঢাকা।",
        reply_markup=ReplyKeyboardRemove() # কীবোর্ড বাটন সরিয়ে ফেলার জন্য
    )
    return ADDRESS

# 📍 ৪. ঠিকানা রিসিভ এবং ফোন নম্বর জিজ্ঞাসা
async def order_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_address'] = update.message.text
    
    await update.message.reply_text(
        "**ধাপ ৪:** আপনার সচল মোবাইল নম্বরটি (Phone Number) দিন:"
    )
    return PHONE

# 📱 ৫. ফোন নম্বর রিসিভ এবং সামারি দেখানো
async def order_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_phone'] = update.message.text
    
    # কনফার্মেশন বাটন
    reply_keyboard = [['হ্যাঁ, কনফার্ম করছি', 'অর্ডার বাতিল করুন']]
    
    summary = (
        f"📝 **Order Summary (অর্ডারের বিবরণ):**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Product: {context.user_data['order_product']}\n"
        f"🔢 Quantity: {context.user_data['order_qty']}\n"
        f"📍 Address: {context.user_data['order_address']}\n"
        f"📱 Phone: {context.user_data['order_phone']}\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"সব তথ্য কি ঠিক আছে? অর্ডারটি কনফার্ম করতে নিচের বাটনে ক্লিক করুন:"
    )
    
    await update.message.reply_text(
        summary,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM


# 🏁 ৬. ফাইনাল কনফার্মেশন ও অ্যাডমিন নোটিফিকেশন
async def order_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text
    user_name = update.effective_user.first_name
    user_id = update.effective_user.id
    current_time = datetime.now().strftime("%I:%M %p")
    
    if user_choice == 'হ্যাঁ, কনফার্ম করছি':
        # ১. কাস্টমারকে থ্যাঙ্ক ইউ মেসেজ
        await update.message.reply_text(
            "🎉 আলহামদুলিল্লাহ্! আপনার অর্ডারটি সফলভাবে গ্রহণ করা হয়েছে।\n\n"
            "আমাদের প্রতিনিধি খুব দ্রুত আপনার সাথে যোগাযোগ করবেন। আমাদের সাথে থাকার জন্য ধন্যবাদ! 😊",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # ২. অ্যাডমিনকে সম্পূর্ণ অর্ডারের নোটিফিকেশন পাঠানো
        admin_notification = (
            f"🚀 **New Order Placed!**\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Customer: {user_name} (ID: {user_id})\n"
            f"📦 Product: {context.user_data['order_product']}\n"
            f"🔢 Qty: {context.user_data['order_qty']}\n"
            f"📍 Address: {context.user_data['order_address']}\n"
            f"📱 Phone: {context.user_data['order_phone']}\n"
            f"⏰ Time: {current_time}\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_notification)
        except Exception as admin_err:
            print(f"Admin Order Notification Error: {admin_err}")
            
    else:
        await update.message.reply_text(
            "❌ অর্ডারটি বাতিল করা হয়েছে। নতুন করে অর্ডার করতে আবার /order লিখুন।",
            reply_markup=ReplyKeyboardRemove()
        )
        
    return ConversationHandler.END

# 🚫 অর্ডার চলাকালীন কাস্টমার চাইলে বাতিল করতে পারবে
async def order_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚫 অর্ডার প্রক্রিয়াটি বাতিল করা হয়েছে।", 
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ========================================================================

# ✅ /start command
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    user_name=update.effective_user.first_name #user name collect করবে telegram থেকে
    await update.message.reply_text(
        f"🛍️ আস্সালামু আলাইকুম {user_name}!\n\n"
        f"আমি Saif's Kids Store এর AI Assistant।\n\n"
        f"আপনি জিজ্ঞেস করতে পারেন:\n"
        f"• Product এর দাম\n"
        f"• Delivery সময়\n"
        f"• Store পলিসি\n\n"
        f"Commands:\n"
        f"/products — সব products দেখুন\n"
        f"/price — product এর দাম\n"
        f"/delivery — Delivery এর সময়\n"
        f"/policy - Store Policy\n"
        f"/clear — চ্যাট মেমোরি মুছুন\n"
        f"/help — সাহায্য"
        
    ) 

# ✅ /clear command
async def clear_memory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id # ইউজারের ইউনিক আইডি  collect করবে telegram থেকে
    chat_histories[user_id] = []
    await update.message.reply_text("🧹 আপনার সাথে আগের সব আলাপচারিতার স্মৃতি মুছে ফেলা হয়েছে!")


# ✅ /products command
async def products(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍️ আমাদের Products:\n\n"
        "1️⃣ Bangladesh Map Puzzle\n"
        "   💰 ৪৫০ টাকা | 👶 ৫-১২ বছর\n\n"
        "2️⃣ Magic Drawing Board\n"
        "   💰 ৩৫০ টাকা | 👶 ৩-১০ বছর\n\n"
        "3️⃣ Flash Cards\n"
        "   💰 ২৫০ টাকা | 👶 ৩-৬ বছর\n\n"
        "📦 Order করতে Facebook page এ message করুন!"
    )

# ✅ /help command

async def help_command(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 আমি কীভাবে সাহায্য করতে পারি:\n\n"
        "✅ Product এর দাম জানতে চাইলে জিজ্ঞেস করুন\n"
        "✅ Delivery সময় জানতে এলাকার নাম বলুন\n"
        "✅ যেকোনো প্রশ্ন করুন বাংলায়!\n\n"
        "Commands:\n"
        "/start — শুরু করুন\n"
        "/products — সব products\n"
        "/price — product এর দাম\n"
        "/delivery — product এর delivery সময়\n"
        "/policy — Sotre এর Policy\n"
        "/clear — চ্যাট মেমোরি মুছুন\n"
       # "/cancelOrder — আপনাার order বাতিল করতে\n"
        "/help — সাহায্য"
    )

# ✅ /Store Policy
async def policy(update:Update,context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛍️ আমাদের রিটার্ন পলিসি:\n\n"
        "✅পণ্য পাওয়ার ৭ দিনের মধ্যে return করা যাবে।\n"
        "✅পণ্য অবশ্যই অব্যবহৃত এবং original packaging এ থাকতে হবে।\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "🛍️ আমাদের ওয়ারেন্টি পলিসি:\n\n"
        "✅সব পণ্যে ৩০ দিনের ওয়ারেন্টি আছে।\n"
        "✅পণ্য নষ্ট হলে বিনামূল্যে replace করা হবে।\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"

        "📦 Order করতে Facebook page এ message করুন!"
    )

# ✅ /price command
async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_prices = {
        "bangladesh map puzzle": 450,  # ✅ সঠিক দাম
        "magic drawing board": 350,    # ✅ সঠিক দাম
        "flash cards": 250             # ✅ সঠিক দাম
    }

    # ✅ আগে check করো
    if not context.args:
        await update.message.reply_text(
            "📍 কোন Product এর দাম জানতে চাও?\n\n"
            "উদাহরণ:\n"
            "/price bangladesh map puzzle\n"
            "/price magic drawing board\n"
            "/price flash cards"
        )
        return

    # ✅ তারপর join করো
    user_input = " ".join(context.args).strip().lower()

    if user_input in product_prices:
        product_price = product_prices[user_input]
        actual_name = user_input.title()

        message = (
            f"📦 Product: {actual_name}\n"
            f"💰 Price: ৳{product_price} টাকা\n\n"  # ✅ টাকা sign
            f"🛒 Order করতে Facebook Page এ message করুন!"
        )
    else:
        message = (
            "❌ Product পাওয়া যায়নি!\n\n"
            "আমাদের products:\n"
            "• Bangladesh Map Puzzle\n"
            "• Magic Drawing Board\n"
            "• Flash Cards"
        )

    await update.message.reply_text(message)

# ✅ /delivery command
async def delivery(update:Update, context:ContextTypes.DEFAULT_TYPE):
    
    # User কি location দিয়েছে?
    if not context.args:
        await update.message.reply_text(
            "📍 কোন এলাকায় delivery চাও?\n\n"
            "উদাহরণ:\n"
            "/delivery ঢাকা\n"
            "/delivery চট্টগ্রাম\n"
            "/delivery সিলেট"
        )
        return
    # Location নাও
    location = " ".join(context.args)
    # Delivery time check করো
    if "ঢাকা" in location or "dhaka" in location.lower():
        time = "১-২ দিন"
        emoji = "🟢"
    else:
        time = "৩-৫ দিন"
        emoji = "🟡"
    
    await update.message.reply_text(
        f"🚚 Delivery Information\n\n"
        f"📍 এলাকা: {location}\n"
        f"{emoji} সময়: {time}\n\n"
        f"📦 Order করতে:\n"
        f"Facebook page এ message করুন!"
    )



# ✅ AI Message Handler
async def handle_message(update:Update,context:ContextTypes.DEFAULT_TYPE):
    user_message=update.message.text
    user_id = update.effective_user.id  # ইউজারের ইউনিক আইডি  collect করবে telegram থেকে
    user_name = update.effective_user.first_name

    # 🛒 অ্যাডমিন নোটিফিকেশন লজিক
    keywords = ["order", "কিনতে চাই", "কিনবো", "নিতে চাই", "অর্ডার"]
    if any(keyword in user_message.lower() for keyword in keywords):
        current_time = datetime.now().strftime("%I:%M %p")
        notification = (
            f"🛒 New Order Interest!\n"
            f"User: {user_name} (ID: {user_id})\n"
            f"Message: {user_message}\n"
            f"Time: {current_time}"
        )
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=notification
            )
        except Exception as admin_err:
            print(f"Admin Notification Error: {admin_err}")

     # ডিকশনারিতে ইউজারের জন্য হিস্ট্রি না থাকলে নতুন খালি লিস্ট তৈরি হবে
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    # টাইপিং ইন্ডিকেটর
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    # ইউজারের নতুন মেসেজটি তার নিজস্ব মেমোরিতে সেভ করা
    chat_histories[user_id].append({
        "role": "user",
        "content": user_message
    })

     
    try:
        # Ai response
        response=ai_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=f"""তুমি Saif's Kids Store এর AI Assistant।
            বাংলায় সংক্ষেপে উত্তর দাও।
            Telegram এ markdown ব্যবহার করো।

            ⚠️ অত্যন্ত গুরুত্বপূর্ণ নিয়মাবলি:
            ১. 'Store Information'-এ যে দাম দেওয়া আছে, হুবহু সেটাই বলবে। নিজের থেকে কোনো দাম কল্পনা বা পরিবর্তন করবে না (যেমন: Flash Cards এর দাম ২৫০ টাকাই বলবে, ৪৫০ টাকা বলবে না)।
            ২. যদি এমন কোনো প্রোডাক্টের নাম কাস্টমার জিজ্ঞেস করে যা এই তালিকায় নেই, তবে নম্রভাবে বলো যে এই প্রোডাক্টটি বর্তমানে স্টকে নেই।
            ৩. বাংলায় সুন্দরভাবে এবং সংক্ষেপে উত্তর দাও। Telegram এ markdown ফরম্যাট ব্যবহার করো।            

            Store Information:
            {STORE_INFO}""",
            messages=chat_histories[user_id]  # শুধুমাত্র এই নির্দিষ্ট ইউজারের হিস্ট্রি পাঠানো হচ্ছে
        )
        ai_response=response.content[0].text # .text এর জায়গায় সঠিক ইনডেক্সিং করা হয়েছে
        
        # এআই-এর উত্তরটি ওই ইউজারের মেমোরিতে সেভ করা
        chat_histories[user_id].append({
            "role": "assistant",
            "content": ai_response
        })

        await update.message.reply_text(ai_response)
    
    except Exception as e:
        await update.message.reply_text(
             f"❌ দুঃখিত, সমস্যা হয়েছে। আবার চেষ্টা করুন।"
        )
        print(f"Error:{e}")
    
#Main Function
def main():
    print("🤖 Telegram Bot চালু হচ্ছে...")
    app=Application.builder().token(BOT_TOKEN).build()

     # 🛒 Order System Conversation Handler রেজিস্ট্রেশন
    order_handler = ConversationHandler(
        entry_points=[CommandHandler("order", order_start)],
        states={
            PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_product)],
            QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_quantity)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_address)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_phone)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_confirm)],
        },
        fallbacks=[CommandHandler("cancel", order_cancel)],
    )
    

    

    # Handlers যোগ করো
    app.add_handler(order_handler) # অর্ডার হ্যান্ডলারটি সবার আগে যুক্ত করতে হবে
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("delivery", delivery))
    app.add_handler(CommandHandler("clear",clear_memory))
    #app.add_handler(CommandHandler("orderCancel",order_cancel))
    app.add_handler(CommandHandler("policy",policy))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))
    print("✅ Bot চালু! Telegram এ test করো।")
    print("Ctrl+C দিয়ে বন্ধ করো।")

    app.run_polling()

main()

