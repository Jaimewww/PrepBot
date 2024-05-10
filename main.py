import random
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
import mysql.connector
from mysql.connector import Error

REGISTRO, EXAMEN = range(2)

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'botelegram'
}

async def start(update: Update, context: ContextTypes):
    user_id = update.message.from_user.id
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor()
        cursor.execute("SELECT est_cedula FROM estudiante WHERE est_cedula = %s", (str(user_id),))
        usuario = cursor.fetchone()
        if usuario:
            await update.message.reply_text('Ya estás registrado.')
            return ConversationHandler.END
        else:
            await update.message.reply_text('Por favor, ingresa tu cédula y nombres separados por una coma. Ejemplo: 0123456789, Juan Pérez')
            return REGISTRO
    except Error as e:
        await update.message.reply_text('Error al verificar el registro: ' + str(e))
        return ConversationHandler.END
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

async def registro(update: Update, context: ContextTypes):
    
    texto = update.message.text
    if ',' in texto:
        cedula, nombre = texto.split(',', 1)
        cedula = cedula.strip()
        nombre = nombre.strip()

        try:
            conexion = mysql.connector.connect(**db_config)
            cursor = conexion.cursor()
            cursor.execute("SELECT est_id,est_cedula FROM estudiante WHERE est_cedula = %s", (cedula,))
            estudiante = cursor.fetchone()
            if estudiante:
                await update.message.reply_text('Ya estás registrado.')
                context.user_data['est_id'] = estudiante[0]
                return await start_examen(update, context)
            else:
                cursor.execute("INSERT INTO estudiante (est_cedula, est_nombre) VALUES (%s, %s)", (cedula, nombre))
                conexion.commit()
                cursor.execute("SELECT est_id FROM estudiante WHERE est_cedula = %s", (cedula,))
                estudiante = cursor.fetchone()
                context.user_data['est_id'] = estudiante[0]
                await update.message.reply_text('Registro completado con éxito. Comencemos el examen.')
                return await start_examen(update, context)
        except Error as e:
            await update.message.reply_text('Error al registrar: ' + str(e))
        finally:
            if conexion.is_connected():
                cursor.close()
                conexion.close()

        return ConversationHandler.END
    else:
        await update.message.reply_text('No se encontró la coma. Por favor, ingresa tu cédula y nombres separados por una coma. Ejemplo: 0123456789, Juan Pérez')
        return REGISTRO
    

async def start_examen(update: Update, context: ContextTypes):
    context.user_data['preguntas_respondidas'] = 0
    context.user_data['respuestas_correctas'] = 0
    context.user_data['preguntas_usadas'] = set()  # Inicializa el conjunto de preguntas usadas
    await enviar_pregunta(update, context)
    return EXAMEN

async def enviar_pregunta(update: Update, context: ContextTypes):
    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor()

        # Lista de IDs de preguntas ya utilizadas para construir la parte de la consulta SQL
        preguntas_usadas = list(context.user_data['preguntas_usadas'])
        if preguntas_usadas:
            query = "SELECT pre_id, pre_nombre FROM pregunta WHERE pre_id NOT IN (%s)" % ', '.join(['%s'] * len(preguntas_usadas))
            cursor.execute(query, tuple(preguntas_usadas))
        else:
            cursor.execute("SELECT pre_id, pre_nombre FROM pregunta")

        preguntas_disponibles = cursor.fetchall()

        if preguntas_disponibles:
            pregunta = random.choice(preguntas_disponibles)
            context.user_data['pregunta_actual'] = pregunta[0]
            context.user_data['preguntas_usadas'].add(pregunta[0])  # Añade la pregunta actual al conjunto de usadas

            cursor.execute("SELECT res_id, res_nombre FROM respuesta WHERE pre_id = %s", (pregunta[0],))
            respuestas = cursor.fetchall()
            
            mensaje_respuesta = pregunta[1] + "\n"
            for idx, (resp_id, resp) in enumerate(respuestas, start=1):
                mensaje_respuesta += f"{idx}. {resp}\n"
                context.user_data[f"resp_{idx}"] = resp_id
            
            await update.message.reply_text(mensaje_respuesta)
        else:
            await update.message.reply_text("No hay más preguntas disponibles, el examen ha terminado.")
            return ConversationHandler.END
    except Error as e:
        await update.message.reply_text('Error al obtener la pregunta: ' + str(e))
        return ConversationHandler.END
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

async def manejar_respuesta(update: Update, context: ContextTypes):
    seleccion_usuario = update.message.text
    pregunta_actual_id = context.user_data['pregunta_actual']
    estudiante_id = context.user_data['est_id']
    respuesta_id = context.user_data.get(f"resp_{seleccion_usuario}")

    if respuesta_id is None:
        await update.message.reply_text("Por favor, selecciona una opción válida.")
        return EXAMEN

    try:
        conexion = mysql.connector.connect(**db_config)
        cursor = conexion.cursor()

        cursor.execute("SELECT res_valor FROM respuesta WHERE res_id = %s", (respuesta_id,))
        es_correcta = cursor.fetchone()[0]

        if es_correcta:
            await update.message.reply_text("Correcto!")
            context.user_data['respuestas_correctas'] = context.user_data.get('respuestas_correctas', 0) + 1
        else:
            await update.message.reply_text("Incorrecto, intenta con la siguiente pregunta.")
        
        cursor.execute("INSERT INTO examen (est_id, pre_id, res_id) VALUES (%s, %s, %s)", (estudiante_id, pregunta_actual_id, respuesta_id))
        conexion.commit()

        context.user_data['preguntas_respondidas'] += 1
        if context.user_data['preguntas_respondidas'] < 10:
            await enviar_pregunta(update, context)
        else:
            puntaje_final = context.user_data.get('respuestas_correctas', 0) * 10
            await update.message.reply_text(f"Examen completado. ¡Buen trabajo! Tu puntaje es: {puntaje_final} puntos.")
            return ConversationHandler.END
    except Error as e:
        await update.message.reply_text('Error al validar la respuesta o al guardar en la base de datos: ' + str(e))
        return ConversationHandler.END
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()


async def cancelar(update: Update, context: ContextTypes):
    await update.message.reply_text('Registro cancelado.')
    return ConversationHandler.END

if __name__ == '__main__':
    print('Iniciando el bot')
    token = '7147953244:AAEez1U_lGJ3hwLyIfkR2QbsHkQzSB3AsRI'
    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            REGISTRO: [MessageHandler(filters.TEXT & ~filters.COMMAND, registro)],
            EXAMEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_respuesta)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar)],
        #conversation_timeout=60 
    )

    app.add_handler(conv_handler)

    app.run_polling()