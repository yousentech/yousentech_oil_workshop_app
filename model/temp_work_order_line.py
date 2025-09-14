from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class work_order_line(models.Model):
    _name = 'oil.work.order.app.line'


    service_id = fields.Many2one('oil.services',string="Service", required=True)

    product_id = fields.Many2one('product.product', string='Product', domain="[('detailed_type', 'in', ['service','product'])]", help="Select a service-type product", required=True)
    description = fields.Text(string='Description', help='Detailed description of the service')
    quantity = fields.Float(string='Quantity', default=1.0, digits='Product Unit of Measure', help='Quantity of service units')
    unit_price = fields.Float(string='Unit Price', digits='Product Price', default=0.0, help='Price per unit of service')
    tax_id = fields.Many2one('account.tax', string='Taxes', domain=[('type_tax_use', '=', 'sale')], help='Taxes to be applied')
    price_subtotal = fields.Float(string='Subtotal', compute='_compute_amount', digits='Account', store=True, help='Total without taxes')
    price_tax = fields.Float(string='Tax Amount', compute='_compute_amount', digits='Account', store=True, help='Total tax amount')
    price_total = fields.Float(string='Total', compute='_compute_amount', digits='Account', store=True, help='Total with taxes')
    order_id = fields.Many2one("oil.work.order.app", string="Work Order",ondelete="cascade",copy=False)

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
            
           