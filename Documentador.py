import os
import tempfile
from io import BytesIO
from flask import Flask, render_template, request, send_file, after_this_request
from docx import Document
from docx.shared import Inches
import requests
import json
from apscheduler.schedulers.background import BackgroundScheduler
from google.oauth2 import service_account
import gspread
from flask import Flask, jsonify, render_template, send_from_directory

app = Flask(__name__)

template_path = r'C:\Users\Administrator\Documents\doc\TemplateDocument.docx'
api_url = os.environ.get('API_URL') or 'http://18.229.136.181/api/getclientes.php'
spreadsheet_id = "1k9EnmxSRI-5Z6zp6THn7UnQszBzSRdKtiKn7OvFy9mo"
credentials = service_account.Credentials.from_service_account_file(
    r'C:\Users\Administrator\Desktop\documentador\key\DocKey.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)

temp_dir = tempfile.mkdtemp()

scheduler = BackgroundScheduler()
# scheduler.add_job(lambda: clean_temp_folder(temp_dir), 'interval', minutes=5)
scheduler.start()

#def clean_temp_folder(temp_folder):
   # for file_name in os.listdir(temp_folder):
    #    file_path = os.path.join(temp_folder, file_name)
     #   try:
      #      if os.path.isfile(file_path):
       #         os.unlink(file_path)
       # except Exception as e:
        #    print(f"Error deleting file: {e}")
        
def get_data_from_api(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise HTTPError for bad responses

        # Remove UTF-8 BOM manually
        content = response.content.decode('utf-8')
        if content.startswith('\ufeff'):
            content = content[1:]

        data = json.loads(content)

        return data
    except requests.RequestException as e:
        print(f"Error in API request: {e}")
        return None

@app.route('/')
def index():
    # Fetch data from the API
    clients_data = get_data_from_api(api_url)

    # Print the received data for debugging
    #print("Received clients data:", clients_data)

    # Pass the data to the HTML template
    return render_template('index.html', clients=clients_data)

@app.route('/fetch_chamado_data', methods=['POST'])
def fetch_chamado_data():
    chamado_value = request.form['chamado']

    # Fetch data from the Google Sheets based on the chamado value
    result = get_data_by_chamado(chamado_value)

    # Return the result as JSON
    return jsonify(result)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/get_client_code', methods=['POST'])
def get_client_code():
    client_name = request.form.get('client_name')

    # Make a request to your XAMPP API to get the client code
    xampp_api_url = 'http://18.229.136.181/api/get_client_code.php'  # Adjust the URL accordingly
    response = requests.post(xampp_api_url, data={'clientName': client_name})

    if response.status_code == 200:
        data = response.json()
        if data['success']:
            return jsonify({'success': True, 'clientCode': data['clientCode']})
        else:
            return jsonify({'success': False, 'message': 'Client not found'})
    else:
        return jsonify({'success': False, 'message': 'Error in the XAMPP API request'})


@app.route('/process_template', methods=['POST'])
def process_template():
    doc = Document(template_path)

    # Replace placeholders with data from the form
    replace_placeholder(doc, '@chamado', request.form['data1'])
    replace_placeholder(doc, '@cliente', request.form['data2'])
    replace_placeholder(doc, '@modulo', request.form['data3'])
    replace_placeholder(doc, '@data', request.form['data4'])
    replace_placeholder(doc, '@descricao', request.form['data5'])

    client_name = request.form['data2']
    chamado_value = request.form['data1']

    # Fetch data from Google Sheets based on chamado
    chamado_data = get_data_by_chamado(chamado_value)

    if chamado_data:
        # Use chamado_data['cliente'] for further operations

        # Make a request to your XAMPP API to get the client code
        xampp_api_url = f'http://18.229.136.181/api/get_client_code.php?clientName={client_name}'  # Adjust the URL accordingly

    try:
        response = requests.get(xampp_api_url)

        if response.status_code == 200:
            print(response.text)  # Print the full response content for debugging

        # Remove BOM from the response
            response_text = response.text.lstrip('\ufeff')

            try:
            # Attempt to parse JSON response
                response_json = json.loads(response_text)
                client_code = response_json.get('clientCode')

                if client_code:
                # Replace the placeholder in the document
                    replace_placeholder(doc, '@caminho', f'J:\\clientes\\{client_code}\\teorema.fdb')
                else:
                    print('Client code not found in the API response.')
            except json.JSONDecodeError as je:
                print(f'Error decoding JSON: {je}')
        else:
            print('Error in the XAMPP API request:', response.status_code)
    except Exception as e:
        print(f'Error in the XAMPP API request: {e}')


    # Save the modified document
    modified_filename = f'DOCUMENTAÇÃO - {request.form["data2"]}.docx'
    modified_path = os.path.join(temp_dir, modified_filename)
    doc.save(modified_path)

    # Handle multiple image uploads for "Prints" field
    files = request.files.getlist('data6[]')
    image_paths = [save_image(file) for file in files]
    insert_images_after_placeholder(modified_path, image_paths)

    return send_file(modified_path, as_attachment=True)

def get_data_by_chamado(chamado_value):
    gc = gspread.authorize(credentials)

    # Open the Google Sheets document by key or URL
    spreadsheet = gc.open_by_key(spreadsheet_id)

    # Select the first sheet in the document
    sheet = spreadsheet.get_worksheet(0)

    try:
        # Find the row where column E (5th column) matches the chamado value
        cell = sheet.find(chamado_value, in_column=5)

        # Get data from columns A, D, E, and G based on the found row
        data_a = sheet.cell(cell.row, 1).value
        data_c = sheet.cell(cell.row, 3).value  # Assuming 3rd column is the one you want to check
        data_e = sheet.cell(cell.row, 5).value  # Assuming 5th column is chamado
        data_b = sheet.cell(cell.row, 6).value  # Assuming 6th column is modulo
        cliente_data = sheet.cell(cell.row, 7).value  # Assuming 7th column is cliente

        # Filter data based on column D
        if data_c == 'A':
            return {
                'chamado': data_e,
                'cliente': cliente_data,
                'modulo': data_b,
                'data': data_a
    }
        else:
            return None
    except Exception as e:
        print(f"Error in get_data_by_chamado: {e}")
        return None



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
    image_folder = os.path.join(temp_dir)
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    image_path = os.path.join(image_folder, file.filename)
    file.save(image_path)
    return image_path

def insert_images_after_placeholder(doc_path, image_paths, placeholder='@prints'):
    doc = Document(doc_path)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if placeholder in paragraph.text:
                        # Clear the existing paragraph with the @prints placeholder
                        paragraph.clear()

                        # Insert new paragraphs with images after the cleared one
                        for image_path in image_paths:
                            p = cell.add_paragraph()
                            run = p.add_run()
                            run.add_picture(image_path, width=Inches(5.0))

    # Save the modified document
    doc.save(doc_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)