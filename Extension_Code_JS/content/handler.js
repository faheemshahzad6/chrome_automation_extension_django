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

    // In content/handler.js
    setupMessageListener() {
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            if (message.type === 'EXECUTE_ACTION') {
                // Handle non-navigation commands
                if (!message.action.script.startsWith('navigate')) {
                    this.handleAction(message.action)
                        .then(result => {
                            sendResponse({
                                type: 'SCRIPT_RESULT',
                                status: 'success',
                                result: result,
                                command_id: message.action.command_id
                            });
                        })
                        .catch(error => {
                            sendResponse({
                                type: 'SCRIPT_ERROR',
                                status: 'error',
                                error: error.message,
                                stack: error.stack,
                                command_id: message.action.command_id
                            });
                        });
                    return true;
                }
            }
        });
    }

    async handleAction(action) {
        window.automationLogger.info('Handling action', action);
        try {
            if (action.type !== 'EXECUTE_SCRIPT') {
                throw new Error(`Unknown action type: ${action.type}`);
            }

            const { command, params } = this.parseCommand(action.script);

            // Log available commands for debugging
            window.automationLogger.info('Available commands:', Object.keys(this.commands));

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
                // Handle navigation commands specially
                if (['navigate', 'back', 'forward', 'refresh'].includes(command)) {
                    const result = await this.handleNavigationCommand(command, params);
                    this.activeRequests.delete(requestId);
                    return result;
                }

                // Execute regular command
                const result = await this.commands[command](params);
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

    parseCommand(script) {
    try {
        if (typeof script !== 'string') {
            throw new Error('Invalid command format');
        }

        const parts = script.split('|');
        const command = parts[0].trim();

        let params = {};
        if (parts.length > 1) {
            try {
                // Try parsing as JSON
                params = JSON.parse(parts[1]);
            } catch {
                // For navigation commands, wrap url in object
                if (command === 'navigate') {
                    params = { url: parts[1] };
                } else {
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