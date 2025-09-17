from datetime import datetime, time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class oil_temp_message_confirm(models.TransientModel):
    _name = 'oil.temp.message.confirm'

    service_car_id = fields.Many2one('oil.service.cars',string="Service Car", required=True)

    def confirm(self):
        model = self._context.get('active_model')
     
        records = self.env[model].search([('id','=', self._context.get('active_id'))])
     
        if records and self.service_car_id:
            if not self.service_car_id.user_id:
                raise UserError(_("The Service Car is not related with Employee"))
            
              
            records.write({'employee_user_id': self.service_car_id.user_id.id})
            records.write({'supervisor_user_id': self.env.uid})
            records.write({'employee_id': self.service_car_id.user_id.employee_id.id})
            records.write({'state': 'tech_assign'})
           
    
