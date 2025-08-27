document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    const audioFile = document.getElementById('audio-file');
    const loadingDiv = document.getElementById('loading');
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

        const formData = new FormData();
        if (audioFile.files.length > 0) {
            formData.append('audio', audioFile.files[0]);
        } else {
            displayError('Please select an audio file to upload.');
            return;
        }

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            loadingDiv.classList.add('hidden');

            if (response.ok) {
                const data = await response.json();
                if (data.transcription) {
                    transcribedTextP.textContent = data.transcription;
                    transcriptionResultDiv.classList.remove('hidden');
                } else {
                    displayError('Transcription failed: No transcription data received.');
                }
            } else {
                const errorData = await response.json();
                displayError(errorData.error || 'An unknown error occurred during upload.');
            }
        } catch (error) {
            loadingDiv.classList.add('hidden');
            displayError(`Network error: ${error.message}`);
        }
    });

    function displayError(message) {
        errorTextP.textContent = message;
        errorMessageDiv.classList.remove('hidden');
    }
});
