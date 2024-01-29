import os
import base64
import io
import pandas as pd
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'verysecretkey'  # Change for production
app.config['UPLOAD_FOLDER'] = 'uploads'

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def plot_data(df, column_name):
    plt.switch_backend('Agg')  # Use the 'Agg' backend to avoid GUI-related issues
    plt.figure(figsize=(10, 5))
    df[column_name].value_counts().plot(kind='bar')
    plt.title(f'Distribution of {column_name}')
    plt.ylabel('Count')
    plt.xlabel(column_name)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')
    return plot_url

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            flash('Invalid file')
            return redirect(request.url)
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return redirect(url_for('view_data', filename=filename))
    return render_template('upload.html')

@app.route('/data/<filename>', methods=['GET', 'POST'])
def view_data(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        df = pd.read_csv(filepath)
        columns = df.columns.tolist()

        if request.method == 'POST':
            column_name_1 = request.form.get('column_name_1')
            column_name_2 = request.form.get('column_name_2')

            plot_url = plot_data(df, column_name_1)
            
            plt.switch_backend('Agg')
            plt.figure(figsize=(10, 5))
            df.groupby([column_name_2, column_name_1]).size().unstack().plot(kind='bar', stacked=True)
            plt.title(f'Distribution based on {column_name_2} and {column_name_1}')
            plt.ylabel('Count')
            plt.xlabel(column_name_2)
            plt.tight_layout()

            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            plot_url = base64.b64encode(buf.getvalue()).decode('utf-8')

            grouped_data = df.groupby([column_name_2, column_name_1]).size().reset_index(name='counts').to_html(classes='table table-striped', header="true", index=False)
            return render_template('view_data.html', columns=columns, filename=filename, plot_url=plot_url, grouped_data=grouped_data)

        return render_template('view_data.html', columns=columns, filename=filename)
    except FileNotFoundError:
        flash('File not found')
        return redirect(url_for('upload_file'))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
