###
This file outlines the basic secondary screen server as part of the
interactive Framer.JS prototype for the MHCI Harman Capstone at 
Carnegie Mellon University, 2018.

This is a Framer Module to be used as a basic protocol to be implemented

Functions to be implemented in base Framer project:
runReset()
beginShiftingLeft()
stopShiftingLeft()
startShiftingRight()
stopShiftingRight()
startSpeedingUp()
stopSpeedingUp()
startSlowingDown()
stopSlowingDown()
stop()
###

PORT_NUM = 8020
OK_RESPONSE = 200


exports.start_secondary_screen_server = ->
  server = http.createServer (req, res) ->
    console.log res.url

    content = req.url[1..] # Getting the passed command

    # Case on content
    switch content
      when 'reset' then runReset()
      when 'left' then beginShiftingLeft()
      when 'left_stop' then stopShiftingLeft()
      when 'right' then startShiftingRight()
      when 'right_stop' then stopShiftingRight()
      when 'speed_up' then startSpeedingUp()
      when 'speed_up_stop' then stopSpeedingUp()
      when 'slow_down' then startSlowingDown()
      when 'slow_down_stop' then stopSlowingDown()
      when 'stop' then stop()

    data = 'Got Your Message\n'
    res.writeHead OK_RESPONSE,
        'Content-Type':     'text/plain'
        'Content-Length':   data.length
    res.end data

  server.listen PORT_NUM
