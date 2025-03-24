# Standard Library
from typing import List, Dict, Tuple, Callable, Optional
from itertools import combinations, chain
from collections import defaultdict

# Third Party
import numpy as np

# Local
from ..utilities import modularity_matrix, modularity, _modularity

#########
# HELPERS
#########

def initialize_node_to_comm(adj_matrix):
    return list(range(len(adj_matrix)))


def invert_node_to_comm(node_to_comm):
    communities = defaultdict(set)
    for node, community in enumerate(node_to_comm):
        communities[community].add(node)

    return list(communities.values())


def get_all_edges(nodes):
    return chain(combinations(nodes, 2), ((u, u) for u in nodes))

########
# PHASES ONE: MOVE EACH NODE TO EACH COMMUNITY FOR MERGEING
########

def run_first_phase(node_to_comm, adj_matrix, m, force_merge=False, max_iter:int=100, delta:float=1e-4):
    M = modularity_matrix(adj_matrix)
    best_node_to_comm = node_to_comm.copy()
    _, size_communities = np.unique(best_node_to_comm, return_counts=True)
    is_updated = not np.any(size_communities >= m)
    ani_frames = [{"C": best_node_to_comm, "Q": None}]
    # QUESTION: Randomize the order of the nodes before iterating?
    iteration = 0
    loss = 1
    while is_updated:
        iteration += 1
        is_updated = False
        _, size_communities = np.unique(best_node_to_comm, return_counts=True)
        loss = np.mean([(size-m)**2 for size in size_communities])
        if loss < delta or iteration > max_iter:
            break
        for i, neighbors in enumerate(adj_matrix):
            # if len(set(best_node_to_comm)) <= n:
            #     break
            max_delta_Q = 0.0
            best_Q = modularity(M, invert_node_to_comm(best_node_to_comm))
            updated_node_to_comm, visited_communities = best_node_to_comm, set()
            #ipdb.set_trace(context=10)
            for j, weight in enumerate(neighbors): #neighbor is also the row
                # Skip if self-loop or not neighbor
                if i == j or not weight: #weight={0,1}
                    continue
                neighbor_comm = best_node_to_comm[j]
                if neighbor_comm in visited_communities:
                    continue
                # Remove node i from its community and place it in the community
                # of its neighbor j
                candidate_node_to_comm = best_node_to_comm.copy()
                candidate_node_to_comm[i] = neighbor_comm
                # This neighbor is not suit for inserting
                _, size_communities = np.unique(candidate_node_to_comm, return_counts=True)
                if np.any(size_communities > m): #make sure no size of community large than m
                    continue
                candidate_Q = modularity(
                    M,
                    invert_node_to_comm(candidate_node_to_comm)
                )
                delta_Q = candidate_Q - best_Q
                if (delta_Q > max_delta_Q) or (force_merge and not max_delta_Q): #zero modularity will be forced to 
                    updated_node_to_comm = candidate_node_to_comm
                    max_delta_Q = delta_Q
                    ani_frames.append({
                        "C": candidate_node_to_comm,
                        "Q": _modularity(
                            M,
                            invert_node_to_comm(candidate_node_to_comm)
                        )
                    })
                visited_communities.add(neighbor_comm)
            # Set Q for first frame
            if not i and ani_frames[0]["C"] == best_node_to_comm:
                ani_frames[0]["Q"] = _modularity(
                            M,
                            invert_node_to_comm(best_node_to_comm)
                        )
            if best_node_to_comm != updated_node_to_comm:
                best_node_to_comm = updated_node_to_comm
                is_updated = True
    if ani_frames[-1]["C"] != best_node_to_comm:
        ani_frames.append({"C": best_node_to_comm, 
                           "Q": _modularity(
                                M,
                                invert_node_to_comm(best_node_to_comm)
                            )
                          })
    # print(iteration, loss)
    return best_node_to_comm, ani_frames

