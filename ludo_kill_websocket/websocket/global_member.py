import asyncio
from threading import Thread
import time
import json
from .models import UserRoom
from django.contrib.auth.models import User

class GlobalMember:
    uid_ws_dict = {}
    uid_loop_dict = {} #asyncio.new_event_loop()

class KeepMeAlive(Thread):
    def __init__(self, ws, message, loop): 
        Thread.__init__(self) 
        self.ws = ws
        self.message = message
        self.loop = loop

    def run(self): 
        while True:
            time.sleep(15)
            try:
                async def ping_pong_cor():
                    self.message['message_type'] = 'PING'
                    await self.ws.send(json.dumps(self.message))
                    print(await self.ws.recv())

                coroutine = ping_pong_cor()
                asyncio.set_event_loop(self.loop)
                self.loop.run_until_complete(coroutine)
            except Exception as e:
                print(e)
                self.loop.close()
                break