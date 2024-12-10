import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime
from ..commands.registry import CommandRegistry
from ..utils.logger import setup_logger
from channels.layers import get_channel_layer
from ..views import command_responses, store_command_response
from typing import Optional, Dict, Any
from pathlib import Path
import aiofiles

logger = setup_logger(__name__)


class AutomationConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_file = None
        self.logs_dir = None
        self.command_registry = CommandRegistry()
        self.command_task: Optional[asyncio.Task] = None
        self.storage_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.connected = False
        self.extension_connected = False
        self.pending_commands = {}

    async def connect(self):
        """Handle WebSocket connection"""
        try:
            logger.info("WebSocket connection attempt received")
            await self.accept()
            self.connected = True
            logger.info("WebSocket connection accepted")

            # Add to automation group
            await self.channel_layer.group_add("automation", self.channel_name)

            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self.periodic_cleanup())

            # Send connection confirmation
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'message': 'Connected to Django WebSocket server',
                'timestamp': datetime.now().isoformat()
            }))

            # Create logs directory if it doesn't exist
            self.logs_dir = Path("network_logs")
            self.logs_dir.mkdir(exist_ok=True)

            # Create a new log file for this session
            self.log_file = self.logs_dir / f"network_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

        except Exception as e:
            logger.error(f"Error in connect: {str(e)}", exc_info=True)
            self.connected = False
            raise

    async def disconnect(self, close_code: int):
        """Handle WebSocket disconnection"""
        try:
            logger.info(f"WebSocket disconnected with code: {close_code}")
            self.connected = False
            self.extension_connected = False

            # Handle any pending commands
            for command_id, command_data in self.pending_commands.items():
                store_command_response(command_id, {
                    'error': 'WebSocket disconnected',
                    'close_code': close_code
                })

            # Cancel cleanup task
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            # Remove from automation group
            await self.channel_layer.group_discard("automation", self.channel_name)

        except Exception as e:
            logger.error(f"Error in disconnect: {str(e)}", exc_info=True)

    async def receive(self, text_data: str):
        """Handle incoming WebSocket messages"""
        logger.info(f"Received message: {text_data}")
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'extension_connected':
                await self.handle_extension_connected(data)
            elif message_type == 'SCRIPT_RESULT':
                await self.handle_script_result(data)
            elif message_type == 'SCRIPT_ERROR':
                await self.handle_script_error(data)
            elif data.get('type') == 'network_request':
                await self.handle_network_request(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)

    async def handle_network_request(self, data):
        """Handle network request data"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()

            # Format the log entry
            log_entry = json.dumps({
                'timestamp': data['timestamp'],
                'event': data['event'],
                'data': data['data']
            })

            # Append to log file
            async with aiofiles.open(self.log_file, mode='a') as f:
                await f.write(log_entry + '\n')

            # Optional: Send confirmation back to client
            await self.send(text_data=json.dumps({
                'type': 'network_log_confirmation',
                'requestId': data['data'].get('requestId'),
                'status': 'logged'
            }))

        except Exception as e:
            print(f"Error handling network request: {str(e)}")
            # Notify client of error
            await self.send(text_data=json.dumps({
                'type': 'network_log_error',
                'error': str(e)
            }))

    async def send_command(self, event: Dict[str, Any]):
        """Handle command messages from group"""
        try:
            if not self.extension_connected:
                logger.warning("Cannot send command: Extension not connected")
                store_command_response(event['command_id'], {
                    'error': 'Extension not connected'
                })
                return

            command = self.command_registry.execute_command(
                event['command'],
                **event.get('params', {})
            )

            # Add command ID for response tracking
            command_id = event['command_id']
            command['command_id'] = command_id

            # Track pending command
            self.pending_commands[command_id] = {
                'command': event['command'],
                'params': event.get('params', {}),
                'timestamp': datetime.now().isoformat()
            }

            await self.send(text_data=json.dumps({
                'type': 'automation_command',
                'command': command,
                'timestamp': datetime.now().isoformat()
            }))

            logger.info(f"Command sent: {event['command']} with ID: {command_id}")

        except Exception as e:
            logger.error(f"Error sending command: {str(e)}", exc_info=True)
            store_command_response(event['command_id'], {
                'error': f'Error sending command: {str(e)}'
            })

    async def handle_extension_connected(self, data: Dict[str, Any]):
        """Handle extension connection message"""
        logger.info("Extension connected successfully")
        self.extension_connected = True

        # Clear any previous pending commands
        self.pending_commands = {}

        await self.send(text_data=json.dumps({
            'type': 'connection_confirmed',
            'message': 'Connection established successfully',
            'timestamp': datetime.now().isoformat()
        }))

    async def handle_script_result(self, data: Dict[str, Any]):
        """Handle successful script execution result"""
        logger.info("Script execution successful")
        try:
            result = data.get('result')
            command_id = data.get('command_id')

            # Parse result if it's a JSON string
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    pass  # Keep original string if not valid JSON

            if command_id:
                logger.info(f"Storing response for command {command_id}")
                store_command_response(command_id, result)
                self.pending_commands.pop(command_id, None)

            logger.info(f"Result: {result}")

        except Exception as e:
            logger.error(f"Error handling script result: {str(e)}", exc_info=True)
            if command_id:
                store_command_response(command_id, {
                    'error': f'Error processing result: {str(e)}'
                })
                self.pending_commands.pop(command_id, None)

    # In consumer.py, update the handle_script_error method:
    async def handle_script_error(self, data: Dict[str, Any]):
        """Handle script execution error"""
        error = data.get('error')
        command_id = data.get('command_id')
        stack = data.get('stack')

        logger.error(f"Script execution failed: {error}")
        if stack:
            logger.error(f"Error stack trace: {stack}")

        if command_id:
            # Store error response for the command
            store_command_response(command_id, {
                'error': error,
                'stack': stack,
                'timestamp': datetime.now().isoformat()
            })

            # Remove from pending commands
            self.pending_commands.pop(command_id, None)

            # Notify client about error
            try:
                await self.send(text_data=json.dumps({
                    'type': 'command_error',
                    'command_id': command_id,
                    'error': error,
                    'timestamp': datetime.now().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error sending error notification: {str(e)}")

    async def periodic_cleanup(self):
        """Periodically clean up old pending commands"""
        try:
            while self.connected:
                self.cleanup_pending_commands()
                await asyncio.sleep(60)  # Run every minute
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {str(e)}", exc_info=True)

    def cleanup_pending_commands(self, max_age_seconds: int = 60):
        """Clean up old pending commands"""
        current_time = datetime.now()
        to_delete = []

        for command_id, command_data in self.pending_commands.items():
            try:
                command_time = datetime.fromisoformat(command_data['timestamp'])
                age = (current_time - command_time).total_seconds()

                if age > max_age_seconds:
                    to_delete.append(command_id)
                    store_command_response(command_id, {
                        'error': f'Command timed out after {max_age_seconds} seconds'
                    })
            except (ValueError, KeyError) as e:
                logger.error(f"Error processing command timestamp: {str(e)}")
                to_delete.append(command_id)

        for command_id in to_delete:
            self.pending_commands.pop(command_id, None)
