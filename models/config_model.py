from odoo import modules,models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64
      
class MasterConfigBankAccount(models.Model):
    _name = 'master.config.bank.account'
    _inherit = 'mail.thread'
    _description = 'Master Configuration Bank Account'
    
    name = fields.Char(string='Nama Bank')
    bank_ac_name = fields.Char(string='Nama Pemilik Rek',track_visibility='onchange')
    bank_ac_no = fields.Char(string='A/C No',track_visibility='onchange')
    
    @api.multi
    def name_get(self):
        res = []
        for value in self:
            res.append([value.id, "%s-%s" % (value.bank_ac_name, value.name)])
        return res