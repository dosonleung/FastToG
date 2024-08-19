import copy
import numpy as np
import igraph as ig
import matplotlib.pyplot as plt
from collections import deque
from itertools import combinations
from typing import List, Dict, Tuple, Callable, Set
from community_algorithm.communities.algorithms import girvan_newman,\
    louvain_method,hierarchical_clustering,spectral_clustering

#Prims Algorithm for MST
def prims(adj_matrix:np.ndarray) -> np.ndarray:
    num_nodes = adj_matrix.shape[0]
    if num_nodes <= 1:
        return adj_matrix
    in_mst = np.full(num_nodes, False)
    mst_edges = np.zeros_like(adj_matrix)
    edge_weights = np.full(num_nodes, np.inf)
    parent = np.full(num_nodes, -1)
    # Start from node 0
    edge_weights[0] = 0
    for _ in range(num_nodes):
        # Find the minimum edge not yet included in the MST
        min_weight = np.inf
        u = -1
        for i in range(num_nodes):
            if not in_mst[i] and edge_weights[i] < min_weight:
                min_weight = edge_weights[i]
                u = i
        # Include this vertex in MST
        in_mst[u] = True
        # Update the cost of edges connected to this vertex
        for v in range(num_nodes):
            if adj_matrix[u][v] == 1 and not in_mst[v] and edge_weights[v] > adj_matrix[u][v]:
                edge_weights[v] = adj_matrix[u][v]
                parent[v] = u
    # Use the parent array to construct the MST
    for v in range(1, num_nodes):
        u = parent[v]
        mst_edges[u][v] = 1
        mst_edges[v][u] = 1
    return mst_edges


#Kruskal Algorithm for MST
def kruskal(adj_matrix:np.ndarray) -> np.ndarray:
    
    def find(parent, i):
        while parent[i] != i:
            i = parent[i]
        return i
        
    def union(parent, rank, x, y):
        # Union operation to merge two sets represented by x and y
        xroot = find(parent, x)
        yroot = find(parent, y)
        if rank[xroot] < rank[yroot]:
            parent[xroot] = yroot
        elif rank[xroot] > rank[yroot]:
            parent[yroot] = xroot
        else:
            parent[yroot] = xroot
            rank[xroot] += 1

    num_nodes = adj_matrix.shape[0]
    if num_nodes <= 1:
        return adj_matrix
        
    mst_edges = np.zeros_like(adj_matrix)
    edges_count = 0
    edges = []
    # Create a list of edges sorted by weight
    for i in range(num_nodes):
        for j in range(i+1, num_nodes):
            if adj_matrix[i][j] > 0:
                edges.append((i, j, adj_matrix[i][j]))
    edges.sort(key=lambda edge: edge[2])  # Sort edges by weight
    parent = [i for i in range(num_nodes)]
    rank = [0 for _ in range(num_nodes)]
    # Construct the MST using Kruskal's algorithm
    while edges_count < num_nodes - 1:
        u, v, weight = edges.pop(0)
        x = find(parent, u)
        y = find(parent, v)
        if x != y:
            edges_count += 1
            mst_edges[u][v] = 1  # Add edge (u, v) to the MST
            mst_edges[v][u] = 1  # Add edge (v, u) to the MST
            union(parent, rank, x, y)  # Merge the sets containing x and y
    return mst_edges

