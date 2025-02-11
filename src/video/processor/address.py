import os
amqp_ip=os.getenv('AMQP_IP') 
amqp_port=os.getenv('AMQP_PORT')
username=os.getenv('AMQP_USER')
password=os.getenv('AMQP_PASS')
topic_read=os.getenv('TOPIC_READ')
topic_write=os.getenv('TOPIC_WRITE')

url='amqp://'+username+':'+password+'@'+amqp_ip+':'+amqp_port+'/topic://'+topic_read


