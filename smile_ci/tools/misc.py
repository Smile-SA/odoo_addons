# -*- coding: utf-8 -*-


def s2human(time, details=False):
    for delay, desc in [(86400, 'd'), (3600, 'h'), (60, 'm')]:
        if time >= delay:
            result = str(int(time / delay)) + desc
            if details and desc == 'h':
                delta = time - int(time / delay) * delay
                result += str(int(delta / 60)).zfill(2)
            return result
    return str(int(time)) + "s"
