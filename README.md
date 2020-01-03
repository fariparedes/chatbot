# Python Chatbot for F-Chat
This is the shell of a chatbot that you can use to create your own private room bots on F-Chat. It contains some nifty standard features to make your life easier, and it already has everything you need set up to the F-List servers. You just need to configure it to log into a bot profile on your account, and then write some commands for it to respond to.

The features the bot ships with include automatic logging sorted by year and month, JSON configuration of the bot so you can easily and extensibly configure it without digging around in the code, tracking of room users (though you'll need to add the hooks for adding and removing them from the list yourself), support for the F-List API, and methods to make the bot talk in a channel, send PMs, and kick or ban people.

To automatically install all the dependencies you need to run the script, run `pip install -r requirements.txt` or `python -m pip install -r requirements.txt` in the project directory. For long-term data storage, I recommend the `sqlite3` library. I also recommend that anything custom you add, you do so in a different Python file which creates a subclass of the Chatbot class and overrides its methods.

Python 3.4+ is recommended.

# Parsing data from the server
All messages received from the server by the bot are sent to `process_socket()`. You can use `receive.startswith("XXX")` to identify a particular three-letter code you wish to respond to (like 'MSG' when a message is sent to a channel the bot is in). The `info` dict includes keys for `"channel"` which gives the code (for private rooms) or name (for public rooms) of the relevant channel, which you can compare against `self.const()["channel"]` to ensure you only reply to commands in the correct room, and `"character"` to get the name of the person who triggered the message.

You can read all of the F-Chat Protocol codes [here](https://wiki.f-list.net/F-Chat_Server_Commands) as well as the dictionary keys they come with. One of the first things you'll want to do is make your bot respond to the `PIN` message with a `PIN` message of its own back to the server, or the server will disconnect it after approximately ten seconds.

After the message is processed, `after_process_socket()` is called. Since messages from the server are so frequent, this method is called a lot, and you can use it to keep track of timers and whatnot.
