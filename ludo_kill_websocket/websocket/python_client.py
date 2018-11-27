import asyncio
import websockets
import requests
import json


async def test_websocket(payload=None):
    #async with websockets.connect('ws://127.0.0.1:8000/chat/stream/') as websocket:
    async with websockets.connect('ws://127.0.0.1:8000/chat/1/') as websocket:
        greeting = await websocket.recv()
        print("response received < {}".format(greeting))
        await websocket.send(data=json.dumps(payload))
        print(">payload send :: {}".format(payload))
        # name = input("What's your name? ")
        #
        # await websocket.send(name)
        # print("> {}".format(name))
        #
        greeting = await websocket.recv()
        print("response received < {}".format(greeting))


if __name__ == '__main__':
    url = 'http://{}:{}/login_user/'.format('127.0.0.1', '8000')
    payload = "{\"username\": \"Abhisek\", \"password\": \"pass123\"}"
    headers = {
        'Content-Type': "application/json",
        'Cache-Control': "no-cache"
    }
    response = requests.request("POST", url=url, data=payload, headers=headers).json()
    print("response:: ", response)
    payload = {"command": "join", "room": 1}
    asyncio.get_event_loop().run_until_complete(test_websocket(payload=payload))
