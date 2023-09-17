{
  'name': "Real-Estate Management",
  'version': '1.0',
  'depends': ['base'],

  'author': "hammad",

  'category': 'Category',

  'description': """

  This is a test module of Real-Estate Management!

  Written for the Odoo Quickstart Tutorial.

  """,

  # data files always loaded at installation

  'data': [
    'security/ir.model.access.csv',
    'views/estate_property_views.xml',
    'views/property_type_view.xml',
    'menu/estate_menus.xml',
    'views/res_users_view.xml',
    'views/property_tag_view.xml',



  ],

  'installable': True,

  'auto_install': False,

  'application': True,
}
