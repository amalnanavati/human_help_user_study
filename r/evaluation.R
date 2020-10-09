require(lme4)
require(emmeans)
require(effects)
require(languageR)
require(tidyr)
require(ggplot2)
library(emmeans)

dataNoBusyness <- read.csv("/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs_evaluation/humanHelpUserStudyDataWithExclusion.csv")

dataNoBusyness <- within(dataNoBusyness, {
  User.ID <- factor(User.ID)
  Policy <- factor(Policy, levels = c("Hybrid", "Contextual", "Individual"))
  Num.Correct.Rooms <- as.integer(Num.Correct.Rooms)
  Num.Asking <- as.integer(Num.Asking)
  Num.Helping <- as.integer(Num.Helping)
  Num.Helping.Rejected <- as.integer(Num.Helping.Rejected)
  Overall.Willingness.To.Help <- as.numeric(Overall.Willingness.To.Help)
  Age <- as.integer(Age)
  Gender <- factor(Gender)
  Prosociality <- as.numeric(Prosociality)
  Video.Game.Experience <- as.integer(Video.Game.Experience)
  Survey.Duration <- as.numeric(Survey.Duration)
  Slowness <- as.numeric(Slowness)
  Tutorial.Overall.Willingness.to.Help <- as.numeric(Tutorial.Overall.Willingness.to.Help)
  Average.Busyness <- as.numeric(Average.Busyness)
})

print(dataNoBusyness)

finalModelCorrectRoomsNoBusyness <- glm(Num.Correct.Rooms ~ Policy , data = dataNoBusyness, family = poisson(link = "log"))
summary(finalModelCorrectRoomsNoBusyness)
pchisq(summary(finalModelCorrectRoomsNoBusyness)$deviance, summary(finalModelCorrectRoomsNoBusyness)$df.residual) # if this value is > 0.05, the model is a good fit
emmeans(finalModelCorrectRoomsNoBusyness, ~ Policy)
contrast(emmeans(finalModelCorrectRoomsNoBusyness, ~ Policy), method = "trt.vs.ctrl", ref = 1)
mean(dataNoBusyness[dataNoBusyness$Policy == "Hybrid",]$Num.Correct.Rooms)
sd(dataNoBusyness[dataNoBusyness$Policy == "Hybrid",]$Num.Correct.Rooms)
mean(dataNoBusyness[dataNoBusyness$Policy == "Contextual",]$Num.Correct.Rooms)
sd(dataNoBusyness[dataNoBusyness$Policy == "Contextual",]$Num.Correct.Rooms)
mean(dataNoBusyness[dataNoBusyness$Policy == "Individual",]$Num.Correct.Rooms)
sd(dataNoBusyness[dataNoBusyness$Policy == "Individual",]$Num.Correct.Rooms)

finalModelAskingNoBusyness <- glm(Num.Asking ~ Policy , data = dataNoBusyness, family = poisson(link = "log"))
summary(finalModelAskingNoBusyness)
pchisq(summary(finalModelAskingNoBusyness)$deviance, summary(finalModelAskingNoBusyness)$df.residual) # if this value is > 0.05, the model is a good fit
contrast(emmeans(finalModelAskingNoBusyness, ~ Policy), method = "trt.vs.ctrl", ref = 1)
mean(dataNoBusyness[dataNoBusyness$Policy == "Hybrid",]$Num.Asking)
sd(dataNoBusyness[dataNoBusyness$Policy == "Hybrid",]$Num.Asking)
mean(dataNoBusyness[dataNoBusyness$Policy == "Contextual",]$Num.Asking)
sd(dataNoBusyness[dataNoBusyness$Policy == "Contextual",]$Num.Asking)
mean(dataNoBusyness[dataNoBusyness$Policy == "Individual",]$Num.Asking)
sd(dataNoBusyness[dataNoBusyness$Policy == "Individual",]$Num.Asking)

finalModelHelpingNoBusyness <- glm(Num.Helping ~ Policy , data = dataNoBusyness, family = poisson(link = "log"))
summary(finalModelHelpingNoBusyness)
pchisq(summary(finalModelHelpingNoBusyness)$deviance, summary(finalModelHelpingNoBusyness)$df.residual) # if this value is > 0.05, the model is a good fit
contrast(emmeans(finalModelHelpingNoBusyness, ~ Policy), method = "trt.vs.ctrl", ref = 1)
mean(dataNoBusyness[dataNoBusyness$Policy == "Hybrid",]$Num.Helping)
sd(dataNoBusyness[dataNoBusyness$Policy == "Hybrid",]$Num.Helping)
mean(dataNoBusyness[dataNoBusyness$Policy == "Contextual",]$Num.Helping)
sd(dataNoBusyness[dataNoBusyness$Policy == "Contextual",]$Num.Helping)
mean(dataNoBusyness[dataNoBusyness$Policy == "Individual",]$Num.Helping)
sd(dataNoBusyness[dataNoBusyness$Policy == "Individual",]$Num.Helping)

