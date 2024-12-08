import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging


class BrowserClient:
    """Simple client for browser automation"""

    def __init__(self, base_url: str = "http://localhost:1234", timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.timeout = timeout
        self.session = requests.Session()

        # Set up logging
        self.logger = logging.getLogger('browser_client')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)

    def _make_request(self,
                      method: str,
                      endpoint: str,
                      params: Optional[Dict] = None,
                      json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to the API"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {str(e)}")
            raise

    def _execute_command(self, command: str, params: Optional[Dict] = None) -> Any:
        """Execute a command and return its result"""
        data = {
            "command": command,
            "params": params or {},
            "timeout": self.timeout
        }

        response = self._make_request('POST', 'commands/execute/', json_data=data)

        if response['status'] == 'success':
            return response['result']
        else:
            raise Exception(f"Command failed: {response.get('error', 'Unknown error')}")

    # DOM Methods
    def getTitle(self) -> str:
        """Get the current page title"""
        return self._execute_command("getTitle")

    def getUrl(self) -> str:
        """Get the current page URL"""
        return self._execute_command("getUrl")

    def getMetadata(self) -> Dict[str, str]:
        """Get page metadata"""
        return self._execute_command("getMetadata")

    def getLinks(self) -> List[Dict[str, str]]:
        """Get all links on the page"""
        return self._execute_command("getLinks")

    def getImages(self) -> List[Dict[str, Any]]:
        """Get all images on the page"""
        return self._execute_command("getImages")

    def getHeaders(self) -> List[Dict[str, Any]]:
        """Get all header elements"""
        return self._execute_command("getHeaders")

    def getElement(self, selector: str) -> Dict[str, str]:
        """Get element by CSS selector"""
        return self._execute_command("get_element", {"selector": selector})

    def getElementAttribute(self, selector: str, attribute: str) -> str:
        """Get element attribute by selector"""
        return self._execute_command("get_element_attribute", {
            "selector": selector,
            "attribute": attribute
        })

    def countElements(self, selector: str = "*") -> int:
        """Count elements matching selector"""
        return self._execute_command("countElements", {"selector": selector})

    def elementExists(self, selector: str) -> bool:
        """Check if element exists"""
        return self._execute_command("checkElementExists", {"selector": selector})

    def getDOMStats(self) -> Dict[str, Any]:
        """Get DOM statistics"""
        return self._execute_command("getDOMStats")

    # Storage Methods
    def getAllStorage(self) -> Dict[str, Any]:
        """Get all storage data"""
        return self._execute_command("get_all_storage")

    def getCookies(self) -> List[Dict[str, str]]:
        """Get all cookies"""
        return self._execute_command("get_cookies")

    def clearStorage(self, storage_type: str = "all") -> Dict[str, Any]:
        """Clear specified storage type"""
        return self._execute_command("clear_storage", {"storage_type": storage_type})

    # Utility Methods
    def getAvailableCommands(self) -> List[Dict[str, Any]]:
        """Get list of all available commands"""
        response = self._make_request('GET', 'commands/list/')
        return response['commands']

    def getCommandHistory(self,
                          command: Optional[str] = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get command execution history"""
        params = {'limit': limit}
        if command:
            params['command'] = command

        response = self._make_request('GET', 'commands/history/', params=params)
        return response['history']


# Example usage
if __name__ == "__main__":
    try:
        # Create browser instance
        browser = BrowserClient()

        # Get and print page title
        title = browser.getTitle()
        print(f"Page Title: {title}")

        # Get and print current URL
        url = browser.getUrl()
        print(f"Current URL: {url}")

        # Get and print metadata
        metadata = browser.getMetadata()
        print("\nPage Metadata:")
        for key, value in metadata.items():
            print(f"{key}: {value}")

        # Get and print DOM stats
        stats = browser.getDOMStats()
        print("\nDOM Statistics:")
        print(f"Total Elements: {stats['totalElements']}")
        print(f"Text Nodes: {stats['textNodes']}")
        print(f"Comments: {stats['comments']}")

    except Exception as e:
        print(f"Error: {str(e)}")

