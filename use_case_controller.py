#!/usr/bin/env python3

# Based off of Keyboard Input Framework from UAB
# Copyright (c) 2017 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).

# Extension by Jordan Stapinski, to allow incoming HTTP connections to provide
# remote control to the vehicle, allowing for cross-language control from
# remote devices, implementing a customized protocol

from __future__ import print_function

import argparse
import logging
import random
import time
import _thread
import requests

from carla import image_converter
from carla import sensor
from carla.client import make_carla_client, VehicleControl
from carla.planner.map import CarlaMap
from carla.settings import CarlaSettings
from carla.tcp import TCPConnectionError
from carla.util import print_over_same_line

# global game instance to be used
game = None

# Default '' refers to '0.0.0.0', or this machine's public IP
THIS_IP = ''
THIS_PORT = 8080

# Target CARLA Machine IP
REMOTE_IP = '172.25.2.19'
REMOTE_PORT = 2000
LATENCY_MEASURE = 1000 # Number of pings to get the message across
QUALITY_LEVEL = 'Epic'
MAP_NAME = 'Town01'

# Target Framer Secondary Screen IP
SECONDARY_IP = ''
SECONDARY_PORT = 3000
SECONDARY_SCREEN_COMMANDS = {
  'reset': 'reset',
  'left': 'left',
  'left_stop': 'left_stop',
  'right': 'right',
  'right_stop': 'right_stop',
  'speed_up': 'speed_up',
  'speed_up_stop': 'speed_up_stop',
  'slow_down': 'slow_down',
  'slow_down_stop': 'slow_down_stop',
  'stop': 'stop'
}

def make_carla_settings(args):
  """Make a CarlaSettings object with the settings we need."""
  settings = CarlaSettings()
  settings.set(
      SynchronousMode=False,
      SendNonPlayerAgentsInfo=True,
      NumberOfVehicles=3,
      NumberOfPedestrians=3,
      WeatherId=random.choice([1, 3, 7, 8, 14]),
      QualityLevel=QUALITY_LEVEL)
  return settings

class CarlaGame(object):
  def __init__(self, carla_client, args):
    self.client = carla_client
    self._carla_settings = make_carla_settings(args)
    self._enable_autopilot = True
    self._is_on_reverse = False
    self._city_name = MAP_NAME
    self._position = None
    self._agent_positions = None
    self._map = CarlaMap(self._city_name, 0.1643, 50.0) if self._city_name is not None else None
    self.measurements = None
    self.enabled_commands = []
    self.vehicle_distance_threshold = 30
    self.traffic_light_distance_threshold = 15
    self.pedestrian_distance_threshold = 10
    self.speed_limit_distance_threshold = 20
    self.lane_tolerance = 0.00002

  def execute(self):
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
    self._is_on_reverse = False
    self.enabled_commands = []

# Callback function to be run continuously throughout the game

  def distance_between(self, car_position, agent_position):
    import math
    (car_x, car_y, car_z) = car_position
    (agent_x, agent_y, agent_z) = agent_position
    sum_x_2 = (agent_x - car_x) ** 2
    sum_y_2 = (agent_y - car_y) ** 2
    sum_z_2 = (agent_z - car_z) ** 2
    return math.sqrt(sum_x_2 + sum_y_2 + sum_z_2)

  def too_close_to(self, field, distance_threshold):
    # Set the player position
    if self._city_name is not None:
      measurements = self.measurements
      car_position = (measurements.player_measurements.transform.location.x,
        measurements.player_measurements.transform.location.y,
        measurements.player_measurements.transform.location.z)
      self._agent_positions = measurements.non_player_agents

    for agent in self.measurements.non_player_agents:
      if agent.HasField(field):
        agent_position = (getattr(agent, field).transform.location.x,
          getattr(agent, field).transform.location.y,
          getattr(agent, field).transform.location.z)
        if self.distance_between(car_position, agent_position) < distance_threshold:
          print(field)
          return True
    return False

  def moving_out_of_lane(self):
    # Lane Position (horizontal)
    measurements = self.measurements
    # Get the position of the car, in the X direction, in terms of sin(its angle)
    lane_orientation = self._map.get_lane_orientation([
        measurements.player_measurements.transform.location.x,
        measurements.player_measurements.transform.location.y,
        measurements.player_measurements.transform.location.z])
    # print(lane_orientation)
    if abs(lane_orientation[0]) > 1 - self.lane_tolerance:
      return False
    if abs(lane_orientation[1]) > 1 - self.lane_tolerance:
      return False
    return True


  def _on_loop(self):
    self.measurements, sensor_data = self.client.read_data()

    # Control
    if self.too_close_to('speed_limit_sign', self.speed_limit_distance_threshold):
      # Just send socket to secondary monitor
      pass

    if self.too_close_to('traffic_light', self.traffic_light_distance_threshold):
      # Send socket to secondary monitor
      # Let the car drive through the intersection
      self.client.send_control(self.measurements.player_measurements.autopilot_control)
      return

    if self.too_close_to('pedestrian', self.pedestrian_distance_threshold):
      # Send socket to secondary monitor
      # Let the car stop and wait
      self.client.send_control(self.measurements.player_measurements.autopilot_control)
      return

    number_of_commands = len(self.enabled_commands)
    if self._enable_autopilot and number_of_commands == 0:
      self.client.send_control(self.measurements.player_measurements.autopilot_control)
    # else:

    lane_position_alert = self.moving_out_of_lane()
    if (number_of_commands > 0):
      for command in self.enabled_commands:
        # if (self.too_close_to('vehicle', self.vehicle_distance_threshold) and
        #     (command == self.accelerate)):
        #   # Send socket to secondary monitor based on vehicle positioning
        #   continue
        if lane_position_alert and command == self.steer_left:
          # Send socket to secondary monitor based on lane positioning
          # Don't allow lane position change
          continue
        if lane_position_alert and command == self.steer_right:
          # Send socket to secondary monitor based on lane positioning
          # Don't allow lane position change
          continue
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
    send_framer_message(SECONDARY_SCREEN_COMMANDS['reset'])

