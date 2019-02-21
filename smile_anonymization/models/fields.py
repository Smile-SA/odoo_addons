
from openerp.fields import Field

from openerp.osv.fields import function


Field.column_attrs += ['data_mask', 'data_mask_locked']


def function_new(self, _computed_field=False, **args):
    if _computed_field:
        # field is computed, we need an instance of a non-function column
        type_class = globals()[self._type]
        return type_class(**args)
    else:
        # HACK: function fields are tricky to recreate, simply return a copy
        if self.store:
            self.data_mask = args.get('data_mask', None)
            self.data_mask_locked = args.get('data_mask_locked')
        import copy
        return copy.copy(self)

function.new = function_new
