export class TabManager {
    constructor() {
        this.activeTabId = null;
        this.setupTabListeners();
        this.initialize();
    }

    async initialize() {
        const tabs = await chrome.tabs.query({active: true, currentWindow: true});
        if (tabs[0]) {
            this.activeTabId = tabs[0].id;
        }
    }

    setupTabListeners() {
        chrome.tabs.onActivated.addListener((activeInfo) => {
            this.activeTabId = activeInfo.tabId;
            console.log('Active tab changed to:', this.activeTabId);
        });

        chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
            if (changeInfo.status === 'complete' && tab.active) {
                this.activeTabId = tabId;
                console.log('Active tab updated:', this.activeTabId);
            }
        });
    }

    async injectContentScript(tabId) {
        try {
            const tab = await chrome.tabs.get(tabId);
            if (!tab.url.startsWith('chrome://')) {
                console.log('Injecting content scripts into tab:', tabId);
                await chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    files: [
                        'content/logger.js',
                        'content/storage-commands.js',
                        'content/basic-commands.js',
                        'content/handler.js',
                        'content/main.js'
                    ]
                });
                console.log('Content scripts injected successfully');
            }
        } catch (error) {
            console.error('Error injecting content scripts:', error);
            throw error;
        }
    }

    async executeCommand(command) {
        if (!this.activeTabId) {
            throw new Error('No active tab found');
        }

        try {
            await this.injectContentScript(this.activeTabId);

            // Ensure command is properly formatted
            const formattedCommand = {
                type: 'EXECUTE_SCRIPT',
                script: typeof command === 'string' ? command : command.script,
                command_id: command.command_id
            };

            return this.sendMessageToTab(this.activeTabId, formattedCommand);
        } catch (error) {
            console.error('Error executing command:', error);
            throw error;
        }
    }

    // In tab-manager.js, update the sendMessageToTab method:
    sendMessageToTab(tabId, command) {
    return new Promise((resolve, reject) => {
        try {
            // Validate command object
            if (!command || typeof command !== 'object') {
                reject(new Error('Invalid command format'));
                return;
            }

            chrome.tabs.sendMessage(
                tabId,
                {
                    type: 'EXECUTE_ACTION',
                    action: command
                },
                (response) => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError);
                        return;
                    }

                    if (!response) {
                        reject(new Error('No response received from content script'));
                        return;
                    }

                    if (response.type === 'SCRIPT_ERROR') {
                        reject(new Error(response.error));
                        return;
                    }

                    resolve(response);
                }
            );
        } catch (error) {
            reject(error);
        }
    });
}

    getActiveTabId() {
        return this.activeTabId;
    }
}