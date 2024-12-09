from browser import EnhancedBrowser
import time

browser = EnhancedBrowser()
try:
    # Navigate to the page
    # browser.get("https://propwire.com/search")

    # Add a small delay to let the page load and scripts initialize
    # time.sleep(2)

    # Try to find and interact with the search box
    try:
        search_box = browser.find_element_by_xpath('//input[@name="search"]')
        search_box.clear()
        search_box.click()
        a = search_box.text
        print(a)
        search_box.send_keys("13912 W Pavillion Dr")
    except Exception as e:
        print(f"Could not find search box: {str(e)}")

finally:
    browser.quit()