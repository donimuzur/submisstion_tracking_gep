from odoo import modules,models, fields, api, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import base64

class Dashboard(models.Model):
    _name = 'dokumen.dashboard'
    _auto = False
    _description = 'List dokumen menunggu untuk di verifikasi'

    name = fields.Char(string='Nomor Dokumen')
    type_dokumen = fields.Char(string='Tipe Dokumen')
    state = fields.Selection([('draft', 'Draft'),('cancelled', 'Cancelled'),('submitted', 'Submitted'),('confirmed', 'Confirmed'),('verified', 'Verified'),('validated', 'Validated'),('onprocess', 'On Process'),('finished', 'Finished') ], string='Status',
      required=True, readonly=True, copy=False, default='draft', 
      track_visibility='onchange'
      )
    
    diajukan_oleh = fields.Many2one(comodel_name='res.users', string='Diajukan Oleh')
    diajukan_tanggal = fields.Date(string='Diajukan Tgl')
    
    is_visible_konfimasi_button = fields.Boolean(string="Is Visible Konfirmasi", compute="_get_is_visible_konfimasi_button")
    is_visible_verifikasi_button = fields.Boolean(string="Is Visible Verifikasi", compute="_get_is_visible_verifikasi_button")
    is_visible_validasi_button = fields.Boolean(string="Is Visible Validasi", compute="_get_is_visible_validasi_button")
    is_visible_approval_button = fields.Boolean(string="Is Visible Approval", compute="_get_is_visible_approval_button")
                
    def _get_is_visible_konfimasi_button(self):
        for rec in self :
            rec.is_visible_konfimasi_button = False
            if  rec.diajukan_oleh in  rec.env.user.bawahan_ids:
                rec.is_visible_konfimasi_button = True
    
    def _get_is_visible_verifikasi_button(self):
        for rec in self :
            rec.is_visible_verifikasi_button = False
            if  rec.env.user.has_group('payment_voucher.submission_tracking_gep_group_verificator') :
                rec.is_visible_verifikasi_button = True
    
    def _get_is_visible_validasi_button(self):
        for rec in self :
            rec.is_visible_validasi_button = False
            if  rec.env.user.has_group('payment_voucher.submission_tracking_gep_group_validator') :
                rec.is_visible_validasi_button = True
    
    def _get_is_visible_approval_button(self):
        for rec in self :
            rec.is_visible_approval_button = False
            if  rec.env.user.has_group('payment_voucher.submission_tracking_gep_group_approval') :
                rec.is_visible_approval_button = True      

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            """
            CREATE or REPLACE VIEW %s as 
            select 
                ROW_NUMBER () OVER (ORDER BY list_dokumen.diajukan_tanggal) as id,* from 
                (
                    select  name, 'Voucher Payable' as type_dokumen , diajukan_tanggal, diajukan_oleh, state from voucher_payable where state not in ( 'draft','finished', 'cancelled')
                    union
                    select  name, 'Voucher Permintaan Kasbon' as type_dokumen , diajukan_tanggal, diajukan_oleh,  state  from voucher_permintaan_kasbon where state  not in ( 'draft','finished', 'cancelled')
                    union
                    select  name, 'Voucher Pertanggungjawaban Kasbon' as type_dokumen , diajukan_tanggal, diajukan_oleh,  state  from voucher_pertanggungjawaban_kasbon  where state  not in ( 'draft','finished', 'cancelled')
                ) as list_dokumen 
            order by list_dokumen.diajukan_tanggal desc
            """ % (self._table)
        )

    @api.multi
    def button_lihat_doc(self):
        model_type = ""
        model_name = ""
        model_type_view =""
        if self.type_dokumen == "Voucher Payable":
            model_type = "voucher.payable"
            model_type_view = "voucher_payable_view_form"
        if self.type_dokumen == "Voucher Permintaan Kasbon":
            model_type = "voucher.permintaan.kasbon"
            model_type_view = "voucher_permintaan_kasbon_view_form"
        if self.type_dokumen == "Voucher Pertanggungjawaban Kasbon":
            model_type = "voucher.pertanggungjawaban.kasbon"
            model_type_view = "voucher_pertanggungjawaban_kasbon_view_form"
            
        records = self.env[model_type].search([('name','=',self.name)], limit=1)
        if not records:
            raise UserError(_("terjadi kesalahan, silahkan hubungi administrator "))
        # raise UserError(_('%s' %records.name))  
        return {
            'res_model' : model_type,
            'res_id'    : records.id,
            'name'      : self.type_dokumen,
            'type'      : 'ir.actions.act_window',
            'view_mode' : 'form',
            'view_type': 'form',
            'flags': {'form': {'action_buttons': False,'create':False, 'Edit':False}}
        }
        
    def button_konfirmasi_doc(self):
        model_type = ""
        model_name = ""
        model_type_view =""
        if self.type_dokumen == "Voucher Payable":
            model_type = "voucher.payable"
            model_type_view = "voucher_payable_view_form"
        if self.type_dokumen == "Voucher Permintaan Kasbon":
            model_type = "voucher.permintaan.kasbon"
            model_type_view = "voucher_permintaan_kasbon_view_form"
        if self.type_dokumen == "Voucher Pertanggungjawaban Kasbon":
            model_type = "voucher.pertanggungjawaban.kasbon"
            model_type_view = "voucher_pertanggungjawaban_kasbon_view_form"
            
        records = self.env[model_type].search([('name','=',self.name)], limit=1)
        
        if not records:
            raise UserError(_("terjadi kesalahan, silahkan hubungi administrator "))
        
        records.write({
            'state': 'confirmed',
            'direkomendasi_oleh':self.env.uid,
            'direkomendasi_tanggal':fields.Date.today()
        })
        
        return {
            'name'      : 'DASHBOARD',
            'type'      : 'ir.actions.act_window',
            'view_type' : 'kanban',
            'view_mode' : 'kanban',
            'res_model' : 'dokumen.dashboard',
            'target'    : 'current',
        }
        
    def button_verifikasi_doc(self):
        model_type = ""
        model_name = ""
        model_type_view =""
        if self.type_dokumen == "Voucher Payable":
            model_type = "voucher.payable"
            model_type_view = "voucher_payable_view_form"
        if self.type_dokumen == "Voucher Permintaan Kasbon":
            model_type = "voucher.permintaan.kasbon"
            model_type_view = "voucher_permintaan_kasbon_view_form"
        if self.type_dokumen == "Voucher Pertanggungjawaban Kasbon":
            model_type = "voucher.pertanggungjawaban.kasbon"
            model_type_view = "voucher_pertanggungjawaban_kasbon_view_form"
            
        records = self.env[model_type].search([('name','=',self.name)], limit=1)
        
        if not records:
            raise UserError(_("terjadi kesalahan, silahkan hubungi administrator "))
        
        records.write({
            'state': 'verified',
            'diverifikasi_oleh':self.env.uid,
            'diverifikasi_tanggal':fields.Date.today()
        })
        
        return {
            'name'      : 'DASHBOARD',
            'type'      : 'ir.actions.act_window',
            'view_type' : 'kanban',
            'view_mode' : 'kanban',
            'res_model' : 'dokumen.dashboard',
            'target'    : 'current',
        }
     
        
    def button_validasi_doc(self):
        model_type = ""
        model_name = ""
        model_type_view =""
        if self.type_dokumen == "Voucher Payable":
            model_type = "voucher.payable"
            model_type_view = "voucher_payable_view_form"
        if self.type_dokumen == "Voucher Permintaan Kasbon":
            model_type = "voucher.permintaan.kasbon"
            model_type_view = "voucher_permintaan_kasbon_view_form"
        if self.type_dokumen == "Voucher Pertanggungjawaban Kasbon":
            model_type = "voucher.pertanggungjawaban.kasbon"
            model_type_view = "voucher_pertanggungjawaban_kasbon_view_form"
            
        records = self.env[model_type].search([('name','=',self.name)], limit=1)
        
        if not records:
            raise UserError(_("terjadi kesalahan, silahkan hubungi administrator "))
        
        records.write({
            'state': 'validated',
            'divalidasi_oleh':self.env.uid,
            'divalidasi_tanggal':fields.Date.today()
        })
        
        return {
            'name'      : 'DASHBOARD',
            'type'      : 'ir.actions.act_window',
            'view_type' : 'kanban',
            'view_mode' : 'kanban',
            'res_model' : 'dokumen.dashboard',
            'target'    : 'current',
        }
           
    def button_setujui_doc(self):
        model_type = ""
        model_name = ""
        model_type_view =""
        if self.type_dokumen == "Voucher Payable":
            model_type = "voucher.payable"
            model_type_view = "voucher_payable_view_form"
        if self.type_dokumen == "Voucher Permintaan Kasbon":
            model_type = "voucher.permintaan.kasbon"
            model_type_view = "voucher_permintaan_kasbon_view_form"
        if self.type_dokumen == "Voucher Pertanggungjawaban Kasbon":
            model_type = "voucher.pertanggungjawaban.kasbon"
            model_type_view = "voucher_pertanggungjawaban_kasbon_view_form"
            
        records = self.env[model_type].search([('name','=',self.name)], limit=1)
        
        if not records:
            raise UserError(_("terjadi kesalahan, silahkan hubungi administrator "))
        
        records.write({
            'state': 'onprocess',
            'disetujui_oleh':self.env.uid,
            'disetujui_tanggal':fields.Date.today()
        })
        
        return {
            'name'      : 'DASHBOARD',
            'type'      : 'ir.actions.act_window',
            'view_type' : 'kanban',
            'view_mode' : 'kanban',
            'res_model' : 'dokumen.dashboard',
            'target'    : 'current',
        }
        
    def button_reject_doc(self):
        model_type = ""
        model_name = ""
        model_type_view =""
        if self.type_dokumen == "Voucher Payable":
            model_type = "voucher.payable"
            model_type_view = "voucher_payable_view_form"
        if self.type_dokumen == "Voucher Permintaan Kasbon":
            model_type = "voucher.permintaan.kasbon"
            model_type_view = "voucher_permintaan_kasbon_view_form"
        if self.type_dokumen == "Voucher Pertanggungjawaban Kasbon":
            model_type = "voucher.pertanggungjawaban.kasbon"
            model_type_view = "voucher_pertanggungjawaban_kasbon_view_form"
            
        records = self.env[model_type].search([('name','=',self.name)], limit=1)
        
        if not records:
            raise UserError(_("terjadi kesalahan, silahkan hubungi administrator "))
        
        records.write({
            'state': 'draft'
        })
        
        return {
            'name'      : 'DASHBOARD',
            'type'      : 'ir.actions.act_window',
            'view_type' : 'kanban',
            'view_mode' : 'kanban',
            'res_model' : 'dokumen.dashboard',
            'target'    : 'current',
        }
        