def run_second_phase(node_to_comm, adj_matrix, true_partition, true_comms):
    comm_to_nodes = defaultdict(lambda: [])
    for i, comm in enumerate(node_to_comm):
        comm_to_nodes[comm].append(i)
    comm_to_nodes = list(comm_to_nodes.items())

    new_adj_matrix, new_true_partition = [], []
    for i, (comm, nodes) in enumerate(comm_to_nodes):
        true_nodes = {v for u in nodes for v in true_partition[u]}
        true_comms[i] = true_comms[comm]

        row_vec = []
        for j, (_, neighbors) in enumerate(comm_to_nodes):
            if i == j:  # Sum all intra-community weights and add as self-loop
                edge_weights = (adj_matrix[u][v]
                                for u, v in get_all_edges(nodes))
                edge_weight = 2 * sum(edge_weights)
            else:
                edge_weights = (adj_matrix[u][v]
                                for u in nodes for v in neighbors)
                edge_weight = sum(edge_weights)

            row_vec.append(edge_weight)

        new_true_partition.append(true_nodes)
        new_adj_matrix.append(row_vec)

    # TODO: Use numpy more efficiently
    return np.array(new_adj_matrix), new_true_partition, true_comms

######
# MAIN
# n: minumum number of communities
# m: maximum size of a community
# m is priority if m,n are not None
######

#n is increasing
def louvain_method(adj_matrix : np.ndarray, m : int = None, max_iter : int = 100, delta : float = 1e-4) -> (list,list):
    optimal_adj_matrix = adj_matrix
    node_to_comm = initialize_node_to_comm(adj_matrix)
    true_partition = [{i} for i in range(len(adj_matrix))]
    true_comms = {c: c for c in node_to_comm}
    if m is None:
        m = int(np.sqrt(adj_matrix) + 0.5)
    elif m == 1: #single node 
        return true_partition, [0] * len(true_partition)
    elif m >= len(adj_matrix):
        return [set(range(len(adj_matrix)))], [0]
    ani_frames = []
    if len(adj_matrix) > m:    
        M = modularity_matrix(adj_matrix)
        def update_frame(frame, partition, comm_aliases, recalculate_Q):
            true_node_to_comm = list(range(len(adj_matrix)))
            for i, community in enumerate(frame["C"]):
                for node in partition[i]:
                    true_node_to_comm[node] = comm_aliases[community]
            frame["P"] = partition
            frame["C"] = true_node_to_comm
            if recalculate_Q:
                frame["Q"] = _modularity(M, invert_node_to_comm(frame["C"]))
            return frame
        iteration = 0
        while True:
            part_size = [len(part) for part in true_partition]
            loss = np.mean([(size-m)**2 for size in part_size])
            if len(true_partition) == 1 or loss < delta or iteration > max_iter:
                break
            #trial pharse
            optimal_node_to_comm, frames = run_first_phase(
                node_to_comm,
                optimal_adj_matrix,
                m,
                False,
                max_iter,
                delta
            )
            #force merge
            if optimal_node_to_comm == node_to_comm:
                optimal_node_to_comm, frames = run_first_phase(
                    node_to_comm,
                    optimal_adj_matrix,
                    m,
                    True,
                    max_iter,
                    delta
                )
            frames = (update_frame(f, true_partition, true_comms, bool(ani_frames)) for f in frames)
            ani_frames.extend(frames)
            new_adj_matrix, new_partition, new_comms = run_second_phase(
                optimal_node_to_comm,
                optimal_adj_matrix,
                true_partition,
                true_comms
            )
            optimal_adj_matrix,true_partition,true_comms = new_adj_matrix,new_partition,new_comms
            node_to_comm = initialize_node_to_comm(optimal_adj_matrix)
            iteration += 1

    #filter the size smaller equal than m
    partition_hist,quality_hist,size_hist,dist_hist = [],[],[],[]
    for index in range(len(ani_frames)):
        size_row = [len(part) for part in ani_frames[index]["P"]]
        dist_row = np.mean([(size-m)**2 for size in size_row])
        if max(size_row) <= m:
            partition_hist.append(ani_frames[index]["P"])
            quality_hist.append(ani_frames[index]["Q"])
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
    
    # ipdb.set_trace(context=10)
    # score_partition,last_score = [],np.zeros_like(adj_matrix)
    # if len(ani_frames) > 0:
    #     last_score = ani_frames[-1]["Q"] #shape as adj_matrix
    # for part in true_partition:
    #     indice = list(part)
    #     score = np.sum(last_score[indice][:, indice])
    #     score_partition.append(score)
    # #return true_partition
    # return true_partition, score_partition
