# -*- coding: utf-8 -*-
"""
Used to regularly dump stacks from server
Usage: python dump_stacks.py
"""


import xmlrpclib
import time


nb_stacks = 10
host = 'localhost'
port = 8069
# http or https
protocol = 'http'
# in seconds
wait_time = 10
log_filename = 'stack_logs_%s' % time.strftime('%Y%m%d_%H%M%S')

path = '{protocol}://{host}:{port}/xmlrpc/common'.format(protocol=protocol, host=host, port=port)
print 'Using %s' % path
print 'Dumping {nb_stacks} stacks every {wait_time} seconds in {log_filename}'.format(nb_stacks=nb_stacks,
                                                                                      wait_time=wait_time,
                                                                                      log_filename=log_filename)

sock = xmlrpclib.ServerProxy(path)
separator = '#' * 50

with open(log_filename, 'w') as log_file:
    for i in xrange(nb_stacks):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        stack = sock.get_stacks()
        log_file.write('{separator} {timestamp}\n{stack}\n'.format(separator=separator,
                                                                   timestamp=timestamp,
                                                                   stack=stack))
        time.sleep(wait_time)
        print '%s / %s stacks captured' % (i + 1, nb_stacks)
