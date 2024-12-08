import { WebSocketManager } from './websocket.js';
import { TabManager } from './tab-manager.js';

class BackgroundManager {
    constructor() {
        this.isEnabled = false;
        this.wsManager = new WebSocketManager();
        this.tabManager = new TabManager();
        this.initialize();
    }

    async initialize() {
        try {
            // Restore state from storage
            const result = await chrome.storage.local.get(['isEnabled']);
            this.isEnabled = result.isEnabled ?? false;

            // Setup WebSocket message handler
            this.wsManager.setMessageHandler((data) => this.handleWebSocketMessage(data));

            // Setup connection state listener
            this.wsManager.addConnectionStateListener((state) => this.handleConnectionStateChange(state));

            if (this.isEnabled) {
                this.wsManager.connect();
            }

            this.setupMessageListeners();
            console.log('[Background] Initialization complete');
        } catch (error) {
            console.error('[Background] Initialization error:', error);
        }
    }

    setupMessageListeners() {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message, sender, sendResponse);
            return true; // Required for async response
        });
    }

    async handleMessage(message, sender, sendResponse) {
        try {
            console.log('[Background] Received message:', message);

            switch (message.action) {
                case 'toggleLogging':
                    await this.handleToggleLogging(message, sendResponse);
                    break;

                case 'getState':
                    sendResponse({
                        isLogging: this.isEnabled,
                        wsState: this.wsManager.getState()
                    });
                    break;

                case 'reconnectWebSocket':
                    if (this.isEnabled) {
                        this.wsManager.close();
                        this.wsManager.connect();
                        sendResponse({ status: 'reconnecting' });
                    } else {
                        sendResponse({ status: 'disabled' });
                    }
                    break;

                default:
                    if (!this.isEnabled) {
                        sendResponse({ error: 'Extension is disabled' });
                        return;
                    }

                    if (message.type === 'SCRIPT_RESULT' || message.type === 'SCRIPT_ERROR') {
                        const sent = this.wsManager.sendMessage(message);
                        sendResponse({ received: true, sent });
                    } else {
                        sendResponse({ error: 'Unknown message type' });
                    }
            }
        } catch (error) {
            console.error('[Background] Error handling message:', error);
            sendResponse({ error: error.message });
        }
    }

    async handleToggleLogging(message, sendResponse) {
        try {
            this.isEnabled = message.value;
            await chrome.storage.local.set({ isEnabled: this.isEnabled });

            if (this.isEnabled) {
                this.wsManager.connect();
            } else {
                this.wsManager.close();
            }

            sendResponse({
                isLogging: this.isEnabled,
                wsState: this.wsManager.getState()
            });
        } catch (error) {
            console.error('[Background] Error toggling logging:', error);
            sendResponse({ error: error.message });
        }
    }

    handleConnectionStateChange(state) {
        console.log('[Background] WebSocket state changed:', state);

        // Update extension icon/badge based on connection state
        const badgeColors = {
            connected: '#4CAF50',
            connecting: '#FFC107',
            disconnected: '#F44336',
            error: '#F44336',
            waiting: '#FF9800',
            failed: '#F44336'
        };

        const badgeText = {
            connected: 'ON',
            connecting: '...',
            disconnected: 'OFF',
            error: 'ERR',
            waiting: 'WAIT',
            failed: 'FAIL'
        };

        chrome.action.setBadgeText({
            text: this.isEnabled ? (badgeText[state.connectionState] || 'OFF') : ''
        });

        if (this.isEnabled) {
            chrome.action.setBadgeBackgroundColor({
                color: badgeColors[state.connectionState] || '#F44336'
            });
        }
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

    cleanup() {
        this.wsManager.reset();
        this.tabManager = null;
    }
}

// Initialize the background manager
console.log('[Background] Initializing BackgroundManager...');
const backgroundManager = new BackgroundManager();

// Handle extension updates/reinstalls
chrome.runtime.onInstalled.addListener(async (details) => {
    console.log('[Background] Extension installed/updated:', details.reason);

    if (details.reason === 'install') {
        await chrome.storage.local.set({ isEnabled: false });
    }
});

// Cleanup on extension unload
chrome.runtime.onSuspend.addListener(() => {
    console.log('[Background] Extension suspending...');
    if (backgroundManager) {
        backgroundManager.cleanup();
    }
});