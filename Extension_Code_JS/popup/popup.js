document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('toggleButton');
    const statusDiv = document.getElementById('status');

    function showStatus(message, isError = false) {
        statusDiv.textContent = message;
        statusDiv.className = isError ? 'error' : 'success';
        statusDiv.style.display = 'block';
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }

    function updateButtonState(isLogging) {
        toggleButton.textContent = isLogging ? 'Stop Logging' : 'Start Logging';
        toggleButton.className = isLogging ? 'stopped' : '';
    }

    // Get initial state
    chrome.runtime.sendMessage({action: 'getState'}, (response) => {
        if (response) {
            updateButtonState(response.isLogging);
        }
    });

    toggleButton.addEventListener('click', () => {
        const willEnable = toggleButton.textContent === 'Start Logging';
        chrome.runtime.sendMessage({
            action: 'toggleLogging',
            value: willEnable
        }, (response) => {
            if (response && response.isLogging !== undefined) {
                updateButtonState(response.isLogging);
                showStatus(`Logging ${response.isLogging ? 'started' : 'stopped'}`);
            } else {
                showStatus('Failed to toggle logging state', true);
            }
        });
    });
});