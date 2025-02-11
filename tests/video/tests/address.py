import os

url = 'amqp://' + os.getenv('AMQP_USER') + ":" + os.getenv('AMQP_PASS') + '@' + os.getenv("AMQP_IP") + ":" + os.getenv('AMQP_PORT') + '/topic://video_anonym'