finalModelHelpingNoBusyness <- glm(Num.Helping.Rejected ~ Policy , data = dataNoBusyness, family = poisson(link = "log"))
summary(finalModelHelpingNoBusyness)
pchisq(summary(finalModelHelpingNoBusyness)$deviance, summary(finalModelHelpingNoBusyness)$df.residual) # if this value is > 0.05, the model is a good fit
contrast(emmeans(finalModelHelpingNoBusyness, ~ Policy), method = "trt.vs.ctrl", ref = 1)
mean(dataNoBusyness[dataNoBusyness$Policy == "Hybrid",]$Num.Helping.Rejected)
sd(dataNoBusyness[dataNoBusyness$Policy == "Hybrid",]$Num.Helping.Rejected)
mean(dataNoBusyness[dataNoBusyness$Policy == "Contextual",]$Num.Helping.Rejected)
sd(dataNoBusyness[dataNoBusyness$Policy == "Contextual",]$Num.Helping.Rejected)
mean(dataNoBusyness[dataNoBusyness$Policy == "Individual",]$Num.Helping.Rejected)
sd(dataNoBusyness[dataNoBusyness$Policy == "Individual",]$Num.Helping.Rejected)

# data <- read.csv("/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs_evaluation/humanHelpUserStudyDataWithExclusionNumeric.csv")
# 
# data <- within(data, {
#   User.ID <- factor(User.ID)
#   Policy <- factor(Policy, levels = c("Proposed", "Only Fixed", "Only Random"))
#   # Busyness <- as.numeric(Busyness)
#   Busyness <- factor(Busyness)
#   Num.Correct.Rooms <- as.integer(Num.Correct.Rooms)
#   Num.Asking <- as.integer(Num.Asking)
#   Num.Helping <- as.integer(Num.Helping)
#   Overall.Willingness.To.Help <- as.numeric(Overall.Willingness.To.Help)
#   Age <- as.integer(Age)
#   Gender <- factor(Gender)
#   Prosociality <- as.numeric(Prosociality)
#   Video.Game.Experience <- as.integer(Video.Game.Experience)
#   Survey.Duration <- as.numeric(Survey.Duration)
#   Slowness <- as.numeric(Slowness)
#   Tutorial.Overall.Willingness.to.Help <- as.numeric(Tutorial.Overall.Willingness.to.Help)
#   Average.Busyness <- as.numeric(Average.Busyness)
# })
# # 
# print(data)
# 
# # baseline <- glmer(Num.Correct.Rooms ~ (1 | User.ID), data = data, family = poisson)
# # summary(baseline)
# # 
# # policyM <- update(baseline, .~ Policy + .)
# # anova(baseline, policyM)
# # busynessM <- update(baseline, .~ Busyness + .)
# # anova(baseline, busynessM)
# # 
# # policyM <- update(busynessM, .~ Policy + .)
# # anova(busynessM, policyM)
# # 
# # finalModel <- update(policyM, .~ Policy:Busyness + .)
# # anova(policyM, finalModel)
# # summary(finalModel)
# 
# # Num Correct Rooms
# finalModelCorrectRooms <- glmer(Num.Correct.Rooms ~ Policy + Policy:Busyness + (1 | User.ID), data = data, family = poisson(link = "log"))
# summary(finalModelCorrectRooms)
# pchisq(summary(finalModelCorrectRooms)$AIC['deviance'], summary(finalModelCorrectRooms)$AIC['df.resid']) # if this value is > 0.05, the model is a good fit
# 
finalModelAsking <- glmer(Num.Asking ~ Policy + Policy:Busyness + (1 | User.ID), data = data, family = poisson(link = "log"))
summary(finalModelAsking)
pchisq(summary(finalModelAsking)$AIC['deviance'], summary(finalModelAsking)$AIC['df.resid']) # if this value is > 0.05, the model is a good fit
pairs(emmeans(finalModelAsking, ~ Policy + Policy:Busyness), by = c("Busyness"))
# contrast(emmeans(finalModelAsking, ~ Policy + Policy:Busyness), method = "trt.vs.ctrl", ref = 1)
