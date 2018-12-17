import websockets
import asyncio

class WebsocketClient(object):

    async def websocket_client(self):
        # Trying to connect an user to a given room name
        ws_url = 'ws://{}:{}/chat/{}/{}/'.format('192.168.0.192', '8000', 'Room_1', '1')
        websocket = await websockets.connect(ws_url)
        while True:
            print(await websocket.recv())

    def startListening(self):
        coroutine = self.websocket_client()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coroutine)


if __name__ == "__main__":
    ws = WebsocketClient()
    ws.startListening()