
import xmlrpclib
import os.path

from plot_usage_graph import write_infos_to_file, dump_stack_traces

if __name__ == '__main__':
    import sys

    usage = """ Usage: python plot_on_high_mem.py filename mem_limit [--browse_records]
    mem_limit expected in kb
    """

    if len(sys.argv) <= 2:
        print usage
        exit()
    filename = sys.argv[1]
    path = os.path.dirname(filename)
    try:
        mem_limit = int(sys.argv[2])
    except ValueError:
        print "mem_limit arg should be an integer"
        exit()

    sock_common = xmlrpclib.ServerProxy('http://localhost: 8069/xmlrpc/common')
    mem_usage = sock_common.get_memory()
    if mem_usage == 'Unknown':
        mem_usage = 0
    else:
        mem_usage = int(mem_usage[: -3])

    if len(sys.argv) == 3:
        if mem_usage >= mem_limit:
            write_infos_to_file(filename)
            dump_stack_traces(path)
    elif sys.argv[3] == '--browse_records':
        if mem_usage >= mem_limit:
            write_infos_to_file(filename, 'browse_records')
            dump_stack_traces(path)
    else:
        print usage
        exit()
