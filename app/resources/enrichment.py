from flask.ext.restful.inputs import boolean
from flask.ext.restful.reqparse import Argument
from app.common import boilerplate


from flask import current_app, request
from flask.ext import restful
from flask.ext.restful import abort, fields, marshal,marshal_with
from flask.ext.restful import reqparse
from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.request_templates import FilterTypes
from app.common.response_templates import CTTVResponse
from types import *
import time


__author__ = 'andreap'

MAX_ELEMENT_SIZE = 1000

class EnrichmentTargets(restful.Resource):

    parser = reqparse.RequestParser()
    parser.add_argument('target', type=str, action='append', required=True, )
    parser.add_argument('pvalue', type=float, required=False, default=0.001)
    parser.add_argument('from', type=int, required=False, default=0)
    parser.add_argument('size', type=int, required=False, default=10)


    @is_authenticated
    @rate_limit
    def get(self):
        """
        Get enriched disease from a set of targets
        """

        args = self.parser.parse_args()
        if len(args['target']) > MAX_ELEMENT_SIZE:
            abort(404, message='maximum number of targets allowed is %i' % MAX_ELEMENT_SIZE)
        return self.get_enrichment_for_targets(args['target'],
                                               args['pvalue'],
                                               args['from'],
                                               args['size'])

    @is_authenticated
    @rate_limit
    def post(self ):
        """
        Get enriched disease from a set of targets

        """

        args = request.get_json(force=True)
        self.remove_empty_params(args)
        if len(args['target']) > MAX_ELEMENT_SIZE:
            abort(404, message='maximum number of targets allowed is %i' % MAX_ELEMENT_SIZE)

        return self.get_enrichment_for_targets(args['target'],
                                               args['pvalue'],
                                               args['from'],
                                               args['size'])


    def get_enrichment_for_targets(self,
                                   targets,
                                   pvalue,
                                   from_,
                                   size):
        es = current_app.extensions['esquery']

        res = es.get_enrichment_for_targets(targets,
                                            pvalue_threshold=pvalue,
                                            from_=from_,
                                            size=size)
        if not res:
            abort(404, message='Cannot find diseases for targets %s'%str(targets))
        return CTTVResponse.OK(res)


    def remove_empty_params(self,args):
        for k,v in args.items():
            if isinstance(v, list):
                if len(v)>0:
                    drop = True
                    for i in v:
                        if i != '':
                            drop =False
                    if drop:
                        del args[k]