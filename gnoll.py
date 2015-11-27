import requests
import base64
import json
import random
import datetime
import time

# global contstants!
# obtenemos el token desde config.py
from config import token
strings = ['Aaarghhh!!!', 'Braaiiinnzzz..', 'Grmbblrr..', 'GRRRRRR...!!', 'Bluuughhrr..']
url = 'https://api.telegram.org/bot' + token + '/'
filename = 'offset.txt'  # updateID compensa para prevenir múltiples respuestas
logfilename = 'log.txt'  # archivo de registros
cancion = ''


# procedimiento para enviar mensaje
def sendSimpleMessage(chatId, text):
    try:
        params = { 'chat_id': chatId, 'text': text }
        response = requests.post(url + 'sendMessage', params)
    except:
        return

# obtenemos notificaciones y respondemos a los mensajes
def doBotStuff(updateId):
    global cancion
    try:
        params = { 'offset': updateId, 'limit': '100', 'timeout': '60'}
        response = requests.post(url + 'getUpdates', params)
        data = json.loads( response.content.decode('utf-8') )
    except:
        return updateId

    file = open(logfilename, 'a')

    if data['ok'] == True:
        for update in data['result']:

            # tomamos el nuevo update id
            updateId = update['update_id'] + 1
            message = update['message']

            # respondemos si el mensaje contiene texto
            if 'text' in message:
                messagetext = str(message['text'])

                # si el comando no es /start
                if messagetext.startswith('/') and not messagetext.startswith('/start'):
                    # comando principal sonando
                    if messagetext.startswith('/sonando'):
                        chatId = message['chat']['id']
                        # hacemos la peticion http a la api de la radio
                        try:
                            api_radiognu = requests.get('http://api.radiognu.org/?img_size=200')
                        except:
                            sendSimpleMessage(chatId, '⚠️ ¡Ocurrió un error al intentar acceder a la API!')
                            break

                        datos = json.loads( api_radiognu.content.decode('utf-8') )
                        imagen_portada = base64.b64decode( bytes(datos['cover'][22:], 'utf-8') )

                        if cancion == '':
                            cancion = datos['title']
                            flood = False
                        elif cancion == datos['title']:
                            flood = True
                        else:
                            cancion = datos['title']
                            flood = False

                        if datos['isLive'] and flood == False:
                            texto = "🎤 «%s» de %s\n🎶 “%s”\n👤 %s\n🎧 %s escuchas\n🔴 #ENVIVO" % (datos['show'], datos['broadcaster'], datos['title'], datos['artist'], datos['listeners'])
                            params = { 'chat_id': chatId, 'caption': texto }
                            cover_file = { 'photo': ('file.png', imagen_portada) }
                            response = requests.post(url + 'sendPhoto', params, files=cover_file)
                        elif datos['isLive'] != True and flood == False:
                            texto = "🎶 %s\n👤 %s\n💿 %s\n📃 %s\n🎧 %s escuchas\n📻 #DIFERIDO" % (datos['title'], datos['artist'], datos['album'], datos['license']['shortname'] if datos["license"] != "" else "", datos['listeners'])
                            params = { 'chat_id': chatId, 'caption': texto }
                            cover_file = { 'photo': ('file.png', imagen_portada) }
                            response = requests.post(url + 'sendPhoto', params, files=cover_file)

                    continue

                # escribimos un poco en el archivo de registro
                file.write(format(updateId) + ': user ' + format(message['from']['id']))
                if ('username' in message['from']):
                    file.write(' (@' + message['from']['username'] + ')')
                file.write(' at ' + datetime.datetime.fromtimestamp(int(message['date'])).strftime('%Y-%m-%d %H:%M:%S') + '\n')

                # componemos y enviamos una respuesta en idioma zombie
                chatId = message['chat']['id']
                text = random.choice(strings)
                sendSimpleMessage(chatId, text)

    file.close()

    return updateId

# aseguramos que el archivo existe y contiene un entero
try:
    file = open(filename, 'rt')
    updateId = int(file.read())
    file.close()
except:
    with open(filename, 'w') as file:
        file.write('0')
    updateId = 0

# bucle principal del programa
while True:

    # procesamos notificaciones
    newUpdateId = doBotStuff(updateId)

    # escribe el update ID a un archivo y espera 3 segundos si procesamos notificaciones
    if (newUpdateId != updateId):
        file = open(filename, 'wt')
        file.write(str(newUpdateId))
        file.close()
        time.sleep(3)
    else:
        # de otro modo, espera 1 segundos
        time.sleep(1)

    # usamos el nuevo update ID
    updateId = newUpdateId
