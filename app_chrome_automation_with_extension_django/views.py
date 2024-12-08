from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services.command_service import CommandService
from .utils.logger import logger
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import asyncio
import uuid
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional

command_service = CommandService()

# Global storage for command responses with thread safety
command_responses: Dict[str, Any] = {}
response_lock = threading.Lock()


def store_command_response(command_id: str, response: Any) -> None:
    """Thread-safe storage of command responses"""
    logger.info(f"Storing response for command {command_id}: {response}")
    with response_lock:
        command_responses[command_id] = {
            'response': response,
            'timestamp': time.time()
        }


def get_command_response(command_id: str, timeout: int = 10) -> Optional[Any]:
    """Get command response with timeout"""
    start_time = time.time()
    poll_interval = 0.1  # 100ms polling interval

    while time.time() - start_time < timeout:
        with response_lock:
            if command_id in command_responses:
                data = command_responses[command_id]
                if data['response'] is not None:
                    return data['response']
        time.sleep(poll_interval)

    return None


def clean_command_response(command_id: str) -> None:
    """Thread-safe cleanup of command responses"""
    with response_lock:
        if command_id in command_responses:
            del command_responses[command_id]


def cleanup_old_responses() -> None:
    """Clean up old command responses"""
    with response_lock:
        current_time = time.time()
        timeout = 300  # 5 minutes timeout
        to_delete = [
            cmd_id for cmd_id, data in command_responses.items()
            if current_time - data['timestamp'] > timeout
        ]
        for cmd_id in to_delete:
            del command_responses[cmd_id]


def dashboard(request):
    """Main dashboard view"""
    return render(request, 'dashboard.html', {
        'page_title': 'Automation Dashboard'
    })


def test_websocket(request):
    """WebSocket test page"""
    return render(request, 'websocket_test.html', {
        'page_title': 'WebSocket Test'
    })


@csrf_exempt
@require_http_methods(["POST"])
def execute_command_api(request):
    """Execute automation command API endpoint"""
    try:
        # Parse request body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format in request body'
            }, status=400)

        command_name = data.get('command')
        params = data.get('params', {})
        timeout = int(data.get('timeout', 10))

        # Input validation
        if not command_name:
            return JsonResponse({
                'status': 'error',
                'message': 'Command name is required'
            }, status=400)

        if timeout < 1 or timeout > 60:
            return JsonResponse({
                'status': 'error',
                'message': 'Timeout must be between 1 and 60 seconds'
            }, status=400)

        # Validate command exists and parameters
        try:
            command = command_service.get_command(command_name)
            if not command.validate_params(**params):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Invalid parameters for command {command_name}'
                }, status=400)
        except KeyError:
            return JsonResponse({
                'status': 'error',
                'message': f'Unknown command: {command_name}'
            }, status=404)

        # Generate command ID and initialize response
        command_id = str(uuid.uuid4())
        store_command_response(command_id, None)

        try:
            # Send command through WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'automation',
                {
                    'type': 'send_command',
                    'command': command_name,
                    'params': params,
                    'command_id': command_id
                }
            )

            logger.info(f"Command sent to WebSocket: {command_name} (ID: {command_id})")

            # Wait for response
            response = get_command_response(command_id, timeout)

            # Clean up stored response
            clean_command_response(command_id)

            if response is None:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Command execution timeout after {timeout} seconds'
                }, status=408)

            # Check for error in response
            if isinstance(response, dict) and 'error' in response:
                return JsonResponse({
                    'status': 'error',
                    'command': command_name,
                    'error': response['error']
                }, status=500)

            # Return successful response
            return JsonResponse({
                'status': 'success',
                'command': command_name,
                'params': params,
                'result': response,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            # Clean up command response if stored
            clean_command_response(command_id)
            raise e

    except Exception as e:
        logger.error(f"Error executing command: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_available_commands_api(request):
    """API endpoint to list all available commands"""
    try:
        command_type = request.GET.get('type')
        response_format = request.GET.get('format', 'full')

        if command_type:
            commands = command_service.get_commands_by_type(command_type)
        else:
            commands = command_service.get_available_commands()

        if response_format == 'simple':
            commands = [{
                'name': cmd['name'],
                'description': cmd['description'],
                'type': cmd.get('type', 'unknown')
            } for cmd in commands]

        return JsonResponse({
            'status': 'success',
            'commands': commands,
            'count': len(commands),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error listing commands: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_command_history_api(request):
    """API endpoint to get command execution history"""
    try:
        command_name = request.GET.get('command')
        status_filter = request.GET.get('status')
        from_date = request.GET.get('from')
        to_date = request.GET.get('to')

        try:
            limit = int(request.GET.get('limit', 100))
            if limit < 1:
                raise ValueError("Limit must be positive")
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid limit parameter: {str(e)}'
            }, status=400)

        # Parse dates if provided
        date_filters = {}
        if from_date:
            try:
                date_filters['from_date'] = datetime.fromisoformat(from_date)
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid from_date format. Use ISO format.'
                }, status=400)

        if to_date:
            try:
                date_filters['to_date'] = datetime.fromisoformat(to_date)
            except ValueError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid to_date format. Use ISO format.'
                }, status=400)

        history = command_service.get_command_history(
            command_name=command_name,
            limit=limit,
            status=status_filter,
            **date_filters
        )

        return JsonResponse({
            'status': 'success',
            'history': history,
            'count': len(history),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting command history: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_storage_data_api(request):
    """API endpoint to get storage data"""
    try:
        storage_type = request.GET.get('type')
        keys = request.GET.get('keys', '').split(',') if request.GET.get('keys') else None

        try:
            timeout = int(request.GET.get('timeout', 10))
            if timeout < 1 or timeout > 60:
                raise ValueError("Timeout must be between 1 and 60 seconds")
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Invalid timeout parameter: {str(e)}'
            }, status=400)

        # Generate command ID
        command_id = str(uuid.uuid4())
        store_command_response(command_id, None)

        try:
            # Prepare command parameters
            command_params = {}
            if storage_type:
                command_params['type'] = storage_type
            if keys:
                command_params['keys'] = keys

            # Send command through WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'automation',
                {
                    'type': 'send_command',
                    'command': 'getAllStorage',
                    'params': command_params,
                    'command_id': command_id
                }
            )

            logger.info(f"Storage data request sent (ID: {command_id})")

            # Wait for response
            response = get_command_response(command_id, timeout)

            # Clean up stored response
            clean_command_response(command_id)

            if response is None:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Storage data retrieval timeout after {timeout} seconds'
                }, status=408)

            # Check for error in response
            if isinstance(response, dict) and 'error' in response:
                return JsonResponse({
                    'status': 'error',
                    'error': response['error']
                }, status=500)

            # Filter response by storage type if specified
            if storage_type and isinstance(response, dict):
                filtered_response = {
                    storage_type: response.get(storage_type),
                    'url': response.get('url'),
                    'timestamp': response.get('timestamp')
                }

                # Further filter by keys if specified
                if keys and storage_type in filtered_response:
                    storage_data = filtered_response[storage_type]
                    if isinstance(storage_data, dict):
                        filtered_response[storage_type] = {
                            k: v for k, v in storage_data.items()
                            if k in keys
                        }
                    elif isinstance(storage_data, list):
                        filtered_response[storage_type] = [
                            item for item in storage_data
                            if any(key in str(item) for key in keys)
                        ]

                response = filtered_response

            return JsonResponse({
                'status': 'success',
                'data': response,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            # Clean up command response if stored
            clean_command_response(command_id)
            raise e

    except Exception as e:
        logger.error(f"Error getting storage data: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

