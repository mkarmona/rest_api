'''
Created on Aug 2, 2016

@author: priyanka

Adapter specific to clustering of text mining data
Algorithms supported - Significant Terms Aggregation, Sampler Aggregation, Carrot2 Clustering - Kmeans,STC,Lingo

'''


from flask import  current_app,request
from request_templates import ClusteringTypes,SourceDataStructureOptions
from elasticsearchclient import BooleanFilterOperator
from app.common.results import PaginatedResult,PaginatedCarrotResult
from config import Config
import time
from elasticsearch.client.utils import _make_path

class ESClusteringQuery():
    
    def __init__(self):
        self.es = current_app.extensions['esquery']
        
    def getClusterFacets(self,
                              
                     targets=[],
                     diseases=[],
                     evidence_types=[],
                     datasources=[],
                     datatypes=[],
                     gene_operator='OR',
                     object_operator='OR',
                     **kwargs):
        params = QueryParams( **kwargs)
        es_clustering_builder = ClusterQueryBuilder(self.es)
        return es_clustering_builder.getClusters(params)
        
        
             
    
class ClusteringHandler(object):
    
    '''
    base handler to build an ES clustering query
    to be subclassed by implementations
    '''
    def __init__(self,
                params):
        self.params = params
        self.query_body = {}
    

    def build_query_clause(self, es, gene_operator='OR',
                     object_operator='OR'):
        '''convert boolean to elasticsearch bool syntax'''
        gene_operator = getattr(BooleanFilterOperator, gene_operator.upper())
        object_operator = getattr(BooleanFilterOperator, object_operator.upper())
        
        '''create multiple condition boolean query'''
        conditions = []
        if self.params.targets:
            conditions.append(es.get_complex_target_filter(self.params.targets, gene_operator))
        if self.params.diseases:
            conditions.append(es.get_complex_disease_filter(self.params.diseases, object_operator, is_direct=False))
        if self.params.datasources or self.params.datatypes:
            requested_datasources = []
            if self.params.datasources:
                requested_datasources.extend(self.params.datasources)
            if self.params.datatypes:
                for datatype in self.params.datatypes:
                    requested_datasources.extend(es.datatypes.get_datasources(datatype))
            requested_datasources = list(set(requested_datasources))
            conditions.append(
                es._get_datasource_query(requested_datasources, BooleanFilterOperator.OR))
         
        '''boolean query joining multiple conditions with an AND'''
       
        self.query_body = {
                      "query": {
                            "bool": { 
                               "must": conditions
                                    }
                                },
            
                      }
       

    def build_agg_clause(self):
        pass

    def build_filter_clause(self):
        raise NotImplementedError
    
    def query_es(self, es):
        return es._cached_search(index=es._index_data,
                                  body=self.query_body,
                                  timeout="10m")

class SigTermsAggClustering(ClusteringHandler):
    
    def build_query_clause(self, es, gene_operator='OR',
                     object_operator='OR'):
        super(SigTermsAggClustering,self).build_query_clause(es = es)
         
    def build_agg_clause(self):
        self.query_body['aggs'] = self._get_sig_terms_aggregation(self.params)
        
    
    def _get_sig_terms_aggregation(self, clustering_params):
        
        return {
                  "most_sig_terms": {
                    "significant_terms": {
                        "field": clustering_params.clustering_field
                    }
                                             }
                  
        }
        
    def query_es(self,es):
        return PaginatedResult(super(SigTermsAggClustering,self).query_es(es),self.params)
    
    def build_filter_clause(self):
        raise NotImplementedError
        
class SamplerAggClustering(ClusteringHandler):
    
    def build_query_clause(self, es, gene_operator='OR',
                     object_operator='OR'):
        super(SamplerAggClustering,self).build_query_clause(es = es)
    
    def build_agg_clause(self):
        self.query_body['aggs'] = self._get_sampler_aggregation( self.params) 
    
    def _get_sampler_aggregation(self, clustering_params ):
        
        return {
                "sample": {
                    "sampler": {
                        "shard_size": clustering_params.sampler_shardsize
                
                                },
                    "aggs": {
                        "significantDiseaseTerms": {
                            "significant_terms": {
                                "field": clustering_params.clustering_field
                            }
                        }
                    }
                }
        }
    
    def query_es(self,es):
        return PaginatedResult(super(SamplerAggClustering,self).query_es(es),self.params)
    
    def build_filter_clause(self):
        raise NotImplementedError


