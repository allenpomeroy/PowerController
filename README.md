# PowerController
Power controller for Garden irrigation project. See https://web.pomeroy.us/2022/12/building-an-irrigation-power-controller

Uses the MCP23017 GPIO expansion chip with integrated I2C and the Adafruit MCP23017 python libraries
https://docs.circuitpython.org/projects/mcp230xx/en/latest/api.html#adafruit_mcp230xx.digital_inout.DigitalInOut.value

Need to install the Adafruit libraries "sudo pip3 install adafruit-circuitpython-mcp230xx"

Provides:
- five (5) 24VAC feeds for common irrigation control valves similar to RainBird model
- two (2)  12VDC feeds to drive external 120VAC relays which control pumps

WARNING WARNING WARNING WARNING WARNING WARNING

It is recommended to only activate a maximum of two (2) valves and either or both pumps simultaneously to limit the aggregate current draw.
Activating more valves simulaneously is likely to cause excessive heat generation and possible permanent damage to the circuit board or components.
