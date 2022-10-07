from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging

_logger = logging.getLogger(__name__)

class UraianRencanaPenggunaanUangMuka(models.Model):
    _name = 'uraian.rencana.penggunaan.uang.muka'
    _description = 'Detail uraian rencana penggunaan uang muka'
    
    name = fields.Char(string='Uraian Penggunaan Uang Muka', required=True)
    nominal = fields.Monetary(string="Rencana",default=0.0,required=True)
    nominal_realisasi = fields.Monetary(string="Realisasi",default=0.0,required=True)
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                string="Company",
                                default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                 related='company_id.currency_id',
                                 default=lambda
                                 self: self.env.user.company_id.currency_id.id)
    voucher_kasbon_id = fields.Many2one('voucher.permintaan.kasbon',
                            string="Voucher Permintaan Kasbon",
                            required=True,
                            store=True,
                            index=True,
                        )