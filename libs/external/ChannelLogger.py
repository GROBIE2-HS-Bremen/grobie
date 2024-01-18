""" 
    A extremely simple channel basaed logger.
    this logger will print messages to the console based on if the channel is defined and enabled. 

    this solution is small in size and easy to use, but not very flexible. 

    it does not support multiple loggers, colouring, timestamps or any other fancy features. 
    it just logs the message and the channel. all default channels are enabled by default.

    the logger has the following channels by default:
        - debug
        - info
        - warning
        - error
        - critical

    usage:
        ```python
        from ChannelLogger import logger

        logger("message", channel="channel_name")
        logger("message") # defaults to channel "debug" 
        
        logger.set_channel("channel_name", True) # enable channel
        logger.set_channel("channel_name", False) # disable channel

        logger.toggle_channel("channel_name") # toggle channel
        logger.toggle_channel("channel_name", True) # enable channel
        logger.toggle_channel("channel_name", False, True) # create channel if not exists and disable it

        
        logger.register_channel("channel_name") # register a new channel
        ```

        the logger will print the following:
        ```
        [channel_name]: message
        ```


"""

class _Logger: 

    channels = {
        "debug": True,
        "info": True,
        "warning": True,
        "error": True,
        "critical": True,
    }

    default_channel = "debug"

    def register_channel(self, name: str):
        """ register a new loggin channel """
        self.channels[name] = True

    def toggle_channel(self, name: str, state = None, register = False):
        """ toggle the state of the channel """
        if name not in self.channels.keys() and not register:
            raise Exception("Channel not registered")
        elif name not in self.channels.keys():
            self.register_channel(name)
            return
    
        if state is not None:
            self.channels[name] = state
            return 

        self.channels[name] = not self.channels[name]

    def set_channel(self, name: str, state: bool):
        """ Set the state of the channel """
        self.channels[name] = state

    def __call__(self, *args, **kwargs):
        """ 
            Log a message to the console based on the channel. this will print the 
            message to the console if the channel is enabled.

            By defualt the channel is debug. this can be set by passing the channel 
            argument to the logger.

            All the arguments except channel will be passed to the print function.

            Args:
                *args: arguments passed to the print function
                **kwargs: keyword arguments passed to the print function
                    channel: the channel to log to. if not provided the default channel will be used

            Example:
                ```python
                logger("message", channel="channel_name")   # log to channel channel_name
                logger("message")                           # log to default channel)
                ```

                the logger will print the following as long as the channel is enabled:
                ```
                [channel_name]: message
                ```

        """

        channel = kwargs.get('channel', self.default_channel)
        if 'channel' in kwargs:
            del kwargs['channel'] 

        if not self.channels[channel]:
            return
        

        print("[{}]:".format(channel), *args, **kwargs)



logger = _Logger()

        
