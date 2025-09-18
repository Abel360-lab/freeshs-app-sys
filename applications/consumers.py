import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'dashboard_updates'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial dashboard data
        await self.send_dashboard_data()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'get_dashboard_data':
            await self.send_dashboard_data()

    async def send_dashboard_data(self):
        """Send current dashboard statistics"""
        data = await self.get_dashboard_stats()
        await self.send(text_data=json.dumps({
            'type': 'dashboard_data',
            'data': data
        }))

    async def dashboard_updated(self, event):
        """Send dashboard update to WebSocket"""
        data = event['data']
        await self.send(text_data=json.dumps({
            'type': 'dashboard_updated',
            'data': data
        }))

    @database_sync_to_async
    def get_dashboard_stats(self):
        """Get current dashboard statistics"""
        try:
            from .models import SupplierApplication
            from django.db.models import Count
            
            total_applications = SupplierApplication.objects.count()
            status_counts = SupplierApplication.objects.values('status').annotate(
                count=Count('id')
            ).order_by('status')
            
            # Calculate status percentages
            status_percentages = {}
            total_percentage = 0
            for status in status_counts:
                percentage = (status['count'] / total_applications * 100) if total_applications > 0 else 0
                # Use more precise rounding to avoid floating point errors
                status_percentages[status['status']] = round(percentage * 10) / 10
                total_percentage += status_percentages[status['status']]
            
            # Normalize percentages to ensure they add up to exactly 100.0
            if total_percentage != 100.0 and total_percentage > 0:
                # Find the largest percentage and adjust it to make the total exactly 100.0
                max_status = max(status_percentages.items(), key=lambda x: x[1])
                if max_status[1] > 0:
                    adjustment = 100.0 - total_percentage
                    status_percentages[max_status[0]] = round((max_status[1] + adjustment) * 10) / 10
            
            # Recent applications
            recent_applications = []
            for app in SupplierApplication.objects.select_related('region').order_by('-created_at')[:5]:
                recent_applications.append({
                    'id': app.id,
                    'business_name': app.business_name,
                    'status': app.status,
                    'created_at': app.created_at.isoformat(),
                    'region__name': app.region.name if app.region else None
                })
            
            return {
                'total_applications': total_applications,
                'status_percentages': status_percentages,
                'recent_applications': recent_applications,
                'timestamp': timezone.now().isoformat()
            }
        except Exception as e:
            # Return safe fallback data if database operations fail
            return {
                'total_applications': 0,
                'status_percentages': {},
                'recent_applications': [],
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            }

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'notification_updates'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'get_notifications':
            await self.send_notifications()

    async def send_notifications(self):
        """Send recent notifications"""
        notifications = await self.get_recent_notifications()
        await self.send(text_data=json.dumps({
            'type': 'notifications',
            'data': notifications
        }))

    async def notification_created(self, event):
        """Send new notification to WebSocket"""
        notification = event['notification']
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'data': notification
        }))

    @database_sync_to_async
    def get_recent_notifications(self):
        """Get recent notifications"""
        from notifications.models import NotificationLog
        
        notifications = []
        for notif in NotificationLog.objects.select_related('application').order_by('-created_at')[:10]:
            notifications.append({
                'id': notif.id,
                'subject': notif.subject,
                'status': notif.status,
                'created_at': notif.created_at.isoformat(),
                'application__business_name': notif.application.business_name if notif.application else None
            })
        return notifications

class ApplicationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.application_id = self.scope['url_route']['kwargs']['application_id']
        self.room_group_name = f'application_{self.application_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'get_application_data':
            await self.send_application_data()

    async def send_application_data(self):
        """Send current application data"""
        data = await self.get_application_data()
        await self.send(text_data=json.dumps({
            'type': 'application_data',
            'data': data
        }))

    async def application_updated(self, event):
        """Send application update to WebSocket"""
        data = event['data']
        await self.send(text_data=json.dumps({
            'type': 'application_updated',
            'data': data
        }))

    @database_sync_to_async
    def get_application_data(self):
        """Get current application data"""
        from .models import SupplierApplication
        
        try:
            application = SupplierApplication.objects.get(id=self.application_id)
            return {
                'id': application.id,
                'business_name': application.business_name,
                'status': application.status,
                'status_display': application.get_status_display(),
                'created_at': application.created_at.isoformat(),
                'updated_at': application.updated_at.isoformat(),
                'tracking_code': application.tracking_code,
            }
        except SupplierApplication.DoesNotExist:
            return None
