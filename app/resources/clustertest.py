'''
Created on Jul 26, 2016

@author: priyankaw
'''
import time


from flask.ext import restful


from app.common.auth import is_authenticated
from app.common.rate_limit import rate_limit
from app.common.response_templates import CTTVResponse
from flask import  current_app, request
from app.common.esclusteringadapter import ESClusteringQuery


class EvidenceCluster(restful.Resource):
    
    @is_authenticated
    @rate_limit
    def get(self ):
        print "In get of clustertest"
        
    
    @is_authenticated
    @rate_limit
    def post(self ):
        """
        Get a list of evidence data clusters - based on specific clustering field e.g. abstract
    
        """
       # import pydevd;pydevd.settrace()
        start_time = time.time()
        args = request.get_json(force=True)
        data=self.get_evidence_clusters( params=args)
        return CTTVResponse.OK(data,
                               took=time.time() - start_time)
        
        

    def get_evidence_clusters(self,
                     params ={}):

        
        es_clustering = ESClusteringQuery()
        res = es_clustering.getClusterFacets(
                              **params)
        return res
