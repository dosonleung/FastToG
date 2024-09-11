import os
import re
import time
import shutil
import argparse
import numpy as np
import pandas as pd
from tqdm import tqdm,trange
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import List, Dict, Tuple, Callable, Optional

from utils import *
import community_tool
import prompt_adapter
from kg_client import neo4j_client
from llms_client import llm_client
from graph2text import graph2text_client
from community_tool import Community,prims,kruskal
from visualization import display_selected_community
from community_algorithm.communities.algorithms import louvain_method,girvan_newman,spectral_clustering,hierarchical_clustering

from enum import Enum
class Status(Enum):
    UNK = 0
    OK = 1
    ENE = 2
    ISOE = 3
    NME = 4
    PER = 5
    RER = 6 
    CUNK = 7
    DER = 8
    COK = 9 #COT OK only used when ToG is Failed
    ESTOP = 10 #no chains statisfy
    EXDTH = 11
    SERR = 12

'''
local community search (LCS)
'''
def community_search(
    kg_client, 
    from_community: Community, 
    method: Callable = louvain_method, 
    search_depth: int = 5, 
    search_width: int = 3, 
    decline: float = 0.5, 
    community_max_size: int = 5
) -> (int, List[Community]):
    from_entity = kg_client.get_node(from_community.cid)
    if from_entity is None:
        return Status.ENE, None
    # Get n-hop distance nodes and relations
    entity_triples = kg_client.get_n_hop_neighbors(from_community.cid, \
                        n_hop=search_depth, max_neighbor=search_width, decline_rate=0.5)
    if len(entity_triples) <= 1:
        return Status.ISOE, None
    relation_triples = kg_client.get_relations_of_nodes([entity_triples[i]['nid'] for i in range(len(entity_triples))])
    entity_triples = [(ent['nid'], ent['label'], ent['distance']) for ent in entity_triples]
    relation_triples = [(rel['n1.nid'], rel['r.value'], rel['n2.nid']) for rel in relation_triples]
    # Get Relation Matrix according to entity_triples list
    relation_matrix = community_tool.triples2matrix(entity_triples, relation_triples) #entity_list: [id, label, dist]
    # Get undirected_rel_matrix and adj matrix
    undirected_rel_matrix = community_tool.directed2undirected(relation_matrix) #community must be in undirected
    adj_matrix = np.where(np.array(undirected_rel_matrix) == None, 0, 1)
    # Get community dict for {tag:List[int]} tag:community tag, List:index of nodes in entity_triples
    community_group,community_score = method(adj_matrix, m=community_max_size)
    communities = community_tool.build_community(entity_triples, relation_triples, community_group, community_score)
    return Status.OK,communities


#visualization tool
def community_display(
    communities:List[Community],
    show_edges=True, 
    random_state=123, 
    figsize=(6,6), 
    dpi=200,
    colors:Optional[List]=None,
    selected_index: Optional[List[int]]=None,
    save_path:str=None
):
    count,nid2index = 0,{}
    if selected_index is None:
        selected_index = list(range(len(communities)))
    for tag,comm in enumerate(communities):
        for ent in comm.ent_triples:
            if ent[0] not in nid2index:
                nid2index[ent[0]] = count #nid index
                count += 1
    label_list,community_tag = [None] * len(nid2index),[-1] * len(nid2index)
    for tag,comm in enumerate(communities):
        for ent in comm.ent_triples:
            community_tag[nid2index[ent[0]]] = tag
            label_list[nid2index[ent[0]]] = ent[1]
    if colors is None: 
        colors = [COLORS[i%len(COLORS)] for i in range(len(communities))]
    directed_rel_matrix,_,_ = community_tool.communiies2matrix(communities)
    undirected_rel_matrix = community_tool.directed2undirected(directed_rel_matrix)
    undirected_adj_matrix = np.array([[]])
    if len(directed_rel_matrix) > 1:
        undirected_adj_matrix = np.where(np.array(undirected_rel_matrix) == None, 0, 1)
    community_center_mask = community_tool.get_community_center_mask(undirected_adj_matrix, community_tag)
    display_selected_community(selected_index, label_list, undirected_rel_matrix, community_tag, community_center_mask, \
        louvain_method, colors=colors, show_edges=show_edges, \
        random_state=random_state, figsize=figsize, dpi=dpi, save_path=save_path)

