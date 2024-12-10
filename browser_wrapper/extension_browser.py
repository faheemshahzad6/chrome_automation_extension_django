from typing import Optional, List, Dict, Any
import requests
import json
import logging
import time
from urllib.parse import urljoin
from requests.exceptions import Timeout, RequestException


class BrowserException(Exception):
    """Custom exception for browser automation errors"""
    pass


class PageLoadTimeout(BrowserException):
    """Thrown when a page load times out"""
    pass


class ElementNotFound(BrowserException):
    """Thrown when an element cannot be found"""
    pass


def wait_until(condition, timeout=30, poll_frequency=0.5):
    """Wait until a condition is true or timeout occurs."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = condition()
            if result:
                return result
        except Exception:
            pass
        time.sleep(poll_frequency)
    raise TimeoutError(f"Timeout waiting for condition after {timeout} seconds")


class WebElement:
    """Represents a DOM element, similar to Selenium's WebElement"""

    def __init__(self, browser, xpath: str):
        self.browser = browser
        self._xpath = xpath

    def click(self):
        """Click the element"""
        return self.browser._execute_command("click_element", {"selector": self._xpath})

    def send_keys(self, value: str):
        """Send keystrokes to the element"""
        return self.browser._execute_command("send_keys", {
            "selector": self._xpath,
            "value": value
        })

    def clear(self):
        """Clear the element's content"""
        return self.browser._execute_command("clear_element", {"selector": self._xpath})

    @property
    def text(self) -> str:
        """Get element's text content"""
        result = self.browser._execute_command("get_element_text", {"selector": self._xpath})
        return str(result) if result is not None else ""

    def get_attribute(self, name: str) -> Optional[str]:
        """Get the value of an element attribute"""
        return self.browser._execute_command("get_element_attribute", {
            "selector": self._xpath,
            "attribute": name
        })

    def is_displayed(self) -> bool:
        """Check if element is visible"""
        return bool(self.browser._execute_command("is_element_displayed", {
            "selector": self._xpath
        }))

    def is_enabled(self) -> bool:
        """Check if element is enabled"""
        return bool(self.browser._execute_command("is_element_enabled", {
            "selector": self._xpath
        }))

    def is_selected(self) -> bool:
        """Check if element is selected (for checkboxes/radio buttons)"""
        return bool(self.browser._execute_command("is_element_selected", {
            "selector": self._xpath
        }))

    def submit(self):
        """Submit a form"""
        return self.browser._execute_command("submit_form", {"selector": self._xpath})


