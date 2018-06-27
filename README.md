# Carla Server/Client
## A Middleware Representation
This is a means of interacting with Version 0.8.2 of the [Carla Open-Source Simulation](https://github.com/carla-simulator/carla).

The main Python file to be used as middleware is `use_case_controller.py`, which waits for an incoming client connection before acting as a client to a running CARLA server on another IP address.

This simulation is meant to run on a static IP, customizable in `use_case_controller.py`.

A GET request can be used to test communication with the server, or with a POST request with the text `testmsg` as the payload.

Here is a table of conventions for the initial client to communicate with the server via POST requests:

| Car Control                          | Text to be Sent (as POST request) |
|--------------------------------------|-----------------------------------|
| Test Connection (Prints Server Side) | testmsg                           |
| Start Carla Server                   | startserver                       |
| Enable Autopilot                     | enable_ap                         |
| Start New Level                      | reset                             |
| Steer Left                           | left                              |
| Steer Right                          | right                             |
| Switch into Reverse                  | reverse                           |
| Accelerate                           | forward                           |
| Slow Down                            | backward                          |
| Engage Hand Break                    | stop                              |

*For all of these cardinal direction controls, there is a `_stop` variant which cancels the existing option*. For example, `left_stop` will stop the car from continuing to turn left.
