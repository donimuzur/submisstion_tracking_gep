from . import terbilang
from odoo import modules,models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64

class VoucherPertanggungjawabanKasbon(models.Model):
    _name = 'voucher.pertanggungjawaban.kasbon'
    _inherit = 'mail.thread'
    _description = 'Voucher Pertanggungjawaban Uang Muka (kasbon)'
    
    @api.model
    def _get_default_name(self):
      next= False
      sequence = self.env['ir.sequence'].search([('code','=','voucher_pertanggungjawaban_kasbon_sequence')])
      next= sequence.get_next_char(sequence.number_next_actual)   
      return next
    
    @api.model
    def create(self, values):
      res = super(VoucherPertanggungjawabanKasbon,self).create(values)
      if not res.uraian_penggunaan_uang_muka_ids:
        raise ValidationError(_('Uraian tidak boleh kosong'))
      
      res.name=self.env['ir.sequence'].next_by_code('voucher_pertanggungjawaban_kasbon_sequence')
      return res
    
    @api.multi
    def write(self, values):
      if self.state == 'onprocess' and values['diterima_oleh']:
          values["state"] = "finished"
          values["dibayar_oleh"] = self.env.uid
          values["dibayar_tanggal"] = fields.Date.today()
          values["diterima_tanggal"] = fields.Date.today()
      res = super(VoucherPertanggungjawabanKasbon,self).write(values)
      return res
    
    name = fields.Char(string='Nomor PJUM')
    tanggal = fields.Date(string='Tanggal',default=fields.Date.today())
    
    state = fields.Selection([('draft', 'Draft'),('cancelled', 'Cancelled'),('submitted', 'Submitted'),('confirmed', 'Confirmed'),('verified', 'verified'),('validated', 'Validated'),('onprocess', 'On Process'),('finished', 'Finished') ], string='Status',
      required=True, readonly=True, copy=False, default='draft', 
      track_visibility='onchange'
      )
    
    cara_pembayaran = fields.Selection(string="Cara Pembayaran", selection=[(1,'Cek / Giro / TT'),(2, 'Transfer'),(3, 'Tunai'),(4, 'Dibayar scr Bertahap')], default=3, required=True,track_visibility='onchange')
    
    bank_nama = fields.Char(string='BANK',track_visibility='onchange')
    
    Cek_billyet_no = fields.Char(string='Nomor Cek/Bilyet',track_visibility='onchange')
    Cek_billyet_tanggal = fields.Char(string='Tanggal Cek/Bilyet',track_visibility='onchange')
    
    bank_ac_name = fields.Char(string='Nama Pemilik Rek',track_visibility='onchange')
    bank_ac_no = fields.Char(string='A/C No',track_visibility='onchange')
    
    bayar_to = fields.Char(string='Nama', required=True,track_visibility='onchange')
    bayar_nik = fields.Char(string='NIK',track_visibility='onchange')
    bayar_unit_kerja = fields.Char(string='Unit Kerja',track_visibility='onchange')
    kode_anggaran = fields.Char(string='Kode Anggaran',track_visibility='onchange')
    sisa_uang_muka_lama = fields.Float(string='Kekurangan/Sisa uang Muka',track_visibility='onchange')
    total_uang = fields.Float(compute='_get_total',string='Jumlah Uang',track_visibility='onchange')
    total_uang_terbilang = fields.Char(compute='_get_terbilang',string='Terbilang',track_visibility='onchange')
    
    uraian_penggunaan_uang_muka_ids =fields.One2many('uraian.rencana.penggunaan.uang.muka', 'voucher_kasbon_id', help='Daftar uraian pembayaran', required=True,track_visibility='onchange')
    voucher_permintaan_kasbon_id = fields.Many2one(comodel_name='voucher.permintaan.kasbon', string='Voucher Permintaan Kasbon', required=True)
    
    attachment_ids = fields.Many2many('ir.attachment',  string="Attachments",track_visibility='onchange')
    
    diajukan_oleh = fields.Many2one(comodel_name='res.users', string='Yang Mempertanggungjawabkan')
    diajukan_tanggal = fields.Date(string='Diajukan Tgl')
    
    direkomendasi_oleh = fields.Many2one(comodel_name='res.users', string='Direkomendasi Oleh')
    direkomendasi_tanggal = fields.Date(string='Direkomendasi Tgl')
    
    diverifikasi_oleh= fields.Many2one(comodel_name='res.users', string='Diverifikasi Oleh')
    diverifikasi_tanggal=fields.Date(string='Diverifikasi Tgl')
        
    disetujui_oleh= fields.Many2one(comodel_name='res.users', string='Disetujui Oleh')
    disetujui_tanggal=fields.Date(string='Disetujui Tgl')
    
    dibukukan_oleh = fields.Many2one(comodel_name='res.users', string='Dibukukan Oleh')
    dibukukan_tanggal = fields.Date(string='Dibukukan Tgl')
    
    diterima_oleh = fields.Char( string='Diterima Oleh')
    diterima_tanggal = fields.Date(string='Diterima Tgl')
    
    dibayar_oleh = fields.Many2one(comodel_name='res.users', string='Dibayar Oleh')
    dibayar_tanggal = fields.Date(string='Dibayar Tgl')
    
    keterangan = fields.Text(string='Keterangan',track_visibility='onchange')
    
    active = fields.Boolean(string='active',default=True)
    is_owner = fields.Boolean(string="Is Visible Konfirmasi", compute="_get_is_owner_doc", default='_get_is_owner_doc')
    is_visible_konfimasi_button = fields.Boolean(string="Is Visible Konfirmasi", compute="_get_is_visible_konfimasi_button")
    is_visible_verifikasi_button = fields.Boolean(string="Is Visible Verifikasi", compute="_get_is_visible_verifikasi_button")
    is_visible_approval_button = fields.Boolean(string="Is Visible Approval", compute="_get_is_visible_approval_button")
    is_visible_reject_button = fields.Boolean(string="Is Visible Reject", compute="_get_is_visible_reject_button")
    
    def _get_is_visible_reject_button(self):
        self.is_visible_reject_button = False
        if self.state == 'submitted' and  self.is_visible_konfimasi_button:
            self.is_visible_reject_button=True
        if self.state == 'confirmed' and  self.is_visible_verifikasi_button:
            self.is_visible_reject_button=True
        if self.state == 'validated' and  self.is_visible_approval_button:
            self.is_visible_reject_button=True
    
    @api.onchange('voucher_permintaan_kasbon_id')
    def _compute_get_uraian_rencana(self):
        related_recordset = self.env["uraian.rencana.penggunaan.uang.muka"].search([("voucher_kasbon_id", "=",self.voucher_permintaan_kasbon_id.id)])
        self.uraian_penggunaan_uang_muka_ids = related_recordset
       
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
    
    def _get_is_visible_approval_button(self):
        self.is_visible_approval_button = False
        if  self.env.user.has_group('payment_voucher.submission_tracking_gep_group_approval') :
            self.is_visible_approval_button = True      

    @api.depends('uraian_penggunaan_uang_muka_ids')
    def _get_total(self):
        for rec_uraian in self.uraian_penggunaan_uang_muka_ids:
            self.total_uang = rec_uraian.nominal_realisasi+self.total_uang
    
    @api.depends('total_uang')
    def _get_terbilang(self):
        t = terbilang.Terbilang()
        self.total_uang_terbilang =t.terbilang(self.total_uang, "IDR", 'id')
        #self.total_uang_terbilang = payment_voucher_terbilang.terbilang(self.total_uang, "IDR", 'id')
    
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
        'diterima_oleh':NULL,
        'diterima_tanggal':NULL,
        'dibayar_oleh':NULL,
        'dibayar_tanggal':NULL
      })
      
    def konfirmasi(self):
      return self.write({
          'state': 'confirmed',
          'direkomendasi_oleh':self.env.uid,
          'direkomendasi_tanggal':fields.Date.today()
      })
      
    def verifikasi(self):
      return self.write({
          'state': 'validated',
          'diverifikasi_oleh':self.env.uid,
          'diverifikasi_tanggal':fields.Date.today()
      }) 
      
    def setujui(self):
      return self.write({
          'state': 'onprocess',
          'disetujui_oleh':self.env.uid,
          'disetujui_tanggal':fields.Date.today()
      })
      
    def action_print_voucher_pertanggungjawaban_kasbon(self):
      return self.env.ref('action_print_report_voucher_pertanggungjawaban_kasbon').report_action(self)
    

class PrintVoucherPertanggungjawabanKasbon(models.AbstractModel):
    _name = 'report.payment_voucher.report_voucher_pertanggungjawaban_kasbon'
    
    @api.model
    def _get_report_values(self,docids, data=None):
        data_voucher = self.env['voucher.pertanggungjawaban.kasbon'].search([('id', '=', docids)])
        filename = modules.get_module_resource('payment_voucher', 
        'static/src/img', 
        'header-pertanggungjawaban-kasbon-transparent.png')
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
    
    
    