import neo4j
import numpy as np
from collections import deque

class neo4j_client():
    def __init__(self, uri, user, password, log_path=None):
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        self.log_path = log_path
        if self.log_path:
            f = open(log_path, 'w')
            f.close()
    
    def runCQL(self, cql, print_cql=False):
        session = self.driver.session()
        result = None
        try:
            if print_cql:
                print(cql)
            result = session.run(cql).data()
            #print(re.sub(r'\s+', ' ', cql))
        except neo4j.exceptions.Neo4jError as err:
            if self.log_path is not None:
                f = open(self.log_path, 'w')
                f.write(cql + '\n')
                f.write(str(err))
                f.close()
            result = -1
        finally:
            session.close()
        return result

    #bfs nodes of N hop from start_node
    #decline_rate: decline rate of max_neighbor of n hop distance node
    #return id array in BFS manner
    def get_n_hop_neighbors(self, start_node_id, n_hop=3, max_neighbor=10, decline_rate=0.5, topk=100, print_cql=False):
        visited,result,hop_count = set(),[],0
        status,content = self.get_node(start_node_id, print_cql)
        if status == 0:
            return result
        node_id,node_label,node_alias = content[0],content[1],content[2]
        queue = deque([(node_id, node_label, hop_count)])  # (id, node, rel, hop_count)
        while queue:
            node_id, node_label, hop_count = queue.popleft() #has been exlcuded
            if hop_count <= n_hop:  # Expand new nodes only if hop count is less than n
                if node_id not in visited: #filter
                    visited.add(node_id)
                    result.append({'nid':node_id, 'label':node_label, 'distance':hop_count})
                    number_neighbor = max(int(max_neighbor * (decline_rate**hop_count)), 1)
                    neighbor_list = self._get_neighbor_nodes(node_id, number_neighbor, print_cql)
                    for node in neighbor_list:
                        #nid as the element identifier in the queue
                        queue.append((node['nid'], node['label'], hop_count + 1))
        if len(result) > topk:
            result.sort(key=lambda x: x['distance'], reverse=False)
            result = result[:topk]
        return result

    #return list of nid and list of label
    def get_node(self, nid, print_cql=False):
        CQL = 'MATCH (n:Entity) \n\
               WHERE n.nid = %s \n\
               RETURN n'%nid
        res = self.runCQL(CQL, print_cql)
        if res != -1 and res is not None:
            if len(res) > 0:
                return 1,(res[0]['n']['nid'], res[0]['n']['label'], res[0]['n'].get('alias'))
            else:
                return 0,None
        else:
            return 0,None

    
    #return entity by label
    def get_node_by_label(self, label, print_cql=False):
        CQL = "MATCH (n:Entity) \n\
               WHERE n.label = '%s' \n\
               RETURN n"%label
        res = self.runCQL(CQL, print_cql)
        if res != -1 and res is not None:
            if len(res) > 0:
                return 1,(res[0]['n']['nid'], res[0]['n']['label'], res[0]['n'].get('alias'))
            else:
                return 0,None
        else:
            return 0,None
    
    #get id array of neighbors of node with nid 
    def _get_neighbor_nodes(self, nid, max_neighbor=5, print_cql=False):
        CQL = 'MATCH (n1:Entity)-[r:Relation]-(n2:Entity) \n\
               WHERE n1.nid = %s \n\
               WITH DISTINCT n2, rand() as random_order \n\
               RETURN n2 \n\
               ORDER BY random_order \n\
               LIMIT %s'%(nid, max_neighbor)
        res = self.runCQL(CQL, print_cql=print_cql)
        node_list = []
        if res != -1 and res is not None:
            for index in range(len(res)):
                nrn_json = res[index]
                node_list.append({'nid':nrn_json['n2']['nid'], 'label':nrn_json['n2']['label']})
        return node_list

    #RETURN relation among node with nid in nid_set format: {n1.nid, r.value, n2.nid}
    def get_relations_of_nodes(self, nid_list:list, print_cql=False):
        CQL = 'MATCH (n1:Entity)-[r]->(n2:Entity) \n\
               WHERE n1.nid IN %s AND n2.nid IN %s \n\
               RETURN n1.nid, r.value, n2.nid' % (str(nid_list), str(nid_list))
        res = self.runCQL(CQL, print_cql)
        rel_set,rel_list = set(),[]
        if res != -1 and res is not None:
            for index in range(len(res)):
                nrn_json = res[index]
                rel_hash = str(nrn_json['n1.nid']) + str(nrn_json['r.value']) + str(nrn_json['n2.nid'])
                if rel_hash not in rel_set:
                    rel_list.append({'n1.nid':nrn_json['n1.nid'], 'r.value':nrn_json['r.value'], 'n2.nid':nrn_json['n2.nid']})
                    rel_set.add(rel_hash)
        return rel_list
            
    def count_node(self, print_cql=False):
        node_count = self.runCQL('MATCH (n) RETURN COUNT(n) AS count', print_cql=print_cql)
        return node_count[0]['count']

    def count_edge(self, print_cql=False):
        edge_count = self.runCQL('MATCH ()-[r]->() RETURN COUNT(r) AS count', print_cql=print_cql)
        return edge_count[0]['count']

    def average_degree(self, sample=5000):
        query = 'MATCH (n) \n\
                 WITH n \n\
                 ORDER BY RAND() \n\
                 LIMIT %s \n\
                 MATCH (n)-[r]-() \n\
                 WITH n, count(r) as degree \n\
                 RETURN avg(degree)'%sample
        avg_degree = np.round(self.runCQL(query, print_cql=print_cql)[0]['avg(degree)'], 3)
        return avg_degree
    
    # def empty_database(self):
    #     self.runCQL('MATCH (n) DETACH DELETE n')
        
    def close(self):
        self.driver.close()