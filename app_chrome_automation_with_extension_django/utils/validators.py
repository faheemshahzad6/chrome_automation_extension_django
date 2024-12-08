from typing import Any, Dict, Optional, Union
import re
from urllib.parse import urlparse


class CommandValidator:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if a string is a valid URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def validate_selector(selector: str) -> bool:
        """Validate if a string is a valid CSS selector"""
        try:
            # Basic CSS selector validation
            if not selector or not isinstance(selector, str):
                return False

            # Check for common invalid characters
            invalid_chars = ['<', '>', '{', '}', '`']
            if any(char in selector for char in invalid_chars):
                return False

            # Check for balanced brackets and parentheses
            brackets = {'[': ']', '(': ')'}
            stack = []

            for char in selector:
                if char in brackets.keys():
                    stack.append(char)
                elif char in brackets.values():
                    if not stack:
                        return False
                    if char != brackets[stack.pop()]:
                        return False

            return len(stack) == 0
        except Exception:
            return False

    @staticmethod
    def validate_storage_type(storage_type: str) -> bool:
        """Validate storage type parameter"""
        valid_types = ['localStorage', 'sessionStorage', 'cookies', 'all']
        return storage_type in valid_types

    @staticmethod
    def validate_command_params(params: Dict[str, Any], required_params: Dict[str, type]) -> bool:
        """Validate command parameters against required parameters"""
        try:
            for param_name, param_type in required_params.items():
                # Check if required parameter exists
                if param_name not in params:
                    return False

                # Check parameter type
                if not isinstance(params[param_name], param_type):
                    return False

            return True
        except Exception:
            return False


class ResponseValidator:
    @staticmethod
    def validate_storage_response(response: Dict[str, Any]) -> bool:
        """Validate storage response format"""
        required_fields = ['url', 'timestamp', 'cookies', 'localStorage', 'sessionStorage']
        return all(field in response for field in required_fields)

    @staticmethod
    def validate_script_result(response: Dict[str, Any]) -> bool:
        """Validate script execution result"""
        return all(field in response for field in ['type', 'status']) and (
                'result' in response or 'error' in response
        )


class DataValidator:
    @staticmethod
    def validate_json_data(data: str) -> bool:
        """Validate if a string is valid JSON"""
        try:
            import json
            json.loads(data)
            return True
        except Exception:
            return False

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Sanitize input string"""
        if not isinstance(input_str, str):
            return ''

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>{}`]', '', input_str)
        return sanitized.strip()