class Community:
    def __init__(
        self, 
        ent_triples: List[Tuple], #[(nid, label, distance),...]
        rel_triples: List[Tuple], #[(n1.nid, r.value, n2.nid),...] 
        center_node_id = None,
        quality = None,
        label = None
    ):
        self.ent_triples = ent_triples 
        self.rel_triples = rel_triples 
        self.ent_nids = set([ent[0] for ent in ent_triples])
        self.relation_matrix = triples2matrix(ent_triples, rel_triples) #relation matrix with row/column as ent_triples
        if center_node_id is None:
            if len(self.relation_matrix) > 0:
                relation_2d_array = np.array(self.relation_matrix)
                center_index = np.argmax(np.sum(np.where(relation_2d_array == None, 0, 1), axis=1)) #maximum degree node as community center
                self.cid = ent_triples[center_index][0] #community center nid as community id
            else:
                self.cid = self.ent_triples[0][0]
        else:
            self.cid = center_node_id
        if quality is not None:
            self.quality = quality
        else:
            if len(self.relation_matrix) > 0:
                self.quality =  np.sum(np.where(np.array(self.relation_matrix) == None, 0, 1))/(len(self.relation_matrix))**2
            else:
                self.quality = 0.0
        self.label = label if label is not None else self.get_label_by_nid(self.cid) #center node label as community label
    
    def get_label_by_nid(self, nid):
        label = None
        for ent in self.ent_triples:
            if ent[0] == nid:
                label = ent[1]
                break
        return label

    def get_index_by_nid(self, nid):
        index = None
        for i,ent in enumerate(self.ent_triples):
            if ent[0] == nid:
                index = i
                break
        return index
    
    # get intra relation triples of community
    def get_intra_rel_triples(self):
        intra_rel_triples = []
        for rel in self.rel_triples:
            if rel[0] in self.ent_nids and rel[2] in self.ent_nids: 
                intra_rel_triples.append(rel)
        return intra_rel_triples

    # get inter relation triples of community
    def get_inter_rel_triples(self, direct=None):
        inter_rel_triples = []
        for rel in self.rel_triples:
            if direct is None:
                if rel[0] not in self.ent_nids or rel[2] not in self.ent_nids: 
                    inter_rel_triples.append(rel)
            elif direct.lower() == 'in':
                if rel[2] in self.ent_nids and rel[0] not in self.ent_nids:
                    inter_rel_triples.append(rel)
            elif direct.lower() == 'out':
                if rel[0] in self.ent_nids and rel[2] not in self.ent_nids:
                    inter_rel_triples.append(rel)
        return inter_rel_triples
        
    # Breadth-First Search (BFS)
    # summary_method = prims/kruskal
    # keep_one = use one way value if two exist
    def bfs2text(self, summary_method=prims, keep_one=True) -> List[str]:
        result = []
        from_node_index = self.get_index_by_nid(self.cid)
        ent_label_list = [ent[1] for ent in self.ent_triples]
        directed_rel_matrix = self.relation_matrix
        undirected_adj_matrix = np.where(np.array(directed2undirected(directed_rel_matrix)) == None, 0, 1)
        if undirected_adj_matrix.shape[0] <= 1: #single-node community
            return result
        if keep_one: 
            undirected_adj_matrix = np.triu(undirected_adj_matrix, 1)
        if summary_method: #Prim, kruskal
            undirected_adj_matrix = summary_method(undirected_adj_matrix)
        visited_node = np.zeros(len(directed_rel_matrix), dtype=np.int8)
        visited_edge = np.zeros((len(directed_rel_matrix), len(directed_rel_matrix)), dtype=np.int8)
        visited_node[from_node_index] = 1
        queue = deque([from_node_index])
        while queue:
            from_node_index = queue.popleft()
            visited_node[from_node_index] = 1
            #print(from_node_index)  # Do something with the node
            for to_node_index in range(len(undirected_adj_matrix)):
                is_connected = undirected_adj_matrix[from_node_index][to_node_index]
                if is_connected > 0: #has undirect relation
                    element = directed_rel_matrix[from_node_index][to_node_index]
                    if visited_node[to_node_index] == 0: #should not be stop
                        queue.append((to_node_index))
                    if visited_edge[from_node_index][to_node_index] == 0:
                        if element is not None: #only dircted elemnt will be added in
                            result.append('(' + ent_label_list[from_node_index] + ', ' + str(element) \
                                 + ', ' + ent_label_list[to_node_index] + ')') # Do something with the edge (directed)
                        visited_edge[from_node_index][to_node_index] == 1                    
        return result
                    
    def _dfs2text(from_node_index, ent_label_list, directed_matrix, undirected_matrix, visited_node=None, visited_edge=None):
        result = []
        if visited_node is None and visited_edge is None:
            visited_node = np.zeros(len(rel_matrix), dtype=np.int8)
            visited_edge = np.zeros((len(rel_matrix), len(rel_matrix)), dtype=np.int8)
        if not visited_node[from_node_index]:
            #print(from_node_index)  # Do something with the node
            visited_node[from_node_index] = 1
            for to_node_index in range(len(rel_matrix[from_node_index])):
                element = directed_matrix[from_node_index][to_node_index]
                is_connected = undirected_matrix[from_node_index][to_node_index]
                if is_connected > 0: 
                    if visited_edge[from_node_index][to_node_index] == 0:
                        if element is not None: #only dircted elemnt will be added in
                            result.append('(' + ent_label_list[from_node_index] + ', ' + str(element) \
                                 + ', ' + ent_label_list[to_node_index] + ')') # Do something with the edge (directed)
                        visited_edge[from_node_index][to_node_index] == 1
                    if visited_node[to_node_index]==0:
                        # Do something with the edge
                        result.extend(_dfs2text(to_node_index, ent_label_list, directed_matrix, undirected_matrix, visited_node, visited_edge))
        return result
    
    # Depth-First Search (DFS)
    #def dfs2text(from_node_index, entity_list, relation_matrix, visited_node=None, visited_edge=None):
    def dfs2text(self, summary_method=prims, keep_one=True) -> List[str]:
        result = []
        ent_label_list = [ent[1] for ent in self.ent_triples]
        directed_matrix = self.relation_matrix
        undirected_adj_matrix = np.where(np.array(directed2undirected(directed_matrix)) == None, 0, 1)
        if undirected_adj_matrix.shape[0] <= 1: #single-node community
            return result
        if keep_one: 
            undirected_adj_matrix = np.triu(undirected_adj_matrix, 1)
        if summary_method:
            undirected_adj_matrix = summary_method(undirected_adj_matrix)
        result = _dfs2text(self.get_index_by_nid(self.cid), ent_label_list, directed_matrix, undirected_adj_matrix, None, None)
        return result

