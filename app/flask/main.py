import uuid
from fileinput import filename
from flask import Flask, jsonify, request
from pypdf import PdfReader
from tools.pdf_tools import extract_tables_from_pdf, convert_tables_to_json, save_file_into_server_from_request
from tools.pdf_tools import delete_file_from_server, download_file_from_s3, upload_file_to_s3
from PyPDF2 import PdfWriter


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


@app.route('/api/v1/link/tools/join-pdfs', methods=['POST'])
def join_pdfs():
    try:
        request_json = request.get_json()
        files = request_json['data']['files']
        new_files = []

        output_filename = str(uuid.uuid1()) + '.pdf'
        s3_file = 'cpa-link/pdf/unions/'+output_filename

        merger = PdfWriter()

        for file in files:
            path_s3 = file['path_s3']

            filename = str(uuid.uuid1()) + '.pdf'
            new_files.append(filename)
            download_file_from_s3(path_s3, filename)
            merger.append(filename)

        merger.write(output_filename)
        merger.close()

        upload_file_to_s3(output_filename, s3_file)

        # Clean up files
        for new_file in new_files:
            delete_file_from_server(new_file)

        return {
            "data": {
                "file": {
                    "name": output_filename,
                    'mimeype': 'application/pdf',
                    'path_s3': s3_file
                }
            }
        }
    except Exception as exception:
        return jsonify({'error': str(exception)}), 500



if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
