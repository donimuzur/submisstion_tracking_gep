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
        
    name = fields.Char(string='Nomor PJUM')
    tanggal = fields.Date(string='Tanggal',default=fields.Date.today())
    
    state = fields.Selection([('draft', 'Draft'),('cancelled', 'Cancelled'),('submitted', 'Submitted'),('confirmed', 'Confirmed'),('verified', 'verified'),('validated', 'Validated'),('onprocess', 'On Process'),('finished', 'Finished') ], string='Status',
      required=True, readonly=True, copy=False, default='draft', 
      track_visibility='onchange'
      )
    
    bayar_to = fields.Char(string='Nama', required=True,track_visibility='onchange')
    bayar_nik = fields.Char(string='NIK',track_visibility='onchange')
    bayar_unit_kerja = fields.Char(string='Unit Kerja',track_visibility='onchange')
    total_uang = fields.Monetary(compute='_get_total',string='Jumlah Uang Yang dipertanggungjawabkan',track_visibility='onchange')
    total_uang_diterima = fields.Monetary(compute='_get_total_diterima',string='Jumlah Uang yang diterima',track_visibility='onchange')
    total_uang_diterima_terbilang = fields.Char(compute='_get_total_diterima_terbilang',string='Terbilang',track_visibility='onchange')
    kekurangan_sisa_uang_muka = fields.Monetary(compute='_get_sisa_kekurangan_uang_muka',string='kekurangan / Sisa Uang Muka ',track_visibility='onchange')
    total_uang_terbilang = fields.Char(compute='_get_terbilang',string='Terbilang',track_visibility='onchange')
    
    uraian_penggunaan_uang_muka_ids =fields.One2many('uraian.rencana.penggunaan.uang.muka', 'voucher_kasbon_id', help='Daftar uraian pembayaran', required=True,track_visibility='onchange')
    voucher_permintaan_kasbon_id = fields.Many2one(comodel_name='voucher.permintaan.kasbon', string='Voucher Permintaan Kasbon', required=True)
    
    bpk_details_ids = fields.One2many('bpk.details.voucher.pertanggungjawaban.kasbon','voucher_pertanggungjawaban_kasbon_id', help='Daftar BPK',track_visibility='onchange')
    
    attachment_ids = fields.Many2many('ir.attachment',  string="Attachments",track_visibility='onchange')
    
    diajukan_oleh = fields.Many2one(comodel_name='res.users', string='Yang Mempertanggungjawabkan')
    diajukan_tanggal = fields.Date(string='Diajukan Tgl')
    
    direkomendasi_oleh = fields.Many2one(comodel_name='res.users', string='Direkomendasi Oleh')
    direkomendasi_tanggal = fields.Date(string='Direkomendasi Tgl')
    
    diverifikasi_oleh= fields.Many2one(comodel_name='res.users', string='Diverifikasi Oleh')
    diverifikasi_tanggal=fields.Date(string='Diverifikasi Tgl')
        
    divalidasi_oleh= fields.Many2one(comodel_name='res.users', string='Divalidasi Oleh')
    divalidasi_tanggal=fields.Date(string='Divalidasi Tgl')
    
    disetujui_oleh= fields.Many2one(comodel_name='res.users', string='Disetujui Oleh')
    disetujui_tanggal=fields.Date(string='Disetujui Tgl')
    
    dibukukan_oleh = fields.Many2one(comodel_name='res.users', string='Dibukukan Oleh')
    dibukukan_tanggal = fields.Date(string='Dibukukan Tgl')
    
    keterangan = fields.Text(string='Keterangan',track_visibility='onchange')
    
    active = fields.Boolean(string='active',default=True)

    company_id = fields.Many2one('res.company', store=True, copy=False,
        string="Company",
        default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
        related='company_id.currency_id',
        default=lambda
        self: self.env.user.company_id.currency_id.id)
    
    is_owner = fields.Boolean(string="Is Visible Konfirmasi", compute="_get_is_owner_doc", default='_get_is_owner_doc')
    is_visible_konfimasi_button = fields.Boolean(string="Is Visible Konfirmasi", compute="_get_is_visible_konfimasi_button")
    is_visible_verifikasi_button = fields.Boolean(string="Is Visible Verifikasi", compute="_get_is_visible_verifikasi_button")
    is_visible_validasi_button = fields.Boolean(string="Is Visible Validasi", compute="_get_is_visible_validasi_button")
    is_visible_approval_button = fields.Boolean(string="Is Visible Approval", compute="_get_is_visible_approval_button")
    is_visible_reject_button = fields.Boolean(string="Is Visible Reject", compute="_get_is_visible_reject_button")
    is_visible_print_button = fields.Boolean(string="Is Visible Print Button", compute="_get_is_visible_print_button")
    is_visible_set_to_finish_button = fields.Boolean(string="Is Visible Set To Finish Button", compute="_get_is_visible_set_to_finish_button")
    is_lower_than_zero = fields.Boolean(string="Is lower than zero", compute="_get_is_lower_than_zero")
    
    def _get_is_lower_than_zero(self):
      self.is_lower_than_zero = False
      if self.kekurangan_sisa_uang_muka < 0 :
        self.is_lower_than_zero = True
    
    def _get_is_visible_set_to_finish_button(self):
        self.is_visible_set_to_finish_button = False
        if self.bpk_details_ids and self.is_visible_verifikasi_button:
          self.is_visible_set_to_finish_button = True  
            
    def _get_is_visible_reject_button(self):
        self.is_visible_reject_button = False
        if self.state == 'submitted' and  self.is_visible_konfimasi_button:
            self.is_visible_reject_button=True
        if self.state == 'confirmed' and  self.is_visible_verifikasi_button:
            self.is_visible_reject_button=True
        if self.state == 'verified' and  self.is_visible_validasi_button:
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
    
    def _get_is_visible_validasi_button(self):
        self.is_visible_validasi_button = False
        if  self.env.user.has_group('payment_voucher.submission_tracking_gep_group_validator') :
            self.is_visible_validasi_button = True
          
    def _get_is_visible_approval_button(self):
        self.is_visible_approval_button = False
        if  self.env.user.has_group('payment_voucher.submission_tracking_gep_group_approval') :
            self.is_visible_approval_button = True       

    def _get_is_visible_print_button(self):
        self.is_visible_print_button = False
        if self.bpk_details_ids and self.is_visible_verifikasi_button:
          self.is_visible_print_button = True  
          
    @api.depends('uraian_penggunaan_uang_muka_ids')
    def _get_total(self):
        for rec_uraian in self.uraian_penggunaan_uang_muka_ids:
            self.total_uang = rec_uraian.nominal_realisasi+self.total_uang
            
    @api.depends('uraian_penggunaan_uang_muka_ids')
    def _get_total_diterima(self):
        for rec_uraian in self.uraian_penggunaan_uang_muka_ids:
            self.total_uang_diterima = rec_uraian.nominal+self.total_uang_diterima
                
    @api.depends('uraian_penggunaan_uang_muka_ids')
    def _get_sisa_kekurangan_uang_muka(self):
      self.kekurangan_sisa_uang_muka = abs(self.total_uang_diterima - self.total_uang)
          
    @api.depends('total_uang')
    def _get_terbilang(self):
      t = terbilang.Terbilang()
      self.total_uang_terbilang =t.terbilang(self.total_uang, "IDR", 'id')
    
    @api.depends('total_uang_diterima')
    def _get_total_diterima_terbilang(self):
      t = terbilang.Terbilang()
      self.total_uang_diterima_terbilang =t.terbilang(self.total_uang_diterima, "IDR", 'id')
                
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
          'state': 'finished'
        })
          
    def set_draft(self):
      return self.write({
        'active':True,
        'state': 'draft',
        'diajukan_oleh':None,
        'diajukan_tanggal':None,
        'direkomendasi_oleh':None,
        'direkomendasi_tanggal':None,
        'disetujui_oleh':None,
        'disetujui_tanggal':None,
        'diverifikasi_oleh':None,
        'diverifikasi_tanggal':None,
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
      
    def reject(self):
      return self.write({
          'state': 'draft',
          'diajukan_oleh':None,
          'diajukan_tanggal':None,
          'direkomendasi_oleh':None,
          'direkomendasi_tanggal':None,
          'disetujui_oleh':None,
          'disetujui_tanggal':None,
          'diverifikasi_oleh':None,
          'diverifikasi_tanggal':None,
          'divalidasi_oleh':None,
          'divalidasi_tanggal':None,
          'keterangan':None
      }) 
            
    def add_bpk(self): 
      return {    
        'name': "Tambah BPK",
        'type': 'ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'form',
        'res_model': 'bpk.details.voucher.pertanggungjawaban.kasbon',
        'target': 'new',
        'context': {'default_voucher_pertanggungjawaban_kasbon_id': self.id, 'default_nominal': self.kekurangan_sisa_uang_muka}
      }
      
      
    def action_print_voucher_pertanggungjawaban_kasbon(self):
      return self.env.ref('payment_voucher.action_print_report_voucher_pertanggungjawaban_kasbon').report_action(self)
    

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
    

class BpkDetailsVoucherPertanggungjawabanKasbon(models.Model):
    _name = 'bpk.details.voucher.pertanggungjawaban.kasbon'
    _description = 'list BPK Voucher Pertanggungjawaban Kasbon'
    
    nominal = fields.Monetary(string="Nominal",default=0.0,required=True)
    bpk_no = fields.Char(string='BPK. No.',required=True)
    bpk_tanggal = fields.Date(string='BPK Tanggal',required=True)
    
    cara_pembayaran = fields.Selection(string="Cara Pembayaran", selection=[(1,'Cek / Giro / TT'),(2, 'Transfer'),(3, 'Tunai')], default=3, required=True)
        
    Cek_billyet_no = fields.Char(string='Nomor Cek/Bilyet')
    Cek_billyet_tanggal = fields.Date(string='Tanggal Cek/Bilyet')
    
    bank_account_ids = fields.Many2one('master.config.bank.account', store=True, copy=False,
        string="Nomer Account")
    
    diterima_oleh = fields.Char( string='Diterima Oleh',track_visibility='onchange')
    diterima_tanggal = fields.Date(string='Diterima Tgl',track_visibility='onchange')
    
    company_id = fields.Many2one('res.company', store=True, copy=False,
        string="Company",
        default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
        related='company_id.currency_id',
        default=lambda
        self: self.env.user.company_id.currency_id.id)
    voucher_pertanggungjawaban_kasbon_id = fields.Many2one('voucher.pertanggungjawaban.kasbon',
        string="Voucher Pertanggungjawaban Kasbon",
        required=True,
        store=True,
        index=True,
    )
    
    @api.onchange('cara_pembayaran')
    def _onchange_cara_pembayaran(self):
      self.Cek_billyet_no = None      
      self.Cek_billyet_tanggal = None