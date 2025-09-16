from odoo import models, api, fields, _


class sale_order(models.Model):
    _inherit = "sale.order"

    work_order_app_id = fields.Many2one('oil.work.order.app',string="Work order App No")

    def _prepare_invoice(self):
        res = super(sale_order, self)._prepare_invoice()
        res.update({'work_order_app_id': self.work_order_app_id.id or False,
                    'car_number': self.work_order_app_id.car_number,
                    'car_letters': self.work_order_app_id.car_letters,
                    'mobile_number':self.work_order_app_id.mobile_number,
                    'car_type_id':self.work_order_app_id.car_type_id.id,
                    'vin_no':self.work_order_app_id.vin_no,
                    'car_model':self.work_order_app_id.car_model,
                    'car_version_id':self.work_order_app_id.car_version_id.id,
                    'current_distance':self.work_order_app_id.current_distance,
                    'car_notes':self.work_order_app_id.car_notes,
                    
                    })

        return res
