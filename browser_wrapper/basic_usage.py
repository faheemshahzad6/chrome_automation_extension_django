from extension_browser import ExtensionBrowser
import time

browser = ExtensionBrowser()
try:
    # Navigate to the page
    # browser.get("https://propwire.com/search")

    # Add a small delay to let the page load and scripts initialize
    # time.sleep(2)

    # Try to find and interact with the search box
    try:
        # s = browser.get_all_storage()
        # print(s)
        # browser.refresh()

        # Get all storage
        # storage = browser.get_all_storage()
        # print(storage)

        # Get just cookies
        # cookies = browser.get_cookies()
        # print("Cookies:", cookies)

        search_box = browser.find_element_by_xpath('//input[@name="search"]')
        # a = search_box.text
        search_box.click()
        # search_box.clear()
        # print(a)
        search_box.send_keys("13912 W Pavillion Dr")
        time.sleep(5)
        search_box.press_enter()
        time.sleep(5)

        drop_down = browser.find_element_by_xpath('//div[@class="dropdown"]')
        d_t = drop_down.text

        if "No results" in d_t:
            print("Address not found")
        else:
            print(f"Address found: {d_t}")

        owner_tab = browser.find_element_by_xpath("//div[contains(text(), 'Owner')]")
        owner_tab.click()
        time.sleep(5)

        # skip_trace_button = browser.find_element_by_xpath("//button[contains(text(), 'Skip Trace')]")
        # time.sleep(5)
        # skip_trace_now_button = browser.find_element_by_xpath("//button[contains(text(), 'Skip Trace Now')]")
        # time.sleep(5)
        # skip_trace_continue_button = browser.find_element_by_xpath("//button[contains(text(), 'Continue')]")


    except Exception as e:
        print(f"Could not find search box: {str(e)}")

finally:
    # browser.quit()
    pass