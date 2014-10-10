# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Smile (<http://www.smile.fr>). All Rights Reserved
#                       author cydef@smile.fr
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from collections import namedtuple
from openerp.osv import fields, orm

from openerp.addons.connector.exception import MappingError
from openerp.addons.connector.unit.backend_adapter import BackendAdapter
from openerp.addons.connector.unit.mapper import (mapping, only_create, backend_to_m2o)
from openerp.addons.connector.exception import IDMissingInBackend
from openerp.addons.magentoerpconnect.unit.mapper import normalize_datetime
from openerp.addons.magentoerpconnect.backend import magento
from openerp.addons.magentoerpconnect.partner import (PartnerAdapter, PartnerImport, PartnerImportMapper, BaseAddressImportMapper,
                                                      PartnerAddressBook, AddressAdapter, AddressImportMapper)



class ResPartner(orm.Model):
    _inherit = 'res.partner'
    
    _columns = {
        'saleshop_id': fields.many2one('sale.shop', 'Magasin'),
    }


@magento(replacing=PartnerImport)
class ECommercePartnerImport(PartnerImport):

    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.magento_record
        if record['partner_category_id']:
            self._import_dependency(record['partner_category_id'], 'magento.res.partner.category')
    
    def _get_magento_data(self):
        
        # Here, we should ask for magento data
        # Customer_id, shipping_address_id, billing_address_id and product_id are the IDs on Magento
        
        partner = {
            "email": "wonderful@email.com",
            "created_at": "2014-12-23 09:41:28",
            "updated_at": "2014-12-23 09:41:28",
            "name": "Wonderful Partner",
            "ecommerce_store_id": "StoreOnMagentoID",
            "is_company": False,
            "customer": True,
            "partner_category_id": "",
            "title": "Miss",
        }
        return partner


@magento(replacing=PartnerAdapter)
class ECommercePartnerAdapter(PartnerAdapter):

    def search(self, filters=None, from_date=None, to_date=None, magento_website_ids=None):

        # TODO : Replace this by the API used to return the fields we need.
        # Keep the same name for the API method (search), but change the model
        # For the moment : customer.search
        return [1]


@magento(replacing=PartnerImportMapper)
class ECommercePartnerImportMapper(PartnerImportMapper):

    direct = [
        ('email', 'email'),
        (normalize_datetime('created_at'), 'created_at'),
        (normalize_datetime('updated_at'), 'updated_at'),
        ('name', 'name'),
        ('partner_category_id', 'group_id'),
        ('is_company', 'is_company'),
        ('customer', 'customer'),
    ]

    @mapping
    def partner_category_id(self, record):
        if record.get('partner_category_id', False):
            binder = self.get_binder_for_model('magento.res.partner.category')
            try:
                category_id = binder.to_openerp(record['partner_category_id'], unwrap=True)
            except AssertionError:
                raise MappingError("The partner category with magento id {} does not exist", format(record['group_id']))
            return {'category_id': [(4, category_id)]}

    @mapping
    def title(self, record):
        prefix = record['title']
        if prefix:
            title_ids = self.session.search('res.partner.title', [('shortcut', 'ilike', prefix)])
            if title_ids:
                return {'title': title_ids[0]}

    @mapping
    def ecommerce_store_id(self, record):
        ecommerce_store_id = record['ecommerce_store_id']
        binder = self.get_binder_for_model('magento.store')
        try:
            saleshop_id = binder.to_openerp(ecommerce_store_id, unwrap=True)
        except AssertionError:
            raise MappingError("The saleshop with magento id {} does not exist", format(ecommerce_store_id))

        ecommerce_store_id = self.session.search('magento.store', [('magento_id','=',ecommerce_store_id)])
        website_id = self.session.browse('magento.store', ecommerce_store_id)[0].website_id.id

        return {'saleshop_id': saleshop_id, 'website_id': website_id}

    @only_create
    @mapping
    def openerp_id(self, record):
        """Overwrite"""
        pass
    
    @only_create
    @mapping
    def customer(self, record):
        """Overwrite"""
        pass
    
    @mapping
    def lang(self, record):
        """Overwrite"""
        pass

    @mapping
    def website_id(self, record):
        """Overwrite"""
        pass
    
    @mapping
    def customer_group_id(self, record):
        """Overwrite"""
        pass

    @only_create
    @mapping
    def is_company(self, record):
        """Overwrite"""
        pass

    @mapping
    def names(self, record):
        """Overwrite"""
        pass

AddressInfos = namedtuple('AddressInfos', ['magento_record', 'partner_binding_id', 'merge'])


@magento(replacing=PartnerAddressBook)
class ECommercePartnerAddressBook(PartnerAddressBook):

    def _get_address_infos(self, magento_partner_id, partner_binding_id):
        get_unit = self.get_connector_unit_for_model
        adapter = get_unit(BackendAdapter)
        mag_address_ids = adapter.search({'customer_id': {'eq': magento_partner_id}})
        if not mag_address_ids:
            return
        for address_id in mag_address_ids:
            magento_record = adapter.read(address_id)

            # We don't wanna merge anything. Code removed
            address_infos = AddressInfos(magento_record=magento_record,
                                         partner_binding_id=partner_binding_id,
                                         merge=False)
            yield address_id, address_infos


@magento(replacing=AddressAdapter)
class ECommerceAddressAdapter(AddressAdapter):
    _model_name = 'magento.address'
    _magento_model = 'customer_address'

    def search(self, filters=None):
        """ Overwritten for tests """
#         return [int(row['customer_address_id']) for row
#                 in self._call('%s.list' % self._magento_model, [filters] if filters else [{}])]
        return [1]
    
    def read(self, id, attributes=None):
        """ Overwritten for tests """
        address = {
            "postcode": 91140,
            "city": "Villejust",
            "country_id": "BH",
            "name": 'Adresse Contact',
            "street": "3 rue du bois courtin\n 2ème ligne de l'adresse",
            "phone": "03948274",
            "fax": "FAXNUMBER",
            "is_default_billing": True,
            "is_default_shipping": True,
        }
        
        return address

######################## 
# Monkey patch : 
# BaseAddressImportMapper is not a @magento class, so we can't overwrite his mapping methods with a replacing=xxx
    
    @mapping
    def new_title(self, record):
        """Overwrite"""
        pass
    
    @mapping
    def new_state(self, record):
        """Overwrite"""
        pass
    
    BaseAddressImportMapper.state = new_state
    BaseAddressImportMapper.title = new_title

# We still use the mapping methods "street" and "country" of BaseAddressImportMapper
#######################

@magento(replacing=AddressImportMapper)
class ECommerceAddressImportMapper(AddressImportMapper):

    direct = [
        ('is_default_billing', 'is_default_billing'),
        ('is_default_shipping', 'is_default_shipping'),
        ('name', 'name'),
        ('phone', 'phone'),
        ('fax', 'fax'),
        ('postcode', 'zip'),
        ('city', 'city'),
    ]
    
    @mapping
    def names(self, record):
        """Overwrite"""
        pass
