import asyncio
import websockets
import time
from common import encode, decode

LATENCY = 0.2

async def delayed_send(ws, data):
    await asyncio.sleep(LATENCY)
    await ws.send(data)

async def delayed_recv(ws):
    await asyncio.sleep(LATENCY)
    return await ws.recv()

async def game_client():
    ws = await websockets.connect("ws://localhost:8000")
    print("Connected to server.")

    # Movement keys
    print("Use keys: w/a/s/d + ENTER")

    async def sender():
        while True:
            key = input().strip().lower()
            vx = vy = 0
            if key == "w": vy = -1
            elif key == "s": vy = 1
            elif key == "a": vx = -1
            elif key == "d": vx = 1

            await delayed_send(ws, encode({
                "type": "input",
                "vx": vx,
                "vy": vy
            }))

    async def receiver():
        while True:
            msg = await delayed_recv(ws)
            data = decode(msg)

            print("\n=== GAME STATE ===")
            for pid, p in data["players"].items():
                print(f"Player {pid}: x={p['x']:.1f}, y={p['y']:.1f}, score={p['score']}")
            print("Coins:", [(c["x"], c["y"]) for c in data["coins"]])

    asyncio.create_task(sender())
    await receiver()

asyncio.run(game_client())