class ExtensionBrowser:
    """A Selenium-like browser automation client"""

    def __init__(self, base_url: str = "http://localhost:1234", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.implicit_wait = 0  # seconds
        self.page_load_timeout = timeout

        # Set up logging
        self.logger = logging.getLogger('enhanced_browser')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)

        # Initialize available commands
        self.available_commands = self.get_available_commands()

    def _make_request(self,
                      method: str,
                      endpoint: str,
                      params: Optional[Dict] = None,
                      json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to the API with improved error handling"""
        url = f"{self.base_url}/api/{endpoint}"
        try:
            self.logger.info(f"Making {method} request to: {url}")
            if json_data:
                self.logger.info(f"Request data: {json_data}")

            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout
            )

            if not response.content:
                self.logger.error("Empty response received from server")
                return {}

            try:
                response_data = response.json()
                self.logger.info(f"Response: {response_data}")
                return response_data
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON response: {response.content}")
                raise BrowserException(f"Server returned invalid JSON: {str(e)}")

        except Timeout:
            raise BrowserException(f"Request timeout after {self.timeout} seconds")
        except RequestException as e:
            raise BrowserException(f"Request error: {str(e)}")

    def _wait_for_element(self, xpath: str, timeout: Optional[int] = None) -> bool:
        """Wait for element to be present"""
        timeout = timeout if timeout is not None else self.implicit_wait
        if timeout <= 0:
            return True

        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                result = self._execute_command("findElementByXPath", {"xpath": xpath})
                if result:
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def _execute_command(self, command: str, params: Optional[Dict] = None) -> Any:
        """Execute a command with improved error handling and retry logic"""
        if not command:
            raise BrowserException("Command name cannot be empty")

        data = {
            "command": command,
            "params": params or {},
            "timeout": self.timeout
        }

        max_retries = 3 if command == "navigate" else 1
        retry_delay = 1
        last_error = None

        for attempt in range(max_retries):
            try:
                response = self._make_request('POST', 'commands/execute', json_data=data)

                if response.get('status') == 'success':
                    return response.get('result')
                else:
                    error = response.get('error', 'Unknown error')
                    raise BrowserException(f"Command failed: {error}")

            except Timeout as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise

        raise BrowserException(f"Command failed after {max_retries} attempts: {str(last_error)}")

    def get(self, url: str):
        """Navigate to a URL and wait for page load to complete"""
        try:
            # Send navigation command
            self._execute_command("navigate", {"url": url})

            # Wait for page load to complete
            def page_loaded():
                try:
                    # Try to get the page title - if this succeeds, page has loaded
                    self._execute_command("getTitle")
                    return True
                except Exception:
                    return False

            # Wait for page load with timeout
            wait_until(
                condition=page_loaded,
                timeout=self.page_load_timeout,
                poll_frequency=0.5
            )

            # Add a small buffer for any dynamic content
            time.sleep(0.5)

        except TimeoutError:
            raise PageLoadTimeout(f"Timeout waiting for page to load: {url}")
        except Exception as e:
            raise BrowserException(f"Navigation failed: {str(e)}")

    def find_element_by_xpath(self, xpath: str) -> WebElement:
        """Find element by XPath"""
        if not self._wait_for_element(xpath):
            raise ElementNotFound(f"Element not found: {xpath}")

        result = self._execute_command("find_element_by_xpath", {"xpath": xpath})
        if not result:
            raise ElementNotFound(f"Element not found: {xpath}")

        return WebElement(self, xpath)

    def find_elements_by_xpath(self, xpath: str) -> List[WebElement]:
        """Find multiple elements by XPath"""
        results = self._execute_command("findElementsByXPath", {"xpath": xpath})
        if not results:
            return []

        return [WebElement(self, f"({xpath})[{i + 1}]") for i in range(len(results))]

    def find_element_by_id(self, id_: str) -> WebElement:
        """Find element by ID"""
        return self.find_element_by_xpath(f'//*[@id="{id_}"]')

    def find_element_by_name(self, name: str) -> WebElement:
        """Find element by name attribute"""
        return self.find_element_by_xpath(f'//*[@name="{name}"]')

    def find_element_by_class_name(self, class_name: str) -> WebElement:
        """Find element by class name"""
        return self.find_element_by_xpath(f'//*[contains(@class, "{class_name}")]')

    def implicitly_wait(self, seconds: float) -> None:
        """Set the implicit wait timeout"""
        self.implicit_wait = float(seconds)

    def set_page_load_timeout(self, seconds: float) -> None:
        """Set the page load timeout"""
        self.page_load_timeout = float(seconds)

    def get_available_commands(self) -> List[Dict[str, Any]]:
        """Get list of all available commands"""
        response = self._make_request('GET', 'commands/list')
        return response.get('commands', [])

    @property
    def title(self) -> str:
        """Get the current page title"""
        return str(self._execute_command("getTitle"))

    @property
    def current_url(self) -> str:
        """Get the current page URL"""
        return str(self._execute_command("getUrl"))

    def back(self):
        """Navigate back in browser history"""
        self._execute_command("back")

    def forward(self):
        """Navigate forward in browser history"""
        self._execute_command("forward")

    def refresh(self):
        """Navigate to a URL and wait for page load to complete"""
        try:
            # Send refresh command
            self._execute_command("refresh")

            # Wait for page load to complete
            def page_loaded():
                try:
                    # Try to get the page title - if this succeeds, page has loaded
                    self._execute_command("getTitle")
                    return True
                except Exception:
                    return False

            # Wait for page load with timeout
            wait_until(
                condition=page_loaded,
                timeout=self.page_load_timeout,
                poll_frequency=0.5
            )

            # Add a small buffer for any dynamic content
            time.sleep(0.5)

        except TimeoutError:
            raise PageLoadTimeout(f"Timeout waiting for page to refresh")
        except Exception as e:
            raise BrowserException(f"Navigation failed: {str(e)}")

    def quit(self):
        """Close the browser session"""
        pass
        # self.session.close()

    def close(self):
        """Close the current window (alias for quit)"""
        pass
        # self.quit()

    def get_all_storage(self) -> Dict[str, Any]:
        """Get all storage data including localStorage, sessionStorage, and cookies"""
        return self._execute_command("get_all_storage")

    def get_cookies(self) -> List[Dict[str, str]]:
        """Get all cookies from the current page"""
        return self._execute_command("get_cookies")

    def get_metadata(self) -> Dict[str, str]:
        """Get page metadata"""
        return self._execute_command("get_metadata")