#display chains as png files
def display_chains(center_community, reasoning_chains, save_path):
    select_color = list(mcolors.TABLEAU_COLORS.values())
    reasoning_communities,colors = [],[select_color[0]]
    for i in range(len(reasoning_chains)):
        for j in range(len(reasoning_chains[i])):
            reasoning_communities.append(reasoning_chains[i][j])
            colors.append(select_color[i+1])
    if len(reasoning_communities) > 0:
        community_display(communities=[center_community] + reasoning_communities,
            show_edges=False, random_state=123, figsize=(8,8), dpi=250, 
            colors=colors, save_path=save_path + '.png')
        community_display(communities=[center_community] + reasoning_communities,
            show_edges=True, random_state=123, figsize=(10,10), dpi=350, 
            colors=colors, save_path=save_path + '_with_edges' + '.png')

#save chains as text
def save_chains(center_community, reasoning_chains, summary_method, save_path):
    table = pd.DataFrame(columns=['width','depth','quality','triple2text'])
    center_text = ','.join(center_community.bfs2text(summary_method))
    log_row = ['*', '*', center_community.quality, center_text]
    table.loc[len(table)] = log_row
    for i in range(len(reasoning_chains)):
        for j in range(len(reasoning_chains[i])):
            comm_text = ','.join(reasoning_chains[i][j].bfs2text(summary_method))
            log_row = [i, j, reasoning_chains[i][j].quality, comm_text]
            table.loc[len(table)] = log_row
    table.to_csv(save_path, index=False)

'''
Pruning Methods
'''
# prune the communities by basic graph info
# conn_threshold: threshold for determining whether two communities are neighbor
# max_candidate: number of communities to be kept
# return: List[Community],updated or not
def graph_prune(
    center_community: Community, 
    neighbor_communities: List[Community], 
    max_candidate: int=3
) -> List[Community]:
    pruned_communities = None
    if len(neighbor_communities) <= max_candidate:
        pruned_communities = neighbor_communities
    else:
        pruned_communities,_ = community_tool.get_high_quality_communities(neighbor_communities, max_candidate)
    return pruned_communities   

#LLMs pruning by triples
def community_prune_by_triples(
    llm_client,
    question:str,
    hist_communities:List[Community], 
    cand_communities:List[Community],
    keep_candidate: int=3,
    summary_method=None,
    temperature=0.25,
    log_path=None
) -> (int,List[Community]): #status:(-1,0,1) for network 0 for p_error 1 for ok 
    id_of_comm = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' #use Alapbet as option indicator
    assert len(cand_communities) <= len(id_of_comm)
    premise = []
    for index in range(len(hist_communities)):
        premise_text = ','.join(hist_communities[index].bfs2text(summary_method)) #first parameter
        if index > 0: 
            edges = community_tool.get_community_edges(hist_communities[index-1], hist_communities[index])
            if len(edges) > 0: #edges will be zero length if two community has interset 
                edge_text = ','.join(community_tool.triple2text(list(set(edges)))) #list of str
            premise_text = edge_text + ' ' + premise_text
        if len(premise_text.strip()) > 0:
            premise.append(premise_text)
    premise = '; '.join(premise)
    index2comm = {id_of_comm[index]:comm for index,comm in enumerate(cand_communities)}
    index2comms_text = {}
    for id_ in index2comm: #add edges
        option_text = ','.join(index2comm[id_].bfs2text(summary_method))
        edges = community_tool.get_community_edges(hist_communities[-1], index2comm[id_]) #use edges out first
        if len(edges) > 0: #overlap communities have no edges
            edge_text = ','.join(community_tool.triple2text(list(set(edges))))
            option_text = edge_text + ',' + option_text
        index2comms_text[id_] = option_text
    request = prompt_adapter.get_prune_prompt(premise, question, index2comms_text, 'triple', keep_candidate)
    l_status,response,num_toks,repeat = llm_client.generate(request, temperature=temperature) #int, Dict{str, str}
    if l_status:
        status,answer = prompt_adapter.get_prune_result(index2comm.keys(), response)
        log_content = (
            f"community_prune_by_triples: \n"
            f"number of tokens: {num_toks}\n"
            f"premise: {premise}\n"
            f"question: {question}\n"
            f"choice:\n" + "\n".join([f"{id_}. {index2comms_text[id_]}" for id_ in index2comms_text]) + "\n"
            f"repeat: {repeat}\n"
            f"response:\n{response}\n\n"
            )
        if log_path:
            log_plain_text(log_path, log_content)
        else:
            print(log_content)
        if status > 0 and len(answer) == keep_candidate: #prompt_adapter only return 0 or 1
            selected_comms = [index2comm[id_] for id_ in answer]
            return Status.OK,selected_comms
        else:
            return Status.PER,None
    else: #server or network error
        log_content = (
            f"Status.SERR:\n"
            f"community_prune_by_t2t: \n"
            f"repeat: {repeat}\n"
            f"request:\n{request}\n"
            f"response:\n{response}\n\n"
            )
        if log_path:
            log_plain_text(log_path, log_content)
        else:
            print(log_content)
        return Status.SERR,None

