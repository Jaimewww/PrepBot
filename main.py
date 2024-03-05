from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

token = '7147953244:AAEez1U_lGJ3hwLyIfkR2QbsHkQzSB3AsRI'
user_name = 'jaimeadmin_bot'

async def start(update: Update, context: ContextTypes):
    #await update.message.reply_text('Hola es una prueba')
    await update.message.reply_photo('https://uploadsloxafact.sfo3.digitaloceanspaces.com/logos/KydayaLogo.jpg')

if __name__ == '__main__':
    print('Iniciando el bot')
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler('start', start))

    #app.add_handler((MessageHandler(filters.TEXT,handle_message)))

    app.run_polling(poll_interval=1,timeout=10)