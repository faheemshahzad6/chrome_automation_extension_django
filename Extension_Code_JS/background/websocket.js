export class WebSocketManager {
    constructor() {
        this.ws = null;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        this.messageHandler = null;
    }

    setMessageHandler(handler) {
        this.messageHandler = handler;
    }

    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
            console.log('WebSocket already connecting or connected');
            return;
        }

        this.isConnecting = true;
        console.log('Attempting to connect to WebSocket...');

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
            this.reconnectAttempts = 0;

            this.sendMessage({
                type: 'extension_connected',
                data: { extensionId: chrome.runtime.id }
            });
        };

        this.ws.onmessage = (event) => {
            console.log('WebSocket received message:', event.data);
            try {
                const data = JSON.parse(event.data);
                if (this.messageHandler) {
                    this.messageHandler(data);
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket closed with code:', event.code);
            this.handleConnectionError();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.isConnecting = false;
        };
    }

    handleConnectionError() {
        this.isConnecting = false;
        this.ws = null;

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            console.log(`Attempting to reconnect (${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})...`);
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), this.reconnectDelay);
        }
    }

    sendMessage(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify(message));
            } catch (error) {
                console.error('Error sending WebSocket message:', error);
            }
        }
    }

    close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}