#LLMs pruning by graph2text
def community_prune_by_g2t(
    llm_client, 
    g2t_client,
    question:str,
    hist_communities:List[Community], 
    cand_communities:List[Community],
    keep_candidate: int=3,
    summary_method=None,
    temperature=0.25,
    log_path=None
) -> (int,List[Community]): #status:(-1,0,1) for network 0 for p_error 1 for ok 
    id_of_comm = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' #use Alapbet as option indicator
    assert len(cand_communities) <= len(id_of_comm)
    premise = []
    for index in range(len(hist_communities)):
        premise_text = g2t_client.generate(','.join(hist_communities[index].bfs2text(summary_method))) #first parameter
        if index > 0: 
            edges = community_tool.get_community_edges(hist_communities[index-1], hist_communities[index])
            if len(edges) > 0: #edges will be zero length if two community has interset 
                edge_text = g2t_client.generate(','.join(community_tool.triple2text(list(set(edges)))))                
            premise_text = edge_text + ' ' + premise_text
        if len(premise_text.strip()) > 0:
            premise.append(premise_text)
    premise = '; '.join(premise)
    index2comm = {id_of_comm[index]:comm for index,comm in enumerate(cand_communities)} #key:[comm]
    index2comm_text = {}
    for id_ in index2comm: #add edges
        option_text = g2t_client.generate(','.join(index2comm[id_].bfs2text(summary_method)))
        edges = community_tool.get_community_edges(hist_communities[-1], index2comm[id_]) #use edges out first
        if len(edges) > 0: #edges will be zero length if two community has interset 
            edge_text = g2t_client.generate(','.join(community_tool.triple2text(list(set(edges)))))
            option_text = edge_text + ' ' + option_text
        index2comm_text[id_] = option_text
    request = prompt_adapter.get_prune_prompt(premise, question, index2comm_text, 'text', keep_candidate)
    l_status,response,num_toks,repeat = llm_client.generate(request, temperature=temperature) #int, Dict{str, str}
    if l_status:
        status,answer = prompt_adapter.get_prune_result(index2comm.keys(), response)
        log_content = (
            f"community_prune_by_g2t: \n"
            f"number of tokens: {num_toks}\n"
            f"premise: {premise}\n"
            f"question: {question}\n"
            f"choice:\n" + "\n".join([f"{id_}. {index2comm_text[id_]}" for id_ in index2comm_text]) + "\n"
            f"repeat: {repeat}\n"
            f"response:\n{response}\n\n"
            )
        if log_path:
            log_plain_text(log_path, log_content)
        else:
            print(log_content)
        if status > 0 and len(answer) == keep_candidate: #prompt_adapter only return 0 or 1
            selected_comms = [index2comm[id_] for id_ in answer]
            return Status.OK,selected_comms #select_com can be [c1, None, c2, None] None mean llm format error
        else:
            return Status.PER,None
    else: #server or network error
        log_content = (
            f"Status.SERR:\n"
            f"community_prune_by_g2t: \n"
            f"repeat: {repeat}\n"
            f"request:\n{request}\n"
            f"response:\n{response}\n\n"
            )
        if log_path:
            log_plain_text(log_path, log_content)
        else:
            print(log_content)
        return Status.SERR,None

