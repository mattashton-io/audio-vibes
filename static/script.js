document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const audioFile = document.getElementById('audio-file');
    const loadingDiv = document.getElementById('loading');
    const progressBar = document.getElementById('progress-bar');
    const transcriptionResultDiv = document.getElementById('transcription-result');
    const transcribedTextP = document.getElementById('transcribed-text');
    const errorMessageDiv = document.getElementById('error-message');
    const errorTextP = document.getElementById('error-text');

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        // Hide previous results/errors
        transcriptionResultDiv.classList.add('hidden');
        errorMessageDiv.classList.add('hidden');
        loadingDiv.classList.remove('hidden');
        progressBar.style.width = '0%'; // Reset progress bar

        const formData = new FormData();
        if (audioFile.files.length > 0) {
            formData.append('audio', audioFile.files[0]);
        } else {
            displayError('Please select an audio file to upload.');
            loadingDiv.classList.add('hidden'); // Hide loading if no file selected
            return;
        }

        // Simulate progress for demonstration
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            if (progress <= 90) { // Stop at 90% until actual response
                progressBar.style.width = progress + '%';
            }
        }, 500);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            clearInterval(interval); // Stop simulating progress
            progressBar.style.width = '100%'; // Complete progress bar

            if (response.ok) {
                const reader = response.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let receivedText = '';

                // Clear previous transcription
                transcribedTextP.textContent = '';
                transcriptionResultDiv.classList.remove('hidden');

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) {
                        break;
                    }
                    const chunk = decoder.decode(value, { stream: true });
                    // Assuming each 'data:' line contains a transcription segment
                    const lines = chunk.split('\n');
                    lines.forEach(line => {
                        if (line.startsWith('data:')) {
                            const data = line.substring(5).trim();
                            try {
                                // If the backend sends JSON, parse it. Otherwise, treat as plain text.
                                const json_data = JSON.parse(data);
                                if (json_data.transcription_segment) {
                                    transcribedTextP.textContent += json_data.transcription_segment + ' ';
                                }
                            } catch (e) {
                                // If not JSON, append as plain text
                                transcribedTextP.textContent += data + ' ';
                            }
                        }
                    });
                }
                loadingDiv.classList.add('hidden');
            } else {
                loadingDiv.classList.add('hidden');
                const errorData = await response.json();
                displayError(errorData.error || 'An unknown error occurred during upload.');
            }
        } catch (error) {
            clearInterval(interval); // Stop simulating progress
            loadingDiv.classList.add('hidden');
            displayError(`Network error: ${error.message}`);
        }
    });

    function displayError(message) {
        errorTextP.textContent = message;
        errorMessageDiv.classList.remove('hidden');
    }
});
