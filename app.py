from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import os
import base64
import re
from io import BytesIO
from aes import AES
from file import FileHandler

app = Flask(__name__)

def validate_key(key):
    return len(key) == 16

def read_uploaded_file(uploaded_file):
    filename = secure_filename(uploaded_file.filename)
    extension = FileHandler.get_file_extension(filename)

    if extension == ".pdf": 
        content = FileHandler.read_pdf(uploaded_file)
    elif extension == ".docx":
        content = FileHandler.read_docx(uploaded_file)
    else:
        content = uploaded_file.read().decode('utf-8')

    return content, filename, extension

def detect_and_convert_format(content):
    content = "".join(content.split())
    
    if re.match(r'^[0-9a-fA-F]+$', content):
        try:
            return bytes.fromhex(content), "hex"
        except Exception:
            pass
    try:
        if re.match(r'^[A-Za-z0-9+/]+={0,2}$', content):
            return base64.b64decode(content), "base64"
    except Exception:
        pass
    try:
        return base64.b64decode(content), "base64"
    except Exception:
        pass
    
    return None, None

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/enkripsi')
def enkripsi():
    return render_template('enkripsi.html')

@app.route('/dekripsi')
def dekripsi():
    return render_template('dekripsi.html')

@app.route('/encrypt', methods=['POST'])
def encrypt():
    key = request.form['key']
    if not validate_key(key):
        return render_template('error.html', error=f"Panjang kunci harus 16 byte."), 400

    try:
        input_type = request.form['input_type']
        output_type = request.form['output_type']
        aes = AES(key)

        if input_type == 'file':
            uploaded_file = request.files.get('file_plaintext')
            if not uploaded_file or uploaded_file.filename == '':
                return render_template('error.html', error=f"Tidak ada file yang diunggah."), 400

            content, filename, extension = read_uploaded_file(uploaded_file)
            cipher = aes.encrypt(content)
            hex_string = cipher.hex()

            if output_type == 'char':
                cipher = base64.b64encode(bytes.fromhex(hex_string)).decode('utf-8')
            else:
                cipher = hex_string

            output_stream = BytesIO()
            output_stream.write(cipher.encode('utf-8'))
            output_stream.seek(0)

            download_filename = f"{os.path.splitext(filename)[0]}_encrypted{extension if extension not in ['.pdf', '.docx'] else '.txt'}"

            return send_file(
                output_stream,
                as_attachment=True,
                download_name=download_filename,
                mimetype="application/octet-stream"
            )

        elif input_type == 'text':
            plaintext = request.form['plaintext']
            if not plaintext:
                return render_template('error.html', error=f"Tidak ada teks yang dimasukkan."), 400

            cipher = aes.encrypt(plaintext)
            hex_string = cipher.hex()

            if output_type == 'char':
                cipher = base64.b64encode(bytes.fromhex(hex_string)).decode('utf-8')
            else:
                cipher = hex_string

            return render_template('enkripsi.html',
                                   input=input_type,
                                   plaintext=plaintext,
                                   ciphertext=cipher,
                                   key=key)
        else:
            return render_template('error.html', error=f"Jenis input tidak valid."), 400

    except Exception as e:
        return render_template('error.html', error=f"Error during encryption: {str(e)}"), 500

@app.route('/decrypt', methods=['POST'])
def decrypt():
    key = request.form['key']
    if not validate_key(key):
        return render_template('error.html', error=f"Panjang kunci harus 16 byte."), 400

    try:
        input_type = request.form['input_type']
        aes = AES(key)

        if input_type == 'file':
            uploaded_file = request.files.get('file_ciphertext')
            if not uploaded_file or uploaded_file.filename == '':
                return render_template('error.html', error=f"Tidak ada file yang diunggah."), 400

            content, filename, extension = read_uploaded_file(uploaded_file)
            content = content.strip()
            
            ciphertext_bytes, detected_format = detect_and_convert_format(content)
            if not ciphertext_bytes:
                return render_template('error.html', error=f"Format ciphertext tidak valid. Berikan input hex atau base64 yang valid."), 400

            plaintext = aes.decrypt(ciphertext_bytes)

            output_stream = BytesIO()
            output_stream.write(plaintext)
            output_stream.seek(0)

            download_filename = f"{os.path.splitext(filename)[0]}_decrypted{extension if extension not in ['.pdf', '.docx'] else '.txt'}"

            return send_file(
                output_stream,
                as_attachment=True,
                download_name=download_filename,
                mimetype="application/octet-stream"
            )

        elif input_type == 'text':
            ciphertext = request.form['text_ciphertext'].strip()
            ciphertext_bytes, detected_format = detect_and_convert_format(ciphertext)
            if not ciphertext_bytes:
                return render_template('error.html', error=f"Format ciphertext tidak valid. Berikan input hex atau base64 yang valid."), 400

            plaintext = aes.decrypt(ciphertext_bytes)

            return render_template('dekripsi.html',
                                  input=input_type,
                                  ciphertext=ciphertext,
                                  plaintext=plaintext.decode('utf-8'),
                                  key=key,
                                  detected_format=detected_format)

        else:
            return render_template('error.html', error=f"Jenis input tidak valid."), 400

    except Exception as e:
        return render_template('error.html', error=f"Error during decryption: {str(e)}"), 500

if __name__ == '__main__':
    app.run(debug=True)
