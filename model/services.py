from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError

class services(models.Model):
    _name = 'oil.services'
    _description = 'Oil services'
    # _inherit = ['vin.no.validation.mixin']

    name = fields.Char(string="Service name", required=True,copy=False,index=True)
    service_product_id = fields.Many2one('product.product',string="Service product",domain=[('detailed_type','=','service')] required=True,copy=False)
    storable_product_required = fields.Boolean(string="storable product", default=False,copy=False)
    active = fields.Boolean(string='Active', default=True)
    service_price_line_ids = fields.One2many('oil.services.price.line','header_id',ondelete="cascade",copy=False)    
    service_prod_categ_line_ids = fields.One2many('oil.services.product.categ.line','header_id',ondelete="cascade",copy=False)    

class services_price_line(models.Model):
    _name = 'oil.services.price.line'
    _description = 'Oil services prices'

    oil_distance_type_id = fields.Many2one('oil.vehicle.distance',string="Vehicle distance Type")

    car_size_id = fields.Many2one('oil.car.size', string="Car Size")
    oil_brand_id = fields.Many2one('oil.brands', string="Oil Brand")
    service_price = fields.Float(string="Service price", required=True)
    tax_id = fields.Many2one('account.tax',string="Tax type", required=True,domain=[('type_tax_use','=','sale'),('active','=', True)])
    price_readonly = fields.Boolean(string="Price readony", default=False,copy=False)
    header_id = fields.Many2one('oil.services', required=True, ondelete="cascade",copy=False)


class services_product_category_line(models.Model):
    _name = 'oil.services.product.categ.line'
    _description = 'allowd product category in services'
    
    service_type_id = fields.Many2one('oil.service.type',string="Service type", required=True)
    product_categ_ids = fields.Many2many('product.category',string="Allowed product category", required=True)
    header_id = fields.Many2one('oil.services', required=True, ondelete="cascade",copy=False)
