import logging
from flask import Flask, request

app = Flask(__name__)

format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename = 'flask.log', level=logging.INFO, format = format)

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])

@app.route('/<path:path>', methods=['GET', 'POST'])
def log_requests(path):
    client_ip = request.remote_addr
    if request.method == 'GET':
        app.logger.info(f'[+] {client_ip}: Received GET request: "{path}"')
    elif request.method == 'POST':
        app.logger.info(f'[+] {client_ip}: Received POST request: "{path}" with payload:\n{request.data.decode()}')
    return f'ACK'

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=12345)