# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
import sys
if sys.version_info >= (2, 7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        raise ImportError('Please install unittest2 package')

try:
    from ..depreciation_board import DepreciationBoard
except (ImportError, ValueError):
    from depreciation_board import DepreciationBoard


class DepreciationBoardTestCase(unittest.TestCase):

    def _test_depreciation_board(self, kwargs, result):
        board = DepreciationBoard(**kwargs)
        lines = [line.__dict__ for line in board.compute()]
        self.assertEqual(lines, result)

    def test_linear_depr_starts_on_1st_day(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'periods': 5, 'depreciation_start_date': '2012-01-01'}
        result = [
            {'book_value_wo_exceptional': 4000.0, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 1000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 4000.0},
            {'book_value_wo_exceptional': 3000.0, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 2000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 3000.0},
            {'book_value_wo_exceptional': 2000.0, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 3000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 2000.0},
            {'book_value_wo_exceptional': 1000.0, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 4000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 1000.0},
            {'book_value_wo_exceptional': 0.0, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 5000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_doesnt_start_on_1st_day(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'periods': 5, 'depreciation_start_date': '2012-07-15'}
        result = [
            {'book_value_wo_exceptional': 4535.52, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 464.48,
             'accumulated_value': 464.48, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 4535.52},
            {'book_value_wo_exceptional': 3535.52, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 1464.48, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 3535.52},
            {'book_value_wo_exceptional': 2535.52, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 2464.48, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 2535.52},
            {'book_value_wo_exceptional': 1535.52, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 3464.48, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 1535.52},
            {'book_value_wo_exceptional': 535.52, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 4464.48, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 535.52},
            {'book_value_wo_exceptional': 0.0, 'depreciation_date': datetime(2017, 12, 31, 0, 0), 'depreciation_value': 535.52,
             'accumulated_value': 5000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_degressive_depr(self):
        kwargs = {'gross_value': 5000.0, 'method': 'degressive', 'periods': 5, 'degressive_rate': 35.0, 'depreciation_start_date': '2012-07-15'}
        result = [
            {'book_value_wo_exceptional': 4187.16, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 812.84,
             'accumulated_value': 812.84, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 4187.16},
            {'book_value_wo_exceptional': 2721.65, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1465.51,
             'accumulated_value': 2278.35, 'exceptional_value': 0.0, 'base_value': 4187.16, 'readonly': False, 'book_value': 2721.65},
            {'book_value_wo_exceptional': 1769.07, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 952.58,
             'accumulated_value': 3230.93, 'exceptional_value': 0.0, 'base_value': 2721.65, 'readonly': False, 'book_value': 1769.07},
            {'book_value_wo_exceptional': 884.54, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 884.54,
             'accumulated_value': 4115.46, 'exceptional_value': 0.0, 'base_value': 1769.07, 'readonly': False, 'book_value': 884.54},
            {'book_value_wo_exceptional': 0.0, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 884.54,
             'accumulated_value': 5000.0, 'exceptional_value': 0.0, 'base_value': 884.54, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_with_exceptional(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'periods': 5, 'depreciation_start_date': '2012-07-15',
                  'exceptional_values': {'2013-01': 400.0}}
        result = [
            {'book_value_wo_exceptional': 4535.52, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 464.48,
             'accumulated_value': 464.48, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 4535.52},
            {'book_value_wo_exceptional': 3535.52, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 1464.48, 'exceptional_value': 400.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 3135.52},
            {'book_value_wo_exceptional': 2490.35, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 1045.17,
             'accumulated_value': 2509.65, 'exceptional_value': 0.0, 'base_value': 3135.52, 'readonly': False, 'book_value': 2090.35},
            {'book_value_wo_exceptional': 1445.17, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 1045.17,
             'accumulated_value': 3554.83, 'exceptional_value': 0.0, 'base_value': 3135.52, 'readonly': False, 'book_value': 1045.17},
            {'book_value_wo_exceptional': 400.0, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 1045.17,
             'accumulated_value': 4600.0, 'exceptional_value': 0.0, 'base_value': 3135.52, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_with_readonly(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'periods': 4, 'depreciation_start_date': '2012-07-15',
                  'readonly_values': {'2012-01': 812.84, '2013-01': 1465.51}}
        result = [
            {'book_value_wo_exceptional': 4187.16, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 812.84,
             'accumulated_value': 812.84, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': True, 'book_value': 4187.16},
            {'book_value_wo_exceptional': 2721.65, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1465.51,
             'accumulated_value': 2278.35, 'exceptional_value': 0.0, 'base_value': 4187.16, 'readonly': True, 'book_value': 2721.65},
            {'book_value_wo_exceptional': 2089.57, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 632.08,
             'accumulated_value': 2910.43, 'exceptional_value': 0.0, 'base_value': 2721.65, 'readonly': False, 'book_value': 2089.57},
            {'book_value_wo_exceptional': 728.75, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 1360.83,
             'accumulated_value': 4271.25, 'exceptional_value': 0.0, 'base_value': 2721.65, 'readonly': False, 'book_value': 728.75},
            {'book_value_wo_exceptional': 0.0, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 728.75,
             'accumulated_value': 5000.0, 'exceptional_value': 0.0, 'base_value': 2721.65, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_with_ro_and_exceptional(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'periods': 4, 'depreciation_start_date': '2012-07-15',
                  'readonly_values': {'2012-01': 812.84, '2013-01': 1465.51}, 'exceptional_values': {'2013-01': 400.0}}
        result = [
            {'book_value_wo_exceptional': 4187.16, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 812.84,
             'accumulated_value': 812.84, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': True, 'book_value': 4187.16},
            {'book_value_wo_exceptional': 2721.65, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1465.51,
             'accumulated_value': 2278.35, 'exceptional_value': 400.0, 'base_value': 4187.16, 'readonly': True, 'book_value': 2321.65},
            {'book_value_wo_exceptional': 1560.82, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 1160.83,
             'accumulated_value': 3439.18, 'exceptional_value': 0.0, 'base_value': 2321.65, 'readonly': False, 'book_value': 1160.82},
            {'book_value_wo_exceptional': 400.0, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 1160.83,
             'accumulated_value': 4600.0, 'exceptional_value': 0.0, 'base_value': 2321.65, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_with_disposal_date(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'periods': 5, 'depreciation_start_date': '2012-01-01', 'disposal_date': '2014-07-02'}
        result = [
            {'book_value_wo_exceptional': 4000.0, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'readonly': False, 'depreciation_value': 1000.0,
             'accumulated_value': 1000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'book_value': 4000.0},
            {'book_value_wo_exceptional': 3000.0, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'readonly': False, 'depreciation_value': 1000.0,
             'accumulated_value': 2000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'book_value': 3000.0},
            {'book_value_wo_exceptional': 2500.0, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'readonly': False, 'depreciation_value': 500.0,
             'accumulated_value': 2500.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'book_value': 2500.0}
        ]
        self._test_depreciation_board(kwargs, result)
