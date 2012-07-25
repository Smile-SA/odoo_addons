"""
Get data with a cron:
python your_path/smile_server_monitoring/tools/plot_usage_graph.py /home/openerp/graph.log
or:
python your_path/smile_server_monitoring/tools/plot_usage_graph.py --browse_records /home/openerp/graph.log

Get the data in tabular form with:
python your_path/smile_server_monitoring/tools/plot_usage_graph.py --regroup_infos /home/openerp/graph.log
"""


import xmlrpclib
import time
import os.path


def write_infos_to_file(filename, data_type='objects', limit=0, floor=10):
    sock_common = xmlrpclib.ServerProxy('http://localhost: 8069/xmlrpc/common')
    objects_count = []
    if data_type == 'objects':
        objects_count = sock_common.gc_types_count(limit, floor)
    elif data_type == 'browse_records':
        objects_count = sock_common.gc_browse_records_count(limit, floor)
    mem_usage = sock_common.get_memory()
    if mem_usage == 'Unknown':
        mem_usage = 0
    else:
        mem_usage = int(mem_usage[: -3])
    objects_count.insert(0, ('memory', mem_usage))
    point = (time.strftime('%Y-%m-%d %H:%M:%S'), objects_count)
    with open(filename, 'a') as log:
        log.write(repr(point) + '\n')


def dump_stack_traces(path):
    sock_common = xmlrpclib.ServerProxy('http://localhost: 8069/xmlrpc/common')
    stack_traces = sock_common.get_stacks()
    filename = time.strftime('stack_%Y-%m-%d_%H%M%S.log')
    file_path = "%s/%s" % (os.path.abspath(path), filename)
    with open(file_path, 'w') as f:
        f.write(stack_traces)


def load_data_from_file(filename):
    """ Builds points=[
                (time1, [(obj1, count1a), (obj2, count2)],
                (time2, [(obj1, count1b), (obj3, count3)],
                ] from infos stored in filename with the same structure (stored via write_infos_to_file function)"""
    points = []
    with open(filename, 'r') as log:
        for line in log:
            points.append(eval(line))
    return points


def regroup_data_per_object(data):
    object_infos = {}
    for timestamp, object_count in data:
        object_count = object_count
        for objtype, nb in object_count:
            object_infos.setdefault(objtype, []).append((timestamp, nb))
    return object_infos


def has_change(time_counts, min_change=0):
    first_count = 0
    for time, count in time_counts:
        if not first_count:
            first_count = count
        if abs(first_count - count) >= min_change:
            return True
    return False


def filter_unchanging_objects(object_infos, min_change=0):
    filtered_infos = {}
    for obj_type, infos in object_infos.items():
        if has_change(infos, min_change):
            filtered_infos[obj_type] = infos
    return filtered_infos


def print_matrix(object_infos):
    obj_types = object_infos.keys()
    timestamps = set()
    for obj, time_count in object_infos.items():
        for timestamp, count in time_count:
            timestamps.add(timestamp)
    timestamps = list(timestamps)
    timestamps.sort()
    result = "\t".join(['time'] + obj_types) + '\n'
    for curr_timestamp in timestamps:
        line_infos = [curr_timestamp]
        for obj, time_count in object_infos.items():
            for timestamp, count in time_count:
                if curr_timestamp == timestamp:
                    line_infos.append(str(count))
                    break
            else:
                line_infos.append('')
        result += "\t".join(line_infos)
        result += '\n'
    print result


def regroup_per_time(object_infos):
    """ Reformat from object_infos structure to points structure """
    time_infos = {}
    for objtype, time_count in object_infos.items():
        for timestamp, nb in time_count:
            time_infos.setdefault(timestamp, []).append((objtype, nb))
    points = []
    for timestamp in sorted(time_infos):
        points.append((timestamp, time_infos[timestamp]))
    return points


if __name__ == '__main__':
    import sys

    usage = """ Usage: python plot_usage_graph.py filename [--browse_records] [--regroup_infos]"""

    if len(sys.argv) <= 1:
        print usage
        exit()
    filename = sys.argv[1]
    if len(sys.argv) == 2:
        write_infos_to_file(filename)
    elif sys.argv[2] == '--browse_records':
        write_infos_to_file(filename, 'browse_records')
    elif sys.argv[2] == '--regroup_infos':
        data = load_data_from_file(filename)
        object_infos = regroup_data_per_object(data)
        object_infos = filter_unchanging_objects(object_infos, min_change=20)
        #pprint.pprint(object_infos)
        print_matrix(object_infos)

    else:
        print usage
        exit()
