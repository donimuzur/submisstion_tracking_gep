from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging

_logger = logging.getLogger(__name__)

class uraianPembayaranVoucherPayable(models.Model):
    _name = 'uraian.pembayaran.voucher.payable'
    _description = 'Detail uraian Pembayran Voucher'
    
    name = fields.Char(string='Uraian Pembayaran', required=True)
    nominal = fields.Monetary(string="Nominal",default=0.0,required=True)
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                string="Company",
                                default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                 related='company_id.currency_id',
                                 default=lambda
                                 self: self.env.user.company_id.currency_id.id)
    voucher_payable_id = fields.Many2one('voucher.payable',
                            string="Voucher Payable id",
                            required=True,
                            store=True,
                            index=True,
                        )