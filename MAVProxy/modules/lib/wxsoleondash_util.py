'''
MAVProxy soleon dashboard utility classes
'''

import enum



class LiquidLevel(object):
    '''
    Liquid level and time stamp
    '''

    def __init__(self, time_stamp, level):
        self.time_stamp = time_stamp
        self.level = level
