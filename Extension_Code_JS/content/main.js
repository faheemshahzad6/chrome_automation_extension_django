(() => {
    const initializeAutomation = async () => {
        try {
            // Wait for DOM to be fully loaded
            if (document.readyState !== 'complete') {
                await new Promise(resolve => {
                    window.addEventListener('load', resolve);
                });
            }

            window.automationLogger.info('Initializing automation system');

            // Verify required dependencies
            if (!window.automationLogger) {
                throw new Error('Logger not initialized - logger.js may not be loaded');
            }

            if (!window.basicCommands) {
                throw new Error('Basic commands not found - basic-commands.js may not be loaded');
            }

            if (!window.storageCommands) {
                throw new Error('Storage commands not found - storage-commands.js may not be loaded');
            }

            if (typeof window.AutomationHandler !== 'function') {
                throw new Error('AutomationHandler not found - handler.js may not be loaded');
            }

            // Initialize automation handler
            const handler = new window.AutomationHandler();

            // Register all command sets
            try {
                // Register basic DOM and navigation commands
                window.automationLogger.info('Registering basic commands');
                handler.registerCommands(window.basicCommands);

                // Register storage commands
                window.automationLogger.info('Registering storage commands');
                handler.registerCommands(window.storageCommands);

                // Store handler instance globally
                window.automationHandler = handler;

                // Log available commands
                const availableCommands = Object.keys({
                    ...window.basicCommands,
                    ...window.storageCommands
                });

                window.automationLogger.success(
                    'Automation system initialized successfully',
                    `Available commands: ${availableCommands.length}`
                );

                // Send initialization success message
                chrome.runtime.sendMessage({
                    type: 'AUTOMATION_INITIALIZED',
                    success: true,
                    commandCount: availableCommands.length
                });

            } catch (registrationError) {
                throw new Error(`Command registration failed: ${registrationError.message}`);
            }

        } catch (error) {
            window.automationLogger.error('Failed to initialize automation system:', error);

            // Send initialization failure message
            chrome.runtime.sendMessage({
                type: 'AUTOMATION_INITIALIZED',
                success: false,
                error: error.message
            });

            throw error;
        }
    };

    // Set up global error boundary
    const handleError = (error, context = 'Unknown') => {
        window.automationLogger.error(`Error in ${context}:`, error);
        chrome.runtime.sendMessage({
            type: 'AUTOMATION_ERROR',
            context,
            error: {
                message: error.message,
                stack: error.stack
            }
        });
    };

    // Set up mutation observer to handle dynamic page changes
    const setupMutationObserver = () => {
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Log significant DOM changes that might affect automation
                    window.automationLogger.info('Significant DOM change detected', {
                        addedNodes: mutation.addedNodes.length,
                        removedNodes: mutation.removedNodes.length
                    });
                }
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: false,
            characterData: false
        });

        return observer;
    };

    // Initialize the system
    try {
        // Start initialization
        initializeAutomation()
            .then(() => {
                // Set up mutation observer after successful initialization
                const observer = setupMutationObserver();

                // Store observer reference for cleanup if needed
                window.automationObserver = observer;

                window.automationLogger.info('Page monitoring active');
            })
            .catch(error => {
                handleError(error, 'Initialization');
            });

    } catch (error) {
        handleError(error, 'Setup');
    }

    // Listen for unload to clean up
    window.addEventListener('unload', () => {
        try {
            // Clean up mutation observer
            if (window.automationObserver) {
                window.automationObserver.disconnect();
            }

            // Clean up any active requests
            if (window.automationHandler) {
                window.automationHandler.clearActiveRequests();
            }

            window.automationLogger.info('Automation system cleanup complete');
        } catch (error) {
            handleError(error, 'Cleanup');
        }
    });

})();