#get relation matrix from given enetiies and relation triples by entities order
def triples2matrix(ent_triples: List[Tuple], rel_triples: List[Tuple]) -> List[List]:
    assert ent_triples is not None
    if len(ent_triples) == 1:
        return [[]] 
    relation_matrix = [[None for j in range(len(ent_triples))] for i in range(len(ent_triples))]
    nid2index = {ent_triples[i][0]:i for i in range(len(ent_triples))}
    for index in range(len(rel_triples)):
        from_nid = rel_triples[index][0]
        to_nid = rel_triples[index][2]
        if from_nid in nid2index and to_nid in nid2index:
            from_index = nid2index[from_nid] #get entity index by id
            to_index = nid2index[to_nid]
            if from_index != to_index: #ignore self-circle
                relation_matrix[from_index][to_index] = rel_triples[index][1] #1 for value         
    return relation_matrix

#get directed relation matrix and id2index by given communities
#return relation matrix of relation value or None
def communiies2matrix(communities:List[Community]) -> (List[List[str]],Dict,Dict):
    all_ent_triples,all_rel_triples = [],[]
    nid2index,index2nid = {},{} #node id 2 index of relation matrix
    for commu in communities:
        all_ent_triples.extend(commu.ent_triples)
        all_rel_triples.extend(commu.rel_triples)
    for index,ent in enumerate(all_ent_triples):
        index2nid[index] = ent[0]
        nid2index[ent[0]] = index
    rel_matrix = triples2matrix(all_ent_triples, all_rel_triples)
    return rel_matrix,nid2index,index2nid

#transform a directed matrix to undirected matrix by copy or merge
def directed2undirected(directed_matrix: List[List]) -> List[List]:
    undirected_matrix = copy.deepcopy(directed_matrix)
    for index in range(len(undirected_matrix)):
        for jndex in range(index, len(undirected_matrix[index])):
            if undirected_matrix[index][jndex] is not None and undirected_matrix[jndex][index] is not None:
                if undirected_matrix[index][jndex] != undirected_matrix[jndex][index]:
                    value = undirected_matrix[index][jndex] + '/' + undirected_matrix[jndex][index]
                    undirected_matrix[index][jndex] = value
                    undirected_matrix[jndex][index] = value
            elif undirected_matrix[index][jndex] is not None:
                undirected_matrix[jndex][index] = undirected_matrix[index][jndex]
            elif undirected_matrix[jndex][index] is not None:
                undirected_matrix[index][jndex] = undirected_matrix[jndex][index]
    return undirected_matrix

