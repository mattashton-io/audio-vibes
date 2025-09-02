from flask import Flask, request, render_template, jsonify, Response, stream_with_context
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
        import google.generativeai as genai

        # Configure Gemini API (replace with your actual API key or environment variable)
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

        # Return a streaming response
        @stream_with_context
        def event_stream():
            try:
                client = speech.SpeechClient()

                audio = AudioSegment.from_file(filepath)
                
                # Define the chunk size for streaming (e.g., 5 seconds)
                chunk_length_ms = 5 * 1000  # 5 seconds
                
                # Configuration for the streaming recognition
                config = RecognitionConfig(
                    encoding=RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=audio.frame_rate, # Use actual sample rate from audio file
                    language_code="en-US",
                )
                streaming_config = speech.StreamingRecognitionConfig(
                    config=config,
                    interim_results=True # Get interim results for continuous transcription
                )

                # Generator to yield audio chunks
                def generate_audio_chunks():
                    for i in range(0, len(audio), chunk_length_ms):
                        chunk = audio[i:i + chunk_length_ms]
                        # Export chunk to bytes in WAV format
                        buffer = io.BytesIO()
                        chunk.export(buffer, format="wav", parameters=["-acodec", "pcm_s16le", "-ar", str(audio.frame_rate), "-ac", "1"])
                        yield buffer.getvalue()

                # Create a stream of requests
                requests = (speech.StreamingRecognizeRequest(audio_content=chunk)
                            for chunk in generate_audio_chunks())

                # Perform streaming recognition
                responses = client.streaming_recognize(streaming_config, requests)

                model = genai.GenerativeModel('gemini-pro')

                # Process responses
                for response in responses:
                    if not response.results:
                        continue

                    result = response.results[0]
                    if not result.alternatives:
                        continue

                    transcript = result.alternatives[0].transcript
                    
                    if result.is_final:
                        # Send each final segment to Gemini for formatting
                        prompt = f"Format the following text into a paragraph style. Ensure proper punctuation and grammar:\n\n{transcript.strip()}"
                        gemini_response = model.generate_content(prompt)
                        formatted_segment = gemini_response.text
                        
                        # Yield the formatted segment
                        yield f"data: {{\"transcription_segment\": \"{formatted_segment}\"}}\n\n"
            
            except Exception as e:
                error_message = f"Error during streaming transcription or formatting: {e}"
                yield f"data: {{\"error\": \"{error_message}\"}}\n\n"
            finally:
                # Clean up the original uploaded file after the stream is complete
                if os.path.exists(filepath):
                    os.remove(filepath)

        return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5002)
