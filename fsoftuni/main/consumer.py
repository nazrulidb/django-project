from django.conf import settings
from django.db import transaction
from channels.generic.websocket import JsonWebsocketConsumer, SyncConsumer
from channels.exceptions import StopConsumer

from django.core.paginator import Paginator
from django.core.serializers import serialize
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType

import json, asyncio, time, threading
from django_thread import Thread

from threading import current_thread
from datetime import datetime
from asgiref.sync import async_to_sync

# from chat.models import 
from users.models import OnlineUsers

from custom_dashboard.models import StudentRecords
from django.contrib.auth import get_user_model
from wagtail.documents import get_document_model
from channels.layers import get_channel_layer

User = get_user_model()
Document = get_document_model()


class ThreadSafe(Thread):

	def __init__(self, document_id, record_id, channel):
		super(ThreadSafe, self).__init__(name=document_id, daemon=True)
		self.document_id = document_id
		self.record_id = record_id
		self.channel = channel

	@transaction.atomic
	def run(self):
		doc = Document.objects.filter(id=self.document_id).first()
		record = StudentRecords.objects.filter(id=self.record_id).first()
		doc.extract_data(record)
		print("THREAD EXTRACT DONE")

		self.channel.processing_docs.remove(self.document_id)
		print("RETURN THREAD")
		return 1

class NotificationConsumer(JsonWebsocketConsumer):
	user_object = None
	notif_code = 0
	user_ids = []
	admin_ids = []
	processing_docs = []
	group_name = None
 
	def connect(self):
		"""
		Called when the websocket is handshaking as part of initial connection.
		"""
		self.accept()
		print("NotificationConsumer: connect: " + str(self.scope["user"]) )
		

		group_name = "%s-%s" % ("notify", self.scope["user"].id)
		print(self.scope["user"].is_authenticated)
		print("____XXXXXXX")
		is_auth = self.scope["user"].is_authenticated

		if is_auth:
			
			if str(self.scope["user"].role) != "Student":
				if not self.scope["user"].id in self.admin_ids:
					self.admin_ids.append(self.scope["user"].id)
     
				async_to_sync(self.channel_layer.group_add)(
					'background_proc',
					self.channel_name)
    
				async_to_sync(self.channel_layer.group_add)(
					group_name,
					self.channel_name)
                
			async_to_sync(self.channel_layer.group_add)(
				'global',
				self.channel_name
			)
		
			if not self.scope["user"].id in self.user_ids:
				self.user_ids.append(self.scope["user"].id)
				print(self.user_ids)

			connected = connect_user(self.scope["user"])
			print(f"is connected {connected}")

			if connected:
				self.user_connected(self.scope["user"])

			

			
	def user_connected(self, user):
		group_name = "%s-%s" % ("notify", self.scope["user"].id)
		
		async_to_sync(self.channel_layer.group_send)(
			'global',
			{
				"type": "user.connect",
				"notif_type": 99,
				"user_id": user.id,
				"username": user.username,
		
			}
		)

	def user_connect(self, event):
		self.send_json(
			{
				"notif_type": event["notif_type"],
				"user_id": event["user_id"],
				"username": event["username"],
			
			},
		)

	def get_online_users(self):
		connected_users = get_db_online_users(self.scope["user"])
		print("get_db_online_users")
		print(connected_users)
		async_to_sync(self.channel_layer.group_send)(
			'global',
			{
				"type": "online.users",
				"notif_type": 98,
				"online_users": connected_users,
			}
		)

	def online_users(self, event):
		self.send_json(
			{
				"notif_type": event["notif_type"],
				"online_users": event["online_users"],
			},
		)

	def disconnect(self, code):
		"""
		Called when the WebSocket closes for any reason.
		"""
		# Leave the room
		print("NotificationConsumer: disconnect")
		try:
			group_name = "%s-%s" % ("notify", self.scope["user"].id)

			async_to_sync(self.channel_layer.group_discard)(
					group_name,
					self.channel_name
				)

			# async_to_sync(self.channel_layer.group_discard)(
			# 		'global',
			# 		self.channel_name
			# 	)
			
			disconnect_user(self.scope["user"].id)

			if self.scope["user"].id in self.user_ids:
				self.user_ids.remove(self.scope["user"].id)
	
			if self.scope["user"].id in self.admin_ids:
				self.admin_ids.remove(self.scope["user"].id)

			self.get_if_user_connected(self.scope["user"])
		except:
			raise StopConsumer()
			

	def user_disconnected(self, user_id, connected_users):
		async_to_sync(self.channel_layer.group_send)(
			'global',
			{
				"type": "user.disconnect",
				"notif_type": 100,
				"user_id": user_id,
				"connected_users":connected_users,
			}
		)
	
	def get_if_user_connected(self, user):
		
		w = True
		c = 1
		while w:
			if user.id in self.user_ids:
				break
			elif c == 3:
				w = False
			else:
				c += 1
				asyncio.sleep(1)
		else:
			connected, connected_users = is_user_connected(user)
			
			if not connected:
				self.user_disconnected(user.id, connected_users)
				

	def user_disconnect(self, event):
		self.send_json(
			{
				"notif_type": event["notif_type"],
				"user_id": event["user_id"],
				"connected_users": event['connected_users'],
			},
		)

	def receive_json(self, content):
		"""
		Called when we get a text frame. Channels will JSON-decode the payload
		for us and pass it as the first argument.
		"""
		command = content.get("command", None)
		print(content)
		print("NotificationConsumer: receive_json. Command: " + command)

		try:
			if command == "get_online_users":
				print("CALLING GET ONLINE USERS")
				self.get_online_users()

			elif command == "notified_chat":
				payload = notified_chat(self.scope["user"])					
			
		except Exception as e:
			print("EXCEPTION: receive_json: " + str(e))
			pass
    
	def notify_admins(self, event):
		print('notify_admins')
		print(self.admin_ids)
		if event["notif_type"] == 22:
			print("HEEEEEEE")

		else:
			self.send_json(
					{
						"data": event,
						"notif_type": event["notif_type"],
					},
				)

	def extract_data(self, event):
		print("extract_data on consumer")
		if not event["document_id"] in self.processing_docs:
			self.processing_docs.append(event["document_id"])
			print("EXTRACTING")
			
			thread = ThreadSafe(document_id=event["document_id"], record_id=event["record_id"], channel=self)
			thread.start()

			# task = asyncio.create_task(
			# 	extract_data(event["document_id"], event["record_id"]))

			# try:
			# 	asyncio.wait_for(asyncio.shield(task), timeout=1000)
			# except TimeoutError:
			# 	print('The task took more than expected and will complete soon.')
			# 	result = task
			# 	print(result)
			return 1
	
	def extract_done(self, event):
		print("EXTRACT DONE")
		self.processing_docs.remove(event["document_id"])
		return 1

def save_firebase_token(user, installation, messaging):
	if user.is_authenticated:
		return user.save_user_firebase_token(installation, messaging)

def get_db_online_users(user):
	if user.is_authenticated:
		return OnlineUsers.get()

def connect_user(user):
	return OnlineUsers.connect_user(user)

def disconnect_user(user_id):
	print("database disconnect user")
	return OnlineUsers.disconnect_user(user_id)

def is_user_connected(user):
	# time.sleep(5)
	return OnlineUsers.is_user_connected(user)

def notified_chat(user):
	if user.is_authenticated:
		AdminRecentChatMessages.target_notified(user)

