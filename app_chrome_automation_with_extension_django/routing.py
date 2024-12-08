from django.urls import re_path
from .websocket.consumer import AutomationConsumer

websocket_urlpatterns = [
    re_path(r'ws/app_chrome_automation_with_extension_django/$', AutomationConsumer.as_asgi()),
]

# WebSocket Protocol Documentation
"""
WebSocket Protocol Specification:

1. Connection Establishment
   Endpoint: ws://localhost:1234/ws/app_chrome_automation_with_extension_django/

   Connection Flow:
   1. Client initiates WebSocket connection
   2. Server accepts and sends connection_established message
   3. Extension sends extension_connected message
   4. Server confirms with connection_confirmed message

2. Message Types:

   Client -> Server Messages:

   a) Extension Connected:
   {
       "type": "extension_connected",
       "data": {
           "extensionId": "extension_id_string"
       }
   }

   b) Script Result:
   {
       "type": "SCRIPT_RESULT",
       "status": "success",
       "result": any,
       "command_id": "unique_command_id"
   }

   c) Script Error:
   {
       "type": "SCRIPT_ERROR",
       "status": "error",
       "error": "error_message",
       "command_id": "unique_command_id"
   }

   Server -> Client Messages:

   a) Connection Established:
   {
       "type": "connection_established",
       "message": "Connected to Django WebSocket server",
       "timestamp": "ISO_timestamp"
   }

   b) Connection Confirmed:
   {
       "type": "connection_confirmed",
       "message": "Connection established successfully",
       "timestamp": "ISO_timestamp"
   }

   c) Automation Command:
   {
       "type": "automation_command",
       "command": {
           "type": "EXECUTE_SCRIPT",
           "script": "command_string",
           "command_id": "unique_command_id"
       },
       "timestamp": "ISO_timestamp"
   }

3. Error Handling:

   a) Connection Errors:
      - Disconnection handling with reconnection attempts
      - Connection timeout handling
      - Authentication failures (if implemented)

   b) Command Execution Errors:
      - Invalid command format
      - Command timeout
      - Script execution failures
      - Permission errors

   c) Protocol Errors:
      - Invalid message format
      - Unknown message types
      - Missing required fields

4. Command Execution Flow:

   1. API endpoint receives command request
   2. Command is validated and processed
   3. Command is sent through WebSocket
   4. Extension executes command in browser
   5. Result is sent back through WebSocket
   6. API returns result to caller

5. Timeouts and Limits:

   - Connection timeout: 30 seconds
   - Command execution timeout: 60 seconds
   - Reconnection attempts: 5 times
   - Message size limit: 1MB

6. Security Considerations:

   - All sensitive data should be sanitized
   - Command injection prevention
   - XSS protection in script execution
   - Origin verification
   - Rate limiting
"""