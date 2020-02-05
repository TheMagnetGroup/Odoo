# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class Partner(models.Model):
    _inherit = "res.partner"
    default_ups_third_party = fields.Char(string="UPS Account")
    default_fedex_third_party = fields.Char(string="Fedex Account")
    attention_to = fields.Char(string="Attention To")