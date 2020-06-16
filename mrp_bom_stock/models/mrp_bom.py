# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class MrpBomLine(models.Model):
    _inherit = "mrp.bom.line"

    to_exclude = fields.Boolean(string="Exclude in On-hand Calculation")

    def is_shared(self):
        return True if (not self.attribute_value_ids) else False
