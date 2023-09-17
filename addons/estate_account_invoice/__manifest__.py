{
    'name': "Real Estate Account Invoice Management",
    'version': '1.0',
    'depends': ['base', 'estate'],
    'author': "hammad",
    'category': 'Category',
    'description': """
        This is a assignment module of Account Invoice Management!
        Assigned by Axiom.
    """,

    'data': [
      'security/ir.model.access.csv',
      'views/estate_property_invoice_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
