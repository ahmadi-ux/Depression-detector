from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, storage, firestore
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize Firebase
# Make sure to place your Firebase service account key in the backend folder
cred = credentials.Certificate('firebase-key.json')
firebase_admin.initialize_app(cred, {
    'storageBucket': 'depression-detector-d83bb.appspot.com',
    'databaseURL': 'https://depression-detector-d83bb.firebaseio.com'
})

db = firestore.client()
bucket = storage.bucket()

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload to Firebase Storage and save metadata to Firestore
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Sanitize filename
        sanitized_filename = "".join(c if c.isalnum() or c in ('._-') else '_' for c in file.filename)
        
        # Create storage path
        timestamp = int(datetime.now().timestamp() * 1000)
        file_path = f'submissions/{timestamp}_{sanitized_filename}'
        
        # Upload to Firebase Storage
        blob = bucket.blob(file_path)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )
        
        # Get download URL
        download_url = blob.public_url
        
        # Save metadata to Firestore
        db.collection('submissions').add({
            'fileURL': download_url,
            'fileName': file.filename,
            'timestamp': datetime.now(),
            'uploadPath': file_path
        })
        
        return jsonify({
            'success': True,
            'fileURL': download_url,
            'fileName': file.filename,
            'message': 'File uploaded successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
