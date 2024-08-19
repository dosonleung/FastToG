import numpy as np
import igraph as ig
import matplotlib.pyplot as plt

def _short_name(s, trunc_len):
    if len(s) <= trunc_len:
        return s
    words = s.split()
    result = []
    current_line = ''
    line_count = 0
    for word in words:
        if len(current_line) + len(word) <= trunc_len:
            if current_line:
                current_line += ' ' + word
            else:
                current_line = word
        else:
            result.append(current_line)
            current_line = word
            line_count += 1
            if line_count >= 2:
                break
    if current_line:
        result.append(current_line)
    if line_count >= 2:
        return '\n'.join(result) + '...'
    else:
        return '\n'.join(result)

def display_community(label_list, relation_matrix, community_list, 
                      community_centers=None, algo_method=None, colors=None, show_edges=True, 
                      random_state=3, figsize=(6,6), dpi=200, save_path=None):
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi, clear=True)
    random_index = list(range(len(label_list)))
    if random_state > 0:
        np.random.seed(random_state)
        random_index = np.random.choice(range(len(label_list)), len(label_list), replace=False)
    label_list = np.array(label_list)[random_index]
    community_list = np.array(community_list)[random_index]
    _,community_tags = np.unique(community_list, return_inverse=True) #reflect from 0 to N
    community_unique_list = sorted(list(set(community_list)), reverse=False)
    community_centers = np.array(community_centers)[random_index]
    relation_matrix_ = np.array(relation_matrix)
    #ipdb.set_trace(context=15)
    if relation_matrix_.shape[0] > 0 and relation_matrix_.shape[-1] > 0:
        relation_matrix_ = relation_matrix_[random_index]
        relation_matrix_ = relation_matrix_[:, random_index]
    adj_matrix = np.where(np.array(relation_matrix_) == None, 0, 1)
    # Create an igraph Graph from the adjacency matrix A
    edge_label,vertex_label = [],[_short_name(label_list[i], 12) for i in range(len(label_list))]
    if show_edges:
        for index in range(len(relation_matrix_)):
            for jndex in range(index, len(relation_matrix_[index])):
                if relation_matrix_[index][jndex] is not None:
                    edge_label.append(_short_name(relation_matrix_[index][jndex], 15))
    g = ig.Graph.Adjacency((adj_matrix > 0).tolist(), mode="UNDIRECTED")
    comm = ig.VertexClustering(g, membership=community_tags)
    selected_colors,community_mapping = [],True
    if colors is None:
        selected_colors = ig.ClusterColoringPalette(n=len(community_unique_list))
        community_mapping = True
    else:
        for index in range(len(community_tags)):
            selected_colors.append(colors[community_tags[index] % len(community_unique_list)])
        community_mapping = {i:colors[i % len(colors)] for i,_ in enumerate(community_unique_list)}
        community_mapping = community_mapping.items()
    if community_centers is not None:
        vertex_shape = list(map(lambda i: 'triangle' if community_centers[i]==1 else 'circle', range(len(label_list))))
    if show_edges:
        ig.plot(comm,
                vertex_size = 45,
                vertex_shape = vertex_shape,
                vertex_label = vertex_label, 
                edge_label = edge_label, 
                vertex_label_size = 11,
                edge_label_size = 8,
                vertex_color = selected_colors,
                edge_width = 1.5,
                edge_color = ['#00000080'],
                mark_groups = community_mapping,
                target=ax)
    else:
        ig.plot(comm,
                vertex_size = 45,
                vertex_shape = vertex_shape,
                vertex_label = vertex_label, 
                vertex_label_size = 11,
                edge_label_size = 8,
                vertex_color = selected_colors,
                edge_width = 1.5,
                edge_color = ['#00000080'],
                mark_groups = community_mapping,
                target=ax)
    # Create a custom color legend
    legend_handles = []
    for i in range(len(community_unique_list)):
        handle = ax.scatter(
            [], [],
            s=120,
            facecolor=colors[i % len(colors)],
            edgecolor='#00000080',
            label=community_unique_list[i],
        )
        legend_handles.append(handle)
    ax.legend(
        handles=legend_handles,
        title='Community:',
        bbox_to_anchor=(0, 1.0),
        bbox_transform=ax.transAxes,
    )
    if algo_method is None:
        algo_method = 'unknown'
    plt.title(algo_method.__name__)
    if save_path:
        plt.savefig(save_path)
        fig.clear()
        plt.clf()
    else:
        plt.show()
    plt.close(fig)


#selected_index = [0,3]
#display_selected_community(selected_index, label_list, relation_matrix, commtag_list, center_list, \
#                           louvain_method, colors=[COLORS[i] for i in selected_index], random_state=123)
def display_selected_community(select_community, label_list, relation_matrix, commtag_list, center_list, \
                               method, colors, show_edges=True, random_state=123, figsize=(6,6), dpi=200, save_path=None):
    select_index = []
    for index in range(len(select_community)):
        for jndex in range(len(commtag_list)):
            if commtag_list[jndex] == select_community[index]:
                select_index.append(jndex)
    label_list_ = [label_list[i] for i in select_index]
    commtag_list_ = [commtag_list[i] for i in select_index]
    #_,commtag_list_ = np.unique(commtag_list_, return_inverse=True)
    center_list_ = [center_list[i] for i in select_index]
    relation_matrix_ = np.array(relation_matrix)
    if relation_matrix_.shape[0] > 0 and relation_matrix_.shape[-1] > 0:
        relation_matrix_ = relation_matrix_[select_index]
        relation_matrix_ = relation_matrix_[:, select_index]
    display_community(label_list_, relation_matrix_, commtag_list_, center_list_, method, 
        colors=colors, show_edges=show_edges, random_state=random_state, figsize=figsize, dpi=dpi, save_path=save_path)