# encoding: utf-8

from flask import Blueprint

from ckantoolkit import c, NotAuthorized, ObjectNotFound, abort, _, render, get_action

from ckan.plugins import toolkit
import ckan.plugins as p
import time

validation = Blueprint("validation", __name__)


def read(id, resource_id):
    print('HEI in ckanext validation blueprint py def read')

    try:
        validation = get_action(u"resource_validation_show")(
            {u"user": c.user}, {u"resource_id": resource_id}
        )

        resource = get_action(u"resource_show")({u"user": c.user}, {u"id": resource_id})

        dataset = get_action(u"package_show")(
            {u"user": c.user}, {u"id": resource[u"package_id"]}
        )

        # Needed for core resource templates
        c.package = c.pkg_dict = dataset
        c.resource = resource

        # # TEST XLOADER HOOK !!!
        # print('HEI in ckanext validation views py')  
        # callback_url = toolkit.url_for(
        #     "api.action", ver=3, logic_function="xloader_hook", qualified=True
        # )
        # input = {
        #     'result_url': callback_url,
        #     'metadata': {'resource_id': resource_id}
        # }
        # job_dict = dict(metadata=input['metadata'],
        #             status='running')

        # callback_xloader_hook(result_url=input['result_url'],
        #                      api_key=None,                   
        #                   job_dict=job_dict)


        # print('HEI in ckanext validation views py calling after_upload')  
        # for plugin in p.PluginImplementations(xloader_interfaces.IXloader):
        #     plugin.after_upload(resource, dataset)
       
        print('HEI in ckanext validation blueprints py')  

        return render(
            u"validation/validation_read.html",
            extra_vars={
                u"validation": validation,
                u"resource": resource,
                u"dataset": dataset,
                u"pkg_dict": dataset,
            },
        )

    except NotAuthorized:
        abort(403, _(u"Unauthorized to read this validation report"))
    except ObjectNotFound:

        abort(404, _(u"No validation report exists for this resource"))


validation.add_url_rule(
    "/dataset/<id>/resource/<resource_id>/validation", view_func=read
)
