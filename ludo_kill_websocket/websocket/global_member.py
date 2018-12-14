import asyncio
from threading import Thread
import time
import json
from .models import UserRoom
from django.contrib.auth.models import User

class GlobalMember:
    uid_ws_dict = {}
    uid_loop_dict = {}
    TOKEN_DATA_PLAYER_DICT = {
        "0": {"0":[
            {"tokenId":0,"rowIndex":6,"columnIndex":1},
            {"tokenId":1,"rowIndex":6,"columnIndex":2},
            {"tokenId":2,"rowIndex":6,"columnIndex":3},
            {"tokenId":3,"rowIndex":6,"columnIndex":4},
            {"tokenId":4,"rowIndex":7,"columnIndex":1},
            {"tokenId":5,"rowIndex":7,"columnIndex":2},
            {"tokenId":6,"rowIndex":7,"columnIndex":3},
            {"tokenId":7,"rowIndex":7,"columnIndex":4},
            {"tokenId":8,"rowIndex":8,"columnIndex":1},
            {"tokenId":9,"rowIndex":8,"columnIndex":2},
            {"tokenId":10,"rowIndex":8,"columnIndex":3},
            {"tokenId":11,"rowIndex":8,"columnIndex":4},
            {"tokenId":12,"rowIndex":9,"columnIndex":1},
            {"tokenId":13,"rowIndex":9,"columnIndex":2},
            {"tokenId":14,"rowIndex":9,"columnIndex":3},
            {"tokenId":15,"rowIndex":9,"columnIndex":4}
            ]},
        "1": {"1":[
            {"tokenId":0,"rowIndex":1,"columnIndex":1},
            {"tokenId":1,"rowIndex":1,"columnIndex":2},
            {"tokenId":2,"rowIndex":1,"columnIndex":3},
            {"tokenId":3,"rowIndex":1,"columnIndex":4},
            {"tokenId":4,"rowIndex":2,"columnIndex":1},
            {"tokenId":5,"rowIndex":2,"columnIndex":2},
            {"tokenId":6,"rowIndex":2,"columnIndex":3},
            {"tokenId":7,"rowIndex":2,"columnIndex":4},
            {"tokenId":8,"rowIndex":3,"columnIndex":1},
            {"tokenId":9,"rowIndex":3,"columnIndex":2},
            {"tokenId":10,"rowIndex":3,"columnIndex":3},
            {"tokenId":11,"rowIndex":3,"columnIndex":4},
            {"tokenId":12,"rowIndex":4,"columnIndex":1},
            {"tokenId":13,"rowIndex":4,"columnIndex":2},
            {"tokenId":14,"rowIndex":4,"columnIndex":3},
            {"tokenId":15,"rowIndex":4,"columnIndex":4}
            ]},
        "2": {"2":[
            {"tokenId":0,"rowIndex":1,"columnIndex":6},
            {"tokenId":1,"rowIndex":1,"columnIndex":7},
            {"tokenId":2,"rowIndex":1,"columnIndex":8},
            {"tokenId":3,"rowIndex":1,"columnIndex":9},
            {"tokenId":4,"rowIndex":2,"columnIndex":6},
            {"tokenId":5,"rowIndex":2,"columnIndex":7},
            {"tokenId":6,"rowIndex":2,"columnIndex":8},
            {"tokenId":7,"rowIndex":2,"columnIndex":9},
            {"tokenId":8,"rowIndex":3,"columnIndex":6},
            {"tokenId":9,"rowIndex":3,"columnIndex":7},
            {"tokenId":10,"rowIndex":3,"columnIndex":8},
            {"tokenId":11,"rowIndex":3,"columnIndex":9},
            {"tokenId":12,"rowIndex":4,"columnIndex":6},
            {"tokenId":13,"rowIndex":4,"columnIndex":7},
            {"tokenId":14,"rowIndex":4,"columnIndex":8},
            {"tokenId":15,"rowIndex":4,"columnIndex":9}
            ]},
        "3": {"3":[
            {"tokenId":0,"rowIndex":6,"columnIndex":6},
            {"tokenId":1,"rowIndex":6,"columnIndex":7},
            {"tokenId":2,"rowIndex":6,"columnIndex":8},
            {"tokenId":3,"rowIndex":6,"columnIndex":9},
            {"tokenId":4,"rowIndex":7,"columnIndex":6},
            {"tokenId":5,"rowIndex":7,"columnIndex":7},
            {"tokenId":6,"rowIndex":7,"columnIndex":8},
            {"tokenId":7,"rowIndex":7,"columnIndex":9},
            {"tokenId":8,"rowIndex":8,"columnIndex":6},
            {"tokenId":9,"rowIndex":8,"columnIndex":7},
            {"tokenId":10,"rowIndex":8,"columnIndex":8},
            {"tokenId":11,"rowIndex":8,"columnIndex":9},
            {"tokenId":12,"rowIndex":9,"columnIndex":6},
            {"tokenId":13,"rowIndex":9,"columnIndex":7},
            {"tokenId":14,"rowIndex":9,"columnIndex":8},
            {"tokenId":15,"rowIndex":9,"columnIndex":9}
            ]}
    }


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
                    #print(await self.ws.recv())

                coroutine = ping_pong_cor()
                asyncio.set_event_loop(self.loop)
                self.loop.run_until_complete(coroutine)
            except Exception as e:
                print(e)
                #self.ws = self.ws.connect()
                self.loop.close()
                break