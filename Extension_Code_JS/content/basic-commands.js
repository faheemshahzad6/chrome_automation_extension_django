window.basicCommands = {

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
    find_element_by_xpath: (params) => {
        try {
            window.automationLogger.info('Executing find_element_by_xpath command', params);
            const xpath = params.xpath;
            const result = document.evaluate(
                xpath,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            );
            const element = result.singleNodeValue;
            if (!element) {
                return null;
            }
            return {
                tagName: element.tagName,
                id: element.id,
                className: element.className,
                textContent: element.textContent.trim(),
                value: element.value,
                type: element.type,
                attributes: Array.from(element.attributes).reduce((acc, attr) => {
                    acc[attr.name] = attr.value;
                    return acc;
                }, {}),
                isDisplayed: window.getComputedStyle(element).display !== 'none',
                isEnabled: !element.disabled,
                isSelected: element.selected || element.checked || false,
                xpath: xpath
            };
        } catch (error) {
            window.automationLogger.error('Error in find_element_by_xpath', error);
            throw error;
        }
    },

    find_elements_by_xpath: (params) => {
        try {
            window.automationLogger.info('Executing find_elements_by_xpath command', params);
            const xpath = params.xpath;
            const result = document.evaluate(
                xpath,
                document,
                null,
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                null
            );
            const elements = [];
            for (let i = 0; i < result.snapshotLength; i++) {
                const element = result.snapshotItem(i);
                elements.push({
                    tagName: element.tagName,
                    id: element.id,
                    className: element.className,
                    textContent: element.textContent.trim(),
                    value: element.value,
                    type: element.type,
                    attributes: Array.from(element.attributes).reduce((acc, attr) => {
                        acc[attr.name] = attr.value;
                        return acc;
                    }, {}),
                    isDisplayed: window.getComputedStyle(element).display !== 'none',
                    isEnabled: !element.disabled,
                    isSelected: element.selected || element.checked || false,
                    xpath: `(${xpath})[${i + 1}]`
                });
            }
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

    send_keys: (params) => {
        try {
            window.automationLogger.info('Executing send_keys command', params);
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

            // Focus the element
            element.focus();

            // Set the value
            element.value = params.value;

            // Dispatch events
            element.dispatchEvent(new Event('input', { bubbles: true }));
            element.dispatchEvent(new Event('change', { bubbles: true }));

            // Simulate keyboard events for better compatibility
            params.value.split('').forEach(char => {
                element.dispatchEvent(new KeyboardEvent('keydown', { key: char }));
                element.dispatchEvent(new KeyboardEvent('keypress', { key: char }));
                element.dispatchEvent(new KeyboardEvent('keyup', { key: char }));
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