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

from carla import image_converter
from carla import sensor
from carla.client import make_carla_client, VehicleControl
from carla.planner.map import CarlaMap
from carla.settings import CarlaSettings
from carla.tcp import TCPConnectionError
from carla.util import print_over_same_line

game = None

def make_carla_settings(args):
    """Make a CarlaSettings object with the settings we need."""
    settings = CarlaSettings()
    settings.set(
        SynchronousMode=False,
        SendNonPlayerAgentsInfo=True,
        NumberOfVehicles=15,
        NumberOfPedestrians=30,
        WeatherId=random.choice([1, 3, 7, 8, 14]),
        QualityLevel=args.quality_level)
    return settings


class Timer(object):
    def __init__(self):
        self.step = 0
        self._lap_step = 0
        self._lap_time = time.time()

    def tick(self):
        self.step += 1

    def lap(self):
        self._lap_step = self.step
        self._lap_time = time.time()

    def ticks_per_second(self):
        return float(self.step - self._lap_step) / self.elapsed_seconds_since_lap()

    def elapsed_seconds_since_lap(self):
        return time.time() - self._lap_time


class CarlaGame(object):
    def __init__(self, carla_client, args):
        self.client = carla_client
        self._carla_settings = make_carla_settings(args)
        # self._timer = None
        self._enable_autopilot = args.autopilot
        self._is_on_reverse = False
        self._city_name = args.map_name
        self._position = None
        self._agent_positions = None
        self.measurements = None

    def execute(self):
        """Launch the PyGame."""
        self._initialize_game()
        try:
            while True:
                self._on_loop()
        except BaseException as e:
            print(e.message, e.args)

    def _initialize_game(self):
        self._on_new_episode()

    def _on_new_episode(self):
        scene = self.client.load_settings(self._carla_settings)
        number_of_player_starts = len(scene.player_start_spots)
        player_start = np.random.randint(number_of_player_starts)
        print('Starting new episode...')
        self.client.start_episode(player_start)
        # self._timer = Timer()
        self._is_on_reverse = False

    def _on_loop(self):
        self._timer.tick()

        self.measurements, sensor_data = self.client.read_data()

        # Print measurements every second.
        # if self._timer.elapsed_seconds_since_lap() > 1.0:
            # Plot position on the map as well.

            # self._timer.lap()

        # Set the player position
        if self._city_name is not None:
            self._position = self._map.convert_to_pixel([
                measurements.player_measurements.transform.location.x,
                measurements.player_measurements.transform.location.y,
                measurements.player_measurements.transform.location.z])
            self._agent_positions = measurements.non_player_agents


    def trigger_ap(self):
        self._enable_autopilot = not self._enable_autopilot
        self.client.send_control(self.measurements.player_measurements.autopilot_control)

    def trigger_reset(self):
        self._on_new_episode()

    def steer_left(self):
        control = VehicleControl()
        control.steer = -1.0
        control.reverse = self._is_on_reverse
        self.client.send_control(control)

    def steer_right(self):
        control = VehicleControl()
        control.steer = 1.0
        control.reverse = self._is_on_reverse
        self.client.send_control(control)

    def trigger_reverse(self):
        self._is_on_reverse = not self._is_on_reverse

    def accelerate(self):
        control = VehicleControl()
        control.throttle = 1.0
        control.reverse = self._is_on_reverse
        self.client.send_control(control) 

    def decelerate(self):
        control = VehicleControl()
        control.brake = 1.0
        control.reverse = self._is_on_reverse
        self.client.send_control(control)

    def throw_brake(self):
        control = VehicleControl()
        control.hand_brake = True
        self.client.send_control(control)            

 

def main():
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
        default='128.2.100.39',
        help='IP of the host server (default: localhost)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-q', '--quality-level',
        choices=['Low', 'Epic'],
        type=lambda s: s.title(),
        default='Epic',
        help='graphics quality level, a lower level makes the simulation run considerably faster.')
    argparser.add_argument(
        '-m', '--map-name',
        metavar='M',
        default='Town01',
        help='plot the map of the current city (needs to match active map in '
             'server, options: Town01 or Town02)')
    args = argparser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    while True:
        try:
            # Construct server here
            # When response then start client
            with make_carla_client(args.host, args.port) as client:
                global game
                game = CarlaGame(client, args)
                game.execute()
                break

        except TCPConnectionError as error:
            logging.error(error)
            time.sleep(1)

#!/usr/bin/env python
 
from http.server import BaseHTTPRequestHandler, HTTPServer
 
# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
 
  # GET
    def do_GET(self):
        # Send response status code
        print("connection!")
        self.send_response(200)

        # Send headers
        self.send_header('Content-type','text/html')
        self.end_headers()

        # Send message back to client
        message = "Hello world!"
        # Write content as utf-8 data
        self.wfile.write(bytes(message, "utf8"))
        return

    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        content = post_data.decode("utf-8") 
        print(content)
        if content == 'testmsg':
            print("testing connection successful")
        if content == 'startserver':
            main()
        if content == 'enable_ap':
            game.trigger_ap()
        if content == 'reset':
            game.trigger_reset()
        if content == 'left':
            game.steer_left()
        if content == 'right':
            game.steer_right()
        if content == 'reverse':
            game.trigger_reverse()
        if content == 'forward':
            game.accelerate()
        if content == 'backward':
            game.decelerate()
        if content == 'stop':
            game.throw_brake()


def run():
  print('starting server...')
 
  # Server settings
  # Choose port 8080, for port 80, which is normally used for a http server, you need root access
  server_address = ('', 8080)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running server...', httpd.socket.getsockname())
  print(httpd)
  httpd.serve_forever()


if __name__ == '__main__':

    try:
        run()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
