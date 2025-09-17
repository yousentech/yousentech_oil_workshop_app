from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError


class work_order_line(models.Model):
    _name = 'oil.work.order.app.line'

    service_product_id = fields.Many2one('product.product', string='Product', domain="[('detailed_type', 'in', ['service'])]",required=True)
    service_id = fields.Many2one('oil.services',string="Service",)
    package_id = fields.Many2one('oil.package.app',string="Package")
    service_type_id = fields.Many2one('oil.service.type',string="Service type")
    product_id = fields.Many2one('product.product', string='Product', domain="[('detailed_type', 'in', ['service','product'])]", help="Select a service-type product")
    description = fields.Text(string='Description', help='Detailed description of the service')
    quantity = fields.Float(string='Quantity', default=1.0, digits='Product Unit of Measure', help='Quantity of service units')
    unit_price = fields.Float(string='Unit Price', digits='Product Price', default=0.0, help='Price per unit of service')
    tax_id = fields.Many2one('account.tax', string='Taxes', domain=[('type_tax_use', '=', 'sale')], help='Taxes to be applied')
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_amount', digits='Account', store=True, help='Total without taxes')
    price_tax = fields.Float(string='Tax Amount', compute='_compute_amount', digits='Account', store=True, help='Total tax amount')
    price_total = fields.Float(string='Total', compute='_compute_amount', digits='Account', store=True, help='Total with taxes')
    order_id = fields.Many2one("oil.work.order.app", string="Work Order",ondelete="cascade",copy=False)
    price_readonly = fields.Boolean(string="Price readony", default=False,copy=False)

    @api.depends('quantity', 'unit_price', 'tax_id')
    def _compute_amount(self):
        for item in self:
            price = item.unit_price * item.quantity
            taxes = item.tax_id.compute_all(price)

            item.update({
                'price_subtotal': taxes['total_excluded'],
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
            })

    # Validations
    @api.constrains('quantity')
    def _check_quantity(self):
        for item in self:
            if item.quantity <= 0:
                raise ValidationError(_(
                    "Quantity must be greater than zero!"))

    @api.constrains('unit_price')
    def _check_unit_price(self):
        for item in self:
            if item.unit_price < 0:
                raise ValidationError(_(
                    "Unit price cannot be negative!"))
                      
    @api.constrains('product_id', 'order_id')
    def _check_product_categories(self):
        for order in self.mapped('order_id'):
            categories = {}
            for line in order.order_line:
                if line.product_id.categ_id in categories:
                    raise ValidationError(
                        _("Duplicate category detected: %s\n"
                        "Existing product: %s\n"
                        "New product: %s") % (
                        line.product_id.categ_id.name,
                        categories[line.product_id.categ_id],
                        line.product_id.name
                        ))
                categories[line.product_id.categ_id] = line.product_id.name
     
    @api.constrains('product_id', 'order_id')
    def _check_engine_oil_products(self):
        for order in self.mapped('order_id'):
            # Get all engine oils in the order
            engine_oils = order.order_line.mapped('product_id').filtered(
                lambda p: p.product_tmpl_id.is_oil)
            
            # Rule 1: Only one engine oil type allowed
            if len(engine_oils.mapped('product_tmpl_id')) > 1:
                raise ValidationError(
                    _("Multiple engine oil types detected!\n"
                    "You can only have one type of engine oil per order."))
            
    @api.onchange('package_id')
    def get_package_detail(self):
        for rec in self:
            if rec.package_id:
                rec.description= rec.package_id.description
                rec.service_product_id= rec.package_id.package_product_id.id
                rec.quantity= 1
                package_line_detail = rec.get_package_price(rec.package_id,rec.order_id.oil_distance_type_id.id,rec.order_id.car_size_id.id)
                if not package_line_detail:
                       raise UserError(_("Package detail not completed"))
                else:
                    rec.unit_price = package_line_detail.package_price
                    rec.tax_id = package_line_detail.tax_id
                    rec.price_readonly = package_line_detail.price_readonly
                    
                
    def get_package_price(self,package_id,oil_distance_type_id,car_size_id):
        for rec in self:
            package_detail = False
            package_detail = package_id.package_price_line_ids.filtered(lambda x: x.oil_distance_type_id.id == oil_distance_type_id
                                                                        and x.car_size_id.id == car_size_id)
        
              
            return package_detail

    @api.onchange('service_id')
    def get_service_detail(self):
        for rec in self:
            if rec.service_id:
                rec.description= rec.service_id.name
                rec.service_product_id= rec.service_id.service_product_id.id
                rec.quantity= 1
                service_line_detail = rec.get_service_price(rec.service_id,rec.order_id.oil_distance_type_id.id,rec.order_id.car_size_id.id,rec.order_id.oil_brand_id.id)
                if not service_line_detail:
                       raise UserError(_("Service detail not completed"))
                else:
                    rec.unit_price = service_line_detail.service_price
                    rec.tax_id = service_line_detail.tax_id
                    rec.price_readonly = service_line_detail.price_readonly

    def get_service_price(self,service_id,oil_distance_type_id,car_size_id,oil_brand_id):
        for rec in self:
            service_detail = False
            package_detail = service_id.service_price_line_ids.filtered(lambda x: x.oil_distance_type_id.id == oil_distance_type_id
                                                                            and x.car_size_id.id == car_size_id
                                                                            and x.oil_brand_id.id == oil_brand_id
                                                                        )
            return service_detail

    def open_package_lines(self):
        for rec in self:
            package_detail = self.env['oil.wo.package.detail'].search([('package_id','=', rec.package_id.id),('work_order_line_id','=', rec.id)])
            if not package_detail:
                line_ids = []
                for l in rec.package_id.package_services_line_ids:
                    line_dict = {'service_id': l.service_id.id}
                
                    line_ids.append((0, 0, line_dict))

    
                if line_ids:
                    package_detail = self.env['oil.wo.package.detail'].create({
                        'package_id': rec.package_id.id,
                        'work_order_line_id': rec.id,
                        'pckage_line_ids': line_ids})
            print("package_detail================",package_detail)
            action = self.env.ref('yousentech_oil_workshop_app.action_oil_wo_package_detail')
          
            result = action.read()[0]
            result.pop('id', None)
            result['domain'] = [('id','=',package_detail.id)]
            if package_detail:
                res = self.env.ref('yousentech_oil_workshop_app.view_oil_wo_package_detail_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = package_detail.id or False
               
            return result



class work_order_package_detail(models.Model):
    _name = 'oil.wo.package.detail'

    package_id = fields.Many2one('oil.package.app',string="Package")
    work_order_line_id = fields.Many2one('oil.work.order.app.line',string="Package")
    pckage_line_ids = fields.One2many("oil.wo.package.detail.line", "header_id", ondelete="cascade",copy=False)
    
     
class work_order_package_detail_line(models.Model):
    _name = 'oil.wo.package.detail.line'
    
    service_id = fields.Many2one('oil.services',string="Service",)
    product_id = fields.Many2one('product.product', string='Product', domain="[('detailed_type', 'in', ['service','product'])]", help="Select a service-type product",)
    header_id = fields.Many2one("oil.wo.package.detail",  ondelete="cascade",copy=False)