'''
reasoning methods
'''
def reasoning_by_triples(
    llm_client, 
    question:str,
    start_community:Community,
    chains: List[List[Community]],
    summary_method=None,
    temperature=0.7,
    log_path=None
) -> (int, str): #
    clues = {}
    premise = ', '.join(start_community.bfs2text(summary_method)) #first parameter
    text_of_list = [list() for i in range(len(chains))]
    for index in range(len(chains)): #chains width
        for jndex in range(len(chains[index])):
            commu = chains[index][jndex]
            #edge_in_text,edge_out_text = [],[]
            edges = []
            if jndex == 0:
                edges = community_tool.get_community_edges(start_community, commu) #use edges out first
            else:
                edges = community_tool.get_community_edges(chains[index][jndex-1], commu) #use edges out first
            if len(edges) > 0:
                edge_text = community_tool.triple2text(list(set(edges))) #list of str
                if len(edge_text) > 0:
                    text_of_list[index].append(','.join(edge_text))
            commu_text = commu.bfs2text(summary_method) #comm text will be [] if comm is a single-node comm
            if len(commu_text) > 0:
                text_of_list[index].append(','.join(commu_text))
    for index in range(len(text_of_list)):
        if len(text_of_list[index]) > 0:
            clues[len(clues)+1] = '; '.join(text_of_list[index])
    assert len(clues) > 0
    request = prompt_adapter.get_reasoning_prompt(premise, question, clues, 'triple')
    l_status,response,num_toks,repeat = llm_client.generate(request, temperature=temperature)
    if l_status == 1:
        singal,answer = prompt_adapter.get_reasoning_result(response)
        log_content = (
            f"reasoning_by_t2t: \n"
            f"number of tokens: {num_toks}\n"
            f"question:{question}\n"
            f"clues:\n0. {premise}\n" +  "\n".join([f"{id_}. {clues[id_]}" for id_ in clues]) + "\n"
            f"repeat: {repeat}\n"
            f"response:\n{response}\n\n"
            )
        if log_path:
            log_plain_text(log_path, log_content) #'\n' for one reasoning, unknow still be log
        else:
            print(log_content)
        if singal >= 0: #prompt_adapter only return -1,0,1
            if singal == 1:
                return Status.OK, answer
            else: #0 UNK but continue
                return Status.OK, None
        else: #reasoning error
            return Status.RER, None
    log_content = (
        f"Status.SERR:\n"
        f"reasoning_by_t2t: \n"
        f"repeat: {repeat}\n"
        f"request:\n{request}\n"
        f"response:\n{response}\n\n"
        )
    if log_path:
        log_plain_text(log_path, log_content)
    else:
        print(log_content)
    return Status.SERR, None

def reasoning_by_g2t(
    llm_client,
    g2t_client,
    question:str,
    start_community:Community,
    chains: List[List[Community]],
    summary_method=None,
    temperature=0.7,
    log_path=None
) -> (int, str): #
    clues = {}
    premise = g2t_client.generate(', '.join(start_community.bfs2text(summary_method))) #first parameter
    text_of_list = [list() for i in range(len(chains))]
    for index in range(len(chains)): #chains width
        for jndex in range(len(chains[index])): #current depth
            edges = []
            commu = chains[index][jndex]
            if jndex == 0:
                edges = community_tool.get_community_edges(start_community, commu) #use edges out first
            else:
                edges = community_tool.get_community_edges(chains[index][jndex-1], commu) #use edges out first
            if len(edges) > 0:
                edge_text = g2t_client.generate(','.join(community_tool.triple2text(list(set(edges)))))
                if len(edge_text.strip()) > 0:
                    text_of_list[index].append(edge_text)
            commu_text = g2t_client.generate(','.join(commu.bfs2text(summary_method)))
            if len(commu_text.strip()) > 0: 
                text_of_list[index].append(commu_text)
    for index in range(len(text_of_list)):
        if len(text_of_list[index]) > 0:
            clues[len(clues)+1] = '; '.join(text_of_list[index])
    assert len(clues) > 0 #at least one clues
    request = prompt_adapter.get_reasoning_prompt(premise, question, clues, 'text')
    l_status,response,num_toks,repeat = llm_client.generate(request, temperature=temperature)
    if l_status == 1:
        singal,answer = prompt_adapter.get_reasoning_result(response)
        log_content = (
            f"reasoning_by_g2t: \n"
            f"number of tokens: {num_toks}\n"
            f"question:{question}\n"
            f"clues:\n0. {premise}\n" +  "\n".join([f"{id_}. {clues[id_]}" for id_ in clues]) + "\n"
            f"repeat: {repeat}\n"
            f"response:\n{response}\n\n"
            )
        if log_path:
            log_plain_text(log_path, log_content) #'\n' for one reasoning, unknow still be log
        else:
            print(log_content)
        if singal >= 0: #prompt_adapter only return -1,0,1
            if singal == 1:
                return Status.OK, answer
            else: #0 UNK but continue
                return Status.OK, None
        else: #reasoning error
            return Status.RER, None
    log_content = (
        f"Status.SERR:\n"
        f"reasoning_by_g2t: \n"
        f"repeat: {repeat}\n"
        f"request:\n{request}\n"
        f"response:\n{response}\n\n"
        )
    if log_path:
        log_plain_text(log_path, log_content)
    else:
        print(log_content)
    return Status.SERR, None

