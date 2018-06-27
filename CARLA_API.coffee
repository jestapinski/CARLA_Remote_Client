IP_PORT = '' # To be filled in by the user

run_ajax = (msg) ->
  $.ajax
    url: IP_PORT
    data: msg
    method: 'POST'
    crossOrigin: true
    error: (jqXHR, textStatus, errorThrown) ->
      console.log('error')
      $('body').append "AJAX Error: #{textStatus}"
    success: (data, textStatus, jqXHR) ->
      console.log('yes')
      console.log(data)
      $('body').append "Successful AJAX call: #{data}"  

# Begin implementing the communication protocol
# Implemented as wrappers to provide user-level abstraction

# Use in Framer (and other coffeescript tools) by the following
# CARLA_API = require "CARLA_API"
# CARLA_API.begin_server() # To start the CARLA middleware connection
# CARLA_API.toggle_autopilot() # To stop the default autopilot

# Note begin_server must be the first function called to establish
# the server connection to CARLA
exports.begin_server = ->
  run_ajax('startserver')

exports.speed_up = ->
  run_ajax('forward')

exports.stop_speeding_up = ->
  run_ajax('forward_stop')

exports.slow_down = ->
  run_ajax('backward')

exports.stop_slowing_down = ->
  run_ajax('backward_stop')

exports.move_left = ->
  run_ajax('left')

exports.stop_moving_left = ->
  run_ajax('left_stop')

exports.move_right = ->
  run_ajax('right')

exports.stop_moving_right = ->
  run_ajax('right_stop')

exports.hard_stop = ->
  run_ajax('stop')

exports.remove_all_commands = ->
  run_ajax('clear')

exports.toggle_autopilot = ->
  run_ajax('enable_ap')
