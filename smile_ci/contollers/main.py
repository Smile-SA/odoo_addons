# -*- coding: utf-8 -*-

import hashlib
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextToPath
import werkzeug

from odoo.http import Controller, request, route
from odoo.tools import ustr

last_update = '__last_update'


class CiController(Controller):

    def get_build_infos(self, repo_id, branch, kpi):
        domain = [
            ('branch_id.repository_id', '=', repo_id),
            ('branch_id.branch', '=', branch),
            ('state', '!=', 'pending'),
            ('result', '!=', 'killed'),
        ]
        Build = request.env['scm.repository.branch.build'].sudo()
        builds = Build.search_read(domain, ['state', kpi, last_update], limit=1)
        if not builds:
            return {}
        return builds[0]

    def render_badge(self, theme, left_text, right_text, color, build):
        def text_width(s):
            fp = FontProperties(family='DejaVu Sans', size=11)
            w, h, d = TextToPath().get_text_width_height_descent(s, fp, False)
            return int(w + 1)

        class Text(object):
            __slot__ = ['text', 'color', 'width']

            def __init__(self, text, color):
                self.text = ustr(text)
                self.color = color
                self.width = text_width(self.text) + 10

        etag = request.httprequest.headers.get('If-None-Match')
        retag = hashlib.md5(build[last_update]).hexdigest()
        if etag == retag:
            return werkzeug.wrappers.Response(status=304)
        data = {
            'left': Text(left_text, '#555'),
            'right': Text(right_text, color),
        }
        max_age = 5 * 60  # five minutes
        cache_factor = build['state'] == 'testing' and 1 or 2
        headers = [
            ('Content-Type', 'image/svg+xml'),
            ('Cache-Control', 'max-age=%d' % (max_age * cache_factor,)),
            ('ETag', retag),
        ]
        return request.render("smile_ci.badge_" + theme, data, headers=headers)

    @route([
        '/smile_ci/badge/<int:repo_id>/<branch>.svg',
        '/smile_ci/badge/<any(default,flat):theme>/<int:repo_id>/<branch>.svg',
    ], type="http", auth="public", methods=['GET', 'HEAD'])
    def badge(self, repo_id, branch, theme='default'):
        # Inspired by https://github.com/odoo/odoo-extra/blob/master/runbot/runbot.py
        build = self.get_build_infos(repo_id, branch, 'result')
        if not build:
            return request.not_found()
        if build['state'] == 'testing':
            state = 'testing'
        else:
            state = build['result']
        color = {
            'testing': "#007ec6",
            'stable': "#44cc11",
            'unstable': "#dfb317",
            'failed': "#e05d44",
        }[state]
        return self.render_badge(theme, branch, state, color, build)

    @route([
        '/smile_ci/badge/tests/<int:repo_id>/<branch>.svg',
        '/smile_ci/badge/tests/<any(default,flat):theme>/<int:repo_id>/<branch>.svg',
    ], type="http", auth="public", methods=['GET', 'HEAD'])
    def badge_tests(self, repo_id, branch, theme='default'):
        build = self.get_build_infos(repo_id, branch, 'failed_test_ratio')
        if not build:
            return request.not_found()
        if build['state'] == 'testing':
            failed_test_ratio = 'n/a'
            color = '#9b9b9b'
        else:
            failed_test_ratio = build['failed_test_ratio']
            color = '#44cc11'
            failed_tests, all_tests = failed_test_ratio.split(' / ')
            if int(failed_tests):
                color = '#e05d44'
            if not int(all_tests):
                color = '#dfb317'
        return self.render_badge(theme, 'Failed tests', failed_test_ratio, color, build)

    @route([
        '/smile_ci/badge/quality/<int:repo_id>/<branch>.svg',
        '/smile_ci/badge/quality/<any(default,flat):theme>/<int:repo_id>/<branch>.svg',
    ], type="http", auth="public", methods=['GET', 'HEAD'])
    def badge_quality(self, repo_id, branch, theme='default'):
        build = self.get_build_infos(repo_id, branch, 'quality_code_count')
        if not build:
            return request.not_found()
        if build['state'] == 'testing':
            quality_code_count = 'n/a'
            color = '#9b9b9b'
        else:
            quality_code_count = build['quality_code_count']
            color = '#44cc11'
            if quality_code_count:
                color = '#e05d44'
        return self.render_badge(theme, 'Quality errors', quality_code_count, color, build)

    @route([
        '/smile_ci/badge/coverage/<int:repo_id>/<branch>.svg',
        '/smile_ci/badge/coverage/<any(default,flat):theme>/<int:repo_id>/<branch>.svg',
    ], type="http", auth="public", methods=['GET', 'HEAD'])
    def badge_coverage(self, repo_id, branch, theme='default'):
        build = self.get_build_infos(repo_id, branch, 'coverage_avg')
        if not build:
            return request.not_found()
        if build['state'] == 'testing':
            coverage = 'n/a'
            color = '#9b9b9b'
        else:
            color = '#44cc11'
            coverage_avg = build['coverage_avg']
            if coverage_avg < 50.0:
                color = '#e05d44'
            elif coverage_avg < 75.0:
                color = '#dfb317'
            coverage = '%s%%' % coverage_avg
        return self.render_badge(theme, 'Coverage', coverage, color, build)
