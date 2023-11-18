import argparse
import tkinter as tk
import tkinter.ttk as ttk
import logging

import numpy as np

import nipiezojenapy


parser = argparse.ArgumentParser(description='Jena Piezo Scanner Control',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-d', '--daq-name', default = 'Dev1', type=str, metavar = 'daq_name',
                    help='NI DAQ Device Name')
parser.add_argument('--piezo-write-channels', metavar = '<ch0,ch1,ch2>', default = 'ao0,ao1,ao2', type=str,
                    help='List of analog output channels used to control the piezo position')
parser.add_argument('--piezo-read-channels', metavar = '<ch0,ch1,ch2>', default = 'ai0,ai1,ai2', type=str,
                    help='List of analog input channels used to read the piezo position')
parser.add_argument('-s', '--settle-time', metavar = 'settle_time', default = 0.01, type=float,
                    help='''Amount of time, in seconds, that are paused after moving to a new position. 
This allows for the device to "settle" into position.''')
parser.add_argument('-q', '--quiet', action = 'store_true',
                    help='When true,logger level will be set to warning. Otherwise, set to "info".')
parser.add_argument('-t', '--test', action = 'store_true',
                    help='This is for development testing.')
parser.add_argument('-pmin', '--piezo-min-position', metavar = 'microns', default = 0, type=float,
                    help='sets min allowed position on piezo controller.')
parser.add_argument('-pmax', '--piezo-max-position', metavar = 'microns', default = 80, type=float,
                    help='sets min allowed position on piezo controller.')
parser.add_argument('-pscale', '--piezo-scale-microns-per-volt', nargs = "*", default = [8], type=float,
                    help='sets micron to volt scale for piezo controller for all channels or each channel individually.')
parser.add_argument('-poffset', '--piezo-scale-volts-offset', nargs = "*", default = [0], type=float,
                    help='''sets volt offset value for piezo controller for all channels or each channel individually. 
This is the applied voltage that defines the position x, y, z = 0, 0, 0.''')

args = parser.parse_args()

logger = logging.getLogger(__name__)

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

if args.quiet is False:
    logger.setLevel(level=logging.INFO)

class MainApplicationView():
    def __init__(self, main_frame):

        self.current_position = {'x':-1, 'y':-1, 'z':-1}
        self._build_frame(main_frame)

    def _build_frame(self, main_frame):
        frame = tk.Frame(main_frame)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        row = 0
        #left of the separator
        tk.Label(frame, text='Step Changes').grid(row=row, column=0, columnspan =3)

        ttk.Separator(frame, orient='vertical').grid(column=3, row=row, rowspan=5, sticky='ns')

        #right of the separator
        self.go_to_position_button = tk.Button(frame, text="  Go To Position  ")
        self.go_to_position_button.grid(row=row, column=4, columnspan = 3, padx=5)

        row += 1
        #left of the separator
        self.minus_x_button = tk.Button(frame, text="  -  ")
        self.minus_x_button.grid(row=row, column=0,pady = 5)
        self.current_x_pos_text = tk.StringVar()
        tk.Label(frame, textvariable=self.current_x_pos_text).grid(row=row, column=1)
        self.plus_x_button = tk.Button(frame, text="  +  ")
        self.plus_x_button.grid(row=row, column=2, padx=(5,0))

        #right of the separator
        tk.Label(frame, text='x (um): ').grid(row=row, column=4, padx = 10, pady=5)
        self.go_to_x_position_entry = tk.Entry(frame, width=6)
        self.go_to_x_position_entry.grid(row=row, column=5, sticky="e")

        row += 1
        #left of the separator
        self.minus_y_button = tk.Button(frame, text="  -  ")
        self.minus_y_button.grid(row=row, column=0)
        self.current_y_pos_text = tk.StringVar()
        tk.Label(frame, textvariable=self.current_y_pos_text).grid(row=row, column=1)
        self.plus_y_button = tk.Button(frame, text="  +  ")
        self.plus_y_button.grid(row=row, column=2, padx=(5,0))

        #right of the separator
        tk.Label(frame, text='y (um): ').grid(row=row, column=4, padx = 5, pady=5)
        self.go_to_y_position_entry = tk.Entry(frame, width=6)
        self.go_to_y_position_entry.grid(row=row, column=5, sticky="e")

        row += 1
        #left of the separator
        self.minus_z_button = tk.Button(frame, text="  -  ")
        self.minus_z_button.grid(row=row, column=0)
        self.current_z_pos_text = tk.StringVar()
        tk.Label(frame, textvariable=self.current_z_pos_text).grid(row=row, column=1)
        self.plus_z_button = tk.Button(frame, text="  +  ")
        self.plus_z_button.grid(row=row, column=2, padx=(5,0))

        #right of the separator
        tk.Label(frame, text='z (um): ').grid(row=row, column=4, padx = 5, pady=5)
        self.go_to_z_position_entry = tk.Entry(frame, width=6)
        self.go_to_z_position_entry.grid(row=row, column=5, sticky="e")

        row += 1
        #left of the separator
        tk.Label(frame, text='step size (um): ').grid(row=row, column=0,  pady=5, columnspan=2)
        self.step_size_entry = tk.Entry(frame, width=4)
        self.step_size_entry.insert(7, 0.25)
        self.step_size_entry.grid(row=row, column=2)

        row += 1
        #left of the separator
        self.read_position_button = tk.Button(frame, text="Refresh Position")
        self.read_position_button.grid(row=row, column=0, padx = 20,pady = 5, columnspan=2)

        #right of the separator
        self.capture_position_button = tk.Button(frame, text="Capture Position")
        self.capture_position_button.grid(row=row, column=4, padx = 20,pady = 5, columnspan=2)

        self.update_position(20,20,20)

    def update_position(self, x = None, y = None, z = None):

        if x is not None:
            self.current_position['x'] = x
            self.current_x_pos_text.set(f'x: {x:.3f}')
        if y is not None:
            self.current_position['y'] = y
            self.current_y_pos_text.set(f'y: {y:.3f}')
        if z is not None:
            self.current_position['z'] = z
            self.current_z_pos_text.set(f'z: {z:.3f}')

