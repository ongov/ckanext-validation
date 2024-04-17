# encoding: utf-8

from frictionless import Check, errors

class header_rule_2_2_header_length(Check):
    ''' 
    Column headers must be less than 63 characters long (PostgreSQL limit). 
    '''
    Errors = [errors.ForbiddenLabelError]
    def validate_start(self):
        headers = self.resource.labels
        note = 'Column name must be less than 63 characters long.'
        for field_number, header in enumerate(headers):
            if len(header) > 63:
                yield errors.ForbiddenLabelError(note=note, 
                                                row_numbers=list(range(1,len(headers)+1)),
                                                label=header,
                                                labels=headers,
                                                field_number=field_number+1,
                                                field_name=header)