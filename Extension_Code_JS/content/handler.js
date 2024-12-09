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

            // Log all command names being registered
            window.automationLogger.info('Registering commands with names:', Object.keys(commandsObject));

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

        // Convert command name to lowercase for case-insensitive matching
        const normalizedCommand = command.toLowerCase();
        const availableCommands = Object.keys(this.commands).map(cmd => cmd.toLowerCase());

        if (!availableCommands.includes(normalizedCommand)) {
            throw new Error(`Unknown command: ${command}`);
        }

        // Find the actual command name with original casing
        const actualCommand = Object.keys(this.commands).find(
            cmd => cmd.toLowerCase() === normalizedCommand
        );

        // Track the request
        const requestId = action.command_id || Date.now().toString();
        this.activeRequests.set(requestId, {
            command: actualCommand,
            params,
            startTime: Date.now()
        });

        try {
            let result;
            if (actualCommand === 'navigate') {
                result = await this.handleNavigationCommand(actualCommand, params);
            } else {
                result = await Promise.race([
                    Promise.resolve(this.commands[actualCommand](params)),
                    new Promise((_, reject) =>
                        setTimeout(() => reject(new Error('Command execution timeout')), 30000)
                    )
                ]);
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

            // Get the raw command
            const commandRaw = parts[0].trim();

            // Comprehensive command mapping (case-insensitive)
            const commandMap = {
                // Click variations
                'click': 'click_element',
                'clickelement': 'click_element',
                'click_element': 'click_element',

                // Clear variations
                'clear': 'clear_element',
                'clearelement': 'clear_element',
                'clear_element': 'clear_element',

                // Send keys variations
                'sendkeys': 'send_keys',
                'send_keys': 'send_keys',

                // Keep original command mapping intact
                'find_element_by_xpath': 'find_element_by_xpath',
                'find_elements_by_xpath': 'find_elements_by_xpath'
            };

            // Convert to lowercase for matching
            const commandLower = commandRaw.toLowerCase();

            // Get standardized command name, preserving original if no mapping exists
            const standardCommand = commandMap[commandLower] || commandRaw;

            // Parse parameters based on command type
            let params = {};
            if (parts.length > 1) {
                switch (standardCommand) {
                    case 'send_keys':
                        if (parts.length < 3) {
                            throw new Error('send_keys requires both selector and value parameters');
                        }
                        params = {
                            selector: parts[1],
                            value: parts[2]
                        };
                        break;
                    case 'clear_element':
                    case 'click_element':
                        params = {
                            selector: parts[1]
                        };
                        break;
                    case 'find_element_by_xpath':
                    case 'find_elements_by_xpath':
                        params = {
                            xpath: parts[1]
                        };
                        break;
                    case 'navigate':
                        params = {
                            url: parts[1]
                        };
                        break;
                    default:
                        try {
                            // Try parsing as JSON for other commands
                            params = JSON.parse(parts[1]);
                        } catch {
                            // If not JSON, use as-is
                            params = parts.length === 2 ? parts[1] : parts.slice(1);
                        }
                }
            }

            window.automationLogger.info('Parsed command:', {
                original: commandRaw,
                standardized: standardCommand,
                params
            });

            return { command: standardCommand, params };
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