# encoding: utf-8

from frictionless import Check, errors

class header_rule_2_4_first_char(Check):
    ''' 
    Column headers must begin with an alphabetic letter. 
    '''
    Errors = [errors.ForbiddenLabelError]
    def validate_row(self, row):
        for field_number, header in enumerate(list(row)):
            if not header[0].isalpha():
                note = 'Column name must begin with an alphabetic letter.'
                yield errors.ForbiddenLabelError(note=note, 
                                                row_numbers=list(range(1,len(list(row))+1)),
                                                label=header,
                                                labels=list(row),
                                                field_number=field_number+1,
                                                field_name=header)