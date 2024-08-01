from flask import Flask, request, jsonify, render_template
import cv2
import numpy as np
import base64
import requests
import json
import os

app = Flask(__name__)

# External API URL
url = "http://10.10.10.102:11434/api/generate"

# Headers for the API request
headers = {
    'Content-Type': 'application/json'
}

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

"""
@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        file = request.files['file']
        if not file:
            return jsonify({'error': 'No file provided'}), 400

        encoded_image = encode_image_to_base64(file)
        if encoded_image:
            return jsonify({'encoded_image': encoded_image})
        else:
            return jsonify({'error': 'Failed to encode image'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
"""

@app.route('/upload', methods=['POST'])
def upload_image():
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


@app.route('/compare', methods=['POST'])
def compare_images():
    try:
        file1 = request.files.get('file1')
        # file2 = request.files.get('file2')

        if not file1:
            return jsonify({'success': False, 'error': 'Image must be provided'}), 400
        
        # Encode the uploaded image and the static image
        encoded_uploaded_image = encode_image_to_base64(file1)
        encoded_static_image = encode_static_image()

        if encoded_uploaded_image and encoded_static_image:
            data = {
                "model": "llava-llama3",
                "prompt": "Please analyze the two images provided. The first image is a graph of network data. If the first image is not a graph, respond with {'error': 'Please upload a graph'}. If the first image is a graph, compare it to the second image, which is a reference graph. Provide the analysis in the following JSON format:\n\n{\n  'peak_usage_time': '[Provide the peak usage time]',\n  'low_usage_time': '[Provide the low usage time]',\n  'differences': '[Describe the differences between the first and second graph]'\n}",
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

"""
@app.route('/test-connection', methods=['GET'])
def test_connection():
    try:
        image_path1 = os.path.join(app.static_folder, 'graph1.jpg')
        image_path2 = os.path.join(app.static_folder, 'graph2.png')

        print(f"Checking image paths: {image_path1} and {image_path2}")

        if not os.path.exists(image_path1) or not os.path.exists(image_path2):
            return jsonify({'error': 'One or both test images not found'}), 500
        
        with open(image_path1, 'rb') as img_file1, open(image_path2, 'rb') as img_file2:
            encoded_image1 = encode_image_to_base64(img_file1)
            encoded_image2 = encode_image_to_base64(img_file2)

        if encoded_image1 and encoded_image2:
            data = {
                "model": "llava-llama3",
                "prompt": "Compare these two images",
                "images": [encoded_image1, encoded_image2]
            }

            response = requests.post(url, headers=headers, json=data)

            if response.status_code == 200:
                try:
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
"""

if __name__ == '__main__':
    app.run(debug=True)
