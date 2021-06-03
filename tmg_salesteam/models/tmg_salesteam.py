# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # this instruction "blanks-out" the Sales Team when Customer (i.e. partner_id) is blank
    # ... (e.g. when beginning CREATE() of a sales order)
    team_id = fields.Many2one(default=fields.Integer(0))


class tmg_salesteam(models.Model):
    _inherit = 'crm.team'

    team_member_ids = fields.Many2many('res.users', 'team_member_id_rel', 'member_id', 'user_id', string='Channel Team Members', domain= lambda self: [('groups_id', 'in', self.env.ref('base.group_user').id)], help="Add members to the sales team.")

    @api.multi
    def name_get(self):
        result = []
        for team in self:
            result.append((team.id, "%s (%s)" % (team.name, team.user_id.name if team.user_id.name else "N/A")))
        return result

class tmg_crmlead(models.Model):
    _inherit = 'crm.lead'

    # Disable changing sales team when user is changed
    @api.onchange('user_id')
    def _onchange_user_id(self):
        return

    @api.constrains('user_id')
    @api.multi
    def _valid_team(self):
        return

class tmg_team_users(models.Model):
    _inherit = 'res.users'

    user_team_ids = fields.Many2many('crm.team', 'team_member_id_rel', 'user_id', 'member_id', string='User Teams')
