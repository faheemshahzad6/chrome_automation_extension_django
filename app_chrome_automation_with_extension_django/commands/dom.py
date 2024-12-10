from typing import Dict, Any
from .base import DOMCommand


class GetElementCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="get_element",
            description="Get element by selector",
            script_name="findElement"
        )

    def validate_params(self, **kwargs) -> bool:
        return "selector" in kwargs and isinstance(kwargs["selector"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}"


class FindElementByXPathCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="find_element_by_xpath",  # Updated to match
            description="Find element by XPath",
            script_name="find_element_by_xpath"
        )

    def validate_params(self, **kwargs) -> bool:
        return "xpath" in kwargs and isinstance(kwargs["xpath"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['xpath']}"


class FindElementsByXPathCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="find_elements_by_xpath",
            description="Find elements by XPath",
            script_name="findElementsByXPath"
        )

    def validate_params(self, **kwargs) -> bool:
        return "xpath" in kwargs and isinstance(kwargs["xpath"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['xpath']}"


class ClickElementCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="click_element",
            description="Click on an element",
            script_name="clickElement"
        )

    def validate_params(self, **kwargs) -> bool:
        return "selector" in kwargs and isinstance(kwargs["selector"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}"


class SendKeysCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="send_keys",
            description="Send keys to an element",
            script_name="sendKeys"
        )

    def validate_params(self, **kwargs) -> bool:
        return all(key in kwargs for key in ["selector", "value"])

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}|{kwargs['value']}"


class ClearElementCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="clear_element",
            description="Clear an element's value",
            script_name="clearElement"
        )

    def validate_params(self, **kwargs) -> bool:
        return "selector" in kwargs and isinstance(kwargs["selector"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}"


class SubmitFormCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="submit_form",
            description="Submit a form",
            script_name="submitForm"
        )

    def validate_params(self, **kwargs) -> bool:
        return "selector" in kwargs and isinstance(kwargs["selector"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}"


class IsElementEnabledCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="is_element_enabled",
            description="Check if element is enabled",
            script_name="isElementEnabled"
        )

    def validate_params(self, **kwargs) -> bool:
        return "selector" in kwargs and isinstance(kwargs["selector"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}"


class IsElementSelectedCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="is_element_selected",
            description="Check if element is selected",
            script_name="isElementSelected"
        )

    def validate_params(self, **kwargs) -> bool:
        return "selector" in kwargs and isinstance(kwargs["selector"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}"


class IsElementDisplayedCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="is_element_displayed",
            description="Check if element is displayed",
            script_name="isElementDisplayed"
        )

    def validate_params(self, **kwargs) -> bool:
        return "selector" in kwargs and isinstance(kwargs["selector"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}"


class GetElementAttributeCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="get_element_attribute",
            description="Get element attribute by selector",
            script_name="getElementAttribute"
        )

    def validate_params(self, **kwargs) -> bool:
        return all(key in kwargs for key in ["selector", "attribute"])

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}|{kwargs['attribute']}"


class GetElementTextCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="get_element_text",
            description="Get element text content",
            script_name="getElementText"
        )

    def validate_params(self, **kwargs) -> bool:
        return "selector" in kwargs and isinstance(kwargs["selector"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}"


class GetElementCssValueCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="get_element_css_value",
            description="Get element CSS property value",
            script_name="getElementCssValue"
        )

    def validate_params(self, **kwargs) -> bool:
        return all(key in kwargs for key in ["selector", "property_name"])

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['selector']}|{kwargs['property_name']}"


class NavigateCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="navigate",  # Changed from "navigateToUrl"
            description="Navigate to URL",
            script_name="navigate"  # Changed to match the content script
        )

    def validate_params(self, **kwargs) -> bool:
        return "url" in kwargs and isinstance(kwargs["url"], str)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{kwargs['url']}"


class GoBackCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="back",
            description="Navigate back in history",
            script_name="goBack"
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name


class GoForwardCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="forward",
            description="Navigate forward in history",
            script_name="goForward"
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name


class RefreshCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="refresh",
            description="Refresh the current page",
            script_name="refresh"
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name


class GetTitleCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="getTitle",
            description="Get page title",
            script_name="getTitle"
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name


class GetUrlCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="getUrl",
            description="Get current URL",
            script_name="getUrl"
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name


class GetMetadataCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="getMetadata",
            description="Get page metadata",
            script_name="getMetadata"
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name


class GetAllStorageCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="getAllStorage",  # Match the command name in registry
            description="Get all storage data including cookies, localStorage, and sessionStorage",
            script_name="getAllStorage"  # Match the script name in basic-commands.js
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name


class GetCookiesCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="getCookies",
            description="Get all cookies from the current page",
            script_name="getCookies"
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name


class ToggleNetworkMonitorCommand(DOMCommand):
    def __init__(self):
        super().__init__(
            name="toggleNetworkMonitor",
            description="Toggle network request monitoring",
            script_name="toggleNetworkMonitor"
        )

    def validate_params(self, **kwargs) -> bool:
        return "value" in kwargs and isinstance(kwargs["value"], bool)

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|{str(kwargs['value']).lower()}"
