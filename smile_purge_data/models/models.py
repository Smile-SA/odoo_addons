# (C) 2021 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import logging

from odoo.models import BaseModel as OdooBaseModel


_logger = logging.getLogger(__name__)


odoo_unlink = OdooBaseModel.unlink


def unlink(self):
    """
    If dry-run is set in context
    Do not delete records but return the list of records that would be deleted
    """
    if self.env.context.get("dry_run"):
        _logger.debug("Dry-run: %s %s", self._name, self.ids)
        return self
    else:
        return odoo_unlink(self)


OdooBaseModel.unlink = unlink
