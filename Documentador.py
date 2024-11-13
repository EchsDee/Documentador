import os
import tempfile
from io import BytesIO
from flask import Flask, render_template, request, send_file, after_this_request
from docx import Document
from docx.shared import Inches
import requests
import json
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.utils import secure_filename
from docx.opc.exceptions import PackageNotFoundError

app = Flask(__name__, static_folder='static')

template_path = os.path.join(os.getcwd(),'doc', 'TemplateDocument.docx')
api_url = os.environ.get('API_URL') or 'http://3.140.207.100/api/getclientes.php'

temp_dir = tempfile.mkdtemp()
half_template_path = os.path.join(os.getcwd(),'doc', 'templateDocument-half-segundo.docx')  
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: clean_temp_folder(temp_dir), 'interval', minutes=5)
scheduler.start()

def clean_temp_folder(temp_folder):
    for file_name in os.listdir(temp_folder):
        file_path = os.path.join(temp_folder, file_name)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")

# Function to fetch data from the API
def get_data_from_api(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise HTTPError for bad responses
        content = response.content.decode('utf-8-sig')  # Decode using utf-8-sig to handle BOM
        return json.loads(content)
    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return []

@app.route('/index')
def index():
    clients_data = get_data_from_api(api_url)
    return render_template('index.html', clients=clients_data)

@app.route('/')
def front():
    return render_template('front.html')

@app.route('/process_template', methods=['POST'])
def process_template():
    # Get form data
    data1 = request.form.get('data1', '')
    data2 = request.form.get('data2', '')
    data3 = request.form.get('data3', '')
    data4 = request.form.get('data4', '')
    data5 = request.form.get('data5', '')
    usuario = request.form.get('usuario', '')
    support_level = request.form.get('supportLevel', '')

    # Prepare image files and descriptions
    image_files = request.files.getlist('data6[]')
    image_descriptions = request.form.getlist('data7[]')

    # Set modified document path
    modified_filename = f'DOCUMENTAÇÃO - {secure_filename(data2 or "document")}.docx'
    modified_path = os.path.join(temp_dir, modified_filename)

    if support_level == '2' and 'additionalFile' in request.files:
        # Handle uploaded document
        additional_file = request.files['additionalFile']
        additional_file_path = os.path.join(temp_dir, secure_filename(additional_file.filename))
        additional_file.save(additional_file_path)

        try:
            # Merge uploaded document with half-template
            process_uploaded_doc(additional_file_path, modified_path)
        except PackageNotFoundError:
            return "Uploaded file is not a valid DOCX file.", 400

        # Open the merged document
        doc = Document(modified_path)
    else:
        # Use the full template document
        doc = Document(template_path)
        doc.save(modified_path)

    # Replace placeholders in the document
    replace_placeholder(doc, '@chamado', data1)
    replace_placeholder(doc, '@cliente', data2)
    replace_placeholder(doc, '@modulo', data3)
    replace_placeholder(doc, '@data', data4)
    replace_placeholder(doc, '@descricao', data5)
    replace_placeholder(doc, '@usuario', usuario)
    doc.save(modified_path)

    # Insert images into the document
    insert_all_images_with_description(modified_path, image_files, image_descriptions)

    return send_file(modified_path, as_attachment=True)

def replace_placeholder(doc, placeholder, replacement):
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            if placeholder in run.text:
                run.text = run.text.replace(placeholder, replacement)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        if placeholder in run.text:
                            run.text = run.text.replace(placeholder, replacement)

def save_image(file):
    image_folder = temp_dir  # Use the global temp_dir
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    image_path = os.path.join(image_folder, secure_filename(file.filename))
    file.save(image_path)
    return image_path

def insert_all_images_with_description(doc_path, image_files, image_descriptions, insertion_placeholder='@prints'):
    doc = Document(doc_path)
    
    # Search in body paragraphs
    for paragraph in doc.paragraphs:
        if insertion_placeholder in paragraph.text:
            paragraph.text = ''  # Clear the placeholder
            for image_file, description in zip(image_files, image_descriptions):
                image_path = save_image(image_file)
                paragraph.add_run(description + '\n')
                paragraph.add_run().add_picture(image_path, width=Inches(1.0))
            break
    
    # Search in table cells
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if insertion_placeholder in paragraph.text:
                        paragraph.text = ''  # Clear the placeholder
                        for image_file, description in zip(image_files, image_descriptions):
                            image_path = save_image(image_file)
                            paragraph.add_run(description + '\n')
                            paragraph.add_run().add_picture(image_path, width=Inches(1.0))
                        break
    
    doc.save(doc_path)

def process_uploaded_doc(uploaded_doc_path, output_path):
    # Open the uploaded document
    uploaded_doc = Document(uploaded_doc_path)

    # Open the half-template document
    half_template_doc = Document(half_template_path)

    # Apply placeholders to the half-template document
    replace_placeholder(half_template_doc, '@chamado', request.form.get('data1', ''))
    replace_placeholder(half_template_doc, '@cliente', request.form.get('data2', ''))
    replace_placeholder(half_template_doc, '@modulo', request.form.get('data3', ''))
    replace_placeholder(half_template_doc, '@data', request.form.get('data4', ''))
    replace_placeholder(half_template_doc, '@descricao', request.form.get('data5', ''))
    replace_placeholder(half_template_doc, '@usuario', request.form.get('usuario', ''))

    # Find the specific line in the uploaded document
    found = False
    for i, paragraph in enumerate(uploaded_doc.paragraphs):
        if 'PREENCHIMENTO DO TESTE E QUALIDADE' in paragraph.text:
            found = True
            index = i
            break

    if found:
        # Remove all paragraphs after the found line
        for _ in range(len(uploaded_doc.paragraphs) - index - 1):
            p = uploaded_doc.paragraphs[index + 1]
            p._element.getparent().remove(p._element)

        # Append the modified half-template content to the uploaded document
        for element in half_template_doc.element.body:
            uploaded_doc.element.body.append(element)
    else:
        # If the line is not found, handle accordingly (optional)
        pass

    # Save the modified uploaded document to the output path
    uploaded_doc.save(output_path)

if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=True)