class CarrotClustering(ClusteringHandler):
    
    def build_query_clause(self, es, gene_operator='OR',
                     object_operator='OR'):
        
        super(CarrotClustering,self).build_query_clause(es = es)
        query_clause = self.query_body.pop("query")
        self.query_body['search_request'] = {"query" : query_clause, "size" : self.params.carrot_algo_size}
        self.query_body['query_hint'] = ''
        title = [self.params.carrot_title]
        content = [self.params.clustering_field]
        self.query_body['field_mapping'] = {"title": title,
                                            "content": content}
        self.query_body['algorithm'] = 'lingo'
        print self.query_body
    
    def build_agg_clause(self):
        pass
    
    def query_es(self,es):
        return PaginatedCarrotResult(self._cached_search_with_clustering(es=es,index=es._index_data,
                                  body=self.query_body),self.params)
    
    def _cached_search_with_clustering(self, es,*args, **kwargs):
        key = str(args)+str(kwargs)
        no_cache = Config.NO_CACHE_PARAMS in request.values
        res = None
        if not no_cache:
            res = es.cache.get(key)
        if res is None:
            start_time = time.time()
            res = self._search_with_carrot_clustering(es ,**kwargs)
            took = int(round(time.time() - start_time))
            es.cache.set(key, res, took*60)
        return res
    
    def _search_with_carrot_clustering(self,esQuery, index=None, doc_type=None, body=None, params=None):
        if params:
            if 'from_' in params:
                params['from'] = params.pop('from_')

        if doc_type and not index:
            index = '_all'
        data = esQuery.handler.transport.perform_request('POST', _make_path(index,
            doc_type, '_search_with_clusters'), params=params, body=body)
        return data
    
    def build_filter_clause(self):
        raise NotImplementedError
          
class ClusterQueryBuilder():
    
    _CLUSTERING_HANDLER_MAP = { 
                ClusteringTypes.SIGNIFICANT_TERMS_AGG : SigTermsAggClustering,
                ClusteringTypes.SAMPLER_AGG : SamplerAggClustering,
                ClusteringTypes.KMEANS_CARROT_CLUSTERING : CarrotClustering,
                ClusteringTypes.STC_CARROT_CLUSTERING : CarrotClustering,
                ClusteringTypes.LINGO_CARROT_CLUSTERING : CarrotClustering
                
    }   
     
    def __init__(self, es):
        self.es = es 
    
    def getClusters(self, params):
        clusteringHandler = self._CLUSTERING_HANDLER_MAP[params.clustering_algorithm](params=params)
        clusteringHandler.build_query_clause(self.es)
        clusteringHandler.build_agg_clause()
        return clusteringHandler.query_es(self.es)
      
class QueryParams():
    _max_search_result_limit = 10000
    _default_return_size = 10
    
    def __init__(self, **kwargs):
        
        self.targets = kwargs.pop('target',[]) or []
        self.diseases = kwargs.pop('disease',[]) or []
        self.datasources =  kwargs.pop('datasource',[]) or []
        self.datatypes=  kwargs.pop('datatype',[]) or []
        
        self.clustering_algorithm = kwargs.get('clustering_algorithm')
        self.clustering_field = kwargs.get('clustering_field')
        
        self.carrot_title = kwargs.get('carrot_title')
        self.carrot_content = kwargs.get('carrot_content')
        self.sampler_shardsize = kwargs.get('sampler_shardsize')
        
        self.datastructure = kwargs.get('datastructure',
                                        SourceDataStructureOptions.DEFAULT) or SourceDataStructureOptions.DEFAULT

        self.format = kwargs.get('format', 'json') or 'json'
        self.size = kwargs.get('size', self._default_return_size)
        self.carrot_algo_size = kwargs.get('carrot_algo_size')
        
        if self.size is None:
            self.size =  self._default_return_size
        if (self.size > self._max_search_result_limit):
            raise AttributeError('Size cannot be bigger than %i'%self._max_search_result_limit)

        self.start_from = kwargs.get('from', 0) or 0
        
    
