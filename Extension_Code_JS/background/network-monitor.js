// background/network-monitor.js
export class NetworkMonitor {
    constructor(wsManager) {
        this.isEnabled = false;
        this.wsManager = wsManager;
        this.filters = {
            urls: ["<all_urls>"]
        };
        this.requestTypes = [
            "main_frame", "sub_frame", "stylesheet", "script",
            "image", "font", "object", "xmlhttprequest",
            "ping", "csp_report", "media", "websocket", "other"
        ];
    }

    start() {
        if (this.isEnabled) return;

        this.isEnabled = true;

        // Monitor request started
        chrome.webRequest.onBeforeRequest.addListener(
            this.handleRequest.bind(this),
            this.filters,
            ["requestBody"]
        );

        // Monitor request headers
        chrome.webRequest.onBeforeSendHeaders.addListener(
            this.handleRequestHeaders.bind(this),
            this.filters,
            ["requestHeaders"]
        );

        // Monitor response started
        chrome.webRequest.onResponseStarted.addListener(
            this.handleResponse.bind(this),
            this.filters,
            ["responseHeaders"]
        );

        // Monitor request completed
        chrome.webRequest.onCompleted.addListener(
            this.handleCompleted.bind(this),
            this.filters
        );

        // Monitor request errors
        chrome.webRequest.onErrorOccurred.addListener(
            this.handleError.bind(this),
            this.filters
        );

        console.log('[NetworkMonitor] Started monitoring network requests');
    }

    stop() {
        if (!this.isEnabled) return;

        this.isEnabled = false;

        chrome.webRequest.onBeforeRequest.removeListener(this.handleRequest);
        chrome.webRequest.onBeforeSendHeaders.removeListener(this.handleRequestHeaders);
        chrome.webRequest.onResponseStarted.removeListener(this.handleResponse);
        chrome.webRequest.onCompleted.removeListener(this.handleCompleted);
        chrome.webRequest.onErrorOccurred.removeListener(this.handleError);

        console.log('[NetworkMonitor] Stopped monitoring network requests');
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