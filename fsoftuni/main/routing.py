from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path, re_path
from django.core.asgi import get_asgi_application
from main.consumer import NotificationConsumer

from django.conf import settings

application = ProtocolTypeRouter({
			"http": get_asgi_application(),
			'websocket': AllowedHostsOriginValidator(
					AuthMiddlewareStack(
							URLRouter([
								path('', NotificationConsumer.as_asgi()),
							])
					)
			),
			'channel': ChannelNameRouter({
				'global': NotificationConsumer.as_asgi(),
			})
	})