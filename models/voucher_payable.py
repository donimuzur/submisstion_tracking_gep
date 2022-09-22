from odoo import modules,models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64

dic = {       
    'to_19' : ('Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'),
    'tens'  : ('Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'),
    'denom' : ('', 'Thousand', 'Million', 'Billion', 'Trillion', 'Quadrillion', 'Quintillion'),        
    'to_19_id' : ('Nol', 'Satu', 'Dua', 'Tiga', 'Empat', 'Lima', 'Enam', 'Tujuh', 'Delapan', 'Sembilan', 'Sepuluh', 'Sebelas', 'Dua Belas', 'Tiga Belas', 'Empat Belas', 'Lima Belas', 'Enam Belas', 'Tujuh Belas', 'Delapan Belas', 'Sembilan Belas'),
    'tens_id'  : ('Dua Puluh', 'Tiga Puluh', 'Empat Puluh', 'Lima Puluh', 'Enam Puluh', 'Tujuh Puluh', 'Delapan Puluh', 'Sembilan Puluh'),
    'denom_id' : ('', 'Ribu', 'Juta', 'Miliar', 'Triliun', 'Biliun')
}
def terbilang(number, currency, bhs):
    number = '%.2f' % number
    units_name = ' ' + cur_name(currency) + ' '
    lis = str(number).split('.')
    start_word = english_number(int(lis[0]), bhs)
    end_word = english_number(int(lis[1]), bhs)
    cents_number = int(lis[1])
    cents_name = (cents_number > 1) and 'Sen' or 'sen'
    final_result_sen = start_word + units_name + end_word +' '+cents_name
    final_result = start_word + units_name
    if end_word == 'Nol' or end_word == 'Zero':
        final_result = final_result
    else:
        final_result = final_result_sen
    
    return final_result[:1].upper()+final_result[1:]

def _convert_nn(val, bhs):
    tens = dic['tens_id']
    to_19 = dic['to_19_id']
    if bhs == 'en':
        tens = dic['tens']
        to_19 = dic['to_19']
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + ' ' + to_19[val % 10]
            return dcap

