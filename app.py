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
        from pydub import AudioSegment
        import io
        import math

        transcribed_text = ""
        
        try:
            client = speech.SpeechClient()

            audio = AudioSegment.from_file(filepath)
            
            # Google Speech-to-Text API has a limit of 1 minute for synchronous recognition
            # For longer audios, it's recommended to use asynchronous recognition or chunking.
            # Here, we'll chunk the audio into 55-second segments to stay within limits.
            chunk_length_ms = 55 * 1000  # 55 seconds
            total_length_ms = len(audio)
            
            num_chunks = math.ceil(total_length_ms / chunk_length_ms)

            for i in range(num_chunks):
                start_ms = i * chunk_length_ms
                end_ms = min((i + 1) * chunk_length_ms, total_length_ms)
                chunk = audio[start_ms:end_ms]

                # Export chunk to a temporary WAV file
                chunk_filepath = f"{filepath}_chunk_{i}.wav"
                chunk.export(chunk_filepath, format="wav", parameters=["-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1"])

                with io.open(chunk_filepath, "rb") as audio_file:
                    content = audio_file.read()

                audio_gcs = RecognitionAudio(content=content)
                config = RecognitionConfig(
                    encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=16000,
                    language_code="en-US",
                )

                response = client.recognize(config=config, audio=audio_gcs)

                if response.results:
                    for result in response.results:
                        transcribed_text += result.alternatives[0].transcript + " "
                
                os.remove(chunk_filepath) # Clean up the chunk file

            transcribed_text = transcribed_text.strip() # Remove trailing space

        except Exception as e:
            transcribed_text = f"Error processing audio file with Google Cloud Speech: {e}"
        
        os.remove(filepath) # Clean up the original uploaded file
        return jsonify({'transcription': transcribed_text})

if __name__ == '__main__':
    app.run(debug=True, port=5002)
