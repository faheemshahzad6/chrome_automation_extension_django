window.AutomationHandler = class AutomationHandler {
    constructor() {
        window.automationLogger.info('Initializing AutomationHandler');
        this.commands = {};
        this.activeRequests = new Map();
        this.pendingNavigations = new Set();
        this.setupMessageListener();
        this.setupNavigationListener();
        this.setupErrorHandler();
    }

    registerCommands(commandsObject) {
        try {
            // Validate input
            if (!commandsObject || typeof commandsObject !== 'object') {
                throw new Error('Invalid commands object provided');
            }

            // Register each command
            Object.entries(commandsObject).forEach(([name, fn]) => {
                if (typeof fn !== 'function') {
                    window.automationLogger.error(`Invalid command type for ${name}:`, typeof fn);
                    return;
                }
                this.commands[name] = this.wrapCommandFunction(name, fn);
            });

            window.automationLogger.info('Registered commands:', Object.keys(this.commands));
        } catch (error) {
            window.automationLogger.error('Error registering commands:', error);
            throw error;
        }
    }

    wrapCommandFunction(name, fn) {
        return async (...args) => {
            const startTime = performance.now();
            try {
                window.automationLogger.info(`Executing command: ${name}`, args);
                const result = await fn(...args);
                const duration = performance.now() - startTime;
                window.automationLogger.success(`Command ${name} completed in ${duration.toFixed(2)}ms`);
                return result;
            } catch (error) {
                const duration = performance.now() - startTime;
                window.automationLogger.error(`Command ${name} failed after ${duration.toFixed(2)}ms:`, error);
                throw error;
            }
        };
    }

    setupNavigationListener() {
        // Listen for navigation events
        window.addEventListener('beforeunload', () => {
            this.pendingNavigations.add(Date.now());
        });

        window.addEventListener('load', () => {
            this.pendingNavigations.clear();
        });
    }

    setupErrorHandler() {
        window.onerror = (message, source, lineno, colno, error) => {
            window.automationLogger.error('Global error caught', {
                message,
                source,
                lineno,
                colno,
                error: error?.stack
            });
        };

        window.onunhandledrejection = (event) => {
            window.automationLogger.error('Unhandled promise rejection', {
                reason: event.reason
            });
        };
    }

    // In handler.js, replace the setupMessageListener method with:
    setupMessageListener() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        // Immediate validation
        if (!message || !message.type || !message.action) {
            sendResponse({
                type: 'SCRIPT_ERROR',
                status: 'error',
                error: 'Invalid message format'
            });
            return false;
        }

        if (message.type === 'EXECUTE_ACTION') {
            // Send immediate acknowledgment
            sendResponse({
                type: 'RECEIVED',
                status: 'processing',
                command_id: message.action.command_id
            });

            // Handle the action
            this.handleAction(message.action)
                .then(result => {
                    // Send result through runtime message
                    chrome.runtime.sendMessage({
                        type: 'SCRIPT_RESULT',
                        status: 'success',
                        result: result,
                        command_id: message.action.command_id
                    });
                })
                .catch(error => {
                    // Send error through runtime message
                    chrome.runtime.sendMessage({
                        type: 'SCRIPT_ERROR',
                        status: 'error',
                        error: error.message,
                        stack: error.stack,
                        command_id: message.action.command_id
                    });
                });

            return false; // We've already sent the response
        }

        return false; // Not handling other message types
    });
}

    // In handler.js, update the handleAction method:
    async handleAction(action) {
    window.automationLogger.info('Handling action', action);

    try {
        if (action.type !== 'EXECUTE_SCRIPT') {
            throw new Error(`Unknown action type: ${action.type}`);
        }

        const { command, params } = this.parseCommand(action.script);

        if (!this.commands[command]) {
            throw new Error(`Unknown command: ${command}`);
        }

        // Track the request
        const requestId = action.command_id || Date.now().toString();
        this.activeRequests.set(requestId, {
            command,
            params,
            startTime: Date.now()
        });

        try {
            let result;
            // Special handling for navigation commands
            if (command === 'navigate') {
                result = await this.handleNavigationCommand(command, params);
            } else {
                // Execute regular command
                result = await Promise.resolve(this.commands[command](params));
            }

            this.activeRequests.delete(requestId);
            return this.formatResult(result);
        } catch (error) {
            this.activeRequests.delete(requestId);
            throw error;
        }
    } catch (error) {
        window.automationLogger.error('Action handling error:', error);
        throw error;
    }
}

    async handleNavigationCommand(command, params) {
        return new Promise((resolve, reject) => {
            try {
                // Set up navigation completion listener
                const navigationTimeout = setTimeout(() => {
                    reject(new Error('Navigation timeout'));
                }, 30000); // 30 second timeout

                const handleNavigation = () => {
                    clearTimeout(navigationTimeout);
                    window.removeEventListener('load', handleNavigation);
                    resolve(true);
                };

                window.addEventListener('load', handleNavigation);

                // Execute navigation command
                this.commands[command](params);
            } catch (error) {
                reject(error);
            }
        });
    }

    // In handler.js, update the parseCommand method:
    parseCommand(script) {
    try {
        if (!script || typeof script !== 'string') {
            throw new Error('Invalid command format: script must be a string');
        }

        const parts = script.split('|');
        if (parts.length === 0) {
            throw new Error('Invalid command format: empty command');
        }

        const command = parts[0].trim();
        if (!command) {
            throw new Error('Invalid command format: empty command name');
        }

        let params = {};
        if (parts.length > 1) {
            if (command === 'navigate') {
                params = { url: parts[1].trim() };
            } else {
                try {
                    // Try parsing as JSON
                    params = JSON.parse(parts[1]);
                } catch {
                    // For other commands, keep existing behavior
                    const paramParts = parts.slice(1);
                    if (paramParts.length === 1) {
                        params = paramParts[0];
                    } else {
                        params = paramParts;
                    }
                }
            }
        }

        return { command, params };
    } catch (error) {
        throw new Error(`Command parsing error: ${error.message}`);
    }
}

    formatResult(result) {
        try {
            if (result === undefined) return null;
            if (result === null) return null;

            if (result instanceof Promise) {
                return result.then(res => this.formatResult(res));
            }

            if (result instanceof Error) {
                return {
                    error: result.message,
                    stack: result.stack
                };
            }

            if (typeof result === 'function') {
                return `[Function: ${result.name || 'anonymous'}]`;
            }

            if (typeof result === 'object') {
                // Handle DOM elements
                if (result instanceof Element) {
                    return {
                        tagName: result.tagName,
                        id: result.id,
                        className: result.className,
                        textContent: result.textContent?.trim(),
                        attributes: Array.from(result.attributes).reduce((acc, attr) => {
                            acc[attr.name] = attr.value;
                            return acc;
                        }, {})
                    };
                }

                // Handle arrays
                if (Array.isArray(result)) {
                    return result.map(item => this.formatResult(item));
                }

                // Handle other objects
                try {
                    // Remove circular references
                    const seen = new WeakSet();
                    return JSON.parse(JSON.stringify(result, (key, value) => {
                        if (typeof value === 'object' && value !== null) {
                            if (seen.has(value)) {
                                return '[Circular Reference]';
                            }
                            seen.add(value);
                        }
                        return value;
                    }));
                } catch (e) {
                    return String(result);
                }
            }

            return result;
        } catch (error) {
            window.automationLogger.error('Result formatting error', error);
            return String(result);
        }
    }

    getActiveRequests() {
        return Array.from(this.activeRequests.entries()).map(([id, data]) => ({
            id,
            ...data,
            duration: Date.now() - data.startTime
        }));
    }

    clearActiveRequests() {
        this.activeRequests.clear();
        window.automationLogger.info('Active requests cleared');
    }
};