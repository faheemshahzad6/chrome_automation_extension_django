// background/network-monitor.js
export class NetworkMonitor {
    constructor(wsManager) {
        this.isEnabled = false;  // Explicitly start as disabled
        this.wsManager = wsManager;
        this.filters = {
            urls: ["<all_urls>"]
        };
        this.listeners = {
            onBeforeRequest: null,
            onBeforeSendHeaders: null,
            onResponseStarted: null,
            onCompleted: null,
            onErrorOccurred: null
        };
    }

    start() {
        if (this.isEnabled) {
            console.log('[NetworkMonitor] Already running');
            return false;
        }

        console.log('[NetworkMonitor] Starting network capture...');

        // Store bound listeners for removal later
        this.listeners.onBeforeRequest = this.handleRequest.bind(this);
        this.listeners.onBeforeSendHeaders = this.handleRequestHeaders.bind(this);
        this.listeners.onResponseStarted = this.handleResponse.bind(this);
        this.listeners.onCompleted = this.handleCompleted.bind(this);
        this.listeners.onErrorOccurred = this.handleError.bind(this);

        // Add listeners
        chrome.webRequest.onBeforeRequest.addListener(
            this.listeners.onBeforeRequest,
            this.filters,
            ["requestBody"]
        );

        chrome.webRequest.onBeforeSendHeaders.addListener(
            this.listeners.onBeforeSendHeaders,
            this.filters,
            ["requestHeaders"]
        );

        chrome.webRequest.onResponseStarted.addListener(
            this.listeners.onResponseStarted,
            this.filters,
            ["responseHeaders"]
        );

        chrome.webRequest.onCompleted.addListener(
            this.listeners.onCompleted,
            this.filters
        );

        chrome.webRequest.onErrorOccurred.addListener(
            this.listeners.onErrorOccurred,
            this.filters
        );

        this.isEnabled = true;
        console.log('[NetworkMonitor] Network capture started');
        return true;
    }

    stop() {
        if (!this.isEnabled) {
            console.log('[NetworkMonitor] Already stopped');
            return false;
        }

        console.log('[NetworkMonitor] Stopping network capture...');

        // Remove all listeners
        if (this.listeners.onBeforeRequest) {
            chrome.webRequest.onBeforeRequest.removeListener(this.listeners.onBeforeRequest);
        }
        if (this.listeners.onBeforeSendHeaders) {
            chrome.webRequest.onBeforeSendHeaders.removeListener(this.listeners.onBeforeSendHeaders);
        }
        if (this.listeners.onResponseStarted) {
            chrome.webRequest.onResponseStarted.removeListener(this.listeners.onResponseStarted);
        }
        if (this.listeners.onCompleted) {
            chrome.webRequest.onCompleted.removeListener(this.listeners.onCompleted);
        }
        if (this.listeners.onErrorOccurred) {
            chrome.webRequest.onErrorOccurred.removeListener(this.listeners.onErrorOccurred);
        }

        // Reset listeners
        Object.keys(this.listeners).forEach(key => {
            this.listeners[key] = null;
        });

        this.isEnabled = false;
        console.log('[NetworkMonitor] Network capture stopped');
        return true;
    }

    handleToggle(value) {
        console.log(`[NetworkMonitor] Toggle requested: ${value}`);

        const result = value ? this.start() : this.stop();

        return {
            success: result,
            isEnabled: this.isEnabled,
            timestamp: new Date().toISOString()
        };
    }

    handleRequest(details) {
        const requestData = {
            type: 'network_request',
            event: 'started',
            data: {
                requestId: details.requestId,
                url: details.url,
                method: details.method,
                type: details.type,
                timeStamp: details.timeStamp,
                requestBody: details.requestBody
            }
        };

        this.wsManager.sendMessage(requestData);
    }

    handleRequestHeaders(details) {
        const headerData = {
            type: 'network_request',
            event: 'headers',
            data: {
                requestId: details.requestId,
                url: details.url,
                headers: details.requestHeaders
            }
        };

        this.wsManager.sendMessage(headerData);
    }

    handleResponse(details) {
        const responseData = {
            type: 'network_request',
            event: 'response',
            data: {
                requestId: details.requestId,
                url: details.url,
                statusCode: details.statusCode,
                statusLine: details.statusLine,
                responseHeaders: details.responseHeaders,
                timeStamp: details.timeStamp
            }
        };

        this.wsManager.sendMessage(responseData);
    }

    handleCompleted(details) {
        const completedData = {
            type: 'network_request',
            event: 'completed',
            data: {
                requestId: details.requestId,
                url: details.url,
                timeStamp: details.timeStamp,
                fromCache: details.fromCache,
                responseSize: details.responseSize
            }
        };

        this.wsManager.sendMessage(completedData);
    }

    handleError(details) {
        const errorData = {
            type: 'network_request',
            event: 'error',
            data: {
                requestId: details.requestId,
                url: details.url,
                timeStamp: details.timeStamp,
                error: details.error
            }
        };

        this.wsManager.sendMessage(errorData);
    }

    getState() {
        return {
            isEnabled: this.isEnabled,
            timestamp: new Date().toISOString()
        };
    }
}