from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError

class packages(models.Model):
    _name = 'oil.package.app'
    _description = 'Oil package App'
    
    name = fields.Char(string="package name", required=True,copy=False,index=True)
    service_type_id = fields.Many2one('oil.service.type',string="Service type", required=True)
    oil_brand_id = fields.Many2many('oil.brands', string="Oil Brand", required=True)
    package_product_id = fields.Many2one('product.product',string="Package product",domain=[('detailed_type','=','service')], required=True,copy=False)
    package_type = fields.Selection(selection=[('primary', 'Primary'),
                                        ('secondary','Secondary') ],  
                                        string='Package Type',  default='primary',  tracking=True,)    
    active = fields.Boolean(string='Active', default=True)
    package_price_line_ids = fields.One2many('oil.package.price.line','header_id',ondelete="cascade",copy=False)    
    package_services_line_ids = fields.One2many('oil.package.services.line','header_id',ondelete="cascade",copy=False)    

class package_price_line(models.Model):
    _name = 'oil.package.price.line'
    _description = 'Oil package prices'

    oil_distance_type_id = fields.Many2one('oil.vehicle.distance',string="Vehicle distance Type")
    car_size_id = fields.Many2many('oil.car.size', string="Car Size")
    package_price = fields.Float(string="Service price", required=True)
    tax_id = fields.Many2one('account.tax',string="Tax type", required=True,domain=[('type_tax_use','=','sale'),('active','=', True)])
    price_readonly = fields.Boolean(string="Price readony", default=False,copy=False)
    header_id = fields.Many2one('oil.package.app', required=True, ondelete="cascade",copy=False)


class package_services_line(models.Model):
    _name = 'oil.package.services.line'
    _description = 'Package services'
    
    service_id = fields.Many2one('oil.services',string="Service", required=True)
    desc = fields.Char(string="Description")
    header_id = fields.Many2one('oil.package.app', required=True, ondelete="cascade",copy=False)
