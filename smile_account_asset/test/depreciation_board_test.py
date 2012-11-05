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
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'years': 5, 'depreciation_start_date': '2012-01-01'}
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
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'years': 5, 'depreciation_start_date': '2012-07-01'}
        result = [
            {'book_value_wo_exceptional': 4500.0, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 500.0,
             'accumulated_value': 500.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 4500.0},
            {'book_value_wo_exceptional': 3500.0, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 1500.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 3500.0},
            {'book_value_wo_exceptional': 2500.0, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 2500.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 2500.0},
            {'book_value_wo_exceptional': 1500.0, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 3500.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 1500.0},
            {'book_value_wo_exceptional': 500.0, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 4500.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 500.0},
            {'book_value_wo_exceptional': 0.0, 'depreciation_date': datetime(2017, 12, 31, 0, 0), 'depreciation_value': 500.0,
             'accumulated_value': 5000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_degressive_depr(self):
        kwargs = {'gross_value': 5000.0, 'method': 'degressive', 'years': 5, 'degressive_rate': 35.0, 'depreciation_start_date': '2012-07-01'}
        result = [
            {'book_value_wo_exceptional': 4125.0, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 875.0,
             'accumulated_value': 875.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 4125.0},
            {'book_value_wo_exceptional': 2681.25, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1443.75,
             'accumulated_value': 2318.75, 'exceptional_value': 0.0, 'base_value': 4125.00, 'readonly': False, 'book_value': 2681.25},
            {'book_value_wo_exceptional': 1742.81, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 938.44,
             'accumulated_value': 3257.19, 'exceptional_value': 0.0, 'base_value': 2681.25, 'readonly': False, 'book_value': 1742.81},
            {'book_value_wo_exceptional': 871.41, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 871.41,
             'accumulated_value': 4128.59, 'exceptional_value': 0.0, 'base_value': 1742.81, 'readonly': False, 'book_value': 871.41},
            {'book_value_wo_exceptional': 0.0, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 871.41,
             'accumulated_value': 5000.0, 'exceptional_value': 0.0, 'base_value': 871.41, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_with_exceptional(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'years': 5, 'depreciation_start_date': '2012-07-01',
                  'exceptional_values': {'2013-05': 500.0}}
        result = [
            {'book_value_wo_exceptional': 4500.00, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 500.0,
             'accumulated_value': 500.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 4500.0},
            {'book_value_wo_exceptional': 3500.0, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 1500.0, 'exceptional_value': 500.0, 'base_value': 5000.0, 'readonly': False, 'book_value': 3000.0},
            {'book_value_wo_exceptional': 2500.0, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 2500.0, 'exceptional_value': 0.0, 'base_value': 3000.0, 'readonly': False, 'book_value': 2000.0},
            {'book_value_wo_exceptional': 1500.0, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 3500.0, 'exceptional_value': 0.0, 'base_value': 3000.0, 'readonly': False, 'book_value': 1000.0},
            {'book_value_wo_exceptional': 500.0, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 1000.0,
             'accumulated_value': 4500.0, 'exceptional_value': 0.0, 'base_value': 3000.0, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_with_readonly(self):
        kwargs = {'gross_value': 6000.0, 'method': 'linear', 'years': 4, 'depreciation_start_date': '2012-07-01',
                  'readonly_values': {'2012-12': 1500.00, '2013-12': 1500.0}}
        result = [
            {'book_value_wo_exceptional': 4500.0, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 1500.0,
             'accumulated_value': 1500.0, 'exceptional_value': 0.0, 'base_value': 6000.0, 'readonly': True, 'book_value': 4500.0},
            {'book_value_wo_exceptional': 3000.0, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1500.0,
             'accumulated_value': 3000.0, 'exceptional_value': 0.0, 'base_value': 4500.00, 'readonly': True, 'book_value': 3000.0},
            {'book_value_wo_exceptional': 2250.00, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 750.0,
             'accumulated_value': 3750.0, 'exceptional_value': 0.0, 'base_value': 3000.0, 'readonly': False, 'book_value': 2250.0},
            {'book_value_wo_exceptional': 750.0, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 1500.0,
             'accumulated_value': 5250.0, 'exceptional_value': 0.0, 'base_value': 3000.0, 'readonly': False, 'book_value': 750.0},
            {'book_value_wo_exceptional': 0.0, 'depreciation_date': datetime(2016, 12, 31, 0, 0), 'depreciation_value': 750.0,
             'accumulated_value': 6000.0, 'exceptional_value': 0.0, 'base_value': 3000.0, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_with_ro_and_exceptional(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'years': 4, 'depreciation_start_date': '2012-07-01',
                  'readonly_values': {'2012-12': 1500.00, '2013-12': 1500.0}, 'exceptional_values': {'2013-05': 500.0}}
        result = [
            {'book_value_wo_exceptional': 3500.0, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'depreciation_value': 1500.0,
             'accumulated_value': 1500.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'readonly': True, 'book_value': 3500.0},
            {'book_value_wo_exceptional': 2000.0, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'depreciation_value': 1500.0,
             'accumulated_value': 3000.0, 'exceptional_value': 500.0, 'base_value': 3500.0, 'readonly': True, 'book_value': 1500.0},
            {'book_value_wo_exceptional': 1250.0, 'depreciation_date': datetime(2014, 12, 31, 0, 0), 'depreciation_value': 750.0,
             'accumulated_value': 3750.0, 'exceptional_value': 0.0, 'base_value': 1500.0, 'readonly': False, 'book_value': 750.0},
            {'book_value_wo_exceptional': 500.0, 'depreciation_date': datetime(2015, 12, 31, 0, 0), 'depreciation_value': 750.0,
             'accumulated_value': 4500.0, 'exceptional_value': 0.0, 'base_value': 1500.0, 'readonly': False, 'book_value': 0.0}
        ]
        self._test_depreciation_board(kwargs, result)

    def test_linear_depr_with_disposal_date(self):
        kwargs = {'gross_value': 5000.0, 'method': 'linear', 'years': 5, 'depreciation_start_date': '2012-01-01', 'disposal_date': '2014-07-01'}
        result = [
            {'book_value_wo_exceptional': 4000.0, 'depreciation_date': datetime(2012, 12, 31, 0, 0), 'readonly': False, 'depreciation_value': 1000.0,
             'accumulated_value': 1000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'book_value': 4000.0},
            {'book_value_wo_exceptional': 3000.0, 'depreciation_date': datetime(2013, 12, 31, 0, 0), 'readonly': False, 'depreciation_value': 1000.0,
             'accumulated_value': 2000.0, 'exceptional_value': 0.0, 'base_value': 5000.0, 'book_value': 3000.0},
            {'book_value_wo_exceptional': 2501.37, 'depreciation_date': datetime(2014, 7, 1, 0, 0), 'readonly': False, 'depreciation_value': 498.63,
             'accumulated_value': 2498.63, 'exceptional_value': 0.0, 'base_value': 5000.0, 'book_value': 2501.37}
        ]
        self._test_depreciation_board(kwargs, result)
