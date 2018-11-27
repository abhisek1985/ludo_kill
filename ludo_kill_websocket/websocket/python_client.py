import asyncio
import websockets
import requests
import json

async def test_websocket(payload=None):
    # Trying to connect an user to a given room name
    async with websockets.connect('ws://127.0.0.1:8000/chat/' + payload["room"] +'/') as websocket:
        greeting = json.loads(await websocket.recv())["message"]
        print("response received < {}".format(greeting))
        await websocket.send(data=json.dumps(payload))
        print(">payload send :: {}".format(payload))
        greeting = json.loads(await websocket.recv())["message"]
        print("response received < {}".format(greeting))



if __name__ == '__main__':
    print("# ************************************** Test Login API *******************************************")
    url = 'http://{}:{}/login_user/'.format('127.0.0.1', '8000')
    payload = "{\"username\": \"Abhisek\", \"password\": \"pass123\"}"
    headers = {
        'Content-Type': "application/json",
        'Cache-Control': "no-cache"
    }
    user_response = requests.request("POST", url=url, data=payload, headers=headers).json()
    print("response:: ", user_response)

    print("# ************************************** Test Create Room API *************************************")
    url = "http://127.0.0.1:8000/create_room/"
    payload = "{\"title\": \"Room_1\"}"
    headers = {
        'Content-Type': "application/json",
        'Cache-Control': "no-cache"
    }
    room_response = requests.request("POST", url, data=payload, headers=headers).json()
    print(room_response)

    print("# ************************************* Test Websocket Room Join **********************************")
    socket_payload = {"command": "join", "room": room_response.get("room_name"),
                      "username": user_response.get("username")}
    asyncio.get_event_loop().run_until_complete(test_websocket(payload=socket_payload))
