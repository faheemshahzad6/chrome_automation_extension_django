from extension_browser import ExtensionBrowser
import time

browser = ExtensionBrowser()
try:
    # Start capture
    print("Starting network capture...")
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
        if capture_stopped:
            print("Network capture stopped successfully")
        else:
            print("Failed to stop network capture")

except Exception as e:
    print(f"Error: {str(e)}")