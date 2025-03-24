import random
import numpy as np

def split_list_into_n(x, n):
    random.shuffle(x)  # Shuffling the list in-place
    split_size = len(x) // n
    start = 0
    end = split_size
    split_lists = []
    for i in range(n - 1):
        split_lists.append(set(x[start:end]))
        start = end
        end += split_size
    split_lists.append(set(x[start:]))  # Remaining elements into the last sublist
    return split_lists

def random_clustering(adj_matrix : np.ndarray, m : int = None, max_iter : int = 100, delta : float = 1e-4) -> (list,list):
	number_of_comm = int(len(adj_matrix)/m) + 1
	random_partition = split_list_into_n(list(range(len(adj_matrix))), number_of_comm)
	random_quality = [0] * number_of_comm
	return random_partition,random_quality