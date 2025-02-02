from dataclasses import dataclass
import json

from dishka import Provider, Scope, provide, make_async_container, FromDishka
from quart import Quart, Websocket
from quart_dishka import QuartDishka, inject
from quart_dishka.provider import QuartProvider


@dataclass
class ChatSession:
    user_name: str
    message_count: int = 0

    def increment_messages(self) -> None:
        self.message_count += 1


class ChatProvider(Provider):
    @provide(scope=Scope.SESSION)
    def chat_session(self) -> ChatSession:
        return ChatSession(user_name="Anonymous")


app = Quart(__name__)
app.debug = True  # Enable debug mode
container = make_async_container(QuartProvider(), ChatProvider())
QuartDishka(app=app, container=container)


@app.websocket("/chat")
@inject
async def chat(ws: FromDishka[Websocket], session: FromDishka[ChatSession]) -> None:
    print("WebSocket connection attempt...")
    try:
        await ws.accept()
        print("WebSocket connection accepted")

        # Send welcome message
        await ws.send(f"Welcome, {session.user_name}!")
        print("Welcome message sent")

        while True:
            message = await ws.receive()
            print(f"Received message: {message}")
            session.increment_messages()

            # Echo message with stats
            response = {
                "message": message,
                "user": session.user_name,
                "message_count": session.message_count
            }
            await ws.send(json.dumps(response))
            print(f"Sent response: {response}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        try:
            await ws.close(0)
            print("WebSocket connection closed")
        except Exception as e:
            print("Closing websocket connection error", e)
            pass


if __name__ == "__main__":
    print("Starting WebSocket server on http://localhost:8765/chat")
    app.run(port=8765)
