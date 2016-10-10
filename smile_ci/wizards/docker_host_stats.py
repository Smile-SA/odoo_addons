# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DockerHostStats(models.TransientModel):
    _name = 'docker.host.stats'
    _description = 'Docker Host Stats'
    _rec_name = 'docker_host_id'
    _order = 'create_date desc'
    _transient_max_hours = 24 * 3  # max 3 days
    _transient_max_count = 50 * 60 * _transient_max_hours  # max 50 containers each minute

    docker_host_id = fields.Many2one('docker.host', 'Docker host', required=True, readonly=True)
    container = fields.Char('CONTAINER', required=True, readonly=True)
    create_date = fields.Datetime('Created on', readonly=True)
    cpu_usage = fields.Float('CPU %', digits=(5, 2))
    mem_usage = fields.Integer('MEM USAGE (MiB)')
    mem_limit = fields.Integer('MEM LIMIT (MiB)', group_operator='avg')
    mem_percent = fields.Float('MEM %', digits=(5, 2))
    mem_percent_max = fields.Float('MAX %', digits=(5, 2))
    network_input = fields.Float('NETWORK INPUT (MiB)', digits=(16, 3))
    network_output = fields.Float('NETWORK OUTPUT (MiB)', digits=(16, 3))

    @api.model
    def compute_stats(self):
        def compute_MiB(value):
            return round(float(value) / 1024**2, 3)

        for docker_host in self.env['docker.host'].search([]):
            containers = docker_host.get_containers()
            container_names = map(lambda cont: cont['Names'][0].replace('/', ''), containers)
            for container in sorted(container_names):
                stats_gen = docker_host.get_container_stats(container, decode=True)
                pre_stats = stats_gen.next()
                stats = stats_gen.next()
                self.create({
                    'docker_host_id': docker_host.id,
                    'container': container,
                    'cpu_usage': (stats['cpu_stats']['cpu_usage']['total_usage'] -
                                  pre_stats['cpu_stats']['cpu_usage']['total_usage']) * 100.0 /
                                 (stats['cpu_stats']['system_cpu_usage'] -
                                  pre_stats['cpu_stats']['system_cpu_usage']),
                    'mem_usage': compute_MiB(stats['memory_stats']['usage']),
                    'mem_limit': compute_MiB(stats['memory_stats']['limit']),
                    'mem_percent': stats['memory_stats']['usage'] * 100.0 / stats['memory_stats']['limit'],
                    'mem_percent_max': stats['memory_stats']['max_usage'] * 100.0 / stats['memory_stats']['limit'],
                    'network_input': compute_MiB(sum(network['rx_bytes'] for network in stats['networks'].itervalues())),
                    'network_output': compute_MiB(sum(network['tx_bytes'] for network in stats['networks'].itervalues())),
                })
        return True
