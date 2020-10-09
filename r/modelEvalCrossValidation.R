require(lme4)
require(emmeans)
require(effects)
require(languageR)
require(tidyr)
require(ggplot2)
library(emmeans)
require(ez)

data <- read.csv("/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/processedData/80-20/results.csv")

data <- within(data, {
  Partition <- factor(Partition)
  Model <- factor(Model)
  Accuracy <- as.numeric(Accuracy)
  F1 <- as.numeric(F1)
  MCC <- as.numeric(MCC)
})

print(data)


model <- ezANOVA(data, Accuracy, Partition, within=Model)
print(model)
pairwise.t.test(data$Accuracy, data$Model, paired = TRUE, p.adjust.method = "bonferroni")

model <- ezANOVA(data, F1, Partition, within=Model)
print(model)
pairwise.t.test(data$F1, data$Model, paired = TRUE, p.adjust.method = "bonferroni")
