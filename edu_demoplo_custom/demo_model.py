from odoo import models, fields

class DemoModel(models.Model):
	_name = 'edu.demoplo.model'
	_description = 'Demo Model'

	name = fields.Char(string='Name')
