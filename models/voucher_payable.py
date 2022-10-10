from . import terbilang
from odoo import modules,models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64
      
class VoucherPayable(models.Model):
    _name = 'voucher.payable'
    _inherit = 'mail.thread'
    _description = 'Voucher Pengeluaran Kas/Bank'
    
    @api.model
    def _get_default_name(self):
      next= False
      sequence = self.env['ir.sequence'].search([('code','=','voucher_payable_sequence')])
      next= sequence.get_next_char(sequence.number_next_actual)   
      return next
    
    # @api.model
    # def unlink(self):
    #   if self.state == 'finished':
    #      raise ValidationError(_('Tidak bisa dihapus, dokumen sudah selesai'))
    #   self.mapped('uraian_pembayaran_voucher_ids').unlink()
    #   self.mapped('attachment_ids').unlink()
    #   return super(VoucherPayable, self).unlink()       
      
    @api.model
    def create(self, values):
      res = super(VoucherPayable,self).create(values)
      if not res.uraian_pembayaran_voucher_ids:
        raise ValidationError(_('Uraian tidak boleh kosong'))
      res.name=self.env['ir.sequence'].next_by_code('voucher_payable_sequence')
      return res
        
    name = fields.Char(string='No Voucher')
    state = fields.Selection([('draft', 'Draft'),('cancelled', 'Cancelled'),('submitted', 'Submitted'),('confirmed', 'Confirmed'),('verified', 'Verified'),('validated', 'Validated'),('onprocess', 'On Process'),('finished', 'Finished') ], string='Status',
      required=True, readonly=True, copy=False, default='draft', 
      track_visibility='onchange'
      )
    
    cara_pembayaran = fields.Selection(string="Cara Pembayaran", selection=[(1,'Cek / Giro / TT'),(2, 'Transfer'),(3, 'Tunai'),(4, 'Dibayar scr Bertahap')], default=3, required=True,track_visibility='onchange')
    
    bank_nama = fields.Char(string='BANK',track_visibility='onchange')
    
    Cek_billyet_no = fields.Char(string='Nomor Cek/Bilyet',track_visibility='onchange')
    Cek_billyet_tanggal = fields.Date(string='Tanggal Cek/Bilyet',track_visibility='onchange')
    
    bank_ac_name = fields.Char(string='Nama Pemilik Rek',track_visibility='onchange')
    bank_ac_no = fields.Char(string='A/C No',track_visibility='onchange')
        
    tanggal = fields.Date(string='Tanggal',default=fields.Date.today(),track_visibility='onchange')
        
    uraian_pembayaran_voucher_ids = fields.One2many('uraian.pembayaran.voucher.payable', 'voucher_payable_id', help='Daftar uraian pembayaran', required=True,track_visibility='onchange')
        
    bpk_details_ids = fields.One2many('bpk.details.voucher.payable','voucher_id', help='Daftar BPK',track_visibility='onchange')
    
    bayar_to = fields.Char(string='Dibayarkan Kepada',required=True,track_visibility='onchange')
    bayar_alamat = fields.Char(string='Alamat',track_visibility='onchange')
    kode_anggaran = fields.Char(string='Kode Anggaran',track_visibility='onchange')
    total_uang = fields.Float(compute='_get_total',string='Jumlah Uang',track_visibility='onchange')
    total_uang_terbilang = fields.Char(compute='_get_terbilang',string='Terbilang',track_visibility='onchange')
    
    attachment_ids = fields.Many2many('ir.attachment',  string="Attachments",track_visibility='onchange')
    
    diajukan_oleh = fields.Many2one(comodel_name='res.users', string='Diajukan Oleh')
    diajukan_tanggal = fields.Date(string='Diajukan Tgl')
    
    direkomendasi_oleh = fields.Many2one(comodel_name='res.users', string='Direkomendasi Oleh')
    direkomendasi_tanggal = fields.Date(string='Direkomendasi Tgl')
    
    disetujui_oleh= fields.Many2one(comodel_name='res.users', string='Disetujui Oleh')
    disetujui_tanggal=fields.Date(string='Disetujui Tgl')
    
    diverifikasi_oleh= fields.Many2one(comodel_name='res.users', string='Diverifikasi Oleh')
    diverifikasi_tanggal=fields.Date(string='Diverifikasi Tgl')
    
    divalidasi_oleh= fields.Many2one(comodel_name='res.users', string='Divalidasi Oleh')
    divalidasi_tanggal=fields.Date(string='Divalidasi Tgl')
    
    dibukukan_oleh = fields.Many2one(comodel_name='res.users', string='Dibukukan Oleh')
    dibukukan_tanggal = fields.Date(string='Dibukukan Tgl')
    
    keterangan = fields.Text(string='Keterangan',track_visibility='onchange')
    
    active = fields.Boolean(string='active',default=True)

    is_owner = fields.Boolean(string="Is Visible Konfirmasi", compute="_get_is_owner_doc", default='_get_is_owner_doc')
    is_visible_konfimasi_button = fields.Boolean(string="Is Visible Konfirmasi", compute="_get_is_visible_konfimasi_button")
    is_visible_verifikasi_button = fields.Boolean(string="Is Visible Verifikasi", compute="_get_is_visible_verifikasi_button")
    is_visible_validasi_button = fields.Boolean(string="Is Visible Validasi", compute="_get_is_visible_validasi_button")
    is_visible_approval_button = fields.Boolean(string="Is Visible Approval", compute="_get_is_visible_approval_button")
    is_visible_reject_button = fields.Boolean(string="Is Visible Reject", compute="_get_is_visible_reject_button")
    
    def _get_is_visible_reject_button(self):
        self.is_visible_reject_button = False
        if self.state == 'submitted' and  self.is_visible_konfimasi_button:
            self.is_visible_reject_button=True
        if self.state == 'confirmed' and  self.is_visible_verifikasi_button:
            self.is_visible_reject_button=True
        if self.state == 'verified' and  self.is_visible_validasi_button:
            self.is_visible_validasi_button=True
        if self.state == 'validated' and  self.is_visible_approval_button:
            self.is_visible_reject_button=True            
    
    def _get_is_owner_doc(self):
        self.is_owner = False
        if not self.create_uid:
            self.is_owner=True
        if self.create_uid.id == self.env.uid:
            self.is_owner = True
    
    def _get_is_visible_konfimasi_button(self):
        self.is_visible_konfimasi_button = False
        if  self.diajukan_oleh in  self.env.user.bawahan_ids:
            self.is_visible_konfimasi_button = True
    
    def _get_is_visible_verifikasi_button(self):
        self.is_visible_verifikasi_button = False
        if  self.env.user.has_group('payment_voucher.submission_tracking_gep_group_verificator') :
            self.is_visible_verifikasi_button = True
    
    def _get_is_visible_validasi_button(self):
        self.is_visible_validasi_button = False
        if  self.env.user.has_group('payment_voucher.submission_tracking_gep_group_validator') :
            self.is_visible_validasi_button = True
            
    def _get_is_visible_approval_button(self):
        self.is_visible_approval_button = False
        if  self.env.user.has_group('payment_voucher.submission_tracking_gep_group_approval') :
            self.is_visible_approval_button = True      
      
    @api.depends('uraian_pembayaran_voucher_ids')
    def _get_total(self):
        for rec_uraian in self.uraian_pembayaran_voucher_ids:
            self.total_uang = rec_uraian.nominal+self.total_uang
    
    @api.depends('total_uang')
    def _get_terbilang(self):
        t = terbilang.Terbilang()
        self.total_uang_terbilang =t.terbilang(self.total_uang, "IDR", 'id')
    
    @api.multi
    def submit(self):
      state = 'submitted'
      if not self.env.user.atasan:
         state = 'confirmed'
      return self.write({
        'state': state,
        'diajukan_oleh':self.env.uid,
        'diajukan_tanggal':fields.Date.today()
        })
    
    def cancel(self):
      self.write({
        'state': 'cancelled', 
        'active':False,
      })
      return self
    
    def set_finish(self):
      return self.write({
          'state': 'finished',
        })
      
    def set_draft(self):
      return self.write({
          'active':True,
          'state': 'draft',
          'diajukan_oleh':NULL,
          'diajukan_tanggal':NULL,
          'direkomendasi_oleh':NULL,
          'direkomendasi_tanggal':NULL,
          'disetujui_oleh':NULL,
          'disetujui_tanggal':NULL,
          'diverifikasi_oleh':NULL,
          'diverifikasi_tanggal':NULL,
          'divalidasi_oleh':NULL,
          'divalidasi_tanggal':NULL
        })
      
    def konfirmasi(self):
      return self.write({
          'state': 'confirmed',
          'direkomendasi_oleh':self.env.uid,
          'direkomendasi_tanggal':fields.Date.today()
      })
      
    def verifikasi(self):
      return self.write({
          'state': 'verified',
          'diverifikasi_oleh':self.env.uid,
          'diverifikasi_tanggal':fields.Date.today()
      }) 
            
    def validasi(self):
      return self.write({
          'state': 'validated',
          'divalidasi_oleh':self.env.uid,
          'divalidasi_tanggal':fields.Date.today()
      }) 
      
    def setujui(self):
      return self.write({
          'state': 'onprocess',
          'disetujui_oleh':self.env.uid,
          'disetujui_tanggal':fields.Date.today()
      }) 
      
    @api.multi  
    def action_print_voucher_payable(self):
      return self.env.ref('payment_voucher.action_print_report_voucher_payable').report_action(self)
    
