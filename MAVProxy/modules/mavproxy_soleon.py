'''
MAVProxy soleon dashboard module

10.10.2023 [HaRe]: created
'''

from pymavlink import mavutil

from MAVProxy.modules.lib import mp_module
from MAVProxy.modules.lib import mp_util
from MAVProxy.modules.lib import mp_settings
from MAVProxy.modules.lib.mp_settings import MPSetting
from MAVProxy.modules.lib.wxsoleondash import SoleonDashboard
from MAVProxy.modules.lib.wxsoleondash_util import LiquidLevel


import time

class SoleonModule(mp_module.MPModule):
    '''SoleonModule provides a dashboard to display soleon sprayer instrument data'''

    def __init__(self, mpstate):
        super(SoleonModule, self).__init__(mpstate, "soleon", "soleon module")

        # dashboard GUI
        self.soleon_dash = SoleonDashboard(title="Soleon Sprayer Dashboard")

        # mavlink messages
        self.master.mav.command_long_send(
            self.settings.target_system,  # target_system
            self.settings.target_component,  # target_component
            mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # ID of command to send
            0,  # confirmation
            #mavutil.mavlink.SO_STATUS,  # param1: Message ID to be streamed
            50080,   # param1: Message ID to be streamed
            500000,  # param2: Interval in microseconds (500mSec)
            0,  # param3
            0,  # param4
            0,  # param5
            0,  # param6
            0)  # param7

        # data
        self.status_timestamp = 0.0
        self.status_level = 0.0

        self.spray_rate = 0.0

        # control update rate to GUI
        self._msg_list = []
        self._fps = 10.0
        self._last_send = 0.0
        self._send_delay = (1.0/self._fps) * 0.9

        # commands
        self.add_command('soleon', self.cmd_soleon, "soleon dashboard")
        self.add_command('sprayrate', self.cmd_spray_rate, "soleon sprayrate")


    def cmd_spray_rate(self, args):
        usage = "Usage: sprayrate <the rate in %/100mSec>"

        if len(args) == 0:
            print(usage)
            return

        self.spray_rate = float(args[0])

        # mavlink messages
        self.master.mav.command_long_send(
            self.settings.target_system,  # target_system
            self.settings.target_component,  # target_component
            mavutil.mavlink.MAV_CMD_SO_SYSMODE,  # ID of command to send
            0,  # confirmation
            self.spray_rate,  # param1:
            self.spray_rate,  # param2:
            0,  # param3
            0,  # param4
            0,  # param5
            0,  # param6
            0)  # param7

    def cmd_soleon(self, args):
        if len(args) != 1:
            print (self.usage())
            return
        if args[0] == 'status':
            print (self.status_so())

        else:
            print(self.usage())



    def usage(self):
        '''Show help on command line options'''

        return  "Usage: soleon <status>  --> show status information\n" \
                "       sprayrate <x.x>  --> spray rate in % per 100mSec"

    def status_so(self):
        '''Returns information about the soleon sprayer state'''
        return(
            "Sprayer status: fluid_level="+ str(self.status_level) + "; time_stamp="+ str(self.status_timestamp) + ";\n" \
            "                sprayer rate=" + str(self.spray_rate) + ";\n" \
            "MavLink: targetSystem="+ str(self.settings.target_system) + "; targetComponent="+ str(self.settings.target_component) + ";\n"
            )

    def mavlink_packet(self, m):
        '''Handle a mavlink packet'''
        type = m.get_type()
        #sysid = msg.get_srcSystem()
        #compid = msg.get_srcComponent()

        if type == 'SO_STATUS':
           # print (m);
           self.status_timestamp = m.time_boot_ms
           self.status_level = m.soleon_value

           self._msg_list.append(LiquidLevel(m.time_boot_ms, m.soleon_value))


    def idle_task(self):
        '''Idle tasks
            - check if the GUI has received a close event
            - periodically send data to the GUI
        '''
        # tell MAVProxy to unload the module if the GUI is closed
        if self.soleon_dash.close_event.wait(timeout=0.001):
            self.needs_unloading = True

        # send message list via pipe to gui at desired update rate
        if (time.time() - self._last_send) > self._send_delay:
            # pipe data to GUI
            self.soleon_dash.parent_pipe_send.send(self._msg_list)

            # reset counters etc.
            self._msg_list = []
            self._last_send = time.time()

    def unload(self):
        '''Close the GUI and unload module'''

        # close the gui
        self.soleon_dash.close()


def init(mpstate):
    ''' Initialise module'''

    return SoleonModule(mpstate)