'''
Two phases of FastToG
'''
# 1. get neighbor communities from entity (start_community)
# 2. graph pruning for neighbor communities (first-pharse communities)
# 3. append first-pharse communities to reasoning chain
# return center_community, candidate_communities
def initial_pharse(question, kg_cli, llm_cli, g2t_cli, start_community, args, log_path) -> (int,Community,List[Community]):
    status = Status.UNK
    #Build Center Community and search the neighbors
    if log_path is not None:
        print('initial phase...')
    status,communities = community_search(kg_cli, start_community, args.community_detect_algorithm,
        args.search_max_hop, args.search_max_neighbor, args.search_decline_rate, args.community_max_size)
    if status != Status.OK:
        return status,None,None
    center_community = community_tool.find_belonged_community_by_nid(communities, nid=start_community.cid)
    #First community pruning pharse (Basic Pruning)
    neighbor_communities = community_tool.get_neighbor_communities(center_community, communities, args.community_connected_threshold)
    candidate_communities = None
    if len(neighbor_communities) > args.reasoning_chain_width: #graph_prune -> reasoning_chain_width
        candidate_communities = graph_prune(center_community, neighbor_communities, args.community_max_candidate)
    elif len(neighbor_communities) > 0:
        candidate_communities = neighbor_communities
    else:
        return Status.NME,None,None
    #Second community pruning pharse (LLMs Pruning)
    if len(candidate_communities) > args.reasoning_chain_width:
        c_status,pruned_communities = Status.UNK,None 
        if g2t_cli:
            c_status,pruned_communities = community_prune_by_g2t(
                llm_cli, g2t_cli, question, 
                hist_communities = [center_community], 
                cand_communities = candidate_communities,
                keep_candidate = args.reasoning_chain_width, 
                summary_method=args.community_graph_prune_algo,
                temperature=args.llm_prune_temperature,
                log_path=log_path)
        else:
            c_status,pruned_communities = community_prune_by_triples(
                llm_cli, question, 
                hist_communities = [center_community], 
                cand_communities = candidate_communities,
                keep_candidate = args.reasoning_chain_width, 
                summary_method=args.community_graph_prune_algo,
                temperature=args.llm_prune_temperature,
                log_path=log_path)
        if c_status == Status.OK:
            if len(pruned_communities) == args.reasoning_chain_width:
                candidate_communities = pruned_communities
                status = Status.OK
            else:
                candidate_communities = None
                status = Status.PER
        else:
            status = c_status
    else:
        status = Status.OK #not thing to do
    return status,center_community,candidate_communities

