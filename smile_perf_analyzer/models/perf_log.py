# -*- coding: utf-8 -*-
# (C) 2018 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from operator import itemgetter

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.tools import config
from odoo.tools.safe_eval import safe_eval

from ..tools import perf_cursor


class IrLoggingPerfLog(models.Model):
    _name = 'ir.logging.perf.log'
    _description = 'Perf Log'
    _auto = False
    _log_access = False
    _rec_name = 'date'
    _order = 'total_time desc'

    path = fields.Char(readonly=True)
    date = fields.Datetime(readonly=True)
    uid = fields.Integer('User Id', readonly=True)
    model = fields.Char(readonly=True)
    method = fields.Char(readonly=True)
    total_time = fields.Float(
        readonly=True, digits=dp.get_precision('Logging Time'))
    db_time = fields.Float(
        'SQL requests time', readonly=True,
        digits=dp.get_precision('Logging Time'))
    db_count = fields.Integer('SQL requests count', readonly=True)
    args = fields.Text('Arguments', readonly=True)
    result = fields.Text(readonly=True)
    error = fields.Text(readonly=True)
    stats = fields.Text('Python stats', readonly=True)
    db_stats = fields.Text('SQL stats', readonly=True)
    slow_queries = fields.Text('Slow SQL queries', readonly=True)
    slow_recomputation = fields.Text(
        'Slow fields recomputation', readonly=True)

    user_id = fields.Many2one(
        'res.users', 'User', compute='_get_user', search='_search_user')
    db_stats_html = fields.Html(
        'SQL stats - Html', compute='_format_db_stats_in_html')
    slow_queries_html = fields.Html(
        'Slow SQL queries - Html',
        compute='_format_slow_queries_in_html')
    slow_recomputation_html = fields.Html(
        'Slow fields recomputation',
        compute='_format_slow_recomputation_in_html')

    @api.one
    def _get_user(self):
        self.user_id = self.env['res.users'].browse(self.uid)

    @api.model
    def _search_user(self, operator, name):
        users = self.env['res.users'].name_search(name, operator=operator)
        return [('uid', 'in', [res[0] for res in users])]

    @staticmethod
    def _format_in_html(data, header):
        if not data:
            return ''
        thead = ''
        for head in header:
            thead += '<th>%s</th>' % head
        thead = '<thead><tr>%s</tr></thead>' % thead
        tbody = ''
        for line in data:
            row = ''
            for item in line:
                row += '<td>%s</td>' % item
            tbody += '<tr>%s</tr>' % row
        tbody = '<tbody>%s</tbody>' % tbody
        return '<table class="o_list_view table table-condensed ' \
               'table-striped table-hover">' \
               '%s%s</table>' % (thead, tbody)

    @api.one
    def _format_db_stats_in_html(self):
        db_stats = safe_eval(self.db_stats)
        data = []
        for key in db_stats:
            table, statement = key
            duration, count = db_stats[key]
            data.append((table, statement, duration, count))
        data = sorted(data, key=itemgetter(2), reverse=True)
        header = _('Table'), _('Statement'), \
            _('Total time'), _('Requests count')
        self.db_stats_html = self._format_in_html(data, header)

    @api.one
    def _format_slow_queries_in_html(self):
        data = safe_eval(self.slow_queries)
        data = sorted(data, key=itemgetter(1), reverse=True)
        header = _('Slow Query'), _('Duration'), _('Trace')
        self.slow_queries_html = self._format_in_html(data, header)

    @api.one
    def _format_slow_recomputation_in_html(self):
        data = safe_eval(self.slow_recomputation)
        data = sorted(data, key=itemgetter(2), reverse=True)
        header = _('Model'), _('Field'), _('Duration'), _('Count')
        self.slow_recomputation_html = self._format_in_html(data, header)

    @api.model_cr
    def init(self):
        cr = self._cr
        with perf_cursor(cr.dbname) as new_cr:
            perf_dbname = new_cr.dbname
            new_cr.execute("SELECT relname FROM pg_class WHERE relkind "
                           "IN ('r','v') AND relname=%s",
                           (self._table,))
            if not new_cr.rowcount:
                new_cr.execute('CREATE TABLE "%s" '
                               '(id SERIAL NOT NULL, PRIMARY KEY(id))'
                               % (self._table,))
            columns = [(k, f.column_type[1])
                       for k, f in self._fields.items()
                       if f.column_type and f.store]
            for f, t in columns:
                if f == 'id':
                    continue
                new_cr.execute('SELECT c.relname '
                               'FROM pg_class c, pg_attribute a '
                               'WHERE c.relname=%s AND a.attname=%s '
                               'AND c.oid=a.attrelid',
                               (self._table, f))
                if not new_cr.rowcount:
                    new_cr.execute('ALTER TABLE "%s" ADD COLUMN "%s" %s'
                                   % (self._table, f, t))
        cr.execute('CREATE EXTENSION IF NOT EXISTS postgres_fdw')
        cr.execute("SELECT srvname FROM pg_foreign_server "
                   "WHERE srvname='perf_server'")
        if not cr.rowcount:
            db_host = config['db_host'] or 'localhost'
            db_port = str(config['db_port'] or 5432)
            cr.execute("""
                CREATE SERVER perf_server
                FOREIGN DATA WRAPPER postgres_fdw
                OPTIONS (host %s, port %s, dbname %s)
            """, (db_host, db_port, perf_dbname))
        db_user = config['db_user']
        db_password = config['db_password']
        cr.execute('DROP USER MAPPING IF EXISTS FOR %s SERVER perf_server'
                   % db_user)
        cr.execute('CREATE USER MAPPING FOR %s SERVER perf_server OPTIONS '
                   '(user %%s, password %%s)'
                   % db_user, (db_user, db_password))
        cr.execute('DROP FOREIGN TABLE IF EXISTS %s' % (self._table,))
        cr.execute('CREATE FOREIGN TABLE %s (%s) SERVER perf_server'
                   % (self._table, ', '.join('%s %s' % c for c in columns)))
        cr.commit()
