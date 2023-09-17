from odoo import api, fields, models
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Model for Real-Estate Properties"

    name = fields.Char(string="Property Name", required=True, default="Unknown")
    description = fields.Text(string="Description")
    postcode = fields.Char(string="Postcode")
    date_availability = fields.Char(string="Availability From", default="3 Months")
    expected_price = fields.Float(string="Expected Price", required=True)
    selling_price = fields.Float(string="Selling Price", readonly=True, copy=False)
    bedrooms = fields.Integer(string="Bedrooms", default=2)
    living_area = fields.Integer(string="Living Area")
    facades = fields.Integer(string="Facades")
    garage = fields.Boolean(string="Garage")
    garden = fields.Boolean(string="Garden")
    garden_area = fields.Integer(string="Garden Area")
    garden_orientation = fields.Selection([('North', 'North'), ('South', 'South')], string="Garden Orientation")
    state = fields.Selection(
     [('new', 'New'),
      ('offer_received', 'Offer Received'),
      ('offer_accepted', 'Offer Accepted'),
      ('sold', 'Sold'),
      ('canceled', 'Canceled')],
     string="State",
     required=True,
     copy=False,
     default="new"
      )
    best_offer = fields.Float(compute="_compute_highest_offer", string="Highest Offer", store=True)
    total_area = fields.Integer(compute="_compute_total_area", string="Total Area (sqm)", store=True)
    property_type_id = fields.Many2one("estate.property.type", string="Property Type", context="{'no_create': True, 'no_create_edit': True}")
    buyer_id = fields.Many2one("res.partner", string="Buyer", domain="[('is_company', '=', False)]", no_copy=True)
    offer_ids = fields.One2many("estate.property.offer", "property_id", string="Offers")
    salesperson_id = fields.Many2one("res.users", string="Salesperson", domain="[('user_ids', '!=', False)]", default=lambda self: self.env.user)
    tag_ids = fields.Many2many("estate.property.tag", string="Property Tags")

    def cancel(self):
        for prop in self:
            if prop.state == 'sold':
                raise UserError("A sold property cannot be canceled.")
            if prop.state != 'canceled':
                prop.state = 'canceled'

    def sold(self):
        for prop in self:
            if prop.state == 'canceled':
                raise UserError("A canceled property cannot be sold.")
            if prop.state != 'sold':
                prop.state = 'sold'
                generate_invoice()
            # Additional business logic for setting a property as sold goes here


_sql_constraints = [
    ('check_positive_prices', 'CHECK(expected_price > 0 AND selling_price >= 0)', 'Expected Price and Selling Price must be non-negative!')
]


@api.depends("living_area", "garden_area")
def _compute_total_area(self):
    for prop in self:
        prop.total_area = prop.living_area + prop.garden_area


@api.depends("offer_ids.price")
def _compute_highest_offer(self):
    for prop in self:
        highest_offer = max(prop.offer_ids.mapped("price"), default=0.0)
        prop.best_offer = highest_offer


@api.depends('garden')
def _compute_garden_values(self):
    for record in self:
        if record.garden:
            # Set the default values for garden and garden_orientation
            record.garden_area = 10
            record.garden_orientation = 'north'
        else:
            # Clear the fields when garden is unset
            record.garden_area = 0
            record.garden_orientation = False


@api.constrains('expected_price', 'selling_price')
def _check_selling_price(self):
    for prop in self:
        if prop.expected_price <= 0.0:
            raise ValidationError("Expected Price must be strictly positive.")

        if prop.selling_price < 0.0:
            raise ValidationError("Selling price cannot be negative.")

        if 0.0 < prop.selling_price < 0.9 * prop.expected_price:
            raise ValidationError("Selling price cannot be lower than 90% of the expected price.")

        if prop.state == 'new' and any(offer.status == 'accepted' for offer in prop.offer_ids):
            raise ValidationError("Selling price cannot be set until an offer is validated.")


def generate_invoice(self):
    # Create an invoice for the sold property
    self.ensure_one()
    if self.state == 'sold' and self.buyer_id:
        invoice_data = {
            'buyer_id': self.buyer_id.id,
            'property_id': self.id,
            'amount': self.selling_price,
            # Add other relevant data for the invoice
        }
        try:
            self.env['estate.property.invoice'].create(invoice_data)
        except Exception as e:
            raise UserError(f"An error occurred while creating the invoice: {str(e)}")


class EstatePropertyOffer(models.Model):
    _name = "estate.property.offer"
    _description = "Property Offer"

    price = fields.Float(string="Price")
    status = fields.Selection([
        ('accepted', 'Accepted'), ('refused', 'Refused'),
    ], string="Status", no_copy=True, default='refused')
    buyer_id = fields.Many2one("res.partner", string="Partner")
    property_id = fields.Many2one("estate.property", string="Property", required=True)
    validity = fields.Integer(string="Validity (Days)", default=7)
    date_deadline = fields.Date(string="Deadline", compute="_compute_date_deadline", inverse="_inverse_date_deadline")

    @api.depends("validity", "create_date")
    def _compute_date_deadline(self):
        for record in self:
            if not record.create_date:
                record.date_deadline = False
            else:
                create_date = fields.Datetime.from_string(record.create_date)
                record.date_deadline = create_date + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            if record.date_deadline:
                create_date = fields.Datetime.from_string(record.create_date)
                deadline_date = fields.Datetime.from_string(record.date_deadline)
                record.validity = (deadline_date - create_date).days
            else:
                record.validity = 7

    @api.onchange('validity', 'create_date')
    def _onchange_validity(self):
        if self.validity and self.create_date:
            create_date = fields.Datetime.from_string(self.create_date)
            self.date_deadline = create_date + timedelta(days=self.validity)

    def write(self, vals):
        if 'status' in vals and vals['status'] == 'accepted':
            accepted_offers_before_write = self.filtered(lambda offer: offer.status == 'accepted')

            for offer in self:

                other_offers = offer.property_id.offer_ids - offer
                other_offers.write({'status': 'refused'})

                offer.property_id.write({'selling_price': offer.price})

            accepted_offers_after_write = self.filtered(lambda offer: offer.status == 'accepted')

            if len(accepted_offers_before_write) != len(accepted_offers_after_write):
                raise ValidationError("Only Offer Can be Accepted.")

        return super(EstatePropertyOffer, self).write(vals)

    def accept_offer(self):
        for offer in self:
            if offer.status != 'accepted':
                other_accepted_offers = self.property_id.offer_ids.filtered(lambda o: o.status == 'accepted' and o != offer)
                other_accepted_offers.write({'status': 'refused'})
                offer.status = 'accepted'
                if not self.property_id.offer_ids.filtered(lambda o: o.status == 'accepted' and o != offer):
                    self.property_id.buyer_id = offer.buyer_id

    def refuse_offer(self):
        for offer in self:
            if offer.status != 'refused':
                offer.status = 'refused'
                if offer.status == 'accepted':
                    offer.property_id.buyer_id = False