# Second Phase
# for each depth:
#     for each chain:
#         1. search communities
#         2. append to chain
#     reasoning
def main_pharse(question, kg_cli, llm_cli, g2t_cli, center_community, reasoning_chain, args, log_path) -> (int,str):
    count = 0
    is_updated = False
    status = Status.UNK
    communities_been_searched = set([center_community.cid]) #cid set for avoiding repeated communities being joined to reasoning chain
    reasoning_range = None
    if log_path is not None:
        reasoning_range = tqdm(range(args.reasoning_chain_depth-1), desc='reasoning phase...')
    else:
        reasoning_range = range(args.reasoning_chain_depth-1)
    for index in reasoning_range: #max reasoning times
        count += 1
        is_updated = False
        lens = [len(rc) for rc in reasoning_chain]
        if all(l == 0 for l in lens):
            status = Status.ESTOP
            break #all chains are not statisfied
        for jndex in range(len(reasoning_chain)): #width, won't change
            if len(reasoning_chain[jndex]) > 0:
                if len(reasoning_chain[jndex]) == 0: #not any community selected in the first round
                    continue
                current_community = reasoning_chain[jndex][-1] #last as current
                _,communities = community_search(kg_cli, current_community, args.community_detect_algorithm,
                    args.search_max_hop, args.search_max_neighbor, args.search_decline_rate, args.community_max_size)
                new_communities = [] #communities not in communities_been_searched
                for comm in communities:
                    if comm.cid not in communities_been_searched:
                        new_communities.append(comm)
                if len(new_communities) > 0: #only one (best)
                    neighbor_communities = community_tool.get_neighbor_communities(current_community, new_communities, args.community_connected_threshold)
                    if len(neighbor_communities) > 0:
                        candidate_communities = graph_prune(current_community, neighbor_communities, args.community_max_candidate)
                        if len(candidate_communities) == 1: #only one no-neighbor candidate left
                            reasoning_chain[jndex].append(candidate_communities[-1])
                            communities_been_searched.add(candidate_communities[-1].cid)
                            status = Status.OK
                            is_updated = True
                        else:
                            c_status,pruned_communities = Status.UNK,None
                            if g2t_cli:
                                c_status,pruned_communities = community_prune_by_g2t( #best
                                    llm_client = llm_cli, 
                                    g2t_client = g2t_cli,
                                    question = question,
                                    hist_communities = [center_community] + reasoning_chain[jndex],
                                    cand_communities = candidate_communities,
                                    keep_candidate = 1, #BEST SELECTION
                                    summary_method=args.community_graph_prune_algo,
                                    temperature=args.llm_prune_temperature,
                                    log_path=log_path
                                )
                            else:
                                c_status,pruned_communities = community_prune_by_triples( #best
                                    llm_client = llm_cli, 
                                    question = question,
                                    hist_communities = [center_community] + reasoning_chain[jndex],
                                    cand_communities = candidate_communities,
                                    keep_candidate = 1, #BEST SELECTION
                                    summary_method=args.community_graph_prune_algo,
                                    temperature=args.llm_prune_temperature,
                                    log_path=log_path
                                )
                            if c_status == Status.OK: #Single Selection
                                reasoning_chain[jndex].append(pruned_communities[-1])
                                communities_been_searched.add(pruned_communities[-1].cid)
                                status = Status.OK
                                is_updated = True
                            else: #LLM errors, we assume that none of selection are relevant to the question
                                status = c_status 
                                reasoning_chain[jndex] = [] #dispose this chain
                    else: #if len(neighbor_communities) == 0:
                        status = Status.NME
                else: #new_communities == 0
                    status = Status.NME
        if is_updated:
            r_status,answer = Status.UNK,None
            if g2t_cli:
                r_status,answer = reasoning_by_g2t(
                    llm_client = llm_cli,
                    g2t_client = g2t_cli,
                    question = question,
                    start_community = center_community,
                    chains = reasoning_chain,
                    summary_method = args.community_graph_prune_algo,
                    temperature=args.llm_reasoning_temperature,
                    log_path= log_path
                )
            else:
                r_status,answer = reasoning_by_triples(
                    llm_client = llm_cli,
                    question = question,
                    start_community = center_community,
                    chains = reasoning_chain,
                    summary_method = args.community_graph_prune_algo,
                    temperature=args.llm_reasoning_temperature,
                    log_path= log_path
                )
            if r_status == Status.OK:
                if answer is None: #unknown, continue ToG
                    continue
                else: #
                    return Status.OK, answer
            else: #other error
                return r_status, None
        #one reasoning iteration
    if count == args.reasoning_chain_depth-1:
        return Status.EXDTH,None
    else:
        return status,None #other errors

