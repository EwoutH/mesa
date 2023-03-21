from boltzmann_wealth_model.model import BoltzmannWealthModel

model = BoltzmannWealthModel(200)
for i in range(100):
    model.step()

data = model.datacollector.get_agent_vars_dataframe()
data.to_csv("wealth_test.csv")
