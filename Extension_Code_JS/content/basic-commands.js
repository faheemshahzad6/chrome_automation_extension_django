window.basicCommands = {

    // Navigation Commands
    navigate: async (params) => {
        try {
            window.automationLogger.info('Executing navigate command', params);
            if (!params || !params.url) {
                throw new Error('URL is required for navigation');
            }

            // Send response before navigation
            chrome.runtime.sendMessage({
                type: 'SCRIPT_RESULT',
                status: 'success',
                result: true
            });

            // Perform navigation after a small delay
            setTimeout(() => {
                window.location.href = params.url;
            }, 100);

            return true;
        } catch (error) {
            window.automationLogger.error('Error in navigate', error);
            throw error;
        }
    },

    back: () => {
        try {
            window.automationLogger.info('Executing back command');
            window.history.back();
            return true;
        } catch (error) {
            window.automationLogger.error('Error in back', error);
            throw error;
        }
    },

    forward: () => {
        try {
            window.automationLogger.info('Executing forward command');
            window.history.forward();
            return true;
        } catch (error) {
            window.automationLogger.error('Error in forward', error);
            throw error;
        }
    },

    refresh: () => {
        try {
            window.automationLogger.info('Executing refresh command');
            window.location.reload();
            return true;
        } catch (error) {
            window.automationLogger.error('Error in refresh', error);
            throw error;
        }
    },

    // Basic Page Info Commands
    getTitle: () => {
        try {
            window.automationLogger.info('Executing getTitle command');
            return document.title;
        } catch (error) {
            window.automationLogger.error('Error in getTitle', error);
            throw error;
        }
    },

    getUrl: () => {
        try {
            window.automationLogger.info('Executing getUrl command');
            return window.location.href;
        } catch (error) {
            window.automationLogger.error('Error in getUrl', error);
            throw error;
        }
    },

    getMetadata: () => {
        try {
            window.automationLogger.info('Executing getMetadata command');
            return {
                title: document.title,
                url: window.location.href,
                description: document.querySelector('meta[name="description"]')?.content || '',
                keywords: document.querySelector('meta[name="keywords"]')?.content || '',
                author: document.querySelector('meta[name="author"]')?.content || '',
                lastModified: document.lastModified,
                charset: document.characterSet,
                viewport: document.querySelector('meta[name="viewport"]')?.content || '',
                language: document.documentElement.lang || '',
                generator: document.querySelector('meta[name="generator"]')?.content || '',
                themeColor: document.querySelector('meta[name="theme-color"]')?.content || ''
            };
        } catch (error) {
            window.automationLogger.error('Error in getMetadata', error);
            throw error;
        }
    },

    // Element Finding Commands
    find_element_by_xpath: async (params) => {
    try {
        window.automationLogger.info('Executing find_element_by_xpath command', params);

        // Check if params exists and has xpath property
        if (!params || typeof params !== 'object') {
            throw new Error('Invalid parameters: expected object with xpath property');
        }

        if (!params.xpath || typeof params.xpath !== 'string') {
            throw new Error('XPath selector is required');
        }

        // Create XPath evaluator
        const result = document.evaluate(
            params.xpath,
            document,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        );

        const element = result.singleNodeValue;

        // If no element found, return null
        if (!element) {
            window.automationLogger.info('No element found for XPath:', params.xpath);
            return null;
        }

        // Get computed style for visibility check
        const style = window.getComputedStyle(element);

        // Build element properties
        const rect = element.getBoundingClientRect();
        const elementInfo = {
            tagName: element.tagName.toLowerCase(),
            id: element.id || '',
            className: element.className || '',
            textContent: element.textContent?.trim() || '',
            value: element.value || '',
            type: element.type || '',
            attributes: {},
            isDisplayed: style.display !== 'none' &&
                        style.visibility !== 'hidden' &&
                        rect.width > 0 &&
                        rect.height > 0,
            isEnabled: !element.disabled,
            isSelected: element.selected || element.checked || false,
            xpath: params.xpath,
            boundingBox: {
                top: rect.top,
                right: rect.right,
                bottom: rect.bottom,
                left: rect.left,
                width: rect.width,
                height: rect.height
            }
        };

        // Get all attributes
        for (const attr of element.attributes) {
            elementInfo.attributes[attr.name] = attr.value;
        }

        window.automationLogger.success('Element found by XPath', {
            xpath: params.xpath,
            tagName: elementInfo.tagName
        });

        return elementInfo;

    } catch (error) {
        window.automationLogger.error('Error in find_element_by_xpath', error);
        throw error;
    }
},

    find_elements_by_xpath: (params) => {
        try {
            window.automationLogger.info('Executing find_elements_by_xpath command', params);

            if (!params || !params.xpath) {
                throw new Error('XPath selector is required');
            }

            const result = document.evaluate(
                params.xpath,
                document,
                null,
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                null
            );

            const elements = [];
            for (let i = 0; i < result.snapshotLength; i++) {
                const element = result.snapshotItem(i);
                if (!element) continue;

                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();

                elements.push({
                    tagName: element.tagName.toLowerCase(),
                    id: element.id || '',
                    className: element.className || '',
                    textContent: element.textContent?.trim() || '',
                    value: element.value || '',
                    type: element.type || '',
                    attributes: Array.from(element.attributes).reduce((acc, attr) => {
                        acc[attr.name] = attr.value;
                        return acc;
                    }, {}),
                    isDisplayed: style.display !== 'none' &&
                                style.visibility !== 'hidden' &&
                                rect.width > 0 &&
                                rect.height > 0,
                    isEnabled: !element.disabled,
                    isSelected: element.selected || element.checked || false,
                    xpath: `(${params.xpath})[${i + 1}]`,
                    boundingBox: {
                        top: rect.top,
                        right: rect.right,
                        bottom: rect.bottom,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height
                    }
                });
            }

            window.automationLogger.success('Elements found by XPath', {
                xpath: params.xpath,
                count: elements.length
            });

            return elements;
        } catch (error) {
            window.automationLogger.error('Error in find_elements_by_xpath', error);
            throw error;
        }
    },

    // Element Interaction Commands
    click_element: (params) => {
        try {
            window.automationLogger.info('Executing click_element command', params);
            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                throw new Error(`Element not found: ${params.selector}`);
            }

            // Scroll element into view if needed
            element.scrollIntoView({ behavior: 'auto', block: 'center' });

            // Wait for any scrolling to finish
            setTimeout(() => {
                try {
                    element.click();
                } catch (clickError) {
                    // If native click fails, try simulating a click
                    const event = new MouseEvent('click', {
                        view: window,
                        bubbles: true,
                        cancelable: true
                    });
                    element.dispatchEvent(event);
                }
            }, 100);

            return true;
        } catch (error) {
            window.automationLogger.error('Error in click_element', error);
            throw error;
        }
    },

    send_keys: async (params) => {
        try {
            window.automationLogger.info('Executing send_keys command', params);

            if (!params || !params.selector || !params.value) {
                throw new Error('Both selector and value are required for send_keys command');
            }

            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                throw new Error(`Element not found: ${params.selector}`);
            }

            // Check if element is interactable
            const style = window.getComputedStyle(element);
            if (style.display === 'none' || style.visibility === 'hidden') {
                throw new Error('Element is not visible or interactable');
            }

            // Scroll element into view
            element.scrollIntoView({ behavior: 'auto', block: 'center' });

            // Small delay to allow for scrolling
            await new Promise(resolve => setTimeout(resolve, 100));

            // Clear existing value first
            element.value = '';

            // Focus the element
            element.focus();

            // Set the value
            element.value = params.value;

            // Dispatch events
            const events = [
                new Event('input', { bubbles: true }),
                new Event('change', { bubbles: true })
            ];

            // Dispatch keyboard events for each character
            const text = params.value;
            for (let i = 0; i < text.length; i++) {
                const char = text[i];
                events.push(new KeyboardEvent('keydown', { key: char, bubbles: true }));
                events.push(new KeyboardEvent('keypress', { key: char, bubbles: true }));
                events.push(new KeyboardEvent('keyup', { key: char, bubbles: true }));
            }

            // Dispatch all events
            events.forEach(event => element.dispatchEvent(event));

            window.automationLogger.success('send_keys completed successfully', {
                selector: params.selector,
                valueLength: params.value.length
            });

            return true;
        } catch (error) {
            window.automationLogger.error('Error in send_keys', error);
            throw error;
        }
    },

    clear_element: (params) => {
        try {
            window.automationLogger.info('Executing clear_element command', params);
            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                throw new Error(`Element not found: ${params.selector}`);
            }

            // Store original value for undo functionality
            const originalValue = element.value;

            // Clear the value
            element.value = '';

            // Dispatch events
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));

            return true;
        } catch (error) {
            window.automationLogger.error('Error in clear_element', error);
            throw error;
        }
    },

    // Element State Commands
    is_element_displayed: (params) => {
        try {
            window.automationLogger.info('Executing is_element_displayed command', params);
            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                return false;
            }

            const style = window.getComputedStyle(element);
            return style.display !== 'none' &&
                   style.visibility !== 'hidden' &&
                   element.offsetParent !== null;
        } catch (error) {
            window.automationLogger.error('Error in is_element_displayed', error);
            throw error;
        }
    },

    is_element_enabled: (params) => {
        try {
            window.automationLogger.info('Executing is_element_enabled command', params);
            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                return false;
            }

            return !element.disabled;
        } catch (error) {
            window.automationLogger.error('Error in is_element_enabled', error);
            throw error;
        }
    },

    is_element_selected: (params) => {
        try {
            window.automationLogger.info('Executing is_element_selected command', params);
            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                return false;
            }

            return element.selected || element.checked || false;
        } catch (error) {
            window.automationLogger.error('Error in is_element_selected', error);
            throw error;
        }
    },

    // Element Property Commands
    get_element_text: (params) => {
        try {
            window.automationLogger.info('Executing get_element_text command', params);
            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                throw new Error(`Element not found: ${params.selector}`);
            }

            return element.textContent.trim();
        } catch (error) {
            window.automationLogger.error('Error in get_element_text', error);
            throw error;
        }
    },

    get_element_attribute: (params) => {
        try {
            window.automationLogger.info('Executing get_element_attribute command', params);
            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                throw new Error(`Element not found: ${params.selector}`);
            }

            return element.getAttribute(params.attribute);
        } catch (error) {
            window.automationLogger.error('Error in get_element_attribute', error);
            throw error;
        }
    },

    get_element_css_value: (params) => {
        try {
            window.automationLogger.info('Executing get_element_css_value command', params);
            const element = document.evaluate(
                params.selector,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (!element) {
                throw new Error(`Element not found: ${params.selector}`);
            }

            return window.getComputedStyle(element).getPropertyValue(params.property_name);
        } catch (error) {
            window.automationLogger.error('Error in get_element_css_value', error);
            throw error;
        }
    }
};