def fastToG(
    question:str, 
    entity_id:int,
    entity_name:str,
    case_path:str,
    kg_cli,
    llm_cli,
    g2t_cli,
    args
) -> (bool, str):
    reasoning_chains = [list() for i in range(args.reasoning_chain_width)] #WIDTH * DEPTH of Community
    reasoning_text_chains = [list() for i in range(args.reasoning_chain_width)] #WIDTH * DEPTH of Community (Text)
    max_depth = [len(rc) for rc in reasoning_chains]
    center_entity = Community([(entity_id, entity_name, 0)], []) #community as node
    llm_log_file_path = case_path + '/' + args.llm_log_file_name if args.llm_log_file_name is not None else None
    reasoning_chain_log_path = case_path + '/' + args.reasoning_chains_log if args.reasoning_chains_log is not None else None
    reasoning_chain_vis_path = case_path + '/' + args.kg_graph_file_name if args.kg_graph_file_name is not None else None
    
    status,center_community,candidate_communities = initial_pharse(question, kg_cli, llm_cli, g2t_cli, \
                                                                 center_entity, args, llm_log_file_path)
    answer = None
    if status == Status.OK: #something wrong with community searching else #ISOLATED ENTITY etc
        for i in range(len(candidate_communities)):
            if candidate_communities[i] is not None:
                reasoning_chains[i].append(candidate_communities[i]) #first pharse something may be none
        r_status = Status.UNK
        if g2t_cli:
            r_status,answer = reasoning_by_g2t( #first pharse reasoing
                llm_client = llm_cli,
                g2t_client = g2t_cli,
                question = question,
                start_community = center_community,
                chains = reasoning_chains,
                summary_method = args.community_graph_prune_algo,
                temperature=args.llm_reasoning_temperature,
                log_path= llm_log_file_path
            )
        else:
            r_status,answer = reasoning_by_triples( #first pharse reasoing
                llm_client = llm_cli,
                question = question,
                start_community = center_community,
                chains = reasoning_chains,
                summary_method = args.community_graph_prune_algo,
                temperature=args.llm_reasoning_temperature,
                log_path= llm_log_file_path
            )    
        if r_status == Status.OK and answer is not None:
            if reasoning_chain_vis_path:
                display_chains(center_community, reasoning_chains, reasoning_chain_vis_path)
            if reasoning_chain_log_path:
                save_chains(center_community, reasoning_chains, args.community_graph_prune_algo, reasoning_chain_log_path)
            return Status.OK,answer,max_depth
        else: #reasoning error
            #else is 0, which means can not figure out in this round, so continue
            status,answer = main_pharse(question, kg_cli, llm_cli, g2t_cli, center_community, reasoning_chains, args, llm_log_file_path)
            #display
            if reasoning_chain_vis_path:
                display_chains(center_community, reasoning_chains, reasoning_chain_vis_path)
            if reasoning_chain_log_path:
                save_chains(center_community, reasoning_chains, args.community_graph_prune_algo, reasoning_chain_log_path) 

    max_depth = [len(rc) for rc in reasoning_chains]
    return status,answer,max_depth

'''
Basic Arguments
'''
parser = argparse.ArgumentParser('Wider, Deeper, and Faster ToG! ')
parser.add_argument("--base_path", type=str,
                    default='', help="base path for this trial") #if exist, try save log else just output log
parser.add_argument("--query", type=str,
                    default='', help="query for FastToG...")
parser.add_argument("--entity", type=str,
                    default='', help="entity for this trial")
#chain specification
parser.add_argument("--reasoning_chain_width", type=int,
                    default=3, choices=[1,2,3,4], help="maximum width of reasoning chain")
parser.add_argument("--reasoning_chain_depth", type=int,
                    default=5, choices=[1,2,4,8], help="maximum depth of reasoning chain.")
#kg searching specification (based on node)
parser.add_argument("--search_max_hop", type=int,
                    default=3, help="max searching depth for one KG query")
parser.add_argument("--search_max_neighbor", type=int,
                    default=20, help="max searching width for one KG query")
