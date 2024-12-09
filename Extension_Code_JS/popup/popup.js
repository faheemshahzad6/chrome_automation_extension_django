document.addEventListener('DOMContentLoaded', () => {
    const statusDiv = document.getElementById('status');

    function updateStatus(state) {
        const statusMessages = {
            connected: 'Connected to WebSocket',
            connecting: 'Connecting to WebSocket...',
            disconnected: 'Disconnected - Attempting to reconnect...',
            error: 'Connection Error - Retrying...'
        };

        statusDiv.textContent = statusMessages[state.connectionState] || 'Unknown Status';
        statusDiv.className = state.connectionState;
    }

    // Get initial state
    chrome.runtime.sendMessage({action: 'getState'}, (response) => {
        if (response) {
            updateStatus(response.wsState);
        }
    });

    // Listen for status updates
    chrome.runtime.onMessage.addListener((message) => {
        if (message.type === 'CONNECTION_STATE_CHANGED') {
            updateStatus(message.state);
        }
    });
});