class MainTkApplication():

    def __init__(self, controller):
        self.root = tk.Tk()
        self.root.minsize(200,150)
        self.controller = controller

        self.view = MainApplicationView(self.root)
        self.view.plus_x_button.bind("<Button>",  lambda e: self._move('x',1))
        self.view.minus_x_button.bind("<Button>", lambda e: self._move('x',-1))
        self.view.plus_y_button.bind("<Button>",  lambda e: self._move('y',1))
        self.view.minus_y_button.bind("<Button>", lambda e: self._move('y',-1))
        self.view.plus_z_button.bind("<Button>",  lambda e: self._move('z',1))
        self.view.minus_z_button.bind("<Button>", lambda e: self._move('z',-1))

        self.view.go_to_position_button.bind("<Button>", lambda e: self.go_to_position())
        self.view.read_position_button.bind("<Button>", lambda e: self.update_position())
        self.view.capture_position_button.bind("<Button>", lambda e: self.capture_position())

        self.update_position()

        mid = self.controller.maximum_allowed_position - self.controller.minimum_allowed_position
        mid = mid/2
        mid = np.round(mid, 1)
        self.view.go_to_x_position_entry.insert(0,mid)
        self.view.go_to_y_position_entry.insert(0,mid)
        self.view.go_to_z_position_entry.insert(0,mid)

    def run(self):
        self.root.title("Piezo Control")
        self.root.deiconify()
        self.root.mainloop()

    def _move(self, axis, direction=1):
        delta = float(self.view.step_size_entry.get())
        current = self.view.current_position[axis]
        new = current + direction*delta
        kwargs = {axis:new}
        try:
            self.controller.go_to_position(**kwargs)
            logger.info(f'moving {axis}: {current:.3f} -> {new:.3f}')
            self.view.update_position(**kwargs)
        except ValueError as e:
            logger.error(e)
            
    def update_position(self):
        x, y, z = self.controller.get_current_position()
        self.view.update_position(x,y,z)

    def go_to_position(self):
        gotox = float(self.view.go_to_x_position_entry.get())
        gotoy = float(self.view.go_to_y_position_entry.get())
        gotoz = float(self.view.go_to_z_position_entry.get())
        try:
            self.controller.go_to_position(gotox, gotoy, gotoz)
            logger.info(f'go to: {gotox:.3f}, {gotoy:.3f}, {gotoz:.3f}')
            self.view.update_position(gotox,gotoy,gotoz)
        except ValueError as e:
            logger.error(e)

    def capture_position(self):
        x, y, z = self.controller.get_current_position()

        self.view.go_to_x_position_entry.delete(0,tk.END)
        self.view.go_to_y_position_entry.delete(0,tk.END)
        self.view.go_to_z_position_entry.delete(0,tk.END)

        self.view.go_to_x_position_entry.insert(0,np.round(x,3))
        self.view.go_to_y_position_entry.insert(0,np.round(y,3))
        self.view.go_to_z_position_entry.insert(0,np.round(z,3))

def build_controller():
    if args.test:
        controller = nipiezojenapy.BaseControl()
    else:
        if len(args.piezo_scale_microns_per_volt) == 1:
            piezo_scale_microns_per_volt = args.piezo_scale_microns_per_volt * 3
        else:
            piezo_scale_microns_per_volt = args.piezo_scale_microns_per_volt

        if len(args.piezo_scale_volts_offset) == 1:
            piezo_scale_volts_offset = args.piezo_scale_volts_offset * 3
        else:
            piezo_scale_volts_offset = args.piezo_scale_volts_offset

        controller = nipiezojenapy.PiezoControl(device_name = args.daq_name,
                                  write_channels = args.piezo_write_channels.split(','),
                                  read_channels = args.piezo_read_channels.split(','),
                                  move_settle_time = args.settle_time,
                                  min_position = args.piezo_min_position,
                                  max_position = args.piezo_max_position,
                                  scale_microns_per_volt = piezo_scale_microns_per_volt,
                                  zero_microns_volt_offset = piezo_scale_volts_offset)
    return controller

def main():
    tkapp = MainTkApplication(build_controller())
    tkapp.run()

if __name__ == '__main__':
    main()
