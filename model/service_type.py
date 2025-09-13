from odoo import models, fields, _

class services_types(models.Model):
    _inherit = 'oil.service.type'

    services_ids = fields.Many2many('oil.services',string="Additional services in App")
