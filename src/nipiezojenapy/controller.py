import nidaqmx

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
        '''

        if x:
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(self.device_name + '/' + self.write_channels[0])
                task.write(self._microns_to_volts(x))
                self.last_write_values[0] = self._microns_to_volts(x)

        if y:
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(self.device_name + '/' + self.write_channels[1])
                task.write(self._microns_to_volts(y))
                self.last_write_values[1] = self._microns_to_volts(y)

        if z:
            with nidaqmx.Task() as task:
                task.ao_channels.add_ao_voltage_chan(self.device_name + '/' + self.write_channels[2])
                task.write(self._microns_to_volts(z))
                self.last_write_values[2] = self._microns_to_volts(z)


    def get_current_position(self) -> list[float]:
        '''
        Returns the x,y,z position in microns
        '''

        if self.read_channels is None:
            return self.last_write_values

        output = [-1,-1,-1]
        with nidaqmx.Task('xr') as xread, nidaqmx.Task('yr') as yread, nidaqmx.Task('zr') as zread:

             xread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[0])
             yread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[1])
             zread.ai_channels.add_ai_voltage_chan(self.device_name + '/' + self.read_channels[2])

             output[0] = self._volts_to_microns(xread.read())
             output[1] = self._volts_to_microns(yread.read())
             output[2] = self._volts_to_microns(zread.read())

        return output
