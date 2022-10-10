# -*- coding: utf-8 -*-
{
    'name': "Submission Tracking GEP",
    'summary': """System untuk track voucher PT Gunung Emas Putih""",
    'description': """Sistem untuk track voucher, reimburstment, dan cash bond PT Gunung Emas Putih
    """,
    'author': "PT Gunung Emas Putih",
    'website': "https://www.geptambang.co.id",
    'license': 'AGPL-3',
    'development_status': 'Production/Stable',
    'version': '1.0',
    'depends': ['base','product','mail'],
    'maintainers': ['mgosai'],
    'application': True,
    # always loaded
    'data': [
        'data/add_sequence_data.xml',
        'views/voucher_payable_views.xml',
        'security/submission_tracking_gep_group_access.xml',
        'security/security.xml',
        'views/template_voucher_payable_report.xml',
        'views/voucher_permintaan_kasbon_views.xml',
        'views/template_voucher_permintaan_kasbon_report.xml',
        'security/ir.model.access.csv',
        'security/voucher_permintaan_kasbon_security.xml',
        'views/voucher_pertanggungjawaban_kasbon_views.xml',
        'views/template_voucher_pertanggungjawaban_kasbon_report.xml',
        'security/voucher_pertanggungjawaban_kasbon_security.xml',  
        'views/dokumen_dashboard_views.xml',         
        'security/dashboard_security.xml'
    ],
}

