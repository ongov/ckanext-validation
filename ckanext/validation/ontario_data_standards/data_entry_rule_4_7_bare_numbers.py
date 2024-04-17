# encoding: utf-8

from frictionless import Check, errors

class data_entry_rule_4_7_bare_numbers(Check):
    ''' 
    Numeric cell values should be bare numbers.
    Current checks:
    - currency ("$")
    '''
    Errors = [errors.ForbiddenValueError]
    def validate_row(self, row):
        list_chars = [u'$']
        for header in list(row):
            note = []
            this_cell = row[header]
            if isinstance(this_cell, str) and [ele for ele in list_chars if(ele in this_cell)]:
                try:
                    if float(this_cell.strip("$").strip()):
                        note = 'Numeric cell values must be a bare number. Please strip the number of its unit and add the unit to the column name.'
                except ValueError:
                    pass

                if len(note) > 0:
                    yield errors.ForbiddenValueError.from_row(row, 
                                                            note=note,
                                                            field_name=header)
                