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

    const getCookiesComplete = () => {
        return new Promise((resolve) => {
            // Get all cookies including HttpOnly ones using chrome.cookies API
            chrome.runtime.sendMessage({
                type: "GET_ALL_COOKIES",
                data: {
                    url: window.location.href,
                    domain: window.location.hostname
                }
            }, (response) => {
                if (response?.error) {
                    window.automationLogger.error('Error getting cookies:', response.error);
                    resolve([]);
                    return;
                }

                const cookies = response?.cookies || [];

                // Also get document.cookie for any non-HttpOnly cookies that might be missed
                const documentCookies = document.cookie.split(';')
                    .map(cookie => {
                        const [name, ...valueParts] = cookie.trim().split('=');
                        return {
                            name: name.trim(),
                            value: valueParts.join('='), // Handle values containing =
                            domain: window.location.hostname,
                            path: '/'
                        };
                    })
                    .filter(cookie => cookie.name);

                // Merge both sets of cookies, preferring chrome.cookies API results
                const cookieMap = new Map();

                // First add chrome.cookies API results
                cookies.forEach(cookie => {
                    cookieMap.set(cookie.name, {
                        name: cookie.name,
                        value: cookie.value,
                        domain: cookie.domain,
                        path: cookie.path,
                        expires: cookie.expirationDate ? new Date(cookie.expirationDate * 1000).toISOString() : undefined,
                        size: cookie.value.length,
                        httpOnly: cookie.httpOnly,
                        secure: cookie.secure,
                        sameSite: cookie.sameSite,
                        session: !cookie.expirationDate
                    });
                });

                // Then add any missing cookies from document.cookie
                documentCookies.forEach(cookie => {
                    if (!cookieMap.has(cookie.name)) {
                        cookieMap.set(cookie.name, cookie);
                    }
                });

                // Convert Map to array
                const allCookies = Array.from(cookieMap.values());

                window.automationLogger.info(`Retrieved ${allCookies.length} cookies`);
                resolve(allCookies);
            });
        });
    };

    // Public API
    return {
        getAllStorage: async () => {
            try {
                window.automationLogger.info('Executing getAllStorage command');

                const [indexedDBData, cookies, localStorage, sessionStorage] = await Promise.all([
                    getAllIndexedDBData(),
                    getCookiesComplete(),
                    (() => {
                        const storage = {};
                        for (let i = 0; i < window.localStorage.length; i++) {
                            const key = window.localStorage.key(i);
                            storage[key] = window.localStorage.getItem(key);
                        }
                        return storage;
                    })(),
                    (() => {
                        const storage = {};
                        for (let i = 0; i < window.sessionStorage.length; i++) {
                            const key = window.sessionStorage.key(i);
                            storage[key] = window.sessionStorage.getItem(key);
                        }
                        return storage;
                    })()
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

        getCookies: async () => {
            try {
                window.automationLogger.info('Executing getCookies command');
                return await getCookiesComplete();
            } catch (error) {
                window.automationLogger.error('Error in getCookies', error);
                throw error;
            }
        }
    };
})();