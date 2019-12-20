# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

class Partner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _get_default_payment_term(self):
        if self.customer:
            payments = self.env['account.payment.term']
            payment = payments.search([('default_credit_terms', '=', True)])
            self.property_payment_term_id = payment
            self.credit_limit = payment.default_credit_limit
        return payment

    credit_limit = fields.Monetary(string="Credit Limit")
    property_payment_term_id = fields.Many2one('account.payment.term', default=_get_default_payment_term, company_dependent=True,
                                               string='Customer Payment Terms',ondelete='restrict',
                                               help="This payment term will be used instead of the default one for sales orders and customer invoices",
                                               )



    @api.onchange('customer')
    def _set_default_payment_term(self):
        if self.customer:
            if self.property_payment_term_id.id == False:
                payments = self.env['account.payment.term']
                payment = payments.search([('default_credit_terms', '=', True)])
                self.property_payment_term_id = payment
                self.credit_limit = payment.default_credit_limit

    @api.model
    def create(self, values):
        if values['customer']:
            if 'property_payment_term_id' not in values:
                payments = self.env['account.payment.term']
                payment = payments.search([('default_credit_terms', '=', True)])
                values.update({'property_payment_term_id': payment.id})
                values.update({'credit_limit': payment.default_credit_limit})

        result = super(Partner, self).create(values)
        return result
