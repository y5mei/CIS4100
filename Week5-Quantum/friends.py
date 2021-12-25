import dimod
import networkx as nx
from collections import defaultdict
from dwave.system import DWaveSampler, EmbeddingComposite

# Reference: https://www.youtube.com/watch?v=Q4FE4jou5CA
# G = nx.Graph()
Edge = [(0,4),(0,5),(1,2),(1,6),(2,4),(3,7),(5,6),(6,7)]
# G.add_edges_from(Edge)

Q = defaultdict(int)

# Constraint
lagrange = 1
for i in range(8):
    Q[(i,i)] += -7*lagrange
    for j in range(i+1,8):
        Q[(i,j)] += 2*lagrange

# Objective
for i, j in Edge:
    Q[(i,i)] += 1
    Q[(j,j)] += 1
    Q[(i,j)] += -2

# sampler = EmbeddingComposite(DWaveSampler())
# sampleset = sampler.sample_qubo(Q, num_reads = 10, chain_strength = 10)
sampler = dimod.ExactSolver()
sampleset = sampler.sample_qubo(Q)

print(sampleset.first)