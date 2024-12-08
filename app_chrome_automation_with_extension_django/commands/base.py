from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json


class AutomationCommand(ABC):
    """Base class for all automation commands"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def build_command(self, **kwargs) -> Dict[str, Any]:
        """Build the command to be sent to the extension"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary format"""
        return {
            "name": self.name,
            "description": self.description
        }

    def validate_params(self, **kwargs) -> bool:
        """Validate command parameters"""
        return True


class ScriptCommand(AutomationCommand):
    """Base class for commands that execute scripts"""

    def __init__(self, name: str, description: str, script_name: str):
        super().__init__(name, description)
        self.script_name = script_name

    def build_command(self, **kwargs) -> Dict[str, Any]:
        """Build a script execution command"""
        if not self.validate_params(**kwargs):
            raise ValueError(f"Invalid parameters for command {self.name}")

        command = {
            "type": "EXECUTE_SCRIPT",
            "script": self.build_script(**kwargs)
        }
        return command

    @abstractmethod
    def build_script(self, **kwargs) -> str:
        """Build the script to be executed"""
        pass


class StorageCommand(ScriptCommand):
    """Base class for storage-related commands"""

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["type"] = "storage"
        return result


class NavigationCommand(ScriptCommand):
    """Base class for navigation-related commands"""

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["type"] = "navigation"
        return result


class DOMCommand(ScriptCommand):
    """Base class for DOM-related commands"""

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result["type"] = "dom"
        return result