from odoo import models, fields, api, exceptions
from odoo.exceptions import AccessError, UserError, RedirectWarning, \
    ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime

class SaleOrder(models.Model):

    _inherit = 'sale.order'
    order_holds = fields.Many2many('sale.hold' ,string='Order Holds')

    on_production_hold = fields.Boolean(string='On Production Hold')
    on_hold = fields.Boolean(string='On Hold')
    approved_credit = fields.Boolean(string='Approved Credit', default=False)
    had_credit_hold = fields.Boolean(string="Had Credit Hold", default=False)
    def checkSecurity(self, value):
        hasGroup = False
        for grp in value.group_ids:
            rec_dic = grp.get_external_id()
            rec_list = list(rec_dic.values())
            rec_id = rec_list[0]
            if self.env.user.has_group(rec_id):
                hasGroup = True
        if len(value.group_ids) == 0:
            hasGroup = True
        if not hasGroup:
            return False

        else:
            return True

    @api.multi
    def write(self, values):
        'Make sure to ignore any changes that do not affect order_holds'
        changed = self.filtered(
            lambda u: any(u[f] != values[f] if f in values else False
                          for f in {'order_holds'}))
        had_credit_hold = False
        for order in changed:
            note_list = []
            message_text = ''
            'Grab IDs of the records that have been changed'
            changed_holds = values['order_holds']
            # had_credit_hold = any(hol.credit_hold == True for hol in order._cache.record.order_holds)
            # has_credit_hold = False
            'Check to see if one of the changed holds is a removal'
            for cache in order._cache._record.order_holds:
                hasGroup = False
                exists = any(cache.id == hol for hol in changed_holds[0][2])

                'if it is a removal, check to see if the current user has permission to remove'
                if not exists:

                    hasGroup = self.checkSecurity(cache)
                    if not hasGroup:
                        raise Warning('Cannot delete hold due to security on hold ')
                    else:
                        note_list.append('Removed Hold ' + cache.name)
                       # message_text = message_text + 'Removed Hold ' + cache.name + ' <br/>'
            'Check to see if one of the changed holds is an addition'
            for item in changed_holds[0][2]:
                old = any(item == hol.id for hol in order.order_holds)
                if not old:
                    'if it is an additional hold, load the hold object from its ID'
                    hold_obj = self.env['sale.hold']
                    holds = hold_obj.search([('id', '=',item)])
                    # if holds.credit_hold == True:
                    #     has_credit_hold == True

                    'if it is an addition, check to see if the current user has permission to add'
                    for hold in holds:
                        hasGroup = self.checkSecurity(hold)
                        if not hasGroup:
                            raise Warning('Cannot add hold due to security on hold')
                        else:
                            note_list.append('Added Hold ' + hold.name)
                            #message_text = message_text + 'Added Hold ' + hold.name + ' <br/>'
            # if had_credit_hold:
            #     if not has_credit_hold:
            #         order.approved_credit = False
            message_text = self.create_ul_from_list(note_list)
            if message_text != '':
                order.message_post(body=message_text)

        result = super(SaleOrder, self).write(values)

        for order in self:
            credit_hold = False
            has_hold = False
            for hol in order.order_holds:


                had_hold = True

                if hol.credit_hold:
                    if not order.had_credit_hold:
                        order.had_credit_hold = True
                    credit_hold = True
                    if order.approved_credit:
                        order.approved_credit = False
                    break

            if not credit_hold:
                if order.had_credit_hold:
                    order.had_credit_hold = False
            if has_hold == True:
                order.on_hold = True
            else:
                if order.on_hold != False:
                    order.on_hold = False
        return result


    def create_ul_from_list(self, ulist):
        output = ''
        if len(ulist) > 0:
            output = '<ul>'
            for line in ulist:
                output = output + ' <li>' + line + '</li>'
            output = output + ' </ul>'
        return   output


    @api.multi
    @api.onchange('order_holds')
    def on_hold_change(self):
        for order in self:

            if len(order.order_holds) > 0:
                hasShippingBlock = False
                hasProductionBlock = False
                for hold in order.order_holds:
                    if hold.blocks_production:
                        hasProductionBlock = True
                    if hold.blocks_delivery:
                        hasShippingBlock = True
                if hasShippingBlock:
                    for pi in self.picking_ids:
                        order.picking_ids.write({'on_hold': True})
                        order.picking_ids.write({'on_hold_text': 'On Hold'})
                        order.on_hold = True
                else:
                    for pi in self.picking_ids:
                        order.picking_ids.write({'on_hold': False})
                        order.picking_ids.write({'on_hold_text': ''})
                if hasProductionBlock:
                    order.on_production_hold = True
                    order.on_hold = True
                else:
                    order.on_production_hold = False
            if len(order.order_holds) == 0:
                order.on_hold = False
            else:
                order.on_hold = True
            if any(hol.credit_hold == True for hol in order.order_holds):
                order.approved_credit = False
            else:
                if order.had_credit_hold:
                    order.approved_credit = True



    @api.multi
    def check_limit(self):

        self.ensure_one()
        partner = self.partner_id
        moveline_obj = self.env['account.move.line']
        movelines = moveline_obj.search([('partner_id', '=',
                partner.id), ('account_id.user_type_id.name', 'in',
                ['Receivable', 'Payable']), ('full_reconcile_id', '=',
                False)])



        (debit, credit) = (0.0, 0.0)

        today_dt = datetime.strftime(datetime.now().date(), DF)

        for line in movelines:
            credit += line.debit
            debit += line.credit

        if credit - debit + self.amount_total > partner.credit_limit:
            hold = self.env['sale.hold']
            hold_ids = hold.search([('credit_hold', '=', 'True')])

           # holdsObj = hold.browse(hold_ids)

           # self.order_holds.write({''}) = holdsObj

            self.order_holds = self.order_holds | hold_ids

           # res = self.write({'order_holds': holdsObj})
            # return res

    @api.multi
    def action_confirm(self):
        has_stop_hold = False
        for order in self:
            if not order.approved_credit:
                if order.payment_term_id.auto_credit_check:
                    order.check_limit()
            if len(order.order_holds) > 0:
                for hold in order.order_holds:
                    if hold.blocks_production or hold.credit_hold:
                        has_stop_hold = True

        if has_stop_hold == False:
            super(SaleOrder, self)._action_confirm()
        else: return

                            #raise Warning('Cannot add hold due to security on hold')

                            #return
