import nidaqmx
import logging
import time

logger = logging.getLogger(__name__)

class PiezoControl:

    def __init__(self, device_name: str,
                       write_channels: list[str] = ['ao0','ao1','ao2'],
                       read_channels: list[str] = None,
                       scale_microns_per_volt = 8) -> None:

        self.device_name = device_name
        self.write_channels = write_channels
        self.read_channels = read_channels
        self.scale_microns_per_volt = scale_microns_per_volt
        self.last_write_values = [-1, -1, -1]
        self.minimum_allowed_position = 0
        self.maximum_allowed_position = 80
        self.settling_time_in_seconds = 0.400

    def _microns_to_volts(self, microns: float) -> float:
        return microns / self.scale_microns_per_volt

    def _volts_to_microns(self, volts: float) -> float:
        return  self.scale_microns_per_volt * volts

    def _validate_value(self, position: float) -> None:
        if type(position) not in [type(1.0), type(1)]:
            raise TypeError(f'value {position} is not a valid type.')
        if position < self.minimum_allowed_position:
            raise ValueError(f'value {position} is less than zero.')
        if position > self.maximum_allowed_position:
            raise ValueError(f'value {position} is greater than 80.')

    def go_to_position(self, x: float = None,
                             y: float = None,
                             z: float = None) -> None:
        '''
        Sets the x,y,z position in microns.

        You do not need to specify all three axis values in order
        to move in one direction. For example, you can call: go_to_position(z = 40)

        raises ValueError if try to set position out of bounds.
        '''
        logging.info(f'go to position {x}, {y}, {z}')
        if x:
            self._validate_value(x)
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(self.device_name + '/' + self.write_channels[0])
                task.write(self._microns_to_volts(x))
                self.last_write_values[0] = x

        if y:
            self._validate_value(y)
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(self.device_name + '/' + self.write_channels[1])
                task.write(self._microns_to_volts(y))
                self.last_write_values[1] = y

        if z:
            self._validate_value(z)
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(self.device_name + '/' + self.write_channels[2])
                task.write(self._microns_to_volts(z))
                self.last_write_values[2] = z

        time.sleep(self.settling_time_in_seconds) #wait to ensure piezo actuator has settled into position.
        logging.info(f'last write: {self.last_write_values}')

    def step(self, dx: float = None,
                   dy: float = None,
                   dz: float = None) -> None:
        '''
        Step a small amount in any direction.

        You do not need to specify all three axis values in order
        to move in one direction. For example, you can call: step(dz = 0.5)
        '''
        x, y, z = self.get_current_position()

        if dx:
            try:
                self.go_to_position(x = x + dx)
            except ValueError as e:
                logger.warning('Trying to step outside of allowed range (0, 80).')
        if dy:
            try:
                self.go_to_position(y = y + dy)
            except ValueError as e:
                logger.warning('Trying to step outside of allowed range (0, 80).')
        if dz:
            try:
                self.go_to_position(z = z + dz)
            except ValueError as e:
                logger.warning('Trying to step outside of allowed range (0, 80).')

    def get_current_position(self) -> list[float]:
        '''
        Returns the x,y,z position in microns

        If no input analog channels were provided when objected was created,
        returns the last requested position.
        '''

        if self.read_channels is None:
            return self.last_write_values

        else:
            return [self._volts_to_microns(v) for v in self.get_current_voltage()]

    def get_current_voltage(self) -> list[float]:
        '''
        Returns the voltage supplied to the three input analog channels.

        If no input analog channels were provided when objected was created,
        returns [-1,-1,-1]
        '''
        output = [-1,-1,-1]
        if self.read_channels is not None:
            with nidaqmx.Task('xr') as xread, nidaqmx.Task('yr') as yread, nidaqmx.Task('zr') as zread:

                 xread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[0])
                 yread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[1])
                 zread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[2])

                 output[0] = xread.read()
                 output[1] = yread.read()
                 output[2] = zread.read()

        return output
