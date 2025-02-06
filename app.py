from flask import Flask, render_template, request, send_file, redirect, url_for, jsonify
import os
from pdf2image import convert_from_path
from PIL import Image
import img2pdf

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['COMPRESSED_FOLDER'] = 'compressed'

# Create upload and compressed folders if they don't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['COMPRESSED_FOLDER']):
    os.makedirs(app.config['COMPRESSED_FOLDER'])

def compress_pdf(input_pdf, output_pdf, target_size_kb):
    # Convert PDF to images
    images = convert_from_path(input_pdf)
    temp_images = []
    for i, image in enumerate(images):
        temp_image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{i}.jpg")
        image.save(temp_image_path, "JPEG", quality=85)
        temp_images.append(temp_image_path)
    
    # Compress images and convert back to PDF
    while True:
        with open(output_pdf, "wb") as f:
            f.write(img2pdf.convert(temp_images))
        
        # Check if the file size is within the target limit
        size_kb = os.path.getsize(output_pdf) / 1024
        if size_kb <= target_size_kb:
            break
        
        # Reduce image quality further
        for temp_image in temp_images:
            img = Image.open(temp_image)
            img.save(temp_image, "JPEG", quality=int(img.info.get('quality', 85) * 0.9))
    
    # Clean up temporary images
    for temp_image in temp_images:
        os.remove(temp_image)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "No file uploaded"})
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "message": "No file selected"})
        if file:
            # Save the uploaded file
            input_pdf = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            output_pdf = os.path.join(app.config['COMPRESSED_FOLDER'], 'compressed_' + file.filename)
            file.save(input_pdf)
            
            # Compress the PDF
            compress_pdf(input_pdf, output_pdf, 200)
            
            # Return success response with download link
            return jsonify({
                "success": True,
                "download_url": url_for('download', filename='compressed_' + file.filename)
            })
    return render_template('index.html')

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(app.config['COMPRESSED_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
