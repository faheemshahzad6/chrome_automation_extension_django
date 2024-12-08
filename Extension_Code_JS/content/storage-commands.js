window.storageCommands = (() => {
    // Private helper functions
    const getAllIndexedDBData = async () => {
        try {
            const databases = await window.indexedDB.databases();
            const results = {};

            const dbPromises = databases.map(db => new Promise((resolve) => {
                try {
                    const request = indexedDB.open(db.name);

                    request.onsuccess = (event) => {
                        const db = event.target.result;
                        const stores = Array.from(db.objectStoreNames);
                        resolve({ [db.name]: { stores } });
                    };

                    request.onerror = (event) => {
                        window.automationLogger.error(`Error opening IndexedDB ${db.name}`, event.target.error);
                        resolve({ [db.name]: { error: event.target.error.message } });
                    };
                } catch (error) {
                    window.automationLogger.error(`Error accessing IndexedDB ${db.name}`, error);
                    resolve({ [db.name]: { error: error.message } });
                }
            }));

            const dbResults = await Promise.all(dbPromises);
            dbResults.forEach(result => Object.assign(results, result));

            return results;
        } catch (error) {
            window.automationLogger.error('Error getting IndexedDB data', error);
            return { error: error.message };
        }
    };

    const getCookies = () => {
        try {
            return document.cookie.split(';')
                .map(cookie => {
                    const [name, value] = cookie.split('=').map(c => c.trim());
                    return { name, value };
                })
                .filter(cookie => cookie.name);
        } catch (error) {
            window.automationLogger.error('Error getting cookies', error);
            throw error;
        }
    };

    const getLocalStorage = () => {
        try {
            const storage = {};
            for (let i = 0; i < window.localStorage.length; i++) {
                const key = window.localStorage.key(i);
                try {
                    storage[key] = window.localStorage.getItem(key);
                } catch (error) {
                    storage[key] = { error: error.message };
                }
            }
            return storage;
        } catch (error) {
            window.automationLogger.error('Error getting localStorage', error);
            throw error;
        }
    };

    const getSessionStorage = () => {
        try {
            const storage = {};
            for (let i = 0; i < window.sessionStorage.length; i++) {
                const key = window.sessionStorage.key(i);
                try {
                    storage[key] = window.sessionStorage.getItem(key);
                } catch (error) {
                    storage[key] = { error: error.message };
                }
            }
            return storage;
        } catch (error) {
            window.automationLogger.error('Error getting sessionStorage', error);
            throw error;
        }
    };

    // Public API
    return {
        getAllStorage: async () => {
            try {
                window.automationLogger.info('Executing getAllStorage command');

                const [indexedDBData, cookies, localStorage, sessionStorage] = await Promise.all([
                    getAllIndexedDBData(),
                    getCookies(),
                    getLocalStorage(),
                    getSessionStorage()
                ]);

                return {
                    url: window.location.href,
                    timestamp: new Date().toISOString(),
                    cookies,
                    localStorage,
                    sessionStorage,
                    indexedDB: indexedDBData
                };
            } catch (error) {
                window.automationLogger.error('Error in getAllStorage', error);
                throw error;
            }
        },

        clearStorage: async (storageType = 'all') => {
            try {
                window.automationLogger.info('Executing clearStorage command', { storageType });

                const clearPromises = [];

                if (storageType === 'all' || storageType === 'localStorage') {
                    clearPromises.push(window.localStorage.clear());
                }

                if (storageType === 'all' || storageType === 'sessionStorage') {
                    clearPromises.push(window.sessionStorage.clear());
                }

                if (storageType === 'all' || storageType === 'cookies') {
                    document.cookie.split(';').forEach(cookie => {
                        const name = cookie.split('=')[0].trim();
                        document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
                    });
                }

                await Promise.all(clearPromises);
                return { success: true, clearedType: storageType };
            } catch (error) {
                window.automationLogger.error('Error in clearStorage', error);
                throw error;
            }
        }
    };
})();