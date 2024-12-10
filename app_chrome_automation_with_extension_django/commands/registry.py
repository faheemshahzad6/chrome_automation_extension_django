from typing import Dict, Type, List
from .base import AutomationCommand
from .storage import GetAllStorageCommand, GetCookiesCommand, ClearStorageCommand
from .dom import (
    # Basic page commands
    GetTitleCommand,
    GetUrlCommand,
    GetMetadataCommand,

    # Navigation commands
    NavigateCommand,
    GoBackCommand,
    GoForwardCommand,
    RefreshCommand,

    # Element finding commands
    GetElementCommand,
    FindElementByXPathCommand,
    FindElementsByXPathCommand,

    # Element interaction commands
    ClickElementCommand,
    SendKeysCommand,
    ClearElementCommand,
    SubmitFormCommand,

    # Element state commands
    IsElementEnabledCommand,
    IsElementSelectedCommand,
    IsElementDisplayedCommand,

    # Element property commands
    GetElementAttributeCommand,
    GetElementTextCommand,
    GetElementCssValueCommand, ToggleNetworkMonitorCommand
)


class CommandRegistry:
    _instance = None
    _commands: Dict[str, AutomationCommand] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CommandRegistry, cls).__new__(cls)
            cls._instance._initialize_commands()
        return cls._instance

    def _initialize_commands(self):
        """Initialize all available commands"""
        commands = [
            # Basic page commands
            GetTitleCommand(),
            GetUrlCommand(),
            GetMetadataCommand(),

            # Navigation commands
            NavigateCommand(),
            GoBackCommand(),
            GoForwardCommand(),
            RefreshCommand(),

            # Element finding commands
            GetElementCommand(),
            FindElementByXPathCommand(),
            FindElementsByXPathCommand(),

            # Element interaction commands
            ClickElementCommand(),
            SendKeysCommand(),
            ClearElementCommand(),
            SubmitFormCommand(),

            # Element state commands
            IsElementEnabledCommand(),
            IsElementSelectedCommand(),
            IsElementDisplayedCommand(),

            # Element property commands
            GetElementAttributeCommand(),
            GetElementTextCommand(),
            GetElementCssValueCommand(),

            # Storage commands
            GetAllStorageCommand(),
            GetCookiesCommand(),
            ClearStorageCommand(),
            ToggleNetworkMonitorCommand(),
        ]

        for command in commands:
            self._commands[command.name] = command

    def get_command(self, name: str) -> AutomationCommand:
        """Get a command by name"""
        if name not in self._commands:
            raise KeyError(f"Command '{name}' not found")
        return self._commands[name]

    def list_commands(self) -> List[Dict]:
        """List all available commands"""
        return [cmd.to_dict() for cmd in self._commands.values()]

    def execute_command(self, name: str, **kwargs) -> Dict:
        """Execute a command by name with parameters"""
        command = self.get_command(name)
        return command.build_command(**kwargs)

    def register_command(self, command: AutomationCommand):
        """Register a new command"""
        self._commands[command.name] = command

    def get_commands_by_type(self, command_type: str) -> List[Dict]:
        """Get all commands of a specific type"""
        return [
            cmd.to_dict()
            for cmd in self._commands.values()
            if cmd.to_dict().get("type") == command_type
        ]

    def get_command_info(self, name: str) -> Dict:
        """Get detailed information about a command"""
        command = self.get_command(name)
        info = command.to_dict()
        info['parameters'] = self._get_command_parameters(command)
        return info

    def _get_command_parameters(self, command: AutomationCommand) -> Dict:
        """Get command parameter information"""
        # This could be enhanced to provide more detailed parameter information
        params = {}
        if hasattr(command, 'validate_params'):
            # Extract parameter information from validation method
            import inspect
            sig = inspect.signature(command.validate_params)
            for param_name, param in sig.parameters.items():
                if param_name != 'kwargs':
                    params[param_name] = {
                        'required': param.default == inspect.Parameter.empty,
                        'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any'
                    }
        return params

    def clear_commands(self):
        """Clear all registered commands"""
        self._commands.clear()

    def reload_commands(self):
        """Reload all commands"""
        self.clear_commands()
        self._initialize_commands()

    def get_command_count(self) -> int:
        """Get total number of registered commands"""
        return len(self._commands)

    def get_command_types(self) -> List[str]:
        """Get list of unique command types"""
        types = set()
        for command in self._commands.values():
            cmd_dict = command.to_dict()
            if 'type' in cmd_dict:
                types.add(cmd_dict['type'])
        return sorted(list(types))

    def validate_command(self, name: str, params: Dict) -> bool:
        """Validate if command exists and parameters are valid"""
        try:
            command = self.get_command(name)
            return command.validate_params(**params)
        except (KeyError, AttributeError):
            return False