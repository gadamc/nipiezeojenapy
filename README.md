# Control of PiezoSystemJena NV40/3CLE via NI DAQmx

Control of the Jena's piezo accuators via their multi-channel amplifier.
https://www.piezosystem.com/products/amplifiers/multi-channel/40ma-multi-channel-amplifiers/

Uses NIDAQ device to read and write analog voltages between 0 and 10 to
three input and output voltage channels connected to a Jena NV40/3CLE
amplifier. Each input/output channel controls one of three axis (x, y, or z).

When using this software, one must at least provide three analog channels on
the NIDAQ that are connected to the NV40/3CLE amplifier that control (write)
the location of the piezo stage.

This program does not *need* to read voltages from the amplifier. If no read
channels are provided, this program will report the last written values when
reporting the current location.  

This controller does *NOT* lock out usage of analog input and output channels
on the NI-DAQ card. It writes or reads to the analog channels and then releases
the resource. This would allow external programs to access those channels, so
long as the access is not simultaneous.

## Installation

### Requirements

```
pip install nidaqmx
```


### Local Installation

```
git clone https://github.com/gadamc/nipiezojenapy
cd nipiezojenapy
python setup.py install
```

## Usage


# LICENSE

[LICENCE](LICENSE)

##### Acknowledgments
