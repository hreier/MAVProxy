"""
  MAVProxy sailing dashboard gui elements
"""

from MAVProxy.modules.lib.wx_loader import wx
from MAVProxy.modules.lib.wxsoleondash_util import LiquidLevel


import wx.lib.agw.speedmeter as SM

import math
import time

class SoleonDashboardFrame(wx.Frame):
    '''The main frame of the soleon dashboard'''

    def __init__(self, state, title, size):
        super(SoleonDashboardFrame, self).__init__(None, title=title, size=size)
        self._state = state
        self._title = title

        # control update rate
        self._timer = wx.Timer(self)
        self._fps = 10.0
        self._start_time = time.time()

        # events
        self.Bind(wx.EVT_TIMER, self.OnTimer, self._timer)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)

        # restart the timer
        self._timer.Start(milliseconds=100)

        # create wind meters for true and apparent wind
        self._level_meter1 = LiquidLevelMeter(self)
        self._level_meter1.SetLevel(0)

        # instrument display
        self._instr1 = InstrumentDisplay(self)
        self._instr1.label = "LiquidLevel"
        self._instr1.unit = "%"
        self._instr1.value = 0.0

        self._instr2 = InstrumentDisplay(self)
        self._instr2.label = "timestamp"
        self._instr2.unit = "ms"
        self._instr2.value = 0.0

        # instrument panel sizers
        self._instr_sizer1 = wx.BoxSizer(wx.VERTICAL) 
        self._instr_sizer1.Add(self._instr1, 1, wx.EXPAND)
        self._instr_sizer1.Add(self._instr2, 1, wx.EXPAND)

        # top level sizers
        self._top_sizer = wx.BoxSizer(wx.HORIZONTAL) 
        self._top_sizer.Add(self._level_meter1, 2, wx.EXPAND)
        self._top_sizer.Add(self._instr_sizer1, 1, wx.EXPAND)

        # layout sizers
        self.SetSizer(self._top_sizer)
        self.SetAutoLayout(1)

    def OnIdle(self, event):
        '''Handle idle events
        
            - e.g. managed scaling when window resized if needed
        ''' 
        
        pass

    def OnTimer(self, event):
        '''Handle timed tasks'''
        
        # check for close events
        if self._state.close_event.wait(timeout=0.001):
            # stop the timer and destroy the window - this ensures
            # the window is closed when the module is unloaded
            self._timer.Stop()
            self.Destroy()
            return

        # receive data from the module
        while self._state.child_pipe_recv.poll():
            obj_list = self._state.child_pipe_recv.recv()
            for obj in obj_list:
                if isinstance(obj, LiquidLevel):
                    self._level_meter1.SetLevel(obj.level)
                    self._instr1.value = obj.level
                    self._instr2.value = obj.time_stamp

        # reset counters
        self._start_time = time.time()

    def OnKeyPress(self, event):
        '''Handle keypress events'''

        pass



