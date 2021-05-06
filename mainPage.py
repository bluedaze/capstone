import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape
import json
import pyastthing
from tornado.options import define, options
import logging
import os

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html", messages=ChatSocketHandler.cache)

class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    connections = set()
    cache = []
    cache_size = 200


    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}


    def open(self):
        self.connections.add(self)


    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size :]


    @classmethod
    def send_updates(cls, chat):
        logging.info("sending message to %d waiters", len(cls.connections))
        for waiter in cls.connections:
            try:
                waiter.write_message(chat)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        logging.info("got message %r", message)
        userCode = json.loads(message)
        graph = pyastthing.astParser(userCode)
        graphimage = graph.vizdot()
        [connection.write_message(graphimage) for connection in self.connections]

    def on_close(self):
        self.connections.remove(self)


define("port", default=8888, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [(r"/", MainHandler), (r"/websocket", ChatSocketHandler)]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        super().__init__(handlers, **settings)


if __name__ == "__main__":
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()