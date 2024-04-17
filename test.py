from easy_utils_dev.utils import getTimestamp

now = getTimestamp()
later = getTimestamp(5)

print( now > later )

import time
time.sleep(10)
now = getTimestamp()

print( now > later )
