{
    "name": "yousentech_oil_workshop_app",
    "description": "Additional Fields for YUVO Customer",
    "author": "yousen tech Techno Solutions, Odoo SA",
    "depends": ["base", "account", "yousentech_oil_workshop"],
    "application": True,
    "version": "17.0.0.3",
      "data": [
       'security/ir.model.access.csv',
        'security/security.xml',
        "view/services.xml",
        "view/service_type.xml",
        "view/package_app.xml",
        "view/work_order_temp.xml",
        "view/message_confirm_temp.xml",
     ],
    'images': ['static/description/icon.png'],
    'license': 'LGPL-3',
    'sequence': '-100',
    'installable': True,
    'auto_install': False,
    'application': True,

}
