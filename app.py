import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from script import process_file  # Ensure this import matches your script's location

ALLOWED_EXTENSIONS = set(['txt'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app():
    app = Flask(__name__)
    app.secret_key = 'supersecretkey'  # Needed for flashing messages

    @app.route('/', methods=['GET', 'POST'])
    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        if request.method == 'POST':
            file = request.files['file']
            if file and allowed_file(file.filename):
                # Secure and save the original file
                original_filename = secure_filename(file.filename)
                base_filename = os.path.splitext(original_filename)[0]
                
                timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
                new_filename = f'Processed_{base_filename}.txt'
                save_location = os.path.join('input', new_filename)
                file.save(save_location)

                # Process the uploaded file and get the output file name
                output_filename = process_file(save_location)
                download_url = url_for('download_file', filename=output_filename)
                flash(f'File processed successfully. You can download it from <a href="{download_url}">here</a>.')
                return redirect(url_for('upload'))

        return render_template('upload.html')

    @app.route('/files', methods=['GET'])
    def list_files():
        files = os.listdir('output')
        return render_template('download.html', files=files)

    @app.route('/download/<filename>')
    def download_file(filename):
        return send_from_directory('output', filename, as_attachment=True)

    return app

if __name__ == '__main__':
    if not os.path.exists('input'):
        os.makedirs('input')
    if not os.path.exists('output'):
        os.makedirs('output')

    app = create_app()
    app.run(debug=True)
