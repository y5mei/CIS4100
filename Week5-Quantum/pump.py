import dimod
from dwave.system import DWaveSampler, EmbeddingComposite
from dimod import BinaryQuadraticModel
import itertools

pumps = [0, 1, 2, 3]
costs = [[36, 27],
         [56, 65],
         [48, 36],
         [52, 16],
         ]

flow = [2, 7, 3, 8]
demand = 20
time = [0, 1]

# Step-1, build a variable list for each pump

x = [[f'P{p}_AM', f'P{p}_PM'] for p in pumps]
# flat the list of variables
# r = list(itertools.chain(*x))
print(x)

# Step-2, Initialize BOM
bqm = BinaryQuadraticModel('BINARY')

# Step-3, Write the Objective Function
for p in pumps:
    for t in time:
        pump_name = x[p][t]
        cost = costs[p][t]
        print("============= This is a empty variable, cost list ===========")
        print(f'Build Interaction {pump_name} with cost {cost}')
        bqm.add_variable(x[p][t],costs[p][t])

# Constraint-1: Every Pump runs at least once per day
for p in pumps:
    c1 = [(x[p][t], 1) for t in time]
    print(c1)
    bqm.add_linear_inequality_constraint(
        c1,
        lb=1,
        ub=len(time),
        lagrange_multiplier=10,
        label='c1_pump_' + str(p)
    )
print("===================")
# constraint-2: We Can only Run at most 3 pumps per time slot
for t in time:
    c2 = [(x[p][t], 1) for p in pumps]
    print("=========== This is the constraint 2, need 1 pare pump ====================")
    print(c2)
    bqm.add_linear_inequality_constraint(
        c2,
        constant = -3,
        lagrange_multiplier=1,
        label='c2_time'+str(t)
    )

# Constraint-3 satisfy the daily demand
print("===================")
c3 = [(x[p][t], flow[p]) for t in time for p in pumps]
print("=============  This is constraint 3: need to meet the daily demand ===============")
print(c3)
bqm.add_linear_equality_constraint(c3,
                                     constant=-demand,
                                     lagrange_multiplier=28,
                                     # label='C1_PUMP_'+str(p)
                                     )

# sampler = EmbeddingComposite(DWaveSampler())
# sample_set = sampler.sample(bqm, num_reads=1000)
sampler = dimod.ExactSolver()


sampleset = sampler.sample(bqm)
df = sampleset.to_pandas_dataframe()
print(df.head())
print(df.columns)

# sample_set = sampler.sample(bqm)
# sample = sample_set.first.sample
# total_flow = 0
# total_cost = 0
# print(sample)
# print("\n\tAM\tPM")
# for p in pumps:
#     printout = 'P'+str(p)
#     for time in range(2):
#         printout += "\t"+str(sample[x[p][time]])
#         total_flow += sample[x[p][time]]*flow[p]
#         total_cost += sample[x[p][time]]*costs[p][time]
#     print(printout)
#
# print("\nTotal flow:\t", total_flow)
# print("Total Cost:\t", total_cost, "\n")
