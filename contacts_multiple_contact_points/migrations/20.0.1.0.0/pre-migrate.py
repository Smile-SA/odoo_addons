# (C) 2020 Smile (<http://www.smile.fr>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""The 'mobile' contact point type is removed: mobile points become phone points."""


def migrate(cr, version):
    if not version:
        return
    # 1. Drop mobile points whose number already exists as a phone point
    #    for the same partner (the phone one is made main if needed).
    cr.execute("""
        UPDATE res_partner_contact_point ph
           SET is_default = TRUE
          FROM res_partner_contact_point mo
         WHERE mo.contact_point_type = 'mobile' AND mo.is_default
           AND ph.contact_point_type = 'phone'
           AND ph.partner_id = mo.partner_id AND ph.name = mo.name
           AND NOT EXISTS (
               SELECT 1 FROM res_partner_contact_point d
                WHERE d.partner_id = mo.partner_id
                  AND d.contact_point_type = 'phone' AND d.is_default)
    """)
    cr.execute("""
        DELETE FROM res_partner_contact_point mo
         USING res_partner_contact_point ph
         WHERE mo.contact_point_type = 'mobile'
           AND ph.contact_point_type = 'phone'
           AND ph.partner_id = mo.partner_id AND ph.name = mo.name
    """)
    # 2. A mobile point stays main only if the partner has no main phone.
    cr.execute("""
        UPDATE res_partner_contact_point mo
           SET is_default = FALSE
         WHERE mo.contact_point_type = 'mobile' AND mo.is_default
           AND EXISTS (
               SELECT 1 FROM res_partner_contact_point d
                WHERE d.partner_id = mo.partner_id
                  AND d.contact_point_type = 'phone' AND d.is_default)
    """)
    # 3. Tags: standard mobile tags are remapped to the phone ones,
    #    user-created mobile tags become phone tags (not main).
    for suffix in ('work', 'home', 'other'):
        cr.execute("""
            UPDATE res_partner_contact_point cp
               SET tag_id = pt.res_id
              FROM ir_model_data mt, ir_model_data pt
             WHERE mt.module = 'contacts_multiple_contact_points'
               AND mt.name = %s AND mt.model = 'res.partner.contact_point.tag'
               AND pt.module = 'contacts_multiple_contact_points'
               AND pt.name = %s AND pt.model = 'res.partner.contact_point.tag'
               AND cp.tag_id = mt.res_id
        """, ('mobile_tag_' + suffix, 'phone_tag_' + suffix))
    cr.execute("""
        UPDATE res_partner_contact_point_tag
           SET contact_point_type = 'phone', is_default = FALSE
         WHERE contact_point_type = 'mobile'
           AND id NOT IN (SELECT res_id FROM ir_model_data
                           WHERE model = 'res.partner.contact_point.tag'
                             AND module = 'contacts_multiple_contact_points'
                             AND name LIKE 'mobile_tag_%')
    """)
    # 4. Convert the points themselves.
    cr.execute("""
        UPDATE res_partner_contact_point
           SET contact_point_type = 'phone'
         WHERE contact_point_type = 'mobile'
    """)
    # 5. res_partner.phone is stored: align it with the main phone point.
    cr.execute("""
        UPDATE res_partner p
           SET phone = cp.name
          FROM res_partner_contact_point cp
         WHERE cp.partner_id = p.id AND cp.contact_point_type = 'phone'
           AND cp.is_default AND p.phone IS DISTINCT FROM cp.name
    """)
