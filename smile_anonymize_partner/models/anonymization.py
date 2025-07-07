from odoo.tools.sql import SQL


def anonymize_emails(record_id, fields):
    """
    Create SQL fragments for anonymizing email fields.
    Returns a list of SQL objects for each field to be updated.
    """
    return [
        SQL(
            "%(field)s = CASE WHEN %(field)s IS NULL "
            "OR %(field)s = '' THEN %(field)s "
            "ELSE %(email_value)s END",
            field=SQL.identifier(field),
            email_value=f"{field.replace('.', '_')}"
            f"{record_id}-anonymise@anonymise.fr",
        )
        for field in fields
    ]


def anonymize_phones(fields):
    """
    Create SQL fragments for anonymizing phone fields.
    Returns a list of SQL objects for each field to be updated.
    """
    return [
        SQL(
            "%(field)s = CASE WHEN %(field)s IS NULL "
            "OR %(field)s = '' THEN %(field)s "
            "ELSE %(phone_value)s END",
            field=SQL.identifier(field),
            phone_value="+33000000000",
        )
        for field in fields
    ]


def anonymize_fields(record_id, fields):
    """
    Create SQL fragments for anonymizing general fields.
    Returns a list of SQL objects for each field to be updated.
    """
    return [
        SQL(
            "%(field)s = CASE WHEN %(field)s IS NULL "
            "OR %(field)s = '' THEN %(field)s "
            "ELSE %(field_value)s END",
            field=SQL.identifier(field),
            field_value=f"{field[:7]}{record_id}-anonym",
        )
        for field in fields
    ]


def is_anonymized_fields(fields):
    """
    Create SQL fragments for marking fields as anonymized.
    Returns a list of SQL objects for each field to be marked.
    """
    return [
        SQL("%(field)s = TRUE", field=SQL.identifier(field))
        for field in fields
    ]


def anonymize_object(
    self, table, record_id, fields_list=None, phones_list=None, email_list=None
):
    """
        Anonymize specified fields in a database table for a specific record.
        Uses SQL class to safely construct and execute the query.

        Args:
            table (str): Database table name
            record_id (int): ID of the record to anonymize
            fields_list (list): Regular fields to anonymize
            phones_list (list): Phone fields to anonymize
            email_list (list): Email fields to anonymize

        Returns:
            bool: True if anonymization was performed
    """
    update_parts = []
    if email_list:
        update_parts.extend(anonymize_emails(record_id, email_list))
    if phones_list:
        update_parts.extend(anonymize_phones(phones_list))
    if fields_list:
        update_parts.extend(anonymize_fields(record_id, fields_list))

    if update_parts:
        set_clause = SQL(", ").join(update_parts)
        self._cr.execute(SQL(
            "UPDATE %(table)s SET %(set_clause)s WHERE id = %(id)s",
            table=SQL.identifier(table),
            set_clause=set_clause,
            id=record_id
        ))

    return True
