from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
import barcode
from barcode.writer import ImageWriter
_logger = logging.getLogger(__name__)


class DokumenLampiran(models.Model):
    _name = 'dokumen.lampiran'
    _description = 'Dokumen yang dilampirkan'
    
    name = fields.Char(string='name')
    dokumen_type = fields.Char(string='Tipe Dokumen ',required=True)
    jenis_dokumen = fields.Selection(string="Cara Pembayaran", selection=[(1,'Request to Purhchase (RP)'),
                                                                          (2,'Purchase Order (PO)'),
                                                                          (3,'Surat Perintah Kerja (SPK)'),
                                                                          (4,'Surat Jalan'),
                                                                          (5,'Kwitansi/Invoice'),
                                                                          (6,'Faktur Pajak'),
                                                                          (7,'Tanda Terima Barang'),
                                                                          (8,'Debit Nota'),
                                                                          (9,'Lain - lain')], default=3)
    