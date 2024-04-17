# encoding: utf-8

from frictionless import Check, errors

class data_entry_rule_2_6_bullet_lists(Check):
    ''' 
    Cell value cannot contain a bullet list.
    Skip check for non-string cells.
    '''
    Errors = [errors.ForbiddenValueError]
    def validate_row(self, row):
        for header in list(row):
            this_cell = row[header]
            if isinstance(this_cell, str):
                list_chars = [u'•', u'* ', u'- ', u'â€”', u'\n',  u'\t'] # u'â€”' is em-dash
                bullet_check = [ele for ele in list_chars if(ele in this_cell.rstrip())] # strip any trailing spaces
                if len(bullet_check) > 0:
                    note = 'Cell value cannot contain bullets, dashes, new line or tab characters. Please make separate rows.'
                    yield errors.ForbiddenValueError.from_row(row, 
                                                            note=note,
                                                            field_name=header)