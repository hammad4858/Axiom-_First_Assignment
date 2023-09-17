from odoo import fields, models


class EstatePropertyInvoice(models.Model):
    _name = "estate.property.invoice"
    _description = "Property Invoice"

    buyer_id = fields.Many2one("res.partner", string="Buyer", required=True, domain="[('is_company', '=', False)]")
    property_id = fields.Many2one("estate.property", string="Property", required=True)
    amount = fields.Float(string="Amount", required=True)
    date = fields.Date(string="Invoice Date", default=fields.Date.today())