#get connection between from_comm to to_comm
#connection = from_conn or to_conn
def get_community_connection(from_comm:Community, to_comm:Community) -> int:
    from_conn,to_conn = 0,0
    for rel in from_comm.rel_triples:
        if rel[0] in to_comm.ent_nids or rel[2] in to_comm.ent_nids:
            from_conn += 1
    for rel in to_comm.rel_triples:
        if rel[0] in from_comm.ent_nids or rel[2] in from_comm.ent_nids:
            to_conn += 1
    return max(from_conn, to_conn)

#get connected community from center_comm to other communities
def get_connected_community(center_comm:Community, communities:List[Community], minimum_conn=0) -> List[Community]:
    connected_comm = []
    for comm in communities:
        if comm.cid != center_comm.cid:
            conn = get_community_connection(center_comm, comm)
            #ipdb.set_trace(context=10)
            if conn > minimum_conn:
                connected_comm.append(comm)
    return connected_comm

#community like [{0,3},{1,2}] to [0,1,1,0]
def community_dict2list(community_dict):
    community_list = [-1] * len(label_list)
    unique_communities = np.unique(community_dict)
    for community in unique_communities:
        for i,val in enumerate(community_dict): #i is the community tag
            for v in val:
                community_list[v] = i #[v] = i
    return community_list

#community = [{0,1},{2,3}]
def community_list2dict(community_list):
    community_dict = {}
    for index in range(len(community_list)):
        group = list(community_list[index])
        for jndex in range(len(group)):
            community_dict[group[jndex]] = index
    return community_dict 

# get the center node (maximum degree) of given community
# community_tags = [0,1,1,0,2,2]
# center = [1,0,1,0,1] 1 indicates the center of their community
def get_community_center_mask(adj_matrix:np.ndarray, community_tags:List[int]) -> List[int]:
    assert len(adj_matrix) > 0
    if len(adj_matrix) == 1:
        return [1]
    center_list = [0] * len(adj_matrix)
    unique_communities = np.unique(community_tags) #return array([0, 1, 2])
    in_degrees,out_degrees = np.sum(adj_matrix, axis=0),np.sum(adj_matrix, axis=1)  # Calculate in/out degrees
    total_degrees = in_degrees + out_degrees
    for community_tag in unique_communities: #[0, 1, 2]
        comm_node_index = np.where(np.array(community_tags)==community_tag)[0].tolist() 
        max_degree_index = max(comm_node_index, key=lambda x: total_degrees[x])
        center_list[max_degree_index] = 1
    return center_list

def build_community(
    ent_triples: List[Tuple], 
    rel_triples: List[Tuple], 
    commtag2node_index: List[Set[int]], #set is the node index of comm 
    comm_scores: List[int] #len of commtag2node_index
) -> List[Community]:
    index2entity = {index:(ent[0], ent[1], ent[2]) for index,ent in enumerate(ent_triples)} #0,1,2 for nid,label,distance
    nid2index = {index2entity[index][0]:index for index in index2entity}
    index2rel_from = {index:[] for index in index2entity}
    index2rel_to = {index:[] for index in index2entity} #indexofrel
    #split and copy the rel for each community
    for rel in rel_triples:
        from_nid,to_nid = rel[0],rel[2]
        index2rel_from[nid2index[from_nid]].append((rel[0], rel[1], rel[2]))
        index2rel_to[nid2index[to_nid]].append((rel[0], rel[1], rel[2]))
    commtag2entity,commtag2relation,commtag2score,commtag = {},{},{},set() #commtag
    for tag,node_ids in enumerate(commtag2node_index): #index as tag
        if tag not in commtag2entity:
            commtag2entity[tag] = []
            commtag2relation[tag] = []
        for node_index in node_ids:
            commtag2entity[tag].append((index2entity[node_index][0], #nid
                                     index2entity[node_index][1], #val
                                     index2entity[node_index][2])) #dicstance
            commtag2relation[tag].extend(index2rel_from[node_index] + index2rel_to[node_index])
            commtag2score[tag] = comm_scores[tag] #index as tag
            commtag.add(tag)
    #build community
    communities = []
    for tag in commtag:
        ents = commtag2entity[tag]
        rels = commtag2relation[tag]
        score = commtag2score[tag]
        communities.append(Community(ent_triples=ents, rel_triples=rels, quality=score))
    return communities

