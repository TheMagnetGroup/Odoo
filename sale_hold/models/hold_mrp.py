# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError

class hold_mrp(models.Model):
    _inherit = 'mrp.production'
    on_hold = fields.Boolean(string="On Hold")



    @api.multi
    def record_production(self):
        if self.on_hold:
            raise UserError('This order has holds preventing processing.')

        ret = super(hold_mrp, self).record_production()
        return ret

    @api.multi
    def button_plan(self):
        if self.on_hold:
            raise UserError('This order has holds preventing processing.')

        ret = super(hold_mrp, self).button_plan()
        return ret