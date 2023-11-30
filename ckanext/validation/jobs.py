# encoding: utf-8

import logging
import datetime
import json
import re

import requests
from sqlalchemy.orm.exc import NoResultFound
from frictionless import validate, system, Report, Schema, Dialect, Check, errors

from ckan.model import Session
import ckan.lib.uploader as uploader

import ckantoolkit as t

from ckanext.validation.model import Validation
from ckanext.validation.utils import get_update_mode_from_config


log = logging.getLogger(__name__)


def run_validation_job(resource):

    log.debug('Validating resource %s', resource['id'])

    try:
        validation = Session.query(Validation).filter(
            Validation.resource_id == resource['id']).one()
    except NoResultFound:
        validation = None

    if not validation:
        validation = Validation(resource_id=resource['id'])

    validation.status = 'running'
    Session.add(validation)
    Session.commit()

    options = t.config.get(
        'ckanext.validation.default_validation_options')
    if options:
        options = json.loads(options)
    else:
        options = {}

    resource_options = resource.get('validation_options')
    if resource_options and isinstance(resource_options, str):
        resource_options = json.loads(resource_options)
    if resource_options:
        options.update(resource_options)

    dataset = t.get_action('package_show')(
        {'ignore_auth': True}, {'id': resource['package_id']})

    source = None
    if resource.get('url_type') == 'upload':
        upload = uploader.get_resource_uploader(resource)
        if isinstance(upload, uploader.ResourceUpload):
            source = upload.get_path(resource['id'])
        else:
            # Upload is not the default implementation (ie it's a cloud storage
            # implementation)
            pass_auth_header = t.asbool(
                t.config.get('ckanext.validation.pass_auth_header', True))
            if dataset['private'] and pass_auth_header:
                s = requests.Session()
                s.headers.update({
                    'Authorization': t.config.get(
                        'ckanext.validation.pass_auth_header_value',
                        _get_site_user_api_key())
                })

                options['http_session'] = s

    if not source:
        source = resource['url']
    
    # If the CKAN UI dict has been passed in, assign it to schema
    if 'ui_dict' in resource and len(resource['ui_dict']) > 0:
        schema = resource.get('ui_dict')
    else:
        schema = resource.get('schema')
    # schema = resource.get('schema')
    # if schema:
    #     if isinstance(schema, str):
    #         if schema.startswith('http'):
    #             r = requests.get(schema)
    #             schema = r.json()
    #         schema = json.loads(schema)

    _format = resource['format'].lower()
    report = _validate_table(source, _format=_format, schema=schema, **options)

    # Hide uploaded files
    if type(report) == Report:
        report = report.to_dict()

    if 'tasks' in report:
        for table in report['tasks']:
            if table['place'].startswith('/'):
                table['place'] = resource['url']
    if 'warnings' in report:
        validation.status = 'error'
        for index, warning in enumerate(report['warnings']):
            report['warnings'][index] = re.sub(r'Table ".*"', 'Table', warning)
    if 'valid' in report:
        validation.status = 'success' if report['valid'] else 'failure'
        validation.report = json.dumps(report)
    else:
        validation.report = json.dumps(report)
        if 'errors' in report and report['errors']: 
            validation.status = 'error'
            validation.error = {
                'message': [str(err) for err in report['errors']]}
        else:
            validation.error = {'message': ['Errors validating the data']}
    validation.finished = datetime.datetime.utcnow()

    Session.add(validation)
    Session.commit()

    # Store result status in resource
    data_dict = {
        'id': resource['id'],
        'validation_status': validation.status,
        'validation_timestamp': validation.finished.isoformat(),
    }

    if get_update_mode_from_config() == 'sync':
        data_dict['_skip_next_validation'] = True,

    patch_context = {
        'ignore_auth': True,
        'user': t.get_action('get_site_user')({'ignore_auth': True})['name'],
        '_validation_performed': True
    }
    t.get_action('resource_patch')(patch_context, data_dict)