class LiquidLevelMeter(SM.SpeedMeter):
    '''
    class: `LiquidLevelMeter` is a custom `SpeedMeter`for displaying true or apparent liquid level
    '''

    def __init__(self, *args, **kwargs):
        # customise the agw style
        kwargs.setdefault('agwStyle', SM.SM_DRAW_HAND
                          | SM.SM_DRAW_PARTIAL_SECTORS
                          | SM.SM_DRAW_SECONDARY_TICKS
                          | SM.SM_DRAW_MIDDLE_TEXT)

        # initialise super class
        super(LiquidLevelMeter, self).__init__(*args, **kwargs)

        # colours
        dial_colour = wx.ColourDatabase().Find('DARK SLATE GREY')
        port_arc_colour = wx.ColourDatabase().Find('RED')
        stbd_arc_colour = wx.ColourDatabase().Find('GREEN')
        bottom_arc_colour = wx.ColourDatabase().Find('TAN')
        self.SetSpeedBackground(dial_colour)

        # set lower limit to 2.999/2 to prevent the partial sectors from filling
        # the entire dial
        self.SetAngleRange( -math.pi*3/2+0.1*math.pi, -math.pi/2-+0.1*math.pi)

        # create the intervals
        intervals = range(0,120, 20)
        self.SetIntervals(intervals)

        colours =   [port_arc_colour] \
                  + [bottom_arc_colour] \
                  + [dial_colour] \
                  + [dial_colour] \
                  + [stbd_arc_colour]
        self.SetIntervalColours(colours)

        # assign the ticks, colours and font
        ticks = ['0', '20', '40', '60', '80', '100']
        self.SetTicks(ticks)
        self.SetTicksColour(wx.WHITE)
        self.SetNumberOfSecondaryTicks(1)
        self.SetTicksFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

        # set the colour for the first hand indicator
        self.SetHandColour(wx.Colour(210, 210, 210))
        self.SetHandStyle("Hand")

        # do not draw the external (container) arc
        self.DrawExternalArc(False)

        # initialise the meter to zero
        self.SetLevel(0.0)

        # wind speed display
        self.SetMiddleTextColour(wx.WHITE)
        self.SetMiddleTextFont(wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))

    def SetLevel(self, level):
        '''
        Set the liquid level
        '''

        # Convert the wind angle to the meter interval [0 - 360]
        self._level = level
        if self._level < 0:
            self._level = 0
        if self._level > 100:
            self._level = 100

        self.SetSpeedValue(self._level)


class InstrumentDisplay(wx.Panel):
    '''
    class: `InstrumentDisplay` is a panel for displaying sailing instrument data
    '''

    def __init__(self, *args, **kwargs):
        # customise the style
        kwargs.setdefault('style', wx.TE_READONLY)

        # initialise super class
        super(InstrumentDisplay, self).__init__(*args, **kwargs)

        # set the background colour (also for text controls)
        # self.SetBackgroundColour(wx.WHITE)

        # text controls
        self._label_text = wx.TextCtrl(self, style=wx.BORDER_NONE)
        self._label_text.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self._label_text.SetBackgroundColour(self.GetBackgroundColour())
        self._label_text.ChangeValue("---")

        self._value_text = wx.TextCtrl(self, style=wx.BORDER_NONE|wx.TE_CENTRE)
        self._value_text.SetFont(wx.Font(30, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self._value_text.SetBackgroundColour(self.GetBackgroundColour())
        self._value_text.ChangeValue("-.-")
        self._value_text.SetMinSize((60, 40))

        self._unit_text = wx.TextCtrl(self, style=wx.BORDER_NONE|wx.TE_RIGHT)
        self._unit_text.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self._unit_text.SetBackgroundColour(self.GetBackgroundColour())
        self._unit_text.ChangeValue("--")

        # value text needs a nested sizer to centre vertically
        self._value_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._value_sizer.Add(self._value_text,
            wx.SizerFlags(1).Align(wx.ALIGN_CENTRE_VERTICAL).Border(wx.ALL, 0))

        # top level sizers
        self._top_sizer = wx.BoxSizer(wx.VERTICAL) 
        self._top_sizer.Add(self._label_text,
            wx.SizerFlags(0).Align(wx.ALIGN_TOP|wx.ALIGN_LEFT).Border(wx.ALL, 2))
        self._top_sizer.Add(self._value_sizer,
            wx.SizerFlags(1).Expand().Border(wx.ALL, 1))
        self._top_sizer.Add(self._unit_text,
            wx.SizerFlags(0).Align(wx.ALIGN_RIGHT).Border(wx.ALL, 2))

        # layout sizers
        self._top_sizer.SetSizeHints(self)
        self.SetSizer(self._top_sizer)
        self.SetAutoLayout(True)

    @property
    def label(self):
        return self._label_text.GetValue()

    @label.setter
    def label(self, label):
        self._label_text.ChangeValue(label)

    @property
    def value(self):
        return self._value_text.GetValue()

    @value.setter
    def value(self, value):
        self._value_text.ChangeValue("{:.2f}".format(value))

    @property
    def unit(self):
        return self._unit_text.GetValue()

    @unit.setter
    def unit(self, unit):
        self._unit_text.ChangeValue(unit)
