# Carla Server/Client
## A Middleware Representation
This is a means of interacting with Version 0.8.2 of the [Carla Open-Source Simulation](https://github.com/carla-simulator/carla).

The main Python file to be used as middleware is `use_case_controller.py`, which waits for an incoming client connection before acting as a client to a running CARLA server on another IP address.

This simulation is meant to run on a static IP, customizable in `use_case_controller.py`.

Here is a table of conventions for the initial client to communicate with the server:

| Car Control         | Text to be Sent (as POST request) |
|---------------------|-----------------------------------|
| Start Carla Server  | startserver                       |
| Enable Autopilot    | enable_ap                         |
| Start New Level     | reset                             |
| Steer Left          | left                              |
| Steer Right         | right                             |
| Switch into Reverse | reverse                           |
| Accelerate          | forward                           |
| Slow Down           | backward                          |
| Engage Hand Break   | stop                              |