def _validate_table(source, _format='csv', schema=None, **options):

    # This option is needed to allow Frictionless Framework to validate absolute paths
    frictionless_context = { 'trusted': True }
    http_session = options.pop('http_session', None) or requests.Session()
    use_proxy = 'ckan.download_proxy' in t.config

    if use_proxy:
        proxy = t.config.get('ckan.download_proxy')
        log.debug('Download resource for validation via proxy: %s', proxy)
        http_session.proxies.update({'http': proxy, 'https': proxy})

    frictionless_context['http_session'] = http_session
    resource_schema = Schema.from_descriptor(schema) if schema else None

    # Load the Resource Dialect as described in https://framework.frictionlessdata.io/docs/framework/dialect.html
    if 'dialect' in options:
        dialect = Dialect.from_descriptor(options['dialect'])
        options['dialect'] = dialect

    # Load the list of checks and its parameters declaratively as in https://framework.frictionlessdata.io/docs/checks/table.html
    if 'checks' in options:
        checklist = [Check.from_descriptor(c) for c in options['checks']]
        options['checks'] = checklist

    with system.use_context(**frictionless_context):
        #report = validate(source, format=_format, schema=resource_schema, **options)
        # FOR TESTING ONLY!!!
        report = validate(source, 
                          format=_format, 
                          schema=resource_schema,
                          checks=[header_rule_2_2_header_length(),
                                  header_rule_2_3_snake_case(),
                                  header_rule_2_4_underscore(),
                                  data_entry_rule_2_6_bullet_lists()])
        log.debug('Validating source: %s', source)

    return report


def _get_site_user_api_key():

    site_user_name = t.get_action('get_site_user')({'ignore_auth': True}, {})
    site_user = t.get_action('get_site_user')(
        {'ignore_auth': True}, {'id': site_user_name})
    return site_user['apikey']


# WORKS AS A CellError using custom class in frictionless errors/cell.py
# class header_rule_2_4_underscore(Check):
#     Errors = [errors.ForbiddenHeaderError]
#     def validate_row(self, row):
#         for header in list(row):
#             if header[0]=='_':
#                 note = 'Column header cannot begin with an underscore.'
#                 yield errors.ForbiddenHeaderError.from_row(row, note=note, field_name=header)

# Define custom LabelError checks for header rules.
# Uses custom class ForbiddenLabelError in frictionless errors/label.py
class header_rule_2_2_header_length(Check):
    ''' 
    Column headers must be less than 63 characters long (PostgreSQL limit). 
    '''
    Errors = [errors.ForbiddenLabelError]
    def validate_row(self, row):
        note = 'Column name must be less than 63 characters long.'
        for field_number, header in enumerate(list(row)):
            if len(header) > 63:
                yield errors.ForbiddenLabelError(note=note, 
                                                row_numbers=list(range(1,len(list(row))+1)),
                                                label=header,
                                                labels=list(row),
                                                field_number=field_number+1,
                                                field_name=header)

class header_rule_2_3_snake_case(Check):
    ''' 
    Column headers must be in snake case. 
    Requirements to satisfy snake_case:
        * header name composed only by lowercase letters ([a-z])
        * multiple words separated by underscore
    '''
    Errors = [errors.ForbiddenLabelError]
    def validate_row(self, row):
        note = 'Column name must be in snake_case: use lower case only and replace any space separators with underscore.'
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

class header_rule_2_4_underscore(Check):
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

# Data entry rules
class data_entry_rule_2_6_bullet_lists(Check):
    ''' 
    Cell value cannot contain a bullet list. 
    '''
    Errors = [errors.ForbiddenValueError]
    def validate_row(self, row):
        for header in list(row):
            this_cell = row[header]
            list_chars = [u'•', u'*', u'- ', u'â€”', u'\n',  u'\t'] # u'â€”' is em-dash
            bullet_check = [ele for ele in list_chars if(ele in this_cell)]
            if len(bullet_check) > 0:
                note = 'Cell value cannot contain bullets, dashes, new line or tab characters. Please make separate rows.'
                yield errors.ForbiddenValueError.from_row(row, 
                                                        note=note,
                                                        field_name=header)