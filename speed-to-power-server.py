import asyncio
from bleak import BleakClient, BleakScanner
from pycycling.cycling_speed_cadence_service import CyclingSpeedCadenceService, CSCMeasurement
import websockets
import nest_asyncio
nest_asyncio.apply()
import json
import threading
import time
import subprocess
import os
import curses

last_rev = 0
last_time = 0
should_run = True

WHEEL_CIRCUMFERENCE = 2110 # in mm
lever = 2

CONNECTIONS: set[websockets.ClientConnection] = set()

def update_gear(stdscr):
    global lever
    stdscr.clear()
    stdscr.addstr(0, 0, "Press 'q' to quit, '1' to '9' to change gear")
    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif ord('1') <= key <= ord('9'):
            lever = key - ord('0')
            stdscr.addstr(2, 0, f"Gear changed to: {lever}")
            stdscr.refresh()

async def handler(websocket):
    await register(websocket)
    try:
        async for _ in websocket:
            pass
    except websockets.ConnectionClosed:
        pass

async def register(websocket):
    CONNECTIONS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)

def notify_connections(power):
    for connection in CONNECTIONS:
        loop = asyncio.new_event_loop()
        async def send_power(connection: websockets.ClientConnection, power):
            await connection.send(json.dumps({"power": power}))
        loop.run_until_complete(send_power(connection, power))
        loop.close()

def s2p(speed): # speed in kmh
    global lever
    assert (lever > 0 and lever < 11)
    
    gradients = [12.85, 11.35, 10.95, 10, 8.5, 7.5, 6.4, 5.44, 4.3, 3.3]
    shifts = [-67, -50, -70, -70, -54, -50, -40, -30, -30, -20]
    gradients.reverse()
    shifts.reverse()

    w = speed * gradients[lever - 1] - shifts[lever - 1]

    return w if w > 0 else 0

async def find_device():
    devices = await BleakScanner.discover()
    for d in devices:
        if d.name and d.name.startswith("SPD"):
            return d.address
        
    return None

async def speed_sensor_server(address):
    global last_rev, last_time, should_run
    try:
        async with BleakClient(address, timeout=5) as client:
            # print(f"Connected to {address}")
            def handle_rev_data(data: CSCMeasurement):
                global last_time, last_rev
                if last_time == 0:
                    last_time = data.last_wheel_event_time

                if last_rev == 0:
                    last_rev = data.cumulative_wheel_revs
                else:
                    delta_revs = data.cumulative_wheel_revs - last_rev
                    last_rev = data.cumulative_wheel_revs
                    delta_time = data.last_wheel_event_time - last_time
                    last_time = data.last_wheel_event_time

                    if delta_time > 0 and delta_revs > 0:
                        distance = delta_revs * WHEEL_CIRCUMFERENCE / 1000.0 # in meters
                        speed = distance / (delta_time / 1000.0)
                        
                        # print(f"Speed: {speed * 3.6:.2f} km/h, Power: {s2p(speed * 3.6):.2f} W")
                        notify_connections(s2p(speed * 3.6))

            await client.is_connected()
            trainer = CyclingSpeedCadenceService(client)
            trainer.set_csc_measurement_handler(handle_rev_data)
            await trainer.enable_csc_measurement_notifications()
            try:
                while should_run:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("Disconnecting...")
                # await trainer.disable_csc_measurement_notifications()
                should_run = False
    except Exception as e:
        print(f"Error: {e}")
        await asyncio.sleep(1)


async def run():
    await websockets.serve(handler, "localhost", 54399)
    # print("WebSocket server started on ws://localhost:8765")

    global should_run
    while should_run:
        address = None
        while address is None:
            address = await find_device()
            if address is None:
                # print("No SPD device found, retrying...")
                await asyncio.sleep(0.5)
        print(f"Found SPD device: {address}")
        await speed_sensor_server(address)

def run_simulator():
    time.sleep(5)
    proc = subprocess.Popen(["npm", "run", "main"], cwd=os.path.dirname(os.path.abspath(__file__)), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    proc.wait()

if __name__ == "__main__":
    # Start the gear update thread
    stdscr = curses.initscr()
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(True)
    gear_thread = threading.Thread(target=update_gear, args=(stdscr,))
    gear_thread.start()
    
    simulator_thread = threading.Thread(target=run_simulator)
    simulator_thread.start()

    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())