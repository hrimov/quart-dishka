import asyncio

from wsproto import WSConnection, ConnectionType
from wsproto.events import (
    Request, AcceptConnection, TextMessage, CloseConnection,
    RejectConnection, RejectData
)


async def test_websocket():
    uri = "ws://localhost:8765/chat"
    print(f"Connecting to {uri}...")

    try:
        # Create a TCP connection
        reader, writer = await asyncio.open_connection('localhost', 8765)

        # Create WebSocket connection
        ws = WSConnection(ConnectionType.CLIENT)

        # Send handshake request
        request = Request(
            host='localhost:8765',
            target='/chat',
            extra_headers=[
                (b'Origin', b'http://localhost:8765'),
                (b'Sec-WebSocket-Protocol', b'chat')
            ]
        )
        data = ws.send(request)
        writer.write(data)
        await writer.drain()

        # Read response
        data = await reader.read(1024)
        ws.receive_data(data)

        for event in ws.events():
            if isinstance(event, AcceptConnection):
                print("Connection established")

                # Send test messages
                for i in range(3):
                    message = f"Hello {i}!"
                    print(f"Sending: {message}")
                    writer.write(ws.send(TextMessage(message)))
                    await writer.drain()

                    # Read response
                    data = await reader.read(1024)
                    ws.receive_data(data)

                    for e in ws.events():
                        if isinstance(e, TextMessage):
                            print(f"Server: {e.data}")

                    await asyncio.sleep(1)

                # Close connection
                writer.write(ws.send(CloseConnection(code=1000)))
                await writer.drain()
                break
            elif isinstance(event, RejectConnection):
                print(f"Connection rejected: {event.status_code}")
                break
            elif isinstance(event, RejectData):
                print(f"Connection rejected with data: {event.data}")
                break

        writer.close()
        await writer.wait_closed()

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(test_websocket())
