<!-- This is one of the ugliest pieces of code I have ever written. -->

## About

This repository contains one of the most outrageus pieces of code I have ever written but it works.

This is meant for Garmin Speed Sensor 2 used with Tacx Boost rullo as resistances are calculated only for that trainer.

This works by settings up a server which will send the virtual power through a web socket to a script which then can act as a bluetooth sensor which apps like `zwift` and `mywhoosh` can detect.

Also this script has a tendency to fuck itself (if you close it at a wrong time) so if you ever encounter a `Error: ` that is empty just restart the raspberry pi.

## Showcase



## Dependencies

1. All the dependencies listed under `https://github.com/abandonware/bleno#running-on-linux`

2. May god help you installing dependencies for this project as npm's package.json will most likely fuck itself all I'm going to say is run `npm i` and then try installing each dependecy by itself. Also keep in mind somehow the order of instalation also matters a lot in this case.

`npm install bleno@npm:@abandonware/bleno` Will help you