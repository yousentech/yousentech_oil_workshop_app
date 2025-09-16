from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict
import re

class WorkOrderTemp(models.Model):
    _name = 'oil.work.order.app'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'product.catalog.mixin']
    _rec_name = "partner_id"

    state = fields.Selection(selection=[('draft', 'Customer Info'), ('services', 'Services'), ('confirm', 'confirmed'), ('cancel_confirm', 'Cancel Confirm'), ('cancel_request', 'Cancel Request'), ('in_service', 'Completed')], string='Status', default='draft', tracking=True)
    oil_brand_id = fields.Many2one('oil.brands', string="Oil Brand",)
   
    oil_distance_type_id = fields.Many2one('oil.vehicle.distance',string="Vehicle distance Type")
    car_size_id = fields.Many2many('oil.car.size', string="Car Size")
    mobile_number = fields.Char(string='Mobile Number',)

    partner_id = fields.Many2one('res.partner', string='Car Owner')
    car_number = fields.Char(string='Car Number', help='Vehicle chassis number')
    car_letters = fields.Char(string='Car Letters', help='Vehicle chassis Letters')
    car_type_id = fields.Many2one('oil.car.type', string='Car Type', help='Type/Model of the vehicle')
    car_size_id = fields.Many2one('oil.car.size', string='Car Size', )
    vin_no = fields.Char(string='VIN Number', help='Vehicle Identification Number (VIN)')
    current_distance = fields.Float(string='Current Distance', help='Total distance traveled by the vehicle in kilometers', digits=(16, 2), default=0.0)
    # order_date = fields.Date(string="Order Date", default=fields.Date.today, required=True)
    order_date = fields.Datetime(
        string="Order Date",
        required=True,
        default=fields.Datetime.now
    )
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',domain="[('techncian_emp_flag','=',True),('company_id','=',company_id)]")
    order_line = fields.One2many("oil.work.order.app.line", "order_id", string="Orders",ondelete="cascade",copy=False)
    city_id = fields.Many2one('oil.city', string='City',)
    picking_type_id = fields.Many2one('stock.picking.type', string='Place Of sale', domain="[('code', '=', ['outgoing']),('company_id','=',company_id)]", required=False)
    negative_quantity_flag = fields.Boolean(string='Failure verify available quantity', default=False)
    sale_order_id = fields.Many2one('sale.order')
    car_model = fields.Integer(string='Car Model')
    car_version_id = fields.Many2one('oil.car.version', string='Car Version')
    pin_code = fields.Char(string='Pin Code')
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")
    car_notes = fields.Char(string='Notes')
    lines_total_price = fields.Float(string='Total Price', compute='_compute_lines_total_price', store=True)
    created_order_date = fields.Date(string="Order Create Date", compute='_compute_create_date_only')
    
    employee_user_id = fields.Many2one(
        "res.users",
        string="Employee User name",
       
        copy=False,
        tracking=True,
      
    )
    supervisor_user_id = fields.Many2one(
        "res.users",
        string="supervisor name",
        readonly=True,
        copy=False,
        
    )

    def open_services(self):
        for rec in self:
            rec.write({'state': 'services'})

            
    def back_to_main_info(self):
        for rec in self:
            rec.write({'state': 'draft'})
 
    @api.depends('create_date')
    def _compute_create_date_only(self):
        for rec in self:
            rec.created_order_date = rec.create_date.date() if rec.create_date else False

    @api.depends('order_line.price_total')
    def _compute_lines_total_price(self):
        for rec in self:
            rec.lines_total_price = sum(rec.order_line.mapped('price_total'))

    def confirm_btn(self):
        for rec in self:
            action = self.env.ref('yousentech_oil_workshop.oil_message_confirm_wo_temp_action')
            result = action.read()[0]
            result.pop('id', None)
         
            return result
       
    def _default_picking_type_id(self):
        for rec in self:
            user_config = rec.env['res.user.inventory.config'].search([('user_id', '=', rec.employee_user_id.id),('company_id', '=', rec.company_id.id),('operation_type', '=', 'outgoing')], limit=1)
            is_exsiting_field_in_company = self.env['ir.model.fields'].sudo().search([('name', '=', 'sale_picking_type_id'), ('model', '=', 'res.company')])
            if user_config and user_config.picking_type_id:
                # Use the picking type from user's inventory config
                rec.picking_type_id = user_config.picking_type_id.id
            elif is_exsiting_field_in_company:
                if rec.company_id.sale_picking_type_id and rec.company_id.sale_picking_type_id.company_id.id == rec.company_id.id:
                    # Company's default if no user-specific setting
                    rec.picking_type_id = rec.company_id.sale_picking_type_id.id
            else:
                rec.picking_type_id = False


    @api.onchange('car_letters', 'car_number')
    def _onchange_car_details(self):
        for record in self:
            if record.car_letters and record.car_number:
                car_data = self.env['oil.car.data'].search(
                    [('car_letters', '=', record.car_letters.upper()), ('car_number', '=', record.car_number),], limit=1)
                if car_data:
                    record.partner_id = car_data.partner_id.id,
                    record.mobile_number = car_data.mobile_number
                    record.car_type_id = car_data.car_type_id.id
                    record.vin_no = car_data.vin_no
                    record.car_letters = car_data.car_letters.upper()
                    record.car_number = car_data.car_number
                    record.car_model = car_data.car_model
                    record.car_version_id = car_data.car_version_id.id
                    
                else:
                    raise ValidationError(
                        _("The current number and letter combination you entered does not exist"))

    @api.constrains('car_letters', 'car_number')
    def _check_exist_letters_car_number(self):
        for record in self:
            if record.car_letters and record.car_number:
                car_data = self.env['oil.car.data'].search(
                    [('car_letters', '=', record.car_letters), ('car_number', '=', record.car_number),], limit=1)
                if not car_data:
                    raise ValidationError(
                        _("The current number and letter combination you entered does not exist"))

    def _validate_entries(self):
        for rec in self:
            rec._default_picking_type_id()
            
            if not rec.order_line:
                raise UserError(
                    ("Please add at least one order line before creating a sale order"))
            for line in rec.order_line:
                if not line.product_id:
                    raise UserError(_("Product is required for all order lines"))
           
            if not rec.partner_id:
                raise UserError(_("Customer Name is required"))
          
            if not rec.mobile_number:
                    raise UserError(_("Mobile Number is required"))
           
            if not rec.car_number:
                raise UserError(_("Vehicle Plate Number is required"))
            
            if not rec.car_letters:
                    raise UserError(_("Vehicle Plate Letters is required"))

            if not rec.vin_no:
                    raise UserError(_("Vin No is required"))


            if not rec.car_type_id:
                raise UserError(_("Car Type No is required"))


            if not rec.car_version_id:
                raise UserError(_("Car Version is required"))
         
            if not rec.car_model:
                 raise UserError(_("Car Model No is required"))

         
            if not rec.employee_id:
                 raise UserError(_("Technical name is required"))

    @api.constrains('current_distance')
    def _validate_current_distance(self):
        for record in self:
            if record.car_letters and record.car_number:
                if record.current_distance == 0:
                    raise ValidationError(
                        _("The current distance cannot accept a value of zero"))


    def validate_car_details(self, car_number, car_letters):
        config = self.env['ir.config_parameter'].sudo()
        max_letters = float(config.get_param('yousentech_oil_workshop.max_letters', default='4'))
        max_numbers = float(config.get_param('yousentech_oil_workshop.max_numbers', default='4'))

        # car number part

        if not car_number:
            raise ValidationError("رقم اللوحة مطلوب")
        if not str(car_number).isdigit():
            raise ValidationError("رقم اللوحة يجب أن يكون أرقام فقط")
        if len(str(car_number)) > max_numbers:
            raise ValidationError(f"الحد الأقصى لرقم السيارة هو {max_numbers} أرقام")

        # car_letters part
        if not car_letters:
            raise ValidationError("أحرف اللوحة مطلوبة")

        if re.sub(r'[^A-Za-z]', '', car_letters) != car_letters:
            raise ValidationError("يسمح فقط بإدخال الأحرف الإنجليزية (A-Z).")
        
        cleaned_letters = re.sub(r'[^A-Za-z]', '', car_letters).upper()

        allowed_letters = {
            "A": "أ", "B": "ب", "J": "ح", "D": "د", "R": "ر", "S": "س",
            "X": "ص", "T": "ط", "E": "ع", "G": "ق", "K": "ك", "L": "ل",
            "Z": "م", "N": "ن", "H": "ه", "U": "و", "V": "ى",
        }

        if not all(char in allowed_letters for char in cleaned_letters):
            raise ValidationError("يرجى إدخال حروف إنجليزية مسموح بها فقط")
        
        if len(cleaned_letters) > max_letters:
            raise ValidationError(f"الحد الأقصى لعدد الأحرف هو {max_letters}")

    