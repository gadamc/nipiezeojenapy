import nidaqmx
import logging
import time
from typing import List

logger = logging.getLogger(__name__)

class BaseControl:
    def __init__(self):
        self.minimum_allowed_position = 0.00
        self.maximum_allowed_position = 80.0
        self.last_write_values = [0, 0, 0]

    def _validate_value(self, position: float) -> None:
        position = float(position)
        if type(position) not in [type(1.0), type(1)]:
            raise TypeError(f'value {position} is not a valid type.')
        if position < self.minimum_allowed_position:
            raise ValueError(f'value {position} is less than {self.minimum_allowed_position:.3f}.')
        if position > self.maximum_allowed_position:
            raise ValueError(f'value {position} is greater than {self.maximum_allowed_position:.3f}.')

    def check_allowed_position(self, x: float = None,
                                     y: float = None,
                                     z: float = None) -> None:
        if x is not None: self._validate_value(x)
        if y is not None: self._validate_value(y)
        if z is not None: self._validate_value(z)

    def go_to_position(self, x: float = None,
                             y: float = None,
                             z: float = None) -> None:
        '''
        '''
        self.check_allowed_position(x,y,z)
        if x is not None:
          self.last_write_values[0] = x
        if y is not None:
          self.last_write_values[1] = y
        if z is not None:
          self.last_write_values[2] = z

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
                logger.error(f'Trying to step outside of allowed range ({self.minimum_allowed_position:.2f}, {self.maximum_allowed_position:.2f}).')
        if dy:
            try:
                self.go_to_position(y = y + dy)
            except ValueError as e:
                logger.error(f'Trying to step outside of allowed range ({self.minimum_allowed_position:.2f}, {self.maximum_allowed_position:.2f}).')
        if dz:
            try:
                self.go_to_position(z = z + dz)
            except ValueError as e:
                logger.error(f'Trying to step outside of allowed range ({self.minimum_allowed_position:.2f}, {self.maximum_allowed_position:.2f}).')

    def get_current_position(self) -> List[float]:

        return self.last_write_values


class PiezoControl(BaseControl):

    def __init__(self, device_name: str,
                       write_channels: List[str] = ['ao0','ao1','ao2'],
                       read_channels: List[str] = None,
                       scale_microns_per_volt: float = 8,
                       move_settle_time: float = 0.001,
                       min_position: float = 0.0,
                       max_position: float = 80.0) -> None:
        super().__init__()

        self.device_name = device_name
        self.write_channels = write_channels
        self.read_channels = read_channels
        self.scale_microns_per_volt = scale_microns_per_volt
        self.minimum_allowed_position = min_position
        self.maximum_allowed_position = max_position
        self.settling_time_in_seconds = move_settle_time #10 millisecond settle time
        self.last_write_values = [None, None, None]

    def _microns_to_volts(self, microns: float) -> float:
        return microns / self.scale_microns_per_volt

    def _volts_to_microns(self, volts: float) -> float:
        return  self.scale_microns_per_volt * volts


    def go_to_position(self, x: float = None,
                             y: float = None,
                             z: float = None) -> None:
        '''
        Sets the x,y,z position in microns.

        You do not need to specify all three axis values in order
        to move in one direction. For example, you can call: go_to_position(z = 40)

        raises ValueError if try to set position out of bounds.
        '''

        def goto(val, idx):
            self._validate_value(val)
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(self.device_name + '/' + self.write_channels[idx])
                task.write(self._microns_to_volts(val))
                self.last_write_values[idx] = val

        debug_string = []
        if x is not None:
            goto(x, 0)
            debug_string.append(f'x: {x:.2f}')
        if y is not None:
            goto(y, 1)
            debug_string.append(f'y: {y:.2f}')
        if z is not None:
            goto(z, 2)
            debug_string.append(f'z: {z:.2f}')

        logger.info(f'go to position {" ".join(debug_string)}')

        time.sleep(self.settling_time_in_seconds) #wait to ensure piezo actuator has settled into position.
        logger.debug(f'last write: {self.last_write_values}')

    def get_current_voltage(self) -> List[float]:
        '''
        Returns the voltage supplied to the three input analog channels.

        If no input analog channels were provided when objected was created,
        returns [-1,-1,-1]
        '''
        output = [-1,-1,-1]
        if self.read_channels is not None:
            with nidaqmx.Task() as xread, nidaqmx.Task() as yread, nidaqmx.Task() as zread:

                 xread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[0], min_val = 0, max_val = 10.0)
                 yread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[1], min_val = 0, max_val = 10.0)
                 zread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[2], min_val = 0, max_val = 10.0)

                 output[0] = xread.read()
                 output[1] = yread.read()
                 output[2] = zread.read()

        return output

    def get_current_position(self) -> List[float]:
        '''
        Returns the x,y,z position in microns

        If no input analog channels were provided when objected was created,
        returns the last requested position.
        '''

        if self.read_channels is None:
            return self.last_write_values

        else:
            return [self._volts_to_microns(v) for v in self.get_current_voltage()]
