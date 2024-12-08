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
            return this.sendMessageToTab(this.activeTabId, command);
        } catch (error) {
            console.error('Error executing command:', error);
            throw error;
        }
    }

    sendMessageToTab(tabId, command) {
        return new Promise((resolve, reject) => {
            chrome.tabs.sendMessage(
                tabId,
                {
                    type: 'EXECUTE_ACTION',
                    action: command
                },
                (response) => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError);
                    } else {
                        resolve(response);
                    }
                }
            );
        });
    }

    getActiveTabId() {
        return this.activeTabId;
    }
}