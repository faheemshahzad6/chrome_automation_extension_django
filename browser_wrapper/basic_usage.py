from browser import EnhancedBrowser
import time

browser = EnhancedBrowser()
try:
    # Find and verify the html element
    html_element = browser.find_element_by_xpath('//html')
    print("\nFound HTML element:")
    print(f"Tag name: {html_element.tag_name}")
    print(f"Class name: {html_element.get_attribute('class')}")

    # Now try to send keys
    search_box = html_element.find_element_by_xpath('//input[@type="search"]')
    if search_box:
        search_box.send_keys("13912 W Pavillion Dr")

except Exception as e:
    print(f"Error: {str(e)}")
finally:
    browser.quit()