import os

env = os.environ

class EnvVar:
    def __init__(self, variable_name=None):
        self._variable_name = variable_name

    def __set_name__(self, owner, name):
        self._name = "_" + name

    def __get__(self, obj, type):
        if self._variable_name:
            return env[self._variable_name]
        else:
            return env[self._name]

    def __set__(self, obj, value):
        raise Exception('ReadOnlyAttribute')
        setattr(obj, self._name, value)


class QRCodeConfig:  
    VARIABILNI_SYMBOL: EnvVar = EnvVar('QR_VARIABILNI_SYMBOL')
    KONSTANTNI_SYMBOL: EnvVar = EnvVar('QR_KONSTANTNI_SYMBOL')
    ACCOUNT: EnvVar = EnvVar('QR_ACCOUNT')


class GSHeetsConfig:
    SAMPLE_SPREADSHEET_ID = "1IayBUd_t14mIXfJIrqDxkRMoW_OslV_y3Ti_oVZOAMM"
    SAMPLE_RANGE_NAME = "Class Data!A1:E"