# Left turning
  def steer_left(self):
    control = VehicleControl()
    control.steer = max(control.steer - 0.01, -0.05)
    control.reverse = self._is_on_reverse
    control.throttle = self.measurements.player_measurements.autopilot_control.throttle
    self.client.send_control(control)

  def add_left(self):
    if self.steer_left not in self.enabled_commands and not(self.moving_out_of_lane()):
      self.enabled_commands.append(self.steer_left)
      send_framer_message(SECONDARY_SCREEN_COMMANDS['left'])

  def remove_left(self):
    if self.steer_left in self.enabled_commands:
      self.enabled_commands.remove(self.steer_left)
      send_framer_message(SECONDARY_SCREEN_COMMANDS['left_stop'])

# Right Turning
  def steer_right(self):
    control = VehicleControl()
    control.steer = min(control.steer + 0.01, 0.05)
    print(control.steer)
    control.reverse = self._is_on_reverse
    control.throttle = self.measurements.player_measurements.autopilot_control.throttle
    self.client.send_control(control)

  def add_right(self):
    if self.steer_right not in self.enabled_commands and not(self.moving_out_of_lane()):
      self.enabled_commands.append(self.steer_right)
      send_framer_message(SECONDARY_SCREEN_COMMANDS['right'])

  def remove_right(self):
    if self.steer_right in self.enabled_commands:
      self.enabled_commands.remove(self.steer_right)
      send_framer_message(SECONDARY_SCREEN_COMMANDS['right_stop'])

# Reverse
  def trigger_reverse(self):
    self._is_on_reverse = not self._is_on_reverse

# Acceleration
  def add_accel(self):
    if self.accelerate not in self.enabled_commands:
      self.enabled_commands.append(self.accelerate)
      send_framer_message(SECONDARY_SCREEN_COMMANDS['speed_up'])

  def remove_accel(self):
    if self.accelerate in self.enabled_commands:
      self.enabled_commands.remove(self.accelerate)
      send_framer_message(SECONDARY_SCREEN_COMMANDS['speed_up_stop'])

  def accelerate(self):
    control = VehicleControl()
    control.throttle = 1.0
    if (self.too_close_to('vehicle', self.vehicle_distance_threshold)):
      control.throttle = self.measurements.player_measurements.autopilot_control.throttle
    control.reverse = self._is_on_reverse
    self.client.send_control(control) 

# Deceleration
  def add_decel(self):
    if self.decelerate not in self.enabled_commands:
      self.enabled_commands.append(self.decelerate)
      send_framer_message(SECONDARY_SCREEN_COMMANDS['slow_down'])

  def remove_decel(self):
    if self.decelerate in self.enabled_commands:
      self.enabled_commands.remove(self.decelerate)
      send_framer_message(SECONDARY_SCREEN_COMMANDS['slow_down_stop'])

  def decelerate(self):
    control = VehicleControl()
    control.brake = 0.5
    control.reverse = self._is_on_reverse
    self.client.send_control(control)

# Braking
  def add_brake(self):
    self.enabled_commands = [self.throw_brake]
    send_framer_message(SECONDARY_SCREEN_COMMANDS['stop'])

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

def send_framer_message(msg):
  r = requests.get('http://localhost' + ':' + str(SECONDARY_PORT) + '/' + msg, data={'msg': msg})
  print(r.status_code, r.reason)
 
# HTTPRequestHandler class
class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
      super().__init__(request, client_address, server)

  # Additional Header from Coffeescript AJAX calls
    def do_OPTIONS(self):           
      self.send_response(200, "ok")       
      self.send_header('Access-Control-Allow-Origin', '*')                
      self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
      self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
      self.end_headers() 
 
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
      content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
      post_data = self.rfile.read(content_length) # <--- Gets the data itself
      content = post_data.decode("utf-8") 
      print(content)
      self.send_response(200)
      self.send_header('Content-type','text/html')
      self.send_header('Access-Control-Allow-Origin', '*')
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
      if content == 'left_stop': #DONE
          game.remove_left()
      if content == 'right': #DONE
          game.add_right()
      if content == 'right_stop': #DONE
          game.remove_right()
      if content == 'reverse': #DONE
          game.trigger_reverse()
      if content == 'forward':
          game.add_accel()
      if content == 'forward_stop':
          game.remove_accel()
      if content == 'backward':
          game.add_decel()
      if content == 'backward_stop':
          game.remove_decel()
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
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running server...', httpd.socket.getsockname())
  print(httpd)
  httpd.serve_forever()


if __name__ == '__main__':

    try:
        run()
    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
