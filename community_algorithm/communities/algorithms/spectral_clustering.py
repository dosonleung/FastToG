# Standard Library
import random
import networkx as nx
from copy import deepcopy

# Third Party
import numpy as np

# Local
from ..utilities import laplacian_matrix,modularity_matrix,_modularity


##############
# MATH HELPERS
##############

def eigenvector_matrix(L, n):
    eigvals, eigvecs = np.linalg.eig(L)
    sorted_eigs = sorted(zip(eigvals, eigvecs.T), key=lambda e: e[0])

    n_eigvecs = []
    for index, (eigval, eigvec) in enumerate(sorted_eigs):
        if not index:
            continue
        elif index >= n:
            break
        n_eigvecs.append(eigvec)

    return np.vstack(n_eigvecs).T

#################
# K-MEANS HELPERS
#################

def init_communities(num_nodes, k):
    # QUESTION: Forgy method vs. Random Partition method?
    return [{i} for i in random.sample(range(num_nodes), k)]

def calc_centroids(V, communities):
    centroids = []
    for community in communities:
        centroid = V[list(community)].mean(axis=0)
        centroids.append(centroid)
    C = np.vstack(centroids)
    return C

def update_assignments(V, C, communities):
    for i in range(len(V)):
        best_sim, best_comm_index = -1, 0
        for c_i in range(len(C)):
            cosine_sim = np.dot(V[i], C[c_i])
            cosine_sim /= np.linalg.norm(V[i]) * np.linalg.norm(C[c_i])
            if cosine_sim < best_sim:
                continue
            best_sim = cosine_sim
            best_comm_index = c_i
        communities[best_comm_index].add(i)
    return communities

######
# MAIN
######

def spectral_clustering(adj_matrix : np.ndarray, m : int, max_iter:int = 100, delta:float = 1e-4) -> list:
    if m == 1: #single node 
        return [{i} for i in range(len(adj_matrix))], [0] * len(adj_matrix)
    elif m >= len(adj_matrix):
        return [set(range(len(adj_matrix)))], [0]
    k = int(len(adj_matrix)/m)+1
    L = laplacian_matrix(adj_matrix)
    M = modularity_matrix(adj_matrix)
    V = eigenvector_matrix(L, k)

    iteration = 0
    communities = init_communities(len(adj_matrix), k)
    while True:
        iteration += 1
        C = calc_centroids(V, communities)
        updated_communities = update_assignments(V, C, deepcopy(communities))
        comm_size = [len(comm) for comm in updated_communities]
        loss = np.mean([(size-m)**2 for size in comm_size])
        if updated_communities == communities or loss < delta or iteration > max_iter:
            break
        communities = updated_communities

    quality = _modularity(M, communities)
    scores = []
    for comm in communities:
        indice = list(comm)
        score = np.sum(quality[indice][:, indice])
        scores.append(score)
    
    return communities,scores

#modularity as value
#n is increasing
# def spectral_clustering(adj_matrix : np.ndarray, m : int, max_iter : int = 10) -> list: 
#     n = int(len(adj_matrix)/m)
#     L = laplacian_matrix(adj_matrix)
#     M = modularity_matrix(adj_matrix)
#     V = None
#     #V = eigenvector_matrix(L, n)
#     P_history,Q_history = [],[]

#     communities = init_communities(len(adj_matrix), n)
#     n2m = list(range(n, len(adj_matrix)))
#     n2m.reverse()
#     current_n,iteration = 0,0
#     while True:
#         cluster_size = np.array([len(comm) for comm in communities])
#         if current_n >= len(n2m):
#             break
#         iteration += 1
#         V = eigenvector_matrix(L, n2m[current_n])
#         print(iteration, n2m[current_n])
#         # if updated_communities == communities:
#         #     break
#         if iteration > max_iter:
#             current_n += 1
#             iteration = 0
#             continue

#         C = calc_centroids(V, communities)
#         updated_communities = update_assignments(V, C, deepcopy(communities))
#         communities = updated_communities
#         P_history.append(communities)
#         Q_history.append(_modularity(M, communities))

#     ipdb.set_trace(context=10)
#     part_hist,qual_hist,size_hist,dist_hist = [],[],[],[]
#     for index in range(len(P_history)):
#         size_row = [len(part) for part in P_history[index]]
#         dist_row = np.mean([(size-m)**2 for size in size_row])
#         #we can not assert all size of part_hist are less than m
#         part_hist.append(P_history[index])
#         qual_hist.append(Q_history[index])
#         size_hist.append(size_row)
#         dist_hist.append(dist_row)

#     ipdb.set_trace(context=10)
#     select_index = np.argmin(dist_hist)
#     selected_partition = part_hist[select_index]
#     selected_quality = []
#     for part in selected_partition:
#         indice = list(part)
#         score = np.sum(qual_hist[select_index][indice][:, indice])
#         selected_quality.append(score)
    
#     return selected_partition,selected_quality
