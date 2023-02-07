from enum import IntEnum

class STATE(IntEnum):
    INIT = 0
    REQUEST = 1
    HELD = 2
    RELEASE = 3


class MSG_TYPE(IntEnum):
    REQUEST = 0
    GRANT = 1
    RELEASE = 2
    FAIL = 3
    INQUIRE = 4
    YIELD = 5

    def __json__(self):
        return self

    def to_str(self):
        if self == 0:
            return 'REQUEST'
        elif self == 1:
            return 'GRANT'
        elif self == 2:
            return 'RELEASE'
        elif self == 3:
            return 'FAIL'
        elif self == 4:
            return 'INQUIRE'
        elif self == 5:
            return 'YIELD'
        else:
            return None
