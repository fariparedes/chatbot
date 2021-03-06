import json, re
import websockets, asyncio
import requests
import time, datetime
import math
import os
import traceback
from collections import defaultdict

class Chatbot:
	def __init__(self):
		self.bot_name = "Chatbot"
		self.service_name = "Python F-List Chatbot"
		self.service_version = 1
		self.__account_name = ""
		self.__password = ""
		raise NotImplementedError("You must fill in your account details so the bot can connect.")
		self.__websocket = None
		self.__ticket = None
		self.__constants = defaultdict(str)
		self.__messages = defaultdict(str)
		self.__current_room_users = set()
		self.__dispatch = {}
			
	def const(self):
		return self.__constants
	def msgs(self):
		return self.__messages
	def dispatch_map(self):
		return self.__dispatch
	def update_constants(self, bot_constants):
		for key in bot_constants:
			self.const()[key] = bot_constants[key]
	def update_messages(self, bot_msgs):
		for key in bot_msgs:
			self.msgs()[key] = bot_msgs[key]
	def add_dispatch(self, key, val):
		self.__dispatch[key] = val
	def remove_dispatch(self, key):
		self.__dispatch.pop(key, None)
		
	async def send_websocket(self, code, info_dict, delay = 0):
		message = "{} {}".format(code, json.dumps(info_dict))
		await self.timestamp_logs(message)
		await self.get_websocket().send(message)
		if delay > 0:
			await asyncio.sleep(delay)
	async def ban(self, character, time):
		await self.send_websocket("CTU", {"channel": self.const()["channel"], "character": character, "length" : time})
	async def kick(self, character):
		await self.send_websocket("CKU", {"channel": self.const()["channel"], "character": character})
	async def message(self, character, msg):
		await self.send_websocket("PRI", {"recipient": character, "message": msg}, 1)
	async def announce(self, channel, msg):
		await self.send_websocket("MSG", {"channel": channel, "message": msg}, 1)
		
	def print_error(self, text):
		print('\nError: ',text)
		try:
			if 'ticket' in text:
				self.clear_ticket()
		except TypeError:
			return
		
	def post_json(self, url, forms = {}):
		succeeded = False
		while not succeeded:
			try:
				resp = requests.post(url, data = forms, timeout=10)
				succeeded = True
			except Exception as e:
				self.print_error(e)
		return resp.json()
	def request_character(self, name, ticket):
		forms = {"account" : self.__account_name, "ticket" : ticket, "name" : name}
		character_json = self.post_json('https://www.f-list.net/json/api/character-data.php', forms)
		return character_json
	def request_ticket(self, bookmarks = None):
		forms = {"account" : self.__account_name, "password" : self.__password}
		ticket_json = self.post_json('https://www.f-list.net/json/getApiTicket.php', forms)
		if bookmarks != None:
			bookmarks |= set([x['name'] for x in ticket_json['bookmarks']] + [x['source_name'] for x in ticket_json['friends']] + ticket_json['characters'])
		if ticket_json['error'] == '':
			return ticket_json['ticket']
		else:
			self.print_error(ticket_json['error'])
			return 0
	def ticket(self, bookmarks = None):
		if self.__ticket == None:
			self.__ticket = self.request_ticket(bookmarks)
		return self.__ticket
	def clear_ticket(self):
		self.__ticket = None
		
	def user_entered(self, user):
		self.__current_room_users.add(user)
	def user_left(self, user):
		self.__current_room_users.remove(user)
	def current_users(self):
		return self.__current_room_users
	
	async def timestamp_logs(self, msg):
		if not os.path.isdir("logs"):
			try:
				os.makedirs("logs")
			except OSError:
				pass
		ts = time.time()
		month = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m')
		if not os.path.isdir(os.path.join("logs", month)):
			try:
				os.makedirs(os.path.join("logs", month))
			except OSError:
				pass
		stamp = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
		log_file = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
		logs = open(os.path.join("logs","{}","{}.txt").format(month,log_file), mode='a', encoding='utf-8')
		logs.write("{} {}\n".format(stamp, msg))
		logs.close()

	def get_websocket(self):
		return self.__websocket
	def set_websocket(self, socket):
		self.__websocket = socket
		
	async def handle_ping(self, receive, info, character):
		await self.get_websocket().send('PIN')
	async def after_process_socket(self):
		pass
	
	def initialize_bot(self):
		json_cfg = open("chatbot.json", encoding='utf-8')
		bot_cfg = json.loads(json_cfg.read())
		json_cfg.close()
		self.update_constants(bot_cfg["constants"])
		self.update_messages(bot_cfg["messages"])
		for key, dispatch_name in self.const()["dispatchers"].items():
			self.add_dispatch(key, getattr(self,dispatch_name))
		return bot_cfg
		
	async def __run_bot(self, ticket):
		async with websockets.connect('wss://{0}:{1}'.format(self.const()["host"], self.const()["port"])) as websocket:
			self.set_websocket(websocket)
			await self.send_websocket("IDN", {"method": "ticket", "account": self.__account_name, "ticket" : ticket, "character": self.bot_name, "cname": self.service_name, "cversion": str(self.service_version)})
			while True:
				receive = await websocket.recv()
				await self.timestamp_logs(receive)
				break
			await self.send_websocket("STA", {"status": "online", "statusmsg": self.__messages["status"].format(self.__constants["channel_name"],self.const()["channel"])})
			await self.send_websocket("JCH", {"channel" : self.const()["channel"]})
			while True:
				receive = await websocket.recv()
				code = receive[:3].strip()
				info = json.loads(receive[4:]) if len(receive) > 3 else {}
				channel = info["channel"].lower() if "channel" in info else None
				user = info["character"] if "character" in info else None
				if code in self.const()["valid_codes"]:
					if (not 'channel' in info) or (channel == self.const()["channel"]):
						if not receive.startswith("FLN") or info['character'] in self.current_users():
							await self.timestamp_logs(receive)
				try:
					if code in self.dispatch_map().keys():
						await self.dispatch_map()[code](info, channel, user)
				except Exception as e:
					self.print_error(traceback.format_exc())
				await self.after_process_socket()
				
	def run_bot(self):
		self.initialize_bot()
		asyncio.get_event_loop().run_until_complete(self.__run_bot(self.ticket()))
