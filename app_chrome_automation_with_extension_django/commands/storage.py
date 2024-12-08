from typing import Dict, Any
from .base import StorageCommand

class GetAllStorageCommand(StorageCommand):
    def __init__(self):
        super().__init__(
            name="get_all_storage",
            description="Retrieve all storage data including cookies, localStorage, and sessionStorage",
            script_name="getAllStorage"
        )

    def build_script(self, **kwargs) -> str:
        return self.script_name

class GetCookiesCommand(StorageCommand):
    def __init__(self):
        super().__init__(
            name="get_cookies",
            description="Retrieve all cookies from the current page",
            script_name="getCookies"
        )

    def build_script(self, **kwargs) -> str:
        return f"{self.script_name}|"

class ClearStorageCommand(StorageCommand):
    def __init__(self):
        super().__init__(
            name="clear_storage",
            description="Clear specified storage type (localStorage, sessionStorage, or cookies)",
            script_name="clearStorage"
        )

    def validate_params(self, **kwargs) -> bool:
        storage_type = kwargs.get("storage_type")
        return storage_type in ["localStorage", "sessionStorage", "cookies", "all"]

    def build_script(self, **kwargs) -> str:
        storage_type = kwargs.get("storage_type", "all")
        return f"{self.script_name}|{storage_type}"