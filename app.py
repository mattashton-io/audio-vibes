from flask import Flask, request, render_template, jsonify
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file part'}), 400
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        from google.cloud import speech
        from google.cloud.speech import RecognitionConfig, RecognitionAudio
        import io

        transcribed_text = "Transcription failed."

        try:
            client = speech.SpeechClient()

            with io.open(filepath, "rb") as audio_file:
                content = audio_file.read()

            audio = RecognitionAudio(content=content)
            config = RecognitionConfig(
                encoding=RecognitionConfig.AudioEncoding.LINEAR16, # Assuming common audio format
                sample_rate_hertz=16000, # Common sample rate, adjust if needed
                language_code="en-US",
            )

            response = client.recognize(config=config, audio=audio)

            if response.results:
                transcribed_text = response.results[0].alternatives[0].transcript
            else:
                transcribed_text = "No transcription results found."

        except Exception as e:
            transcribed_text = f"Error processing audio file with Google Cloud Speech: {e}"
        
        os.remove(filepath) # Clean up the uploaded file
        return jsonify({'transcription': transcribed_text})

if __name__ == '__main__':
    app.run(debug=True, port=5002)
