from extension_browser import ExtensionBrowser
import time
from extension_browser import ExtensionBrowser
import requests
import json
import urllib.parse


def format_cookies_for_header(cookies):
    """Convert cookie list to cookie header string"""
    return '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])


def get_xsrf_token(cookies):
    """Get and decode XSRF token from cookies"""
    xsrf_cookie = next((cookie for cookie in cookies if cookie['name'] == 'XSRF-TOKEN'), None)
    if xsrf_cookie:
        # URL decode the token value
        return urllib.parse.unquote(xsrf_cookie['value'])
    return None


def make_request_with_cookies(cookies):
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'content-type': 'application/json',
        'origin': 'https://propwire.com',
        'referer': 'https://propwire.com/search',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    # Add cookie header
    headers['cookie'] = format_cookies_for_header(cookies)

    # Get and set XSRF token separately
    xsrf_token = get_xsrf_token(cookies)
    if xsrf_token:
        headers['x-xsrf-token'] = xsrf_token
        print("XSRF Token set:", xsrf_token)
    else:
        print("Warning: No XSRF token found in cookies")

    # Get authorization token from cookies
    auth_cookie = next((cookie for cookie in cookies if cookie['name'].lower() == 'authorization'), None)
    if auth_cookie:
        headers['authorization'] = auth_cookie['value']
        print("Authorization header set")

    url = 'https://propwire.com/pw_property_detail'
    data = {"id": 158856396}

    print("\nMaking request with headers:")
    for key, value in headers.items():
        if key.lower() in ['cookie', 'authorization', 'x-xsrf-token']:
            print(f"{key}: [REDACTED]")
        else:
            print(f"{key}: {value}")

    response = requests.post(url, headers=headers, json=data)
    return response


browser = ExtensionBrowser()
try:
    # Start capture
    # browser.refresh()
    # time.sleep(10)
    # print("Starting network capture...")
    # print(browser.get_cookies())
    # cookies = browser.get_cookies()
    #
    # if not cookies:
    #     print("No cookies found!")
    #
    # print(f"Found {len(cookies)} cookies")
    # response = make_request_with_cookies(cookies)
    #
    # print(f"\nResponse status code: {response.status_code}")
    # if response.ok:
    #     print("Response content:", json.dumps(response.json(), indent=2))
    # else:
    #     print("Error response:", response.text)
    #     print("Response headers:", dict(response.headers))
    # browser.get_all_storage()
    capture_started = browser.start_network_capture()

    if capture_started:
        print("Network capture started successfully")
    else:
        print("Failed to start network capture")

    try:
        # Your existing code
        search_box = browser.find_element_by_xpath('//input[@name="search"]')
        search_box.click()
        search_box.send_keys("13912 W Pavillion Dr")
        time.sleep(15)  # Wait to capture network activity
    finally:
        pass
        # Stop capture in inner finally block
        capture_stopped = browser.stop_network_capture()
    print(browser.get_network_logs())
    # print(browser.clear_network_logs())
        # if capture_stopped:
        #     print("Network capture stopped successfully")
        # else:
        #     print("Failed to stop network capture")

except Exception as e:
    print(f"Error: {str(e)}")