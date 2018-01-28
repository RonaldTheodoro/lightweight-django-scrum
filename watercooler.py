#!/usr/bin/env python

import hashlib
import json
import logging
import signal
import time
import uuid

from urllib.parse import urlparse

from decouple import config

from django.core import signing
from django.utils.crypto import constant_time_compare

from redis import Redis

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options, parse_command_line
from tornado.web import Application, HTTPError, RequestHandler
from tornado.websocket import WebSocketClosedError, WebSocketHandler
from tornadoredis import Client
from tornadoredis.pubsub import BaseSubscriber


define('debug', default=False, type=bool, help='Run in debug mode')
define('port', default=8080, type=int, help='Server port')
define(
    'allowed_hosts',
    default='localhost:8080',
    multiple=True,
    help='Allowed hosts for cross domain connections'
)


class RedisSubscriber(BaseSubscriber):

    def on_message(self, msg):
        if msg and msg.kind == 'message':
            try:
                message = json.loads(msg.body)
                sender = message['sender']
                message = message['message']
            except (ValueError, KeyError):
                message = msg.body
                sender = None

            subscribers = list(self.subscribe[msg.channel].keys())
            for subscriber in subscribers:
                if sender is None or sender != subscriber.uid:
                    try:
                        subscriber.write_message(msg.body)
                    except WebSocketClosedError:
                        self.unsubscribe(msg.channel, subscriber)
            super().on_message(msg)

class SprintHandler(WebSocketHandler):
   
    def check_origin(self, origin):
        allowed = super().check_origin(origin)
        parsed = urlparse(origin.lower())
        matched = any(parsed.netloc == host for host in options.allowed_hosts)
        return options.debug or allowed or matched

    def open(self, sprint):
        self.sprint = None
        channel = self.get_argument('channel', None)
        if not channel:
            self.close()
        else:
            try:
                self.sprint = self.application.signer.unsign(
                    channel,
                    max_age=60 * 30
                )
            except (signing.BadSignature, signing.SignatureExpired):
                self.close()
            else:
                self.uid = uuid.uuid4().hex
                self.application.add_subscriber(self.sprint, self)

        self.uuid = uuid.uuid4().hex
        self.application.add_subscriber(self.sprint, self)

    def on_message(self, message):
        if self.sprint is not None:
            self.application.broadcast(
                message,
                channel=self.sprint,
                sender=self
            )

    def on_close(self):
        if self.sprint is not None:
            self.application.remove_subscriber(self.sprint, self)


class UpdateHandler(RequestHandler):

    def post(self, model, pk):
        self._broadcast(model, pk, 'add')

    def put(self, model, pk):
        self._broadcast(model, pk, 'update')

    def delete(self, model, pk):
        self._broadcast(model, pk, 'remove')

    def _broadcast(self, model, pk, action):
        signature = self.request.headers.get('X-Signature', None)

        if not signature:
            raise HTTPError(400)

        try:
            result = self.application.signer.unsign(signature, max_age=60 * 1)
        except (signing.BadSignature, signing.SignatureExpired):
            raise HTTPError(400)
        else:
            method = self.request.method.lower()
            url = self.request.full_url()
            body = hashlib.sha256(self.request.body).hexdigest()

            expected = f'{method}:{url}:{body}'

            if not constant_time_compare(result, expected):
                raise HTTPError(400)

        try:
            body = json.loads(self.request.body.decode('utf-8'))
        except ValueError:
            body = None

        message = json.dumps({
            'model': model,
            'id': pk,
            'action': action,
            'body': body,
        })
        self.application.broadcast(message)
        self.write('Ok')


class ScrumApplication(Application):

    def __init__(self, **kwargs):
        routes = [
            (r'/socket', SprintHandler),
            (r'/(?P<model>task|sprint|user)/(?P<pk>[0-9]+)', UpdateHandler),
        ]
        super().__init__(routes, **kwargs)
        self.subscriber = RedisSubscriber(Client())
        self.publisher = Redis()
        self._key = config('WATERCOOLER_SECRET_KEY')
        self.signer = signing.TimestampSigner(self._key)

    def add_subscriber(self, channel, subscriber):
        self.subscriber.subscribe(['all', channel], subscriber)

    def remove_subscriber(self, channel, subscriber):
        self.subscriber.unsubscribe(channel, subscriber)
        self.subscriber.unsubscribe('all', subscriber)

    def broadcast(self, message, channel=None, sender=None):
        channel = 'all' if channel is None else channel
        message = json.dumps({
            'sender': sender and sender.uid,
            'message': message
        })
        self.publisher.publish(channel, message)


def shutdown(server):
    ioloop = IOLoop.instance()
    logging.info('Stopping server')
    server.stop()

    def finalize():
        ioloop.stop()
        logging.info('Stopped')

    ioloop.add_timeout(time.time() + 1.5, finalize)


if __name__ == '__main__':
    parse_command_line()
    application = ScrumApplication(debug=options.debug)
    server = HTTPServer(application)
    server.listen(options.port)
    signal.signal(signal.SIGINT, lambda sig, frame: shutdown(server))
    logging.info(f'Starting server on localhost:{options.port}')
    IOLoop.instance().start()
