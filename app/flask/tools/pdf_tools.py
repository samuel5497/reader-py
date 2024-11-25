from fileinput import filename

import pandas as pd
from subprocess import check_output
from tabula import read_pdf
from base64 import b64decode
import uuid
import os

def extract_tables_from_pdf(pdf_path):
    # Leer las tablas del PDF usando tabula-py
    dfs = read_pdf(pdf_path, pages='all', multiple_tables=True)
    return dfs

def convert_tables_to_json(tables):
    all_tables_json = []
    for df in tables:
        json_data = df.to_dict(orient='records')
        all_tables_json.append(json_data)
    return all_tables_json


def save_file_into_server_from_request(request):
    request_data = request['data']
    object_file = request_data['file']

    b64 = object_file['b64']
    filename = object_file['name']
    mimetype = object_file['mimetype']

    # Decode the Base64 string, making sure that it contains only valid characters
    _bytes = b64decode(b64, validate=True)

    # Perform a basic validation to make sure that the result is a valid PDF file
    # Be aware! The magic number (file signature) is not 100% reliable solution to validate PDF files
    # Moreover, if you get Base64 from an untrusted source, you must sanitize the PDF contents
    if _bytes[0:4] != b'%PDF':
        raise ValueError('Missing the PDF file signature')

    path_file = str(uuid.uuid1()) + filename + '.pdf'

    # Write the PDF contents to a local file
    f = open(path_file, 'wb')
    f.write(_bytes)
    f.close()

    print(path_file)
    return path_file

def delete_file_from_server(path_file):
    os.remove(path_file)

def download_file_from_s3(path_s3, filename):
    command =  "aws s3 cp 's3://cpa-procesos/"+path_s3+"' ."+filename
    check_output(command, shell=True)

def upload_file_to_s3(filename, s3_file):
    command = "aws s3 cp '"+filename+"' 's3://cpa-procesos/"+s3_file+' 2>&1'
    check_output(command, shell=True)