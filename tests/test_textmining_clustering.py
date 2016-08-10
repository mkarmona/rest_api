import unittest, json


from app import create_app
from tests import GenericTestCase

class ClusteringTestCase(GenericTestCase):
    
    def testClusteringSigTerms(self):
        target = 'ENSG00000171105'
        dataype = 'literature'
        disease = 'EFO_0000400'
        clustering_algorithm = 'significant_terms_agg'
        clustering_field = 'evidence.literature_ref.mined_sentences.text'
        print "Testing Clustering using Significant Terms Aggregations"
      
        response = self._make_request('/api/latest/private/evidence/clustertest',
                                      data=json.dumps({'target':[target],
                                            'datatype':[dataype],
                                            'disease' :[disease],
                                            'clustering_algorithm':clustering_algorithm,
                                            'clustering_field':clustering_field,
                                            'direct':True,
                                            'size': 10
                                            }),content_type='application/json',
                                      method = 'POST',
                                      token=self._AUTO_GET_TOKEN)
 
    
        self.assertTrue(response.status_code == 200)
        
        json_response = json.loads(response.data.decode('utf-8'))
        print "Facets -------------"
        print json_response['facets']
        self.assertIsNotNone(json_response['facets'])
         
    def testClusteringSampler(self):
        target = 'ENSG00000171105'
        dataype = 'literature'
        disease = 'EFO_0000400'
        clustering_algorithm = 'sampler_agg'
        clustering_field = 'evidence.literature_ref.mined_sentences.text'
        print "Testing Clustering using Sampler Aggregations"
      
        response = self._make_request('/api/latest/private/evidence/clustertest',
                                      data=json.dumps({'target':[target],
                                            'datatype':[dataype],
                                            'disease' :[disease],
                                            'clustering_algorithm':clustering_algorithm,
                                            'clustering_field':clustering_field,
                                            'sampler_shardsize': 500,
                                            'direct':True,
                                            'size': 10
                                            }),content_type='application/json',
                                      method = 'POST',
                                      token=self._AUTO_GET_TOKEN)
 
    
        self.assertTrue(response.status_code == 200)
        
        json_response = json.loads(response.data.decode('utf-8'))
        print "Facets -------------"
        print json_response['facets']
        self.assertIsNotNone(json_response['facets'])
       
    def testClusteringCarrotLingo(self):
        target = 'ENSG00000171105'
        dataype = 'literature'
        disease = 'EFO_0000400'
        clustering_algorithm = 'lingo_clustering'
        clustering_field = 'fields.evidence.literature_ref.mined_sentences.text'
        datastructure = 'clusters'
        carrot_title = '_source.target.target_name'
        print "Testing Clustering using ES Carrot2 Plugin - Lingo Algorithm"
     
        response = self._make_request('/api/latest/private/evidence/clustertest',
                                      data=json.dumps({'target':[target],
                                            'datatype':[dataype],
                                            'disease' :[disease],
                                            'clustering_algorithm':clustering_algorithm,
                                            'clustering_field':clustering_field,
                                            'carrot_title':carrot_title,
                                            
                                            'datastructure':datastructure,
                                            'direct':True,
                                            'size': 10,'carrot_algo_size':1000
                                            }),content_type='application/json',
                                      method = 'POST',
                                      token=self._AUTO_GET_TOKEN)

   
        self.assertTrue(response.status_code == 200)
       
        json_response = json.loads(response.data.decode('utf-8'))
        print json_response['clusters']
      
    

if __name__ == "__main__":
    unittest.main()
