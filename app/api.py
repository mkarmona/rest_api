__author__ = 'andreap'

from flask.ext.restful import Api
from flask.ext.restful.utils import cors
from flask_restful_swagger import swagger

def create_api(app, api_version = '0.0', specpath = '' ):
    api = swagger.docs(Api(app,
                           decorators=[cors.crossdomain(origin='*')],
                            ),
                       basePath='http://localhost:8080',
                       resourcePath='/',
                       produces=["application/json", "text/xml"],
                       api_spec_url=specpath,
                       description='CTTV REST API',
                       apiVersion=api_version,
                       swaggerVersion=1.2,
                   )
    '''define api'''
    # api = restful.Api(app)
    # Wrap the Api with swagger.docs. It is a thin wrapper around the Api class that adds some swagger smarts

    from app.resources.genes import GeneInfo
    from app.resources.evidence import Evidence, FilterBy
    from app.resources.efo import EfoLabelFromCode
    from app.resources.evidenceontology import EcoLabelFromCode
    from app.resources.freetextsearch import FreeTextSearch, AutoComplete
    from app.resources.echo import Echo
    from app.resources.association import Association
    from app.resources.auth import RequestToken, ValidateToken





    # api.add_resource(AvailableGenes,
    #                  basepath+'/available-genes')
    api.add_resource(Evidence,
                     '/getbyid',
                     )
    api.add_resource(FilterBy,
                     '/filterby',
                     )
    api.add_resource(Association,
                     '/association',
                     )
    api.add_resource(EfoLabelFromCode,
                     '/efo/<string:code>')
    api.add_resource(EcoLabelFromCode,
                     '/eco/<string:code>')
    api.add_resource(GeneInfo,
                     '/gene/<string:gene_id>')
    api.add_resource(FreeTextSearch,
                     '/search')
    api.add_resource(AutoComplete,
                     '/autocomplete')
    api.add_resource(Echo,
                     '/echo')
    api.add_resource(RequestToken,
                     '/auth/request_token')
    api.add_resource(ValidateToken,
                     '/auth/validate_token')
    return api