from django.urls import path
from . import views

app_name = 'app_chrome_automation_with_extension_django'

urlpatterns = [
    # Web UI endpoints
    path('', views.dashboard, name='dashboard'),
    path('test/', views.test_websocket, name='test_websocket'),

    # API v1 Command Endpoints
    path('api/commands/execute', views.execute_command_api, name='execute_command_api'),  # Removed trailing slash
    path('api/commands/list', views.get_available_commands_api, name='list_commands_api'),  # Removed trailing slash
    path('api/commands/history', views.get_command_history_api, name='command_history_api'),  # Removed trailing slash

    # API v1 Storage Endpoints
    path('api/storage/data', views.get_storage_data_api, name='storage_data_api'),  # Removed trailing slash
]