# get the belonging community if entity with nid in community
def find_belonged_community_by_nid(communities:List[Community], nid:int) -> Community:
    target_comm = None
    for comm in communities:
        for ent in comm.ent_triples:
            if ent[0] == nid:
                target_comm = comm
                break
    return target_comm

#prune the communities of center_community from communities with connection less than minimum_conn
def get_neighbor_communities(center_community, communities, minimum_conn=0):
    neighbor_communities = []
    for commu in communities:
        if commu.cid != center_community.cid:
            neighbor_communities.append(commu)
    return get_connected_community(center_community, neighbor_communities, minimum_conn=minimum_conn)

#prune the neighbor communities by quality 
def get_high_quality_communities(neighbor_communities, topk=3):
    candidate_score  = [neighbor_communities[i].quality for i in range(len(neighbor_communities))]
    candidate_community_score = sorted(zip(neighbor_communities, candidate_score), key=lambda pair:pair[-1], reverse=True) #from high to low
    candidate_communities, candidate_score = zip(*candidate_community_score)
    candidate_communities = list(candidate_communities[:topk])
    return candidate_communities,candidate_score

def get_interset(comm1:Community, comm2:Community):
    return comm1.ent_nids & comm2.ent_nids

# get edges between community (only directed edges)
def get_community_edges(comm1:Community, comm2:Community, keep_out:bool=True) -> List[Tuple]:
    edges = set() #nid, value, nid
    direction = set() #nid, nid
    for rel in comm1.get_inter_rel_triples(): #bidirectional
        from_nid,value,to_nid = rel[0],rel[1],rel[2]
        label1,label2,index1,index2 = None,None,-1,-1 
        if from_nid in comm1.ent_nids and to_nid in comm2.ent_nids:
            index1 = comm1.get_index_by_nid(from_nid)
            index2 = comm2.get_index_by_nid(to_nid)
            id1 = comm1.ent_triples[index1][0]
            id2 = comm2.ent_triples[index2][0]
            label1 = comm1.ent_triples[index1][1]
            label2 = comm2.ent_triples[index2][1]
            edges.add((label1, value, label2))
            direction.add((id1, id2))
        if from_nid in comm2.ent_nids and to_nid in comm1.ent_nids:
            index1 = comm2.get_index_by_nid(from_nid)
            index2 = comm1.get_index_by_nid(to_nid)
            id1 = comm2.ent_triples[index1][0]
            id2 = comm1.ent_triples[index2][0]
            label1 = comm2.ent_triples[index1][1]
            label2 = comm1.ent_triples[index2][1]
            if keep_out:
                if (id1, id2) in direction or (id2, id1) in direction:
                    continue
            edges.add((label1, value, label2))
            direction.add((id1, id2))
    for rel in comm2.get_inter_rel_triples(): #bidirectional
        from_nid,value,to_nid = rel[0],rel[1],rel[2]
        label1,label2,index1,index2 = None,None,-1,-1 
        if from_nid in comm1.ent_nids and to_nid in comm2.ent_nids:
            index1 = comm1.get_index_by_nid(from_nid)
            index2 = comm2.get_index_by_nid(to_nid)
            id1 = comm1.ent_triples[index1][0]
            id2 = comm2.ent_triples[index2][0]
            label1 = comm1.ent_triples[index1][1]
            label2 = comm2.ent_triples[index2][1]
            edges.add((label1, value, label2))
            direction.add((id1, id2))
        if from_nid in comm2.ent_nids and to_nid in comm1.ent_nids:
            index1 = comm2.get_index_by_nid(from_nid)
            index2 = comm1.get_index_by_nid(to_nid)
            id1 = comm2.ent_triples[index1][0]
            id2 = comm1.ent_triples[index2][0]
            label1 = comm2.ent_triples[index1][1]
            label2 = comm1.ent_triples[index2][1]
            if keep_out:
                if (id1, id2) in direction or (id2, id1) in direction:
                    continue
            edges.add((label1, value, label2))
            direction.add((id1, id2))
    edges = list(edges)
    return edges

#just return the text of edges with label - (r.value) -> label format 
def triple2text(edges:List[Tuple]) -> List[str]:
    result = []
    for i in range(len(edges)):
        result.append('(' + edges[i][0] + ', ' + edges[i][1] + ', ' + edges[i][2] + ')')
    return result

