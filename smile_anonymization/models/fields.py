from openerp.fields import Field

from openerp.osv.fields import function


def function_new(self, **args):
    self.data_mask = args.get('data_mask', None)
    self.data_mask_locked = args.get('data_mask_locked')
    import copy
    return copy.copy(self)


function.new = function_new
Field.column_attrs += ['data_mask', 'data_mask_locked']
