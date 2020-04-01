# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError

class hold_mrp(models.Model):
    _inherit = 'mrp.production'
    on_hold = fields.Boolean(string="On Hold")
    on_hold_text = fields.Char(string="On Hold Text")


    @api.multi
    def record_production(self):
        if self.on_hold:
            raise UserError('This order has holds preventing processing.')

        ret = super(hold_mrp, self).record_production()
        return ret

    @api.multi
    @api.depends('on_hold')
    def update_on_change_text(self):
        for order in self:
            for pick in order.picking_ids:
                if order.on_hold:
                    pick.on_hold = True
                else:
                    pick.on_hold = False

    @api.multi
    def button_plan(self):
        if self.on_hold:
            raise UserError('This order has holds preventing processing.')

        ret = super(hold_mrp, self).button_plan()
        return ret

    @api.multi
    def produce_product(self):
        if self.on_hold:
            raise UserError('This order has holds preventing processing.')

        ret = super(hold_mrp, self).produce_product()
        return ret

    @api.multi
    def open_produce_product(self):
        if self.on_hold:
            raise UserError('This order has holds preventing processing.')

        ret = super(hold_mrp, self).open_produce_product()
        return ret