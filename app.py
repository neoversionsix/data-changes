from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io
import webbrowser
import threading
import os
import sys
import traceback

app = Flask(__name__)

def open_browser():
    webbrowser.open_new('http://localhost:5000/')

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    try:
        file_a = request.files['file_a']
        file_b = request.files['file_b']
        key_column = request.form['key_column']

        # Read Excel files in chunks
        chunk_size = 10000  # Adjust this based on your system's memory
        a_chunks = pd.read_excel(file_a, chunksize=chunk_size)
        b_chunks = pd.read_excel(file_b, chunksize=chunk_size)

        a_keys = set()
        b_keys = set()
        new_rows_count = 0
        non_existing_rows_count = 0

        for chunk in a_chunks:
            if key_column not in chunk.columns:
                raise ValueError(f"Key column '{key_column}' not found in file A")
            a_keys.update(chunk[key_column])

        for chunk in b_chunks:
            if key_column not in chunk.columns:
                raise ValueError(f"Key column '{key_column}' not found in file B")
            b_keys.update(chunk[key_column])
            new_rows_count += sum(~chunk[key_column].isin(a_keys))

        non_existing_rows_count = sum(key not in b_keys for key in a_keys)

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

        chunk_size = 10000  # Adjust this based on your system's memory
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if download_type == 'new_rows':
                a_keys = set(pd.read_excel(file_a, usecols=[key_column])[key_column])
                for chunk in pd.read_excel(file_b, chunksize=chunk_size):
                    new_rows = chunk[~chunk[key_column].isin(a_keys)]
                    new_rows.to_excel(writer, index=False, header=True if writer.sheets.get('Sheet1') is None else False)
                filename = 'new_rows.xlsx'
            else:
                b_keys = set(pd.read_excel(file_b, usecols=[key_column])[key_column])
                for chunk in pd.read_excel(file_a, chunksize=chunk_size):
                    non_existing_rows = chunk[~chunk[key_column].isin(b_keys)]
                    non_existing_rows.to_excel(writer, index=False, header=True if writer.sheets.get('Sheet1') is None else False)
                filename = 'non_existing_rows.xlsx'

        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name=filename)
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    os.chdir(application_path)
    threading.Timer(1.25, open_browser).start()
    app.run(debug=True, port=5000)  # Set debug=True for development