# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.tools.misc import format_date


class Company(models.Model):
    _inherit = 'res.company'

    remit_to_id = fields.Many2one('res.partner', string='Remit To', required=False)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _check_make_stub_line(self, invoice):
        """ Add invoice date to the stub line
        """
        tmg_stub_line = super(AccountPayment, self)._check_make_stub_line(invoice)

        tmg_stub_line['invoice_date'] = format_date(self.env, invoice.date_invoice)
        return tmg_stub_line

class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    cost_total = fields.Float('Cost Total', readonly=True)
    bom_type = fields.Selection([
        ('normal', 'Manufacture'),
        ('phantom', 'Kit')
        ], string='BoM Type', readonly=True)

    def _select(self):
        select_str = super(AccountInvoiceReport, self)._select()
        select_str += ', sub.cost_total'
        select_str += ', sub.bom_type'
        return select_str

    def _sub_select(self):
        select_str = super(AccountInvoiceReport, self)._sub_select()
        select_str += ', SUM(ail.quantity * irp.value_float) AS cost_total'
        select_str += ', bom.type as bom_type'
        return select_str

    def _from(self):
        from_str = super(AccountInvoiceReport, self)._from()
        from_str += """ left join ir_property irp on concat('product.product,',ail.product_id) = irp.res_id and irp.name='standard_price'"""
        from_str += ' left join mrp_bom bom on pt.id = bom.product_tmpl_id'
        return from_str

    def _group_by(self):
        group_by_str = super(AccountInvoiceReport, self)._group_by()
        group_by_str += ', bom.type'
        return group_by_str