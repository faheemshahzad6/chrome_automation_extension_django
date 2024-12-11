from typing import Dict, Any, Optional, List, NamedTuple
from dataclasses import dataclass
from extension_browser import ExtensionBrowser
import requests
import json
import urllib.parse
from enum import Enum
import time


@dataclass
class PropertyResult:
    id: int
    address: str
    city: str
    state: str
    zip: str
    county: str
    apn: str
    latitude: float
    longitude: float
    searchType: str


class PropwireEndpoint(Enum):
    PROPERTY_DETAIL = 'pw_property_detail'
    SKIP_TRACE = 'skip_trace'
    AUTO_COMPLETE = 'auto_complete'


class PropwireClient:
    """Client for interacting with Propwire APIs"""

    def __init__(self, base_url: str = "https://propwire.com", user_id: str = "117830"):
        self.base_url = base_url.rstrip('/')
        self.api_base_url = f"https://api.{base_url.replace('https://', '')}/api"
        self.browser = ExtensionBrowser()
        self.cookies = None
        self.headers = None
        self.auth_token = None
        self.user_id = user_id

    def _format_cookies_for_header(self, cookies: list) -> str:
        """Convert cookie list to cookie header string"""
        return '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

    def _get_xsrf_token(self, cookies: list) -> Optional[str]:
        """Get and decode XSRF token from cookies"""
        xsrf_cookie = next((cookie for cookie in cookies if cookie['name'] == 'XSRF-TOKEN'), None)
        if xsrf_cookie:
            return urllib.parse.unquote(xsrf_cookie['value'])
        return None

    def _get_auth_token_from_logs(self, logs):
        """Extract authorization token from network logs"""
        for log_entry in logs:
            if isinstance(log_entry, dict) and log_entry.get("event") == "headers":
                headers_data = log_entry.get("data", {}).get("headers", [])
                for header in headers_data:
                    if header.get("name") == "Authorization":
                        return header.get("value")
        return None

    def _capture_auth_token(self):
        """Capture authorization token by monitoring network requests"""
        try:
            print("Refreshing the page for freshning up cookies ...")
            self.browser.refresh()
            time.sleep(10)
            print("Starting network capture to get auth token...")
            capture_started = self.browser.start_network_capture()
            # if not capture_started:
            #     raise Exception("Failed to start network capture")

            # Find and interact with search box
            search_box = self.browser.find_element_by_xpath('//input[@name="search"]')
            search_box.click()
            search_box.send_keys("13912 W Pavillion Dr")  # Trigger auto-complete

            # Wait for requests to complete
            time.sleep(7)

            # Stop capture and get logs
            self.browser.stop_network_capture()
            logs = self.browser.get_network_logs()

            # clear logs after getting data
            self.browser.clear_network_logs()

            # Extract token from logs
            token = self._get_auth_token_from_logs(logs)
            if not token:
                raise Exception("Authorization token not found in network logs")

            self.auth_token = token
            print("Successfully captured authorization token")
            return token

        except Exception as e:
            print(f"Error capturing auth token: {str(e)}")
            raise

    def initialize(self) -> None:
        """Initialize the client by getting cookies and auth token from browser"""

        # Capture auth token
        self._capture_auth_token()

        print("Getting cookies from browser...")
        self.cookies = self.browser.get_cookies()

        if not self.cookies:
            raise Exception("No cookies found! Make sure you're logged into Propwire")

        print(f"Found {len(self.cookies)} cookies")

        # Set up base headers
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/json',
            'origin': self.base_url,
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest',
            'cookie': self._format_cookies_for_header(self.cookies),
            'authorization': self.auth_token,
            'x-user-id': self.user_id
        }

        # Get and set XSRF token
        xsrf_token = self._get_xsrf_token(self.cookies)
        if xsrf_token:
            self.headers['x-xsrf-token'] = xsrf_token
            print("XSRF Token set successfully")
        else:
            print("Warning: No XSRF token found in cookies")

    def make_request(self, endpoint: PropwireEndpoint, payload: Dict[str, Any],
                     referer: Optional[str] = None, use_api_base: bool = False) -> Dict[str, Any]:
        """Make a request to a Propwire endpoint"""
        if not self.headers:
            self.initialize()

        # Copy headers so we can modify them for this request
        request_headers = self.headers.copy()

        # Add referer if provided
        if referer:
            request_headers['referer'] = f"{self.base_url}/{referer}"

        base = self.api_base_url if use_api_base else self.base_url
        url = f"{base}/{endpoint.value}"

        print(f"\nMaking request to {endpoint.value}")
        print("Payload:", json.dumps(payload, indent=2))

        response = requests.post(url, headers=request_headers, json=payload)

        if response.ok:
            return response.json()
        else:
            raise Exception(f"Request failed with status {response.status_code}: {response.text}")

    def auto_complete(self, search_text: str, search_types: Optional[List[str]] = None) -> List[PropertyResult]:
        """Get auto-complete suggestions and return structured property results"""
        if not self.auth_token:
            raise Exception("Authorization token not available. Call initialize() first")

        if search_types is None:
            search_types = ["C", "Z", "N", "T", "A"]

        payload = {
            "search": search_text,
            "search_types": search_types
        }

        result = self.make_request(
            PropwireEndpoint.AUTO_COMPLETE,
            payload,
            referer="search",
            use_api_base=True
        )

        # Convert results to PropertyResult objects
        properties = []
        for item in result.get('data', []):
            properties.append(PropertyResult(
                id=item['id'],
                address=item['street'],
                city=item['city'],
                state=item['state'],
                zip=item['zip'],
                county=item['county'],
                apn=item['apn'],
                latitude=item['latitude'],
                longitude=item['longitude'],
                searchType=item['searchType']
            ))

        print(f"Found {len(properties)} properties")
        return properties

    def get_property_details(self, property_id: int) -> Dict[str, Any]:
        """Get detailed property information using ID from auto-complete"""
        print(f"\nGetting property details for ID: {property_id}")
        return self.make_request(
            PropwireEndpoint.PROPERTY_DETAIL,
            {"id": property_id},
            referer="search"
        )

    def skip_trace_from_property(self, property: PropertyResult,
                                 mail_address: Optional[Dict[str, str]] = None,
                                 force_refresh: bool = False) -> Dict[str, Any]:
        """Perform skip trace using property information from auto-complete"""
        payload = {
            "city": property.city,
            "state": property.state,
            "address": property.address,
            "zip": property.zip,
            "property_id": property.id,
            "match_requirements": {"phones": True},
            "force_refresh": force_refresh
        }

        # Add mailing address if provided
        if mail_address:
            payload.update({
                "mail_city": mail_address["city"],
                "mail_state": mail_address["state"],
                "mail_address": mail_address["address"],
                "mail_zip": mail_address["zip"]
            })

        print(f"\nPerforming skip trace for property: {property.address}")
        return self.make_request(
            PropwireEndpoint.SKIP_TRACE,
            payload,
            referer=f"realestate/{property.address}/{property.id}/owner-details"
        )

    def cleanup(self):
        """Clean up resources"""
        if self.browser:
            self.browser.quit()
        # Stop capture and get logs
        self.browser.stop_network_capture()

        # clear logs after getting data
        self.browser.clear_network_logs()

