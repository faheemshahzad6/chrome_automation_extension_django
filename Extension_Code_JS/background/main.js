import { WebSocketManager } from './websocket.js';
import { TabManager } from './tab-manager.js';
import { NetworkMonitor } from './network-monitor.js';

class BackgroundManager {
    constructor() {
        this.wsManager = new WebSocketManager();
        this.tabManager = new TabManager();
        this.networkMonitor = new NetworkMonitor(this.wsManager);
        this.statusCheckInterval = null;
        this.initialize();
    }

    async initialize() {
        try {
            // Setup WebSocket message handler
            this.wsManager.setMessageHandler((data) => this.handleWebSocketMessage(data));

            // Setup connection state listener
            this.wsManager.addConnectionStateListener((state) => this.handleConnectionStateChange(state));

            // Start WebSocket connection immediately
            this.wsManager.connect();

            // Start network monitoring
            this.networkMonitor.start();

            // Start periodic status check
            this.startStatusCheck();

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
                case 'getState':
                    sendResponse({
                        wsState: this.wsManager.getState(),
                        networkMonitorState: this.networkMonitor.getState()
                    });
                    break;

                case 'reconnectWebSocket':
                    this.wsManager.close();
                    this.wsManager.connect();
                    sendResponse({ status: 'reconnecting' });
                    break;

                case 'toggleNetworkMonitor':
                    if (message.value) {
                        this.networkMonitor.start();
                    } else {
                        this.networkMonitor.stop();
                    }
                    sendResponse({
                        status: 'success',
                        state: this.networkMonitor.getState()
                    });
                    break;

                default:
                    if (message.type === 'SCRIPT_RESULT' || message.type === 'SCRIPT_ERROR') {
                        const sent = await this.wsManager.sendMessage(message);
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

    handleConnectionStateChange(state) {
        console.log('[Background] WebSocket state changed:', state);

        // Update extension icon/badge based on connection state
        const badgeColors = {
            connected: '#4CAF50',
            connecting: '#FFC107',
            disconnected: '#F44336',
            error: '#F44336'
        };

        const badgeText = {
            connected: 'ON',
            connecting: '...',
            disconnected: 'OFF',
            error: 'ERR'
        };

        chrome.action.setBadgeText({
            text: badgeText[state.connectionState] || 'OFF'
        });

        chrome.action.setBadgeBackgroundColor({
            color: badgeColors[state.connectionState] || '#F44336'
        });

        // Notify popup if it's open
        chrome.runtime.sendMessage({
            type: 'CONNECTION_STATE_CHANGED',
            state: state
        }).catch(() => {}); // Ignore errors if popup is closed
    }

    async handleWebSocketMessage(data) {
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

    startStatusCheck() {
        // Clear any existing interval
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }

        // Check status every 10 seconds
        this.statusCheckInterval = setInterval(() => {
            const state = this.wsManager.getState();
            console.log(`[WebSocket Status Check] Status: ${state.connectionState}`);

            // Attempt to reconnect if disconnected
            if (state.connectionState === 'disconnected') {
                console.log('[WebSocket Status Check] Attempting to reconnect...');
                this.wsManager.connect();
            }
        }, 10000);
    }

    cleanup() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
        this.wsManager.close();
        this.networkMonitor.stop();
    }
}

// Initialize the background manager
console.log('[Background] Initializing BackgroundManager...');
const backgroundManager = new BackgroundManager();

// Handle extension updates/reinstalls
chrome.runtime.onInstalled.addListener((details) => {
    console.log('[Background] Extension installed/updated:', details.reason);
});

// Cleanup on extension unload
chrome.runtime.onSuspend.addListener(() => {
    console.log('[Background] Extension suspending...');
    if (backgroundManager) {
        backgroundManager.cleanup();
    }
});