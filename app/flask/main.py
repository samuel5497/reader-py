from flask import Flask, jsonify, request
from pypdf import PdfReader
from tools.pdf_tools import extract_tables_from_pdf, convert_tables_to_json, save_file_into_server_from_request, delete_file_from_server

app = Flask(__name__)

@app.route("/ping")
def show():
    return {
        "data": {
            "attributes": {
                "content": "Este es un mensaje de prueba para configurar el subdominio"
            }
        }
    }


@app.route("/api/v1/link/tools/simple-extraction", methods=['POST'])
def store():
    request_json = request.get_json()
    file_path = save_file_into_server_from_request(request_json)

    pagination = {}
    reader = PdfReader(file_path)
    number_of_pages = len(reader.pages)

    for page in range(number_of_pages):
        page_object = reader.pages[page]
        page_content = page_object.extract_text()
        index_page = page + 1
        paginate = str(index_page)
        pagination[paginate] = page_content.replace('\n', ' ').strip()

    # Clean up
    delete_file_from_server(file_path)

    return {
        "data": {
            "attributes": {
                "pages": pagination
            }
        }
    }


@app.route('/api/v1/link/tools/tables-extraction', methods=['POST'])
def extract_data_tables():
    # if 'file' not in request.files:
    #     return jsonify({'error': 'No file part'}), 400
    #
    # file = request.files['file']
    # if file.filename == '':
    #     return jsonify({'error': 'No selected file'}), 400

    # Save the file to a temporary location
    #file_path = save_file_into_server_from_request(request)
    request_json = request.get_json()
    file_path = save_file_into_server_from_request(request_json)

    # Process the file
    tables = extract_tables_from_pdf(file_path)
    tables_json = convert_tables_to_json(tables)

    # Clean up
    delete_file_from_server(file_path)

    return jsonify(tables_json)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
