from odoo import models, fields


class EstateProperType(models.Model):
    _name = "estate.property.type"
    _description = "Model for property types"

    name = fields.Char(string="Name", required=True)

