
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_approval = fields.Boolean(string='Is Approval')
    is_verificator = fields.Boolean(string='Is Verificator')
    atasan = fields.Many2one(comodel_name='res.users', string='Supervisor')
    bawahan_ids = fields.One2many('res.users', 'atasan',string="Subordinate", help='Daftar uraian pembayaran')
    signature = fields.Binary(string='Signatures')