from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/backoffice/dashboard/$', consumers.DashboardConsumer.as_asgi()),
    re_path(r'ws/backoffice/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/backoffice/applications/(?P<application_id>\w+)/$', consumers.ApplicationConsumer.as_asgi()),
]
