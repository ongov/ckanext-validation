# encoding: utf-8

from frictionless import Check, errors

class header_rule_2_4_first_char(Check):
    ''' 
    Column headers must begin with an alphabetic letter. 
    '''
    Errors = [errors.ForbiddenLabelError]
    def validate_start(self):
        headers = self.resource.labels
        for field_number, header in enumerate(headers):
            if len(header) > 0 and not header[0].isalpha():
                note = 'Column name must begin with an alphabetic letter.'
                yield errors.ForbiddenLabelError(note=note, 
                                                row_numbers=list(range(1,len(headers)+1)),
                                                label=header,
                                                labels=headers,
                                                field_number=field_number+1,
                                                field_name=header)