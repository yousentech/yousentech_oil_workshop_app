from odoo import models, api, fields, _
from odoo.exceptions import UserError


class account_move(models.Model):
    _inherit = "account.move"

    work_order_app_id = fields.Many2one('oil.work.order.app',string="Work order App No")
    
    def create(self,vals):
   
        res= super().create(vals)
        if res.work_order_app_id and res.move_type == 'out_invoice':
            res.work_order_app_id.write({'account_move_id': res.id})
            
        is_exsiting_field = self.env['ir.model.fields'].sudo().search([('name', '=', 'salesman_id'), ('model', '=', 'oil.work.order.app')])
        if is_exsiting_field:
          res.salesman_id = res.work_order_app_id.salesman_id.id
        return res

        
