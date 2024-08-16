from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np
import base64
import requests
import json
import os
import mysql.connector
import pandas as pd
from io import StringIO

app = Flask(__name__)

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'HappyHippo!',
    'database': 'compareTo'
}

# External API URL
url = "http://10.10.10.102:11434/api/generate"

# Headers for the API request
headers = {
    'Content-Type': 'application/json'
}

# Function to connect to the MySQL database
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    print("Successfully connected to MySQL")
    return conn

# Function to read and encode image file to base64
def encode_image_to_base64(image_file):
    try:
        image_bytes = image_file.read()
        return base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to read and encode a static reference image
def encode_static_image():
    static_image_path = os.path.join('static', 'network3.png')
    try:
        with open(static_image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The static file {static_image_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while encoding static image: {e}")
        return None

# Function to process incremental JSON responses
def process_incremental_response(response_chunks):
    responses = []
    for raw_response in response_chunks:
        try:
            data = json.loads(raw_response)
            responses.append(data['response'])
            if data['done']:
                break
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
    
    combined_response = ''.join(responses)
    return combined_response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400

        # Ensure the 'static' directory exists
        if not os.path.exists('static'):
            os.makedirs('static')

        # Save the file
        filename = file.filename
        file_path = os.path.join('static', filename)
        file.save(file_path)

        # Return the URL of the saved image
        return jsonify({'success': True, 'image_url': f'/static/{filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-csv', methods=['POST'])
def upload_csv():
    print("CSV upload")
    try:
        file = request.files.get('file')
        if not file or not file.filename.endswith('.csv'):
            return jsonify({'error': 'No CSV file provided or file is not a CSV'}), 400
        
        # Reads CSV file and decode it from binary
        csv_data = file.read().decode('utf-8')

        # Replaces b' with an empty string to clean up binary markers
        csv_data = csv_data.replace("b'", "").replace("'", "")

        # Converts CSV data to a dataframe
        df = pd.read_csv(StringIO(csv_data))

        # Verify the columns in the dataframe
        expected_columns = ['Application', 'Bytes Received', 'Bytes Sent', 'Bytes']
        if not all(col in df.columns for col in expected_columns):
            return jsonify({'error': 'CSV file is missing required columns'}), 400

        # Connect to MySQL and insert data
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create a table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flight_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                application VARCHAR(255),
                bytes_received VARCHAR(255),
                bytes_sent VARCHAR(255),
                total_bytes VARCHAR(255)
            )
        """)

        # Insert data into table
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO flight_data (application, bytes_received, bytes_sent, total_bytes)
                VALUES (%s, %s, %s, %s)
            """, (row['Application'], row['Bytes Received'], row['Bytes Sent'], row['Bytes']))

        conn.commit()
        cursor.close()
        conn.close()

        print('success')
        return jsonify({'success': True, 'message': 'CSV data uploaded and stored successfully.'})
    except Exception as e:
        print('fail')
        return jsonify({'error': str(e)}), 500


@app.route('/compare', methods=['POST'])
def compare_images():
    print("Analyzing...")
    try:
        file1 = request.files.get('file')
        if not file1:
            return jsonify({'success': False, 'error': 'Image must be provided'}), 400
        
        # Encode the uploaded image and the static image
        encoded_uploaded_image = encode_image_to_base64(file1)
        encoded_static_image = encode_static_image()

        if encoded_uploaded_image and encoded_static_image:
            data = {
                "model": "llava-llama3",
                "prompt": "You are an AI chatbot designed to provide a post-flight connectivity summary to business aviation customers. Analyze this graph of incoming and outgoing traffic in mbps on a client's aircraft throughout their flight. Provide a post-flight connectivity summary as if you are talking to a client who's jet just landed. Keep the summary brief and get straight to the point. Include the peak usage time, low usage time, and differences compared to past flights. Start with 'During your flight...'",
                "images": [encoded_uploaded_image, encoded_static_image]
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                try:
                    # Process the incremental JSON response
                    response_chunks = response.text.splitlines()
                    combined_response = process_incremental_response(response_chunks)

                    return jsonify({'success': True, 'comparison_result': combined_response})
                except json.JSONDecodeError:
                    return jsonify({'success': False, 'error': 'Failed to decode JSON response', 'response': response.text}), 500
            else:
                return jsonify({'success': False, 'error': f'Request failed with status code {response.status_code}', 'response': response.text}), 500
        else:
            return jsonify({'success': False, 'error': 'Failed to encode one or both images'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