class PrintVoucherPayable(models.AbstractModel):
    _name = 'report.payment_voucher.report_voucher_payable'
    
    @api.model
    def _get_report_values(self,docids, data=None):
        data_voucher = self.env['voucher.payable'].search([('id', '=', docids)])
        filename = modules.get_module_resource('payment_voucher', 
        'static/src/img', 
        'header-transparent.png')
        f = open(filename, mode="rb")
        image = f.read()
        image = base64.b64encode(image)    
        
        
        filename_signed = modules.get_module_resource('payment_voucher', 
        'static/src/img', 
        'stamp_signed.png')
        f_signed = open(filename_signed, mode="rb")
        image_signed = f_signed.read()
        image_signed = base64.b64encode(image_signed)    
        return {
            'image' : image,  
            'image_signed':image_signed,
            'data': data_voucher
        }

class BpkDetailsVoucherPayable(models.Model):
    _name = 'bpk.details.voucher.payable'
    _description = 'list BPK Voucher Payable'
    
    nominal = fields.Monetary(string="Nominal",default=0.0,required=True,track_visibility='onchange')
    Cek_billyet_no = fields.Char(string='Nomor Cek/Bilyet',track_visibility='onchange')
    Cek_billyet_tanggal = fields.Date(string='Tanggal Cek/Bilyet',track_visibility='onchange')
    bpk_no = fields.Char(string='BPK. No.',required=True,track_visibility='onchange')
    bpk_tanggal = fields.Date(string='BPK Tanggal',required=True,track_visibility='onchange')
    company_id = fields.Many2one('res.company', store=True, copy=False,
        string="Company",
        default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
        related='company_id.currency_id',
        default=lambda
        self: self.env.user.company_id.currency_id.id)
    voucher_id = fields.Many2one('voucher.payable',
        string="Voucher Payable",
        required=True,
        store=True,
        index=True,
    )