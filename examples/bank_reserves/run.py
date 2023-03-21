from bank_reserves.server import server

from bank_reserves.model import BankReserves

model = BankReserves(init_people=200)
for i in range(100):
    model.step()

data = model.datacollector.get_agent_vars_dataframe()
data.to_csv("wealth_test.csv")

