import { WebSocketManager } from './websocket.js';
import { TabManager } from './tab-manager.js';

class BackgroundManager {
    constructor() {
        this.isEnabled = false;
        this.wsManager = new WebSocketManager();
        this.tabManager = new TabManager();
        this.initialize();
        this.navigationPromises = new Map();
    }

    async initialize() {
        // Restore state from storage
        const result = await chrome.storage.local.get(['isEnabled']);
        this.isEnabled = result.isEnabled || false;

        // Setup WebSocket message handler
        this.wsManager.setMessageHandler((data) => this.handleWebSocketMessage(data));

        if (this.isEnabled) {
            this.wsManager.connect();
        }

        this.setupMessageListeners();
    }

    setupMessageListeners() {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message, sender, sendResponse);
            return true; // Required for async response
        });
    }

    async handleMessage(message, sender, sendResponse) {
        try {
            switch (message.action) {
                case 'toggleLogging':
                    await this.handleToggleLogging(message, sendResponse);
                    break;

                case 'getState':
                    sendResponse({ isLogging: this.isEnabled });
                    break;

                default:
                    if (!this.isEnabled) {
                        sendResponse({ error: 'Extension is disabled' });
                        return;
                    }

                    if (message.type === 'SCRIPT_RESULT' || message.type === 'SCRIPT_ERROR') {
                        this.wsManager.sendMessage(message);
                        sendResponse({ received: true });
                    }
            }
        } catch (error) {
            console.error('Error handling message:', error);
            sendResponse({ error: error.message });
        }
    }

    async handleToggleLogging(message, sendResponse) {
        this.isEnabled = message.value;
        await chrome.storage.local.set({ isEnabled: this.isEnabled });

        if (this.isEnabled) {
            this.wsManager.connect();
        } else {
            this.wsManager.close();
        }

        sendResponse({ isLogging: this.isEnabled });
    }

async handleWebSocketMessage(data) {
    if (!this.isEnabled) return;

    try {
        if (data.type === 'error') {
            console.error('[Background] WebSocket error:', data.error);
            return;
        }

        if (data.type === 'automation_command') {
            console.log('[Background] Executing automation command:', data.command);

            // Special handling for navigation commands
            if (data.command.script?.startsWith('navigate|')) {
                const url = data.command.script.split('|')[1];
                const tab = await chrome.tabs.update({ url: url });

                // Send success response
                this.wsManager.sendMessage({
                    type: 'SCRIPT_RESULT',
                    status: 'success',
                    result: true,
                    command_id: data.command.command_id
                });

                return;
            }

            // Handle other commands
            await this.tabManager.executeCommand(data.command);
        }
    } catch (error) {
        console.error('[Background] Error handling WebSocket message:', error);
        this.wsManager.sendMessage({
            type: 'SCRIPT_ERROR',
            status: 'error',
            error: error.message,
            stack: error.stack,
            command_id: data.command?.command_id
        });
    }
}
}

// Initialize the background manager
const backgroundManager = new BackgroundManager();