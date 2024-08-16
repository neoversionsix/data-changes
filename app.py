from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io
import webbrowser
import threading
import os
import sys
import traceback
import logging
from logging.handlers import RotatingFileHandler
import tempfile

app = Flask(__name__)

# Clear the log file when the app starts
with open('app.log', 'w') as log_file:
    log_file.write('')

# Set up logging
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

browser_opened = False

def open_browser():
    global browser_opened
    if not browser_opened:
        webbrowser.open_new('http://localhost:5000/')
        browser_opened = True

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


def save_uploaded_file(file):
    _, temp_path = tempfile.mkstemp(suffix='.xlsx')
    file.save(temp_path)
    return temp_path

def read_excel_safe(file_path):
    try:
        return pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        app.logger.error(f"Error reading Excel file: {str(e)}")
        raise ValueError(f"Error reading Excel file: {str(e)}")

@app.route('/process', methods=['POST'])
def process():
    try:
        file_a = request.files['file_a']
        file_b = request.files['file_b']
        key_column = request.form['key_column']

        app.logger.info(f"Processing files with key column: {key_column}")

        temp_file_a = save_uploaded_file(file_a)
        temp_file_b = save_uploaded_file(file_b)

        df_a = read_excel_safe(temp_file_a)
        df_b = read_excel_safe(temp_file_b)

        os.remove(temp_file_a)
        os.remove(temp_file_b)

        if key_column not in df_a.columns:
            raise ValueError(f"Key column '{key_column}' not found in file A")
        if key_column not in df_b.columns:
            raise ValueError(f"Key column '{key_column}' not found in file B")

        a_keys = set(df_a[key_column])
        b_keys = set(df_b[key_column])

        new_rows_count = sum(~df_b[key_column].isin(a_keys))
        non_existing_rows_count = sum(~df_a[key_column].isin(b_keys))

        app.logger.info(f"New rows count: {new_rows_count}")
        app.logger.info(f"Non-existing rows count: {non_existing_rows_count}")

        return jsonify({
            'new_rows_count': new_rows_count,
            'non_existing_rows_count': non_existing_rows_count
        })
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    try:
        file_a = request.files['file_a']
        file_b = request.files['file_b']
        key_column = request.form['key_column']
        download_type = request.form['download_type']

        app.logger.info(f"Downloading {download_type} with key column: {key_column}")

        temp_file_a = save_uploaded_file(file_a)
        temp_file_b = save_uploaded_file(file_b)

        df_a = read_excel_safe(temp_file_a)
        df_b = read_excel_safe(temp_file_b)

        os.remove(temp_file_a)
        os.remove(temp_file_b)

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if download_type == 'new_rows':
                new_rows = df_b[~df_b[key_column].isin(df_a[key_column])]
                new_rows.to_excel(writer, index=False)
                filename = 'new_rows.xlsx'
            else:
                non_existing_rows = df_a[~df_a[key_column].isin(df_b[key_column])]
                non_existing_rows.to_excel(writer, index=False)
                filename = 'non_existing_rows.xlsx'

        output.seek(0)
        app.logger.info(f"Download complete: {filename}")
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name=filename)
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    with open('app.log', 'r') as log_file:
        logs = log_file.read().splitlines()
    return jsonify(logs)

if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)
    threading.Timer(1.25, open_browser).start()
    app.run(debug=False, port=5000)  # Set debug=False for production