from flask import Flask
from flask import request
from flask import abort

from rq import Queue
from redis import Redis
import rq_dashboard

from settings import telebot_token
from translator import main as parser

redis_host = 'redis'
rq_dashboard.default_settings.RQ_DASHBOARD_REDIS_HOST = redis_host

app = Flask(__name__)
app.config.from_object(rq_dashboard.default_settings)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/bot/english/rqX")

redis_conn = Redis(host=redis_host)
queue = Queue('bot', connection=redis_conn)

def bot_request(request, queue, parser):
    if request.method == 'POST':
        # Содержимое сообщения из реквеста
        message = request.get_json()
        # Складываем обработку запроса и его выполнение в очередь
        queue.enqueue(parser, message)
        return 'OK'

    return abort(404)

@app.route('/bot/english/', methods=['GET'])
def hello_world():
    return '<h2>Hello english!</h2>'

@app.route('/bot/english/' + telebot_token, methods=['POST', 'GET'])
def translator_bot():
    return bot_request(request, queue, parser)
