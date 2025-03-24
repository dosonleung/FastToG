# Third Party
import ipdb
import networkx as nx
import numpy as np
from typing import List, Dict, Tuple, Callable, Optional
# Local
from ..utilities import modularity_matrix, modularity, _modularity


#########
# HELPERS
#########


def prune_edges(G):
    init_num_comps = nx.number_connected_components(G)
    curr_num_comps = init_num_comps
    num_nodes = G.number_of_nodes()
    # TODO: Recalculate betweenness of only the edges affected by the removal
    while curr_num_comps <= init_num_comps: #remove edges until components change
        bw_centralities = nx.edge_betweenness_centrality(G)
        if len(bw_centralities) == 0:
            break
        bw_centralities = sorted(
            bw_centralities.items(),
            key=lambda e: e[1],
            reverse=True
        )
        (edge,bw) = bw_centralities[0]
        G.remove_edge(*edge)
        # max_bw = None
        # for edge, bw in bw_centralities:
        #     if max_bw is None:
        #         max_bw = bw
        #     if max_bw == bw:
        #         G.remove_edge(*edge)
        #     else:
        #         break
        curr_num_comps = nx.number_connected_components(G)
    return G


def animation_data(A, P_history, Q_history):
    num_nodes = len(A)
    frames = []
    for P, Q in zip(P_history, Q_history):
        _P = [0 for _ in range(num_nodes)]
        for index, partition in enumerate(P):
            for node in partition:
                _P[node] = index
        frames.append({"C": _P, "Q": Q})
    return frames

######
# MAIN
######

#n is decreasing 
#max_iter for the unchanging len(last_P)
def girvan_newman(adj_matrix : np.ndarray, m : int = None, max_iter : int = 100, delta : float = 1e-4) -> list:
    if m is None:
        m = int(np.sqrt(num_nodes) + 0.5)
    elif m == 1: #single node 
        return [{i} for i in range(len(adj_matrix))], [0] * len(adj_matrix)
    elif m >= len(adj_matrix):
        return [set(range(len(adj_matrix)))], [0]
    M = modularity_matrix(adj_matrix)
    G = nx.from_numpy_array(adj_matrix)
    num_nodes = G.number_of_nodes()
    G.remove_edges_from(nx.selfloop_edges(G))

    best_P = list(nx.connected_components(G)) # Partition
    best_Q = _modularity(M, best_P)
    P_history,Q_history = [best_P],[best_Q]

    iteration = 0
    while True:
        last_P = P_history[-1]
        last_Q = Q_history[-1]
        iteration += 1
        #n is increasing 
        part_size = [len(part) for part in last_P]
        loss = np.mean([(size-m)**2 for size in part_size])
        if loss < delta or iteration > max_iter: #number or cluster greater than n or all cluster 
            best_P,best_Q = last_P,last_Q
            break
        G = prune_edges(G)
        P = list(nx.connected_components(G))
        Q = _modularity(M, P)
        # if Q.sum() >= best_Q.sum():
        #     best_Q = Q
        #     best_P = P
        P_history.append(P)
        Q_history.append(Q)

    partition_hist,quality_hist,size_hist,dist_hist = [],[],[],[]
    for index in range(len(P_history)):
        size_row = [len(part) for part in P_history[index]]
        dist_row = np.mean([(size-m)**2 for size in size_row])
        if max(size_row) <= m:
            partition_hist.append(P_history[index])
            quality_hist.append(Q_history[index])
            size_hist.append(size_row)
            dist_hist.append(dist_row)
    
    select_index = np.argmin(dist_hist)
    selected_partition = partition_hist[select_index]
    selected_quality = []
    for part in selected_partition:
        indice = list(part)
        score = np.sum(quality_hist[select_index][indice][:, indice])
        selected_quality.append(score)
    
    return selected_partition,selected_quality