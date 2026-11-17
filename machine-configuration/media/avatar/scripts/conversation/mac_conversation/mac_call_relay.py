import websockets

PAGE_TAKEN_CODE = 1013


class CallRelay:
    def __init__(self):
        self.capturers = set()
        self.carrying = False

    async def carry_page(self, websocket):
        if self.carrying:
            await websocket.close(PAGE_TAKEN_CODE, "Another page carries the call")
            return
        self.carrying = True
        try:
            async for frame in websocket:
                if isinstance(frame, bytes):
                    websockets.broadcast(self.capturers, frame)
        finally:
            self.carrying = False

    async def carry_capturer(self, websocket):
        self.capturers.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.capturers.discard(websocket)
