from odoo import models, api, fields, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict
import re

class WorkOrderTemp(models.Model):
    _name = 'oil.work.order.app'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'product.catalog.mixin']
    _rec_name = "partner_id"

    order_seq = fields.Integer(string="Sequences", required=True)
    state = fields.Selection(selection=[('send_request', 'Send Request'), 
                                        ('tech_assign', 'Technician Assignment'), 
                                        ('request_accept', 'Request Accepted'),
                                        ('in_way', 'In the way'), 
                                        ('wo_started', 'Work started'),
                                        ('comptete', 'Completed')], string='Status', default='send_request', tracking=True)
    wo_state = fields.Selection(selection=[('main_info', 'main info'),
                                              ('services', 'services'), 
                                               ('preview', 'preview'), ], 
                                                 string='Status', default='main_info', tracking=True)
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
    # sale_order_id = fields.Many2one('sale.order')
    car_model = fields.Integer(string='Car Model')
    car_version_id = fields.Many2one('oil.car.version', string='Car Version')
    pin_code = fields.Char(string='Pin Code')
    latitude = fields.Float(string="Latitude")
    longitude = fields.Float(string="Longitude")
    car_notes = fields.Char(string='Notes')
    lines_total_price = fields.Float(string='Total Price', compute='_compute_lines_total_price', store=True)
    created_order_date = fields.Date(string="Order Create Date", compute='_compute_create_date_only')
    sale_order_id = fields.Many2one('sale.order',copy=False)
    account_move_id = fields.Many2one('account.move',copy=False)
    salesman_id = fields.Many2one(
        "salesman", string="Salesman", default=lambda self: self._default_salesman())
    salesman_enable = fields.Boolean(
        # compute="_compute_salesman_readonly",
        default=lambda self: self.default_salesman_readonly(),
    )
    salesman_domain = fields.Char("salesman_domain", compute="_compute_salesman_domain")
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

    def request_accept_btn(self):
        for rec in self:
            rec.write({'state': 'request_accept'})

    def in_way_btn(self):
        for rec in self:
            rec.write({'state': 'in_way'})
    
    def wo_started_btn(self):
        for rec in self:
            rec.write({'state': 'wo_started'})


    def open_services(self):
        for rec in self:
            rec.write({'wo_state': 'services'})

            
    def back_to_main_info(self):
        for rec in self:
            rec.write({'wo_state': 'main_info'})
    def preview_btn(self):
        for rec in self:
            rec.write({'wo_state': 'preview'})
    def comptete_btn (self):
        for rec in self:
            rec.write({'state': 'comptete'})


 
    @api.depends('create_date')
    def _compute_create_date_only(self):
        for rec in self:
            rec.created_order_date = rec.create_date.date() if rec.create_date else False

    @api.depends('order_line.price_total')
    def _compute_lines_total_price(self):
        for rec in self:
            rec.lines_total_price = sum(rec.order_line.mapped('price_total'))

    def select_car_service(self):
        for rec in self:
            action = self.env.ref('yousentech_oil_workshop_app.oil_message_confirm_wo_temp_action')
            result = action.read()[0]
            result.pop('id', None)
         
            return result
 
    def create_sale_order(self):
        self.ensure_one()
        self._validate_entries()


        if self.sale_order_id:
            if not self.sale_order_id.invoice_ids:
                self.sale_order_id._create_invoices()


            raise UserError(
                _("the Order has Invoice. You can not create again"))
     
        if not self.picking_type_id:
              raise UserError(
                _("Please select the warehouse from which the items will be issued"))

        if not self.order_line:
            raise UserError(
                _("Please add at least one order line before creating a sale order"))
       
        order_vals = {}
        order_vals = {
                'partner_id': self.partner_id.id,
                'date_order': self.order_date,
                'origin': f"Car: {self.car_type_id.name}",
                'work_order_app_id': self.id,
                'company_id': self.company_id.id,
                'user_id': self.user_id.id,
                
            }


        # Create the sale order
        sale_order = self.env['sale.order'].with_context(
            default_company_id=self.company_id.id).create(order_vals)
       

        for line in self.order_line:
            if not line.product_id:
                raise UserError(_("Product is required for all order lines"))

            # Get fiscal position for taxes
            fiscal_position = sale_order.fiscal_position_id

            line_vals = {
                'order_id': sale_order.id,
                'product_id': line.service_product_id.id,
                'name':  line.description or '',
                'product_uom_qty': line.quantity,
                'product_uom': line.product_id.uom_id.id,
                'price_unit': line.unit_price,
                'tax_id': [(6, 0, fiscal_position.map_tax(line.tax_id).ids)],
                'company_id': sale_order.company_id.id,
                'sequence': 10,
                'display_type': False,
            }

            try:
               
                self.env['sale.order.line'].create(line_vals)
               
            except Exception as e:
                raise UserError(_("Failed to create order line: %s") % str(e))

        try:
            # self.state = 'in_service'
            # self.external_request_id.write({'state': 'in_service'})
            self.sale_order_id = sale_order.id
            is_exsiting_field_picking_type_id = self.env['ir.model.fields'].sudo().search([('name', '=', 'picking_type_id'), ('model', '=', 'sale.order')])
            if is_exsiting_field_picking_type_id :
                sale_order.picking_type_id = self.picking_type_id.id
            
            sale_order.action_confirm()
            

        except Exception as e:
            raise UserError(_("Order confirmation failed: %s") % str(e))

    def unlink(self):
        for vehicle in self:
            # Check if vehicle has linked sales orders
            if vehicle.sale_order_id  or vehicle.account_move_id or not self.user_has_groups('yousentech_oil_workshop.group_delete_request'):
                raise UserError(_(
                    "Cannot delete order with State:%s ,For:%s because it has linked sales orders. or you have not permission"
                    "Please archived instead.") % (vehicle.state, vehicle.car_type_id.name))
            return super(WorkOrderTemp, self).unlink()



       
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
                  
            if self.company_id.salesman_required:
                if self.company_id.salesman_required_selection == "new_draft_records":
                    if not self.salesman_id.id:
                        raise ValidationError(_("The Salesman Field is Required"))

  


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

    def default_salesman_readonly(self):
        return self.user_has_groups(
            "yousentech_invoicing_saleman.allow_modify_salesman"
        )
 
    def _default_salesman(self):
        salesman = self.env["salesman"].search(
            [("sale_user", "=", self.env.user.id)], limit=1
        )
        if salesman:
            return salesman
        else:
            return False
 
    @api.depends("company_id")
    def _compute_salesman_domain(self):
        for rec in self:
            company_salesman = self.env["salesman.assignments"].search(
                [("company_id", "=", rec.company_id.id)]
            )
            if company_salesman:
                rec.salesman_domain = [("id", "in", company_salesman.salesman_id.ids)]

            
            else:
                rec.salesman_domain = []

    @api.onchange('company_id')
    def _get_new_order_seq(self):
        sql_query = ""
        if self.company_id:
            sql_query = "select max(COALESCE(order_seq,0)) as seq from oil_work_order_app where company_id='%s'" % self.company_id.id
            self.env.cr.execute(sql_query)
            seq = self.env.cr.fetchone()
            x = seq[0]
            if x:
                x = x + 1
                self.order_seq = x
            else:
                x = 1
                self.order_seq = x
        else:
            self.order_seq = 0

    @api.model
    def create(self, vals):
        if 'order_seq' in vals:
            check_seq = self.env['oil.work.order.app'].search([('order_seq','=',vals['order_seq'])])
            if check_seq:
                sql_query = "select max(COALESCE(order_seq,0)) as seq from oil_work_order_app where company_id='%s'" % self.company_id.id
                self.env.cr.execute(sql_query)
                seq = self.env.cr.fetchone()
                x = seq[0]
                if x:
                    x = x + 1
                
                    vals['order_seq'] = x
                
            
                else:
                    x = 1
                    vals['order_seq'] = x
        
        res = super(WorkOrderTemp, self).create(vals)

        if res.company_id.salesman_required:
            if not res.salesman_id.id:
                raise ValidationError(_("The Salesman Field is Required"))


        return res


