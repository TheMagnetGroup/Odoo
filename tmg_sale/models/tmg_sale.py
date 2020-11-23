# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    decoration_method = fields.Char('Decoration Method', compute='_get_deco_method', store=True, help='Decoration method used on the sale order line')
    # printed_date = fields.Datetime(string="Date")
    @api.multi
    @api.depends('product_no_variant_attribute_value_ids')
    def _get_deco_method(self):
        """ Calculate the decoration method for this sale order line
            * decoration_method - stores the decoration method used on the order line
        """

        for line in self:
            for attribute in line.product_no_variant_attribute_value_ids:
                if attribute.attribute_id.name.strip() == "Decoration Method":
                    line.decoration_method = attribute.name

    def _compute_bom_cost(self, product_id):
        price = 0.0
        for line in product_id.product_tmpl_id.bom_id.bom_line_ids:
            if line.attribute_value_ids:
                if (set(self.product_id.attribute_value_ids.ids) & set(line.attribute_value_ids.ids) or
                    set(self.product_no_variant_attribute_value_ids.product_attribute_value_id.ids) & set(line.attribute_value_ids.ids)):
                    price += (line.product_id.standard_price * line.product_qty)
            else:
                price += (line.product_id.standard_price * line.product_qty)
        return price

    def _compute_margin(self, order_id, product_id, product_uom_id):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = order_id.pricelist_id.currency_id
        if product_id.product_tmpl_id.bom_id:
            purchase_price = self._compute_bom_cost(product_id)
        else:
            purchase_price = product_id.standard_price
        if product_uom_id != product_id.uom_id:
            purchase_price = product_id.uom_id._compute_price(purchase_price, product_uom_id)
        price = frm_cur._convert(
            purchase_price, to_cur, order_id.company_id or self.env.user.company_id,
            order_id.date_order or fields.Date.today(), round=False)
        return price

    @api.model
    def _get_purchase_price(self, pricelist, product, product_uom, date):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = pricelist.currency_id
        if product.product_tmpl_id.bom_id:
            purchase_price = self._compute_bom_cost(product)
        else:
            purchase_price = product.standard_price
        if product_uom != product.uom_id:
            purchase_price = product.uom_id._compute_price(purchase_price, product_uom)
        price = frm_cur._convert(
            purchase_price, to_cur,
            self.order_id.company_id or self.env.user.company_id,
            date or fields.Date.today(), round=False)
        return {'purchase_price': price}