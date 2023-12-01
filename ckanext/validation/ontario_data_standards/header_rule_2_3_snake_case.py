# encoding: utf-8

import re
from frictionless import Check, errors

class header_rule_2_3_snake_case(Check):
    ''' 
    Column headers must be in snake case. 
    Requirements to satisfy snake_case:
        * header name composed only by lowercase letters ([a-z])
        * multiple words separated by underscore
    '''
    Errors = [errors.ForbiddenLabelError]
    def validate_row(self, row):
        note = 'Column name must all be in lower case, and for multiple words, separate them with an underscore.'
        for field_number, header in enumerate(list(row)):
            is_valid = []
            if bool(re.search(r"\s", header)):
                is_valid.append(False)
                
            else:
                for el in header:
                    if el.isupper():
                        is_valid.append(False)
                        

            if len(list(filter(lambda x: (x == False), is_valid))) > 0:    
                yield errors.ForbiddenLabelError(note=note, 
                                                row_numbers=list(range(1,len(list(row))+1)),
                                                label=header,
                                                labels=list(row),
                                                field_number=field_number+1,
                                                field_name=header)
