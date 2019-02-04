from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    planned_amount_sign = fields.Selection([
        ('positive', '+ '),
        ('negative', '-'),
    ], string="Planned Amount Sign", help="Make you able to choose if you want to enter budgets planned"
                                         " amount in a positive or negative form .", default="negative")

    @api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(planned_amount_sign=params.get_param('planned_amount_sign', default="negative"))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("planned_amount_sign", self.planned_amount_sign)
