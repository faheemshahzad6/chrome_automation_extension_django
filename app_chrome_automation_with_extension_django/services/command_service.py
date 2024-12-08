from typing import Dict, Any, List, Optional
from ..commands.registry import CommandRegistry
from ..utils.logger import logger
from ..utils.validators import CommandValidator, ResponseValidator
from datetime import datetime, timedelta
import json
import asyncio
import threading
from collections import defaultdict


class CommandService:
    """Service for handling automation commands"""

    def __init__(self):
        self.command_registry = CommandRegistry()
        self.validator = CommandValidator()
        self.response_validator = ResponseValidator()
        self.command_history: List[Dict[str, Any]] = []
        self.last_execution_time: Dict[str, datetime] = {}
        self.execution_stats = defaultdict(lambda: {
            'attempted': 0,
            'success': 0,
            'failed': 0,
            'pending': 0,
            'avg_execution_time': 0.0
        })
        self._lock = threading.Lock()

    def get_command(self, command_name: str):
        """Get command by name"""
        return self.command_registry.get_command(command_name)

    async def execute_command(self,
                              command_name: str,
                              params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a command with parameters"""
        execution_start = datetime.now()
        params = params or {}

        try:
            command = self.command_registry.get_command(command_name)

            # Validate command parameters
            if not command.validate_params(**params):
                raise ValueError(f"Invalid parameters for command {command_name}")

            # Record execution attempt
            with self._lock:
                self.execution_stats[command_name]['attempted'] += 1
                execution_record = {
                    'command': command_name,
                    'params': params,
                    'timestamp': execution_start.isoformat(),
                    'status': 'pending'
                }
                self.command_history.append(execution_record)
                self.last_execution_time[command_name] = execution_start

            # Build command
            command_data = command.build_command(**params)

            return command_data

        except Exception as e:
            logger.error(f"Error executing command {command_name}: {str(e)}", exc_info=True)
            with self._lock:
                self.execution_stats[command_name]['failed'] += 1

            execution_record = {
                'command': command_name,
                'params': params,
                'timestamp': execution_start.isoformat(),
                'status': 'error',
                'error': str(e),
                'execution_time': (datetime.now() - execution_start).total_seconds()
            }
            self.command_history.append(execution_record)
            raise

    def record_command_result(self,
                              command_name: str,
                              params: Dict[str, Any],
                              result: Any,
                              execution_start: datetime):
        """Record successful command execution"""
        execution_time = (datetime.now() - execution_start).total_seconds()

        with self._lock:
            stats = self.execution_stats[command_name]
            stats['success'] += 1
            stats['avg_execution_time'] = (
                    (stats['avg_execution_time'] * (stats['success'] - 1) + execution_time) /
                    stats['success']
            )

            execution_record = {
                'command': command_name,
                'params': params,
                'timestamp': execution_start.isoformat(),
                'status': 'success',
                'result': result,
                'execution_time': execution_time
            }
            self.command_history.append(execution_record)

    def get_command_history(self,
                            command_name: Optional[str] = None,
                            limit: int = 100,
                            status: Optional[str] = None,
                            from_date: Optional[datetime] = None,
                            to_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get filtered command execution history"""
        with self._lock:
            history = self.command_history.copy()

        # Apply filters
        if command_name:
            history = [h for h in history if h['command'] == command_name]

        if status:
            history = [h for h in history if h.get('status') == status]

        if from_date:
            history = [h for h in history if datetime.fromisoformat(h['timestamp']) >= from_date]

        if to_date:
            history = [h for h in history if datetime.fromisoformat(h['timestamp']) <= to_date]

        # Sort by timestamp in descending order
        history = sorted(
            history,
            key=lambda x: x['timestamp'],
            reverse=True
        )

        return history[:limit]

    def get_available_commands(self) -> List[Dict[str, Any]]:
        """Get list of all available commands with statistics"""
        commands = self.command_registry.list_commands()

        for command in commands:
            command_name = command['name']
            if command_name in self.execution_stats:
                command['statistics'] = dict(self.execution_stats[command_name])
            if command_name in self.last_execution_time:
                command['last_executed'] = self.last_execution_time[command_name].isoformat()

        return commands

    def get_commands_by_type(self, command_type: str) -> List[Dict[str, Any]]:
        """Get all commands of a specific type"""
        return self.command_registry.get_commands_by_type(command_type)

    def get_command_stats(self,
                          command_name: Optional[str] = None,
                          time_range: Optional[str] = None) -> Dict[str, Any]:
        """
        Get command execution statistics

        time_range options: '1h', '24h', '7d', '30d'
        """
        with self._lock:
            if command_name:
                return dict(self.execution_stats[command_name])

            if time_range:
                # Calculate time threshold
                now = datetime.now()
                time_ranges = {
                    '1h': timedelta(hours=1),
                    '24h': timedelta(days=1),
                    '7d': timedelta(days=7),
                    '30d': timedelta(days=30)
                }
                threshold = now - time_ranges.get(time_range, time_ranges['24h'])

                # Filter history by time range
                filtered_history = [
                    h for h in self.command_history
                    if datetime.fromisoformat(h['timestamp']) >= threshold
                ]

                # Calculate statistics
                stats = defaultdict(lambda: {
                    'attempted': 0,
                    'success': 0,
                    'failed': 0,
                    'avg_execution_time': 0.0
                })

                for record in filtered_history:
                    cmd = record['command']
                    stats[cmd]['attempted'] += 1
                    if record['status'] == 'success':
                        stats[cmd]['success'] += 1
                        if 'execution_time' in record:
                            current_avg = stats[cmd]['avg_execution_time']
                            current_count = stats[cmd]['success']
                            stats[cmd]['avg_execution_time'] = (
                                    (current_avg * (current_count - 1) + record['execution_time']) /
                                    current_count
                            )
                    elif record['status'] == 'error':
                        stats[cmd]['failed'] += 1

                return dict(stats)

            return {name: dict(stats) for name, stats in self.execution_stats.items()}

    def clear_history(self,
                      command_name: Optional[str] = None,
                      before_date: Optional[datetime] = None):
        """Clear command execution history"""
        with self._lock:
            if command_name and before_date:
                self.command_history = [
                    h for h in self.command_history
                    if h['command'] != command_name or
                       datetime.fromisoformat(h['timestamp']) >= before_date
                ]
            elif command_name:
                self.command_history = [
                    h for h in self.command_history
                    if h['command'] != command_name
                ]
            elif before_date:
                self.command_history = [
                    h for h in self.command_history
                    if datetime.fromisoformat(h['timestamp']) >= before_date
                ]
            else:
                self.command_history = []

    def reset_stats(self, command_name: Optional[str] = None):
        """Reset command execution statistics"""
        with self._lock:
            if command_name:
                if command_name in self.execution_stats:
                    self.execution_stats[command_name] = {
                        'attempted': 0,
                        'success': 0,
                        'failed': 0,
                        'pending': 0,
                        'avg_execution_time': 0.0
                    }
            else:
                self.execution_stats.clear()

