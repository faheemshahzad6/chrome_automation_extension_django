from browser import EnhancedBrowser
import time
import logging
from typing import Any, Dict, Optional
import unittest


class BrowserAutomationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger('BrowserAutomationTests')

        # Initialize browser
        cls.browser = EnhancedBrowser(base_url="http://localhost:1234")
        cls.browser.implicitly_wait(10)  # Set implicit wait

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()

    def setUp(self):
        # Navigate to test page before each test
        self.browser.get("http://localhost:63342/chrome_automation_with_extension_django/browser_wrapper/test-page.html?_ijt=c0blji0u71orvg8s21iual4t9s&_ij_reload=RELOAD_ON_SAVE")
        time.sleep(2)  # Allow page to fully load

    def test_01_basic_navigation(self):
        """Test basic navigation methods"""
        self.logger.info("Testing basic navigation...")

        # Test title and URL
        self.assertEqual(self.browser.title, "Browser Automation Test Page")
        self.assertTrue(self.browser.current_url.endswith("/test-page.html"))

        # Test navigation methods
        self.browser.refresh()
        time.sleep(1)
        self.browser.back()
        time.sleep(1)
        self.browser.forward()
        time.sleep(1)

    def test_02_element_finding(self):
        """Test element finding methods"""
        self.logger.info("Testing element finding...")

        # Find by ID
        text_input = self.browser.find_element_by_xpath('//input[@id="textInput"]')
        self.assertIsNotNone(text_input)

        # Find by name
        username = self.browser.find_element_by_xpath('//input[@name="username"]')
        self.assertIsNotNone(username)

        # Find by class name
        test_section = self.browser.find_element_by_xpath('//div[@class="test-section"]')
        self.assertIsNotNone(test_section)

    def test_03_element_interaction(self):
        """Test element interaction methods"""
        self.logger.info("Testing element interaction...")

        # Test text input
        text_input = self.browser.find_element_by_xpath('//input[@id="textInput"]')
        text_input.send_keys("Test input")
        self.assertEqual(text_input.get_attribute("value"), "Test input")
        text_input.clear()
        self.assertEqual(text_input.get_attribute("value"), "")

        # Test button click
        submit_button = self.browser.find_element_by_xpath('//button[@id="submitButton"]')
        submit_button.click()

    def test_04_form_interaction(self):
        """Test form interactions"""
        self.logger.info("Testing form interactions...")

        # Fill out form
        self.browser.find_element_by_xpath('//input[@id="username"]').send_keys("testuser")
        self.browser.find_element_by_xpath('//input[@id="password"]').send_keys("password123")

        # Select radio button
        self.browser.find_element_by_xpath('//input[@id="male"]').click()

        # Check checkbox
        self.browser.find_element_by_xpath('//input[@id="coding"]').click()

        # Select dropdown option
        country_select = self.browser.find_element_by_xpath('//select[@id="country"]')
        country_select.find_element_by_xpath('.//option[@value="us"]').click()

        # Fill textarea
        self.browser.find_element_by_xpath('//textarea[@id="comments"]').send_keys("Test comment")

        # Submit form
        self.browser.find_element_by_xpath('//form[@id="testForm"]//button').click()

        # Verify form submission
        time.sleep(1)
        alert = self.browser.find_element_by_xpath('//div[@id="formAlert"]')
        self.assertTrue(alert.is_displayed())

    def test_05_element_state(self):
        """Test element state methods"""
        self.logger.info("Testing element state...")

        # Test element visibility
        visible_element = self.browser.find_element_by_xpath('//div[@id="basicElements"]')
        self.assertTrue(visible_element.is_displayed())

        # Test element enabled state
        enabled_input = self.browser.find_element_by_xpath('//input[@id="textInput"]')
        self.assertTrue(enabled_input.is_enabled())

        # Test element selected state
        checkbox = self.browser.find_element_by_xpath('//input[@id="coding"]')
        self.assertFalse(checkbox.is_selected())
        checkbox.click()
        self.assertTrue(checkbox.is_selected())

    def test_06_dynamic_elements(self):
        """Test handling of dynamic elements"""
        self.logger.info("Testing dynamic elements...")

        # Click button to show delayed element
        self.browser.find_element_by_xpath('//button[contains(text(), "Show Delayed")]').click()

        # Wait for element to appear
        time.sleep(2)
        delayed_element = self.browser.find_element_by_xpath('//div[@id="delayedDiv"]')
        self.assertTrue(delayed_element.is_displayed())

    def test_07_storage_handling(self):
        """Test storage handling methods"""
        self.logger.info("Testing storage handling...")

        # Set storage values
        self.browser.find_element_by_xpath('//button[contains(text(), "Set Storage")]').click()
        time.sleep(1)

        # Verify storage values
        storage_data = self.browser._execute_command("getAllStorage")
        self.assertIn('testKey', storage_data['localStorage'])
        self.assertIn('sessionKey', storage_data['sessionStorage'])

        # Clear storage
        self.browser.find_element_by_xpath('//button[contains(text(), "Clear Storage")]').click()
        time.sleep(1)


if __name__ == '__main__':
    unittest.main(verbosity=2)