parser.add_argument("--search_decline_rate", type=float,
                    default=0.33, help="declining rate for searching hop by hop")
parser.add_argument("--search_topk", type=int,
                    default=100, help="topk nodes if the retrieving number is too large by above conditions")
#community specification
parser.add_argument("--community_detect_algorithm", type=callable,
                    default=louvain_method, choices=[louvain_method, girvan_newman, spectral_clustering], 
                    help="algorithms of community detection")
parser.add_argument("--community_max_size", type=int,
                    default=5, help="max node number of a community")
parser.add_argument("--community_max_candidate", type=int,
                    default=8, help="max number of communities to be pruned by LLMs")
parser.add_argument("--community_connected_threshold", type=int,
                    default=0, help="threshold for deciding two communities are connected")
parser.add_argument("--community_graph_prune_algo", type=callable,
                    default=prims, choices=[prims, kruskal], 
                    help="summary the community for lower token usage")
#LLM specification
parser.add_argument("--llm_api", type=str, required=True,
                    default="", help="llms api")
parser.add_argument("--llm_api_key", type=str, required=True,
                    default="", help="llms api key")
parser.add_argument("--llm_model", type=str, 
                    default="gpt-4o-mini", help="llms model name for normal query (length < token_threshold)")
parser.add_argument("--llm_model_long", type=str, 
                    default="gpt-3.5-turbo-16k", help="llms model name for long query (length >= token_threshold)")
parser.add_argument("--llm_prune_temperature", type=float,
                    default=0.4, help="temperature for LLM pruning")
parser.add_argument("--llm_reasoning_temperature", type=float,
                    default=0.7, help="temperature for LLM reasoning")
parser.add_argument("--llm_cot_temperature", type=float,
                    default=0.7, help="temperature for LLM cot reasoning")
parser.add_argument("--llm_log_file_name", type=str,
                    default="llm_log.txt", help="LLM output without any annotation")
parser.add_argument("--reasoning_chains_log", type=str,
                    default="reasoning_chains_log.csv", help="log the reasoning chains as text")
#KG specification
parser.add_argument("--kg_api", type=str, required=True,
                    default="", help="api for knowledge graph engine")
parser.add_argument("--kg_user", type=str, required=True,
                    default="", help="user for knowledge graph engine")
parser.add_argument("--kg_pw", type=str, required=True,
                    default="", help="password for knowledge graph engine")
parser.add_argument("--kg_graph_file_name", type=str,
                    default="visual", help="path for visualization of local graph, nonable")
#G2T specification
parser.add_argument("--graph2text_path", type=str,
                    default="", help="path for graph2text model")
parser.add_argument("--graph2text_max_length", type=int,
                    default=64, help="max length for graph2text model")

if __name__ == "__main__":
    args = parser.parse_args()
    
    kg_cli = neo4j_client(args.kg_api, args.kg_user, args.kg_pw)
    llm_cli = llm_client(url=args.llm_api, 
                     api_key=args.llm_api_key, 
                     models=args.llm_model,
                     max_tokens=4096,
                     debug=False
                    )
    
    status,res = kg_cli.get_node_by_label(args.entity)
    if status <= 0:
        print(f'entity:{args.entity} is not found.')
        kg_cli.close()
        exit()
    entity_id = res[0]

    case_path = None
    if len(args.base_path) > 0:
        case_path = args.base_path + '/' + args.entity.replace(' ', '_') + '-' + str(int(time.time()))
        if os.path.exists(case_path):
            shutil.rmtree(case_path)
        os.mkdir(case_path)
    if args.community_max_size == 1:
        args.search_max_hop = 1
    
    g2t_cli = None
    if args.graph2text_path:
        g2t_cli = graph2text_client(args.graph2text_path, max_length=args.graph2text_max_length)
    status,pred,depth = fastToG(
        question=args.query, 
        entity_id=entity_id, 
        entity_name=args.entity,
        case_path=case_path,
        kg_cli=kg_cli,
        llm_cli=llm_cli,
        g2t_cli=g2t_cli,
        args=args
    )
    kg_cli.close()
    print(status)
    print(pred)
    if case_path:
        print(f'please see the folder {case_path} for more detail.')