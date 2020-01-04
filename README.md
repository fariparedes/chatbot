# Python Chatbot for F-Chat
This is the shell of a chatbot that you can use to create your own private room bots on F-Chat. It contains some nifty standard features to make your life easier, and it already has everything you need set up to the F-List servers. You just need to configure it to log into a bot profile on your account, and then write some commands for it to respond to.

The features the bot ships with include automatic logging sorted by year and month, JSON configuration of the bot so you can easily and extensibly configure it without digging around in the code, tracking of room users (though you'll need to add the hooks for adding and removing them from the list yourself), support for the F-List API, and methods to make the bot talk in a channel, send PMs, and kick or ban people.

To automatically install all the dependencies you need to run the script, run `pip install -r requirements.txt` or `python -m pip install -r requirements.txt` in the project directory. For long-term data storage, I recommend the `sqlite3` library. I also recommend that anything custom you add, you do so in a different Python file which creates a subclass of the Chatbot class and overrides its methods.

Python 3.4+ is recommended.

# Parsing data from the server
When the bot receives a message from the server, it checks whether the name of a handler function is defined in `dispatchers` in the config file. If so, it calls that function with three variables: `info` (the full dictionary of info sent by the server), `channel` (the channel code, if applicable), and `character` (the name of the relevant character, if applicable). If any variable is not specified in the message its value is `None`.

To make the bot recognize a message and respond to it, simply create a new `async def` function with the above variables and add its name to the `dispatchers` map in the config JSON. An example has been provided in the form of `handle_ping`, which simply responds to `PIN` messages from the server whenever sent so that the bot is not disconnected for inactivity. You can read all of the F-Chat Protocol codes [here](https://wiki.f-list.net/F-Chat_Server_Commands) as well as the dictionary keys they come with.

After the message is processed, `after_process_socket()` is called. Since messages from the server are so frequent (every status change is sent to every user on the server, for example), this method is called a lot, and you can use it to keep track of timers and whatnot.
