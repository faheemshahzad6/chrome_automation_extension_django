window.automationLogger = {
    info: (message, data = null) => {
        const logMessage = data ? `${message} ${JSON.stringify(data)}` : message;
        console.log(`%c[Content Script Info] ${logMessage}`, 'color: #2196F3');
    },
    success: (message, data = null) => {
        const logMessage = data ? `${message} ${JSON.stringify(data)}` : message;
        console.log(`%c[Content Script Success] ${logMessage}`, 'color: #4CAF50');
    },
    error: (message, error = null) => {
        const logMessage = error ? `${message}: ${error.message}` : message;
        console.error(`%c[Content Script Error] ${logMessage}`, 'color: #f44336');
        if (error?.stack) {
            console.error(`%c[Stack Trace] ${error.stack}`, 'color: #f44336');
        }
    }
};