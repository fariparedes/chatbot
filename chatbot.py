import json, re
import websockets, asyncio
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
			
	def const(self):
		return self.__constants
	def msgs(self):
		return self.__messages
	def update_constants(self, bot_constants):
		for key in bot_constants:
			self.const()[key] = bot_constants[key]
	def update_messages(self, bot_msgs):
		for key in bot_msgs:
			self.msgs()[key] = bot_msgs[key]
		
	async def ban(self, character, time):
		ban = "CTU {{\"channel\":\"{0}\",\"character\":\"{1}\",\"length\":\"{2}\"}}".format(self.const()["channel"], character, time)
		await self.get_websocket().send(ban)
		
	async def kick(self, character, time):
		ban = "CKU {{\"channel\":\"{0}\",\"character\":\"{1}\"}}".format(self.const()["channel"], character)
		await self.get_websocket().send(ban)

	async def message(self, character, msg):
		message = "PRI {{\"recipient\":\"{0}\",\"message\":\"{1}\"}}".format(character, msg, self.bot_name)
		await self.timestamp_logs(message)
		await self.get_websocket().send(message)
		await asyncio.sleep(1)
		
	async def announce(self, channel, msg):
		message = "MSG {{\"channel\":\"{0}\",\"message\":\"{1}\"}}".format(channel, msg, self.bot_name)
		await self.timestamp_logs(message)
		await self.get_websocket().send(message)
		await asyncio.sleep(1)
		
	def print_error(self, text):
		print('\nError: ',text)
		try:
			if 'ticket' in text:
				global TICKET
				TICKET = None
		except TypeError:
			return
		
	def post_json(self, url, forms = {}):
		succeeded = False
		while not succeeded:
			try:
				resp = requests.post(url, data = forms, timeout=10)
				succeeded = True
			except Exception as e:
				print_error(e)
		return resp.json()
	def request_character(name, ticket):
		forms = {"account" : self.__account_name, "ticket" : ticket, "name" : name}
		character_json = post_json('https://www.f-list.net/json/api/character-data.php', forms)
		return character_json
	def request_ticket(self, bookmarks = None):
		forms = {"account" : self.__account_name, "password" : self.password}
		ticket_json = post_json('https://www.f-list.net/json/getApiTicket.php', forms)
		if bookmarks != None:
			bookmarks |= set([x['name'] for x in ticket_json['bookmarks']] + [x['source_name'] for x in ticket_json['friends']] + ticket_json['characters'])
		if ticket_json['error'] == '':
			return ticket_json['ticket']
		else:
			print_error(ticket_json['error'])
			return 0
	def ticket(self, bookmarks = None):
		if self.__ticket == None:
			self.__ticket = request_ticket(bookmarks)
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
		
	async def process_socket(self, receive, info, channel):
		raise NotImplementedError
	async def after_process_socket(self):
		raise NotImplementedError
	
	def initialize_bot(self):
		json_cfg = open("chatbot.json", encoding='utf-8')
		bot_cfg = json.loads(json_cfg.read())
		json_cfg.close()
		self.update_constants(bot_cfg["constants"])
		self.update_messages(bot_cfg["messages"])
		
	async def __run_bot(self, ticket):
		async with websockets.connect('wss://{0}:{1}'.format(self.const()["host"], self.const()["port"])) as websocket:
			self.set_websocket(websocket)
			identify = "IDN {{\"method\":\"ticket\",\"account\":\"{0}\",\"ticket\":\"{1}\",\"character\":\"{4}\",\"cname\":\"{2}\",\"cversion\":\"{3}\"}}".format(self.__account_name, ticket, self.service_name, self.service_version, self.bot_name)
			await websocket.send(identify)
			while True:
				receive = await websocket.recv()
				await self.timestamp_logs(receive)
				break
			status = "STA {{\"status\":\"online\", \"statusmsg\":\"{0}\"}}".format(self.__messages["status"].format(self.__constants["channel_name"],self.const()["channel"]))
			await websocket.send(status)
			join = "JCH {{\"channel\":\"{0}\"}}".format(self.const()["channel"])
			await websocket.send(join)
			for channel in self.const()["ad_channels"]:
				join = "JCH {{\"channel\":\"{0}\"}}".format(channel)
				await websocket.send(join)
			while True:
				receive = await websocket.recv()
				info = None
				channel = None
				if receive[:3] in self.const()["valid_codes"]:
					info = json.loads(receive[4:])
					channel = json.loads(receive[4:])
					if (not 'channel' in channel) or (channel['channel'] == self.const()["channel"]):
						if not receive.startswith("FLN") or info['character'] in self.current_users():
							await self.timestamp_logs(receive)
				try:
					await self.process_socket(receive, info, channel)
				except Exception as e:
					self.print_error(traceback.format_exc())
				await self.after_process_socket()
				
	def run_bot(self):
		self.initialize_bot()
		asyncio.get_event_loop().run_until_complete(self.__run_bot(self.ticket()))
