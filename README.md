# Python Chatbot for F-Chat
This is the shell of a chatbot that you can use to create your own private room bots on F-Chat. It contains some nifty standard features to make your life easier, and it already has everything you need set up to the F-List servers. You just need to configure it to log into a bot profile on your account, and then write some commands for it to respond to.

The features the bot ships with include automatic logging sorted by year and month, JSON configuration of the bot so you can easily and extensibly configure it without digging around in the code, tracking of room users, support for the F-List API, and methods to make the bot talk in a channel, send PMs, and kick or ban people.

To automatically install all the dependencies you need to run the script, run `pip install -r requirements.txt` or `python -m pip install -r requirements.txt` in the project directory. For long-term data storage, I recommend the `sqlite3` library. I also recommend that anything custom you add, you do so in a different Python file which creates a subclass of the Chatbot class and overrides its methods.

Python 3.4+ is recommended.
