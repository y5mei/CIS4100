import numpy as np
import pandas as pd

SIZE = 100000
a=np.random.normal(size=SIZE)
prob_x1=np.random.uniform(size = SIZE)
x1=[-10 if i <0.009 else 0 for i in prob_x1]
total1 = a+x1

b=np.random.normal(size=SIZE)
prob_x2=np.random.uniform(size = SIZE)
x2=[-10 if i <0.009 else 0 for i in prob_x2]
total2 = b+x2


res1= np.percentile(total1, 1)
res2= np.percentile(total2, 1)
res= np.percentile(total1+total2, 1)


print(res1)
print(res2)
print(res)

d = {"X":total1,"Y":total2,"X+Y":total1+total2}
df = pd.DataFrame(d)
df.to_csv("Result.csv")