import logging
import os
from flask import Flask, request, send_from_directory, abort

UPLOAD_FOLDER='files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)

format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename = 'flask.log', level=logging.INFO, format = format)

@app.route('/upload', methods=['POST'])
def upload_file():
    client_ip = request.remote_addr
    if request.method == 'POST':
        app.logger.info(f'[+] {client_ip}: File upload request received')
        # check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            return 'No selected file'
        else:
            app.logger.info(f'[+] {client_ip}: File "{file.filename}" uploaded successfully')
            file.save(os.path.join(UPLOAD_FOLDER, file.filename))
            return 'File uploaded successfully'
    return 'OK'

@app.route('/get/<filename>', methods=['GET'])
def get_file(filename):
    client_ip = request.remote_addr
    app.logger.info(f'[+] {client_ip}: File download request received: "{filename}"')
    try:
        return send_from_directory("", filename)
    except FileNotFoundError:
        abort(404) # Return a 404 Not Found if the file doesn't exist


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
    app.run(debug=True, host='0.0.0.0', port=12345)