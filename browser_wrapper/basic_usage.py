from browser import EnhancedBrowser
import time

browser = EnhancedBrowser()
try:
    browser.get("https://propwire.com/search")
    search_box = browser.find_element_by_xpath('//input[@name="search"]')
    search_box.send_keys("13912 W Pavillion Dr")
    # search_box.submit()
finally:
    browser.quit()