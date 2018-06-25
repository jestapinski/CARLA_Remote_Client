#!/usr/bin/env python3

# Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Keyboard controlling for CARLA. Please refer to client_example.py for a simpler
# and more documented example.

from __future__ import print_function

import argparse
import logging
import random
import time
import _thread

from carla import image_converter
from carla import sensor
from carla.client import make_carla_client, VehicleControl
from carla.planner.map import CarlaMap
from carla.settings import CarlaSettings
from carla.tcp import TCPConnectionError
from carla.util import print_over_same_line

game = None
# Default '' refers to '0.0.0.0', or this machine's public IP
THIS_IP = ''
THIS_PORT = 8080
REMOTE_IP = '172.25.2.19'
REMOTE_PORT = 2000
LATENCY_MEASURE = 1000 # Number of pings to get the message across
QUALITY_LEVEL = 'Epic'
MAP_NAME = 'Town01'

def make_carla_settings(args):
    """Make a CarlaSettings object with the settings we need."""
    settings = CarlaSettings()
    settings.set(
        SynchronousMode=False,
        SendNonPlayerAgentsInfo=True,
        NumberOfVehicles=15,
        NumberOfPedestrians=30,
        WeatherId=random.choice([1, 3, 7, 8, 14]),
        QualityLevel=QUALITY_LEVEL)
    return settings


# class Timer(object):
#     def __init__(self):
#         self.step = 0
#         self._lap_step = 0
#         self._lap_time = time.time()

#     def tick(self):
#         self.step += 1

#     def lap(self):
#         self._lap_step = self.step
#         self._lap_time = time.time()

#     def ticks_per_second(self):
#         return float(self.step - self._lap_step) / self.elapsed_seconds_since_lap()

#     def elapsed_seconds_since_lap(self):
#         return time.time() - self._lap_time


class CarlaGame(object):
    def __init__(self, carla_client, args):
        self.client = carla_client
        self._carla_settings = make_carla_settings(args)
        # self._timer = Timer()
        self._enable_autopilot = True
        self._is_on_reverse = False
        self._city_name = MAP_NAME
        self._position = None
        self._agent_positions = None
        self._map = CarlaMap(self._city_name, 0.1643, 50.0) if self._city_name is not None else None
        self.measurements = None
        self.enabled_commands = []

    def execute(self):
        """Launch the PyGame."""
        self._initialize_game()
        try:
            while True:
                self._on_loop()
        except Exception as e:
            print(e.message, e.args)

    def _initialize_game(self):
        self._on_new_episode()

# Callback function to be run whenever the game restarts

    def _on_new_episode(self):
        scene = self.client.load_settings(self._carla_settings)
        number_of_player_starts = len(scene.player_start_spots)
        # Same default start spot
        player_start = 1
        print('Starting new episode...')
        self.client.start_episode(player_start)
        # self._timer = Timer()
        self._is_on_reverse = False
        self.enabled_commands = []

# Callback function to be run continuously throughout the game

    def _on_loop(self):
        # self._timer.tick()

        self.measurements, sensor_data = self.client.read_data()

        # Set the player position
        if self._city_name is not None:
            measurements = self.measurements
            self._position = self._map.convert_to_pixel([
                measurements.player_measurements.transform.location.x,
                measurements.player_measurements.transform.location.y,
                measurements.player_measurements.transform.location.z])
            self._agent_positions = measurements.non_player_agents

        number_of_commands = len(self.enabled_commands)
        if self._enable_autopilot or number_of_commands == 0:
            self.client.send_control(self.measurements.player_measurements.autopilot_control)
        # else:
        if (number_of_commands > 0):
            for command in self.enabled_commands:
                command()

# Interface Functions
# The following functions control the car based on the POST payload

# Autopilot
    def trigger_ap(self):
        self._enable_autopilot = not self._enable_autopilot
        self.clear()

# Reset
    def trigger_reset(self):
        self._on_new_episode()

# Left turning
    def steer_left(self):
        control = VehicleControl()
        control.steer = min(control.steer - 0.001, -1.0)
        control.reverse = self._is_on_reverse
        self.client.send_control(control)

    def add_left(self):
        self.enabled_commands.append(self.steer_left)

# Right Turning
    def steer_right(self):
        control = VehicleControl()
        control.steer = max(control.steer + 0.001, 1.0)
        control.reverse = self._is_on_reverse
        self.client.send_control(control)

    def add_right(self):
        self.enabled_commands.append(self.steer_right)

# Reverse
    def trigger_reverse(self):
        self._is_on_reverse = not self._is_on_reverse

# Acceleration
    def add_accel(self):
        self.enabled_commands.append(self.accelerate)

    def accelerate(self):
        control = VehicleControl()
        control.throttle = 1.0
        control.reverse = self._is_on_reverse
        self.client.send_control(control) 

# Deceleration
    def add_decel(self):
        self.enabled_commands.append(self.decelerate)

    def decelerate(self):
        control = VehicleControl()
        control.brake = 1.0
        control.reverse = self._is_on_reverse
        self.client.send_control(control)

# Braking
    def addBrake(self):
        self.enabled_commands = [self.throw_brake]

    def throw_brake(self):
        control = VehicleControl()
        control.hand_brake = True
        self.client.send_control(control) 

# Clearing all commands
    def clear(self):
        self.enabled_commands = []

def main(obj):
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default=REMOTE_IP,
        help='IP of the host server (default: localhost)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=REMOTE_PORT,
        type=int,
        help='TCP port to listen to (default: 2000)')
    args = argparser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    while True:
        try:
            # Construct server here
            # When response then start client
            print("trying server", args.host, args.port, make_carla_client(args.host, args.port))
            with make_carla_client(args.host, args.port) as client:
                global game
                game = CarlaGame(client, args)
                print("execute")
                game.execute()
                break

        except TCPConnectionError as error:
            print("error")
            logging.error(error)
            time.sleep(1)

#!/usr/bin/env python
 
from http.server import BaseHTTPRequestHandler, HTTPServer
 
# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

 
  # GET
    def do_GET(self):
        # Send response status code
        print("connection!")
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()

        # Send message back to client
        message = "Connection Successful!"
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        return

    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        content = post_data.decode("utf-8") 
        print(content)
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        # Send message back to client to help in completing transaction
        message = "POST!"
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        if content == 'testmsg':
            print("testing connection successful")
        if content == 'startserver':
            # Dispatch a thread to start a new game instance and save globally
            _thread.start_new_thread(main, (self,))
        if content == 'enable_ap': #DONE
            game.trigger_ap()
        if content == 'reset': #BROKEN
            game.trigger_reset()
        if content == 'left': #DONE
            game.add_left()
        if content == 'right': #DONE
            game.add_right()
        if content == 'reverse': #DONE
            game.trigger_reverse()
        if content == 'forward':
            game.add_accel()
        if content == 'backward':
            game.add_decel()
        if content == 'stop':
            game.add_brake()
        # ADD CLEAR
        if content == 'clear':
            game.clear()
        print("sending Response")

def run():
  print('starting server...')
 
  # Server settings
  server_address = (THIS_IP, THIS_PORT)
  # print(make_carcla_client(REMOTE_IP, REMOTE_PORT))
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running server...', httpd.socket.getsockname())
  print(httpd)
  httpd.serve_forever()


if __name__ == '__main__':

    try:
        run()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