def _convert_nnn(val, bhs):
    word = ''; rat = ' Ratus'; to_19 = dic['to_19_id']
    if bhs == 'en':
        rat = ' Hundred'
        to_19 = dic['to_19']
    (mod, rem) = (val % 100, val // 100)
    if rem == 1:
        word = 'Seratus'
        if mod > 0:
            word = word + ' '   
    elif rem > 1:
        word = to_19[rem] + rat
        if mod > 0:
            word = word + ' '
    if mod > 0:
        word = word + _convert_nn(mod, bhs)
    return word

def english_number(val, bhs):
    denom = dic['denom_id']
    if bhs == 'en':
        denom = dic['denom']
    if val < 100:
        return _convert_nn(val, bhs)
    if val < 1000:
        return _convert_nnn(val, bhs)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn(l, bhs) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ' ' + english_number(r, bhs)
            if bhs == 'id':
                if val < 2000:
                    ret = ret.replace("Satu Ribu", "Seribu")
            return ret

def cur_name(cur="idr"):
    cur = cur.lower()
    if cur=="usd":
        return "Dollars"
    elif cur=="aud":
        return "Dollars"
    elif cur=="idr":
        return "Rupiah"
    elif cur=="jpy":
        return "Yen"
    elif cur=="sgd":
        return "Dollars"
    elif cur=="usd":
        return "Dollars"
    elif cur=="eur":
        return "Euro"
    else:
        return cur
      
class VoucherPayable(models.Model):
    _name = 'voucher.payable'
    _description = 'Bukti Pengeluaran Kas/Bank'
    
    @api.model
    def _get_default_name(self):
      next= False
      sequence = self.env['ir.sequence'].search([('code','=','voucher_payable_sequence')])
      next= sequence.get_next_char(sequence.number_next_actual)   
      return next
    
    @api.model
    def unlink(self):
      if self.state == 'finished':
         raise ValidationError(_('Tidak bisa dihapus, dokumen sudah selesai'))
      self.mapped('uraian_pembayaran_voucher_ids').unlink()
      return super(VoucherPayable, self).unlink()       
      
    @api.model
    def create(self, values):
      res = super(VoucherPayable,self).create(values)
      if not res.uraian_pembayaran_voucher_ids:
        raise ValidationError(_('Uraian tidak boleh kosong'))
      res.name=self.env['ir.sequence'].next_by_code('voucher_payable_sequence')
      return res
    
    @api.multi
    def write(self, values):
      if self.state == 'onprocess' and values['bpk_no']  and  values['bpk_tanggal']:
          values["state"] = "finished"
          
      
      res = super(VoucherPayable,self).write(values)
      return res
    
    name = fields.Char(string='No Voucher')
    state = fields.Selection([('draft', 'Draft'),('cancelled', 'Cancelled'),('submitted', 'Submitted'),('confirmed', 'Confirmed'),('validated', 'Validated'),('onprocess', 'On Process'),('finished', 'Finished') ], string='Status',
      required=True, readonly=True, copy=False, default='draft')
    cara_pembayaran = fields.Selection(string="Cara Pembayaran", selection=[(1,'Cheque / Giro / TT'),(2, 'Transfer'),(3, 'Tunai'),(4, 'Dibayar scr Bertahap')], default=3, required=True)
    bank_no = fields.Char(string='Nomor', index=True)
    bank_nama = fields.Char(string='BANK')
    bank_tanggal = fields.Date(string='Tanggal',default=fields.Date.today())
    bank_ac_name = fields.Char(string='Nama Pemilik Rek')
    bank_ac_no = fields.Char(string='A/C No')
    
    uraian_pembayaran_voucher_ids = fields.One2many('uraian.pembayaran.voucher.payable', 'voucher_payable_id', help='Daftar uraian pembayaran', required=True)
    
    bayar_to = fields.Char(string='Dibayarkan Kepada')
    bayar_alamat = fields.Char(string='Alamat')
    kode_anggaran = fields.Char(string='Kode Anggaran')
    total_uang = fields.Float(compute='_get_total',string='Jumlah Uang')
    total_uang_terbilang = fields.Char(compute='_get_terbilang',string='Terbilang')
    
    bpk_no = fields.Char(string='BPK. No.')
    bpk_tanggal = fields.Date(string='BPK Tanggal')
    
    attachment_ids = fields.Many2many('ir.attachment',  string="Attachments")
    
    diajukan_oleh = fields.Many2one(comodel_name='res.users', string='Diajukan Oleh')
    diajukan_tanggal = fields.Date(string='Diajukan Tgl')
    
    direkomendasi_oleh = fields.Many2one(comodel_name='res.users', string='Direkomendasi Oleh')
    direkomendasi_tanggal = fields.Date(string='Direkomendasi Tgl')
    
    disetujui_oleh= fields.Many2one(comodel_name='res.users', string='Disetujui Oleh')
    disetujui_tanggal=fields.Date(string='Disetujui Tgl')
    
    diverifikasi_oleh= fields.Many2one(comodel_name='res.users', string='Diverifikasi Oleh')
    diverifikasi_tanggal=fields.Date(string='Diverifikasi Tgl')
    
    dibukukan_oleh = fields.Many2one(comodel_name='res.users', string='Dibukukan Oleh')
    dibukukan_tanggal = fields.Date(string='Dibukukan Tgl')
    
    keterangan = fields.Text(string='Keterangan')
    
    active = fields.Boolean(string='active',default=True)
    
    @api.depends('uraian_pembayaran_voucher_ids')
    def _get_total(self):
      for rec in self:
        for rec_uraian in rec.uraian_pembayaran_voucher_ids:
            rec.total_uang = rec_uraian.nominal+rec.total_uang
    
    @api.depends('total_uang')
    def _get_terbilang(self):
      for rec in self:
        rec.total_uang_terbilang = terbilang(rec.total_uang, "IDR", 'id')
    
    
    @api.multi
    def submit(self):
      state = 'submitted'
      if not self.env.user.bawahan_ids:
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
          'state': 'draft',
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
      
    def action_print_voucher_payable(self):
      return self.env.ref('action_print_report_voucher_payable').report_action(self)
    

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




class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    def human_size(size):
      units = "Bytes,Kb,Mb,Gb,Tb,Pb,Eb,Zb,Yb".split(',')
      i = 0
      while size >= 1024:
          size /= 1024
          i += 1
      return "%.4g %s " % (size, units[i])
    
    @api.one
    @api.constrains('file_size')
    def _check_mimetype_file_size(self):
        if 'file_size' in self.env.context and self.env.context['file_size'] < self.file_size:
            raise ValidationError("Only text files smaller than %s are allowed!" % human_size(self.env.context['file_size']))