{
    "name": "yousentech_oil_workshop_app",
    "description": "Additional Fields for YUVO Customer",
    "author": "yousen tech Techno Solutions, Odoo SA",
    "depends": ["base", "account", "yousentech_oil_workshop"],
    "application": True,
    "version": "17.0.0.3",
    "license": "AGPL-3",
    "installable": True,
    "data": [
       'security/ir.model.access.csv',
        'security/security.xml',
        "view/services.xml",
    ],
    "images": [],
}
