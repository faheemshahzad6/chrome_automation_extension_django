// websocket.js
export class WebSocketManager {
    constructor() {
        this.ws = null;
        this.isConnecting = false;
        this.reconnectTimer = null;
        this.statusCheckTimer = null;
        this.messageHandler = null;
        this.connectionStateListeners = new Set();
        this.connectionState = 'disconnected';
    }

    setMessageHandler(handler) {
        this.messageHandler = handler;
    }

    addConnectionStateListener(listener) {
        this.connectionStateListeners.add(listener);
    }

    removeConnectionStateListener(listener) {
        this.connectionStateListeners.delete(listener);
    }

    updateConnectionState(state) {
        this.connectionState = state;
        this.connectionStateListeners.forEach(listener => listener({
            connectionState: state,
            timestamp: new Date().toISOString()
        }));

        // Log status to console
        console.log(`[WebSocket Status]: ${state} - ${new Date().toISOString()}`);
    }

    connect() {
        if (this.isConnecting) {
            return;
        }

        this.isConnecting = true;
        this.updateConnectionState('connecting');

        try {
            this.ws = new WebSocket('ws://localhost:1234/ws/app_chrome_automation_with_extension_django/');
            this.setupWebSocketHandlers();
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.handleConnectionError();
        }
    }

    setupWebSocketHandlers() {
        this.ws.onopen = () => {
            console.log('Connected to Django server');
            this.isConnecting = false;
            this.updateConnectionState('connected');

            // Clear any existing reconnect timer
            if (this.reconnectTimer) {
                clearTimeout(this.reconnectTimer);
                this.reconnectTimer = null;
            }

            this.sendMessage({
                type: 'extension_connected',
                data: { extensionId: chrome.runtime.id }
            });
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (this.messageHandler) {
                    this.messageHandler(data);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.ws.onclose = () => {
            this.handleConnectionError();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.handleConnectionError();
        };
    }

    handleConnectionError() {
        this.isConnecting = false;
        this.ws = null;
        this.updateConnectionState('disconnected');

        // Schedule reconnection
        if (!this.reconnectTimer) {
            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null;
                this.connect();
            }, 10000); // Reconnect every 10 seconds
        }
    }

    startStatusCheck() {
        // Clear any existing timer
        if (this.statusCheckTimer) {
            clearInterval(this.statusCheckTimer);
        }

        // Check status every 10 seconds
        this.statusCheckTimer = setInterval(() => {
            const isConnected = this.ws && this.ws.readyState === WebSocket.OPEN;
            console.log(`[WebSocket Status Check] ${isConnected ? 'Connected' : 'Disconnected'}`);

            if (!isConnected && !this.reconnectTimer && !this.isConnecting) {
                this.connect();
            }
        }, 10000);
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
                return true;
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
                return false;
            }
        }
        return false;
    }

    getState() {
        return {
            connectionState: this.connectionState,
            timestamp: new Date().toISOString()
        };
    }

    reset() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.statusCheckTimer) {
            clearInterval(this.statusCheckTimer);
            this.statusCheckTimer = null;
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}