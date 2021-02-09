require(lme4)
require(emmeans)
require(effects)
require(languageR)
require(tidyr)
require(ggplot2)
library(data.table)
require(car)
library(sjmisc)
library(sjmisc)

data <- read.csv("/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/humanHelpUserStudyPerResponseData.csv")

data <- within(data, {
  UUID <- factor(UUID)
  TaskI <- factor(TaskI)
  Busyness <- factor(Busyness, levels = c("free time", "medium", "high"))
  # Past.Frequency.of.Asking <- factor(Past.Frequency.of.Asking)
  Past.Frequency.of.Asking <- as.numeric(Past.Frequency.of.Asking)
  # Past.Frequency.of.Helping.Accurately <- factor(Past.Frequency.of.Helping.Accurately)
  Past.Frequency.of.Helping.Accurately <- as.numeric(Past.Frequency.of.Helping.Accurately)
  Human.Response <- factor(Human.Response)
  Prosociality <- as.numeric(Prosociality)
  Slowness <- as.numeric(Slowness)
  # Busyness.Numeric <- factor(Busyness.Numeric)
  Busyness.Numeric <- as.numeric(Busyness.Numeric)
  Num.Recent.Times.Did.Not.Help <- as.integer(Num.Recent.Times.Did.Not.Help)
  Age <- as.integer(Age)
  Navigational.Ability <- as.numeric(Navigational.Ability)
})

print(data)

# estimate the model and store results in m
# model <- glmer(Human.Response ~ Busyness.Numeric + (Busyness.Numeric | UUID) + Past.Frequency.of.Asking + Busyness.Numeric*Past.Frequency.of.Asking + Prosociality, data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
# model <- glmer(Human.Response ~ Busyness.Numeric + (Busyness.Numeric | UUID) + Past.Frequency.of.Asking + Prosociality, data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
# model <- glmer(Human.Response ~ Busyness.Numeric + (Busyness.Numeric | UUID) + Past.Frequency.of.Asking + Past.Frequency.of.Asking:Past.Frequency.of.Helping.Accurately + Prosociality, data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
# model <- glmer(Human.Response ~ Past.Frequency.of.Asking + (1 | UUID), data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))

# Pick the best model using the forward selecction technique of stepwise regression.
baseline <- glmer(Human.Response ~ (1 | UUID), data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))

# Step 1
busynessM <- update(baseline, .~ Busyness.Numeric + .)
anova(baseline, busynessM)
freqOfAskingM <- update(baseline, .~ Past.Frequency.of.Asking + .)
anova(baseline, freqOfAskingM)
# freqOfHelpingAccuratelyM <- update(baseline, .~ Past.Frequency.of.Helping.Accurately + .)
# anova(baseline, freqOfHelpingAccuratelyM)
# numRecentTimesDidNotHelpM <- update(baseline, .~ Num.Recent.Times.Did.Not.Help + .)
# anova(baseline, numRecentTimesDidNotHelpM)
# # prosocialityM <- update(baseline, .~ Prosociality + .)
# # anova(baseline, prosocialityM)
# # ageM <- update(baseline, .~ Age + .)
# # anova(baseline, ageM)

# Step 2 -- build onto busynessM
freqOfAskingM <- update(busynessM, .~ Past.Frequency.of.Asking + .)
anova(busynessM, freqOfAskingM)
# freqOfHelpingAccuratelyM <- update(busynessM, .~ Past.Frequency.of.Helping.Accurately + .)
# anova(busynessM, freqOfHelpingAccuratelyM)
# numRecentTimesDidNotHelpM <- update(busynessM, .~ Num.Recent.Times.Did.Not.Help + .)
# anova(busynessM, numRecentTimesDidNotHelpM)
# # prosocialityM <- update(busynessM, .~ Prosociality + .)
# # anova(busynessM, prosocialityM)
# # ageM <- update(busynessM, .~ Age + .)
# # anova(busynessM, ageM)

# # Step 3 -- build onto numRecentTimesDidNotHelpM
# freqOfAskingM <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Asking + .)
# anova(numRecentTimesDidNotHelpM, freqOfAskingM)
# freqOfHelpingAccuratelyM <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Helping.Accurately + .)
# anova(numRecentTimesDidNotHelpM, freqOfHelpingAccuratelyM)
# # prosocialityM <- update(numRecentTimesDidNotHelpM, .~ Prosociality + .)
# # anova(numRecentTimesDidNotHelpM, prosocialityM)
# # ageM <- update(numRecentTimesDidNotHelpM, .~ Age + .)
# # anova(numRecentTimesDidNotHelpM, ageM)

# # Step 4 -- build on prosocialityM
# freqOfAskingM <- update(prosocialityM, .~ Past.Frequency.of.Asking + .)
# anova(prosocialityM, freqOfAskingM)
# freqOfHelpingAccuratelyM <- update(prosocialityM, .~ Past.Frequency.of.Helping.Accurately + .)
# anova(prosocialityM, freqOfHelpingAccuratelyM)
# ageM <- update(prosocialityM, .~ Age + .)
# anova(prosocialityM, ageM)

# Step 4 - None of the above are significant -- we will now move onto interaction effects and continue building onto numRecentTimesDidNotHelpM
busyness_freqOfAskingI <- update(busynessM, .~ Busyness.Numeric:Past.Frequency.of.Asking + .)
anova(busynessM, busyness_freqOfAskingI)
# busyness_freqOfHelpingAccuratelyI <- update(numRecentTimesDidNotHelpM, .~ Busyness.Numeric:Past.Frequency.of.Helping.Accurately + .)
# anova(numRecentTimesDidNotHelpM, busyness_freqOfHelpingAccuratelyI)
# busyness_numRecentTimesDidNotHelpI <- update(numRecentTimesDidNotHelpM, .~ Busyness.Numeric:Num.Recent.Times.Did.Not.Help + .)
# anova(numRecentTimesDidNotHelpM, busyness_numRecentTimesDidNotHelpI)
# # busyness_prosocialityI <- update(numRecentTimesDidNotHelpM, .~ Busyness.Numeric:Prosociality + .)
# # anova(numRecentTimesDidNotHelpM, busyness_prosocialityI)
# # busyness_ageI <- update(numRecentTimesDidNotHelpM, .~ Busyness.Numeric:Age + .)
# # anova(numRecentTimesDidNotHelpM, busyness_ageI)
# freqOfAsking_freqOfHelpingI <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Asking:Past.Frequency.of.Helping.Accurately + .)
# anova(numRecentTimesDidNotHelpM, freqOfAsking_freqOfHelpingI)
# freqOfAsking_numRecentTimesDidNotHelpI <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Asking:Num.Recent.Times.Did.Not.Help + .)
# anova(numRecentTimesDidNotHelpM, freqOfAsking_numRecentTimesDidNotHelpI)
# # freqOfAsking_prosocialityI <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Asking:Prosociality + .)
# # anova(numRecentTimesDidNotHelpM, freqOfAsking_prosocialityI)
# # freqOfAsking_ageI <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Asking:Age + .)
# # anova(numRecentTimesDidNotHelpM, freqOfAsking_ageI)
# freqOfHelping_numRecentTimesDidNotHelpI <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Helping.Accurately:Num.Recent.Times.Did.Not.Help + .)
# anova(numRecentTimesDidNotHelpM, freqOfHelping_numRecentTimesDidNotHelpI)
# # freqOfHelping_prosocialityI <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Helping.Accurately:Prosociality + .)
# # anova(numRecentTimesDidNotHelpM, freqOfHelping_prosocialityI)
# # freqOfHelping_ageI <- update(numRecentTimesDidNotHelpM, .~ Past.Frequency.of.Helping.Accurately:Age + .)
# # anova(numRecentTimesDidNotHelpM, freqOfHelping_ageI)

# # Step 5 -- build onto busyness_freqOfAskingI
# busyness_freqOfHelpingAccuratelyI <- update(busyness_freqOfAskingI, .~ Busyness.Numeric:Past.Frequency.of.Helping.Accurately + .)
# anova(busyness_freqOfAskingI, busyness_freqOfHelpingAccuratelyI)
# busyness_numRecentTimesDidNotHelpI <- update(busyness_freqOfAskingI, .~ Busyness.Numeric:Num.Recent.Times.Did.Not.Help + .)
# anova(busyness_freqOfAskingI, busyness_numRecentTimesDidNotHelpI)
# # busyness_prosocialityI <- update(busyness_freqOfAskingI, .~ Busyness.Numeric:Prosociality + .)
# # anova(busyness_freqOfAskingI, busyness_prosocialityI)
# # busyness_ageI <- update(busyness_freqOfAskingI, .~ Busyness.Numeric:Age + .)
# # anova(busyness_freqOfAskingI, busyness_ageI)
# freqOfAsking_freqOfHelpingI <- update(busyness_freqOfAskingI, .~ Past.Frequency.of.Asking:Past.Frequency.of.Helping.Accurately + .)
# anova(busyness_freqOfAskingI, freqOfAsking_freqOfHelpingI)
# freqOfAsking_numRecentTimesDidNotHelpI <- update(busyness_freqOfAskingI, .~ Past.Frequency.of.Asking:Num.Recent.Times.Did.Not.Help + .)
# anova(busyness_freqOfAskingI, freqOfAsking_numRecentTimesDidNotHelpI)
# # freqOfAsking_prosocialityI <- update(busyness_freqOfAskingI, .~ Past.Frequency.of.Asking:Prosociality + .)
# # anova(busyness_freqOfAskingI, freqOfAsking_prosocialityI)
# # freqOfAsking_ageI <- update(busyness_freqOfAskingI, .~ Past.Frequency.of.Asking:Age + .)
# # anova(busyness_freqOfAskingI, freqOfAsking_ageI)
# freqOfHelping_numRecentTimesDidNotHelpI <- update(busyness_freqOfAskingI, .~ Past.Frequency.of.Helping.Accurately:Num.Recent.Times.Did.Not.Help + .)
# anova(busyness_freqOfAskingI, freqOfHelping_numRecentTimesDidNotHelpI)
# # freqOfHelping_prosocialityI <- update(busyness_freqOfAskingI, .~ Past.Frequency.of.Helping.Accurately:Prosociality + .)
# # anova(busyness_freqOfAskingI, freqOfHelping_prosocialityI)
# # freqOfHelping_ageI <- update(busyness_freqOfAskingI, .~ Past.Frequency.of.Helping.Accurately:Age + .)
# # anova(busyness_freqOfAskingI, freqOfHelping_ageI)

# # Build on busyness_ageI
# busyness_freqOfHelpingAccuratelyI <- update(busyness_ageI, .~ Busyness.Numeric:Past.Frequency.of.Helping.Accurately + .)
# anova(busyness_ageI, busyness_freqOfHelpingAccuratelyI)
# busyness_numRecentTimesDidNotHelpI <- update(busyness_ageI, .~ Busyness.Numeric:Num.Recent.Times.Did.Not.Help + .)
# anova(busyness_ageI, busyness_numRecentTimesDidNotHelpI)
# busyness_prosocialityI <- update(busyness_ageI, .~ Busyness.Numeric:Prosociality + .)
# anova(busyness_ageI, busyness_prosocialityI)
# freqOfAsking_freqOfHelpingI <- update(busyness_ageI, .~ Past.Frequency.of.Asking:Past.Frequency.of.Helping.Accurately + .)
# anova(busyness_ageI, freqOfAsking_freqOfHelpingI)
# freqOfAsking_numRecentTimesDidNotHelpI <- update(busyness_ageI, .~ Past.Frequency.of.Asking:Num.Recent.Times.Did.Not.Help + .)
# anova(busyness_ageI, freqOfAsking_numRecentTimesDidNotHelpI)
# freqOfAsking_prosocialityI <- update(busyness_ageI, .~ Past.Frequency.of.Asking:Prosociality + .)
# anova(busyness_ageI, freqOfAsking_prosocialityI)
# freqOfAsking_ageI <- update(busyness_ageI, .~ Past.Frequency.of.Asking:Age + .)
# anova(busyness_ageI, freqOfAsking_ageI)
# freqOfHelping_numRecentTimesDidNotHelpI <- update(busyness_ageI, .~ Past.Frequency.of.Helping.Accurately:Num.Recent.Times.Did.Not.Help + .)
# anova(busyness_ageI, freqOfHelping_numRecentTimesDidNotHelpI)
# freqOfHelping_prosocialityI <- update(busyness_ageI, .~ Past.Frequency.of.Helping.Accurately:Prosociality + .)
# anova(busyness_ageI, freqOfHelping_prosocialityI)
# freqOfHelping_ageI <- update(busyness_ageI, .~ Past.Frequency.of.Helping.Accurately:Age + .)
# anova(busyness_ageI, freqOfHelping_ageI)

# # Build on freqOfAsking_numRecentTimesDidNotHelpI
# busyness_freqOfHelpingAccuratelyI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Busyness.Numeric:Past.Frequency.of.Helping.Accurately + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, busyness_freqOfHelpingAccuratelyI)
# busyness_numRecentTimesDidNotHelpI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Busyness.Numeric:Num.Recent.Times.Did.Not.Help + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, busyness_numRecentTimesDidNotHelpI)
# busyness_prosocialityI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Busyness.Numeric:Prosociality + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, busyness_prosocialityI)
# freqOfAsking_freqOfHelpingI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Past.Frequency.of.Asking:Past.Frequency.of.Helping.Accurately + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, freqOfAsking_freqOfHelpingI)
# freqOfAsking_prosocialityI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Past.Frequency.of.Asking:Prosociality + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, freqOfAsking_prosocialityI)
# freqOfAsking_ageI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Past.Frequency.of.Asking:Age + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, freqOfAsking_ageI)
# freqOfHelping_numRecentTimesDidNotHelpI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Past.Frequency.of.Helping.Accurately:Num.Recent.Times.Did.Not.Help + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, freqOfHelping_numRecentTimesDidNotHelpI)
# freqOfHelping_prosocialityI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Past.Frequency.of.Helping.Accurately:Prosociality + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, freqOfHelping_prosocialityI)
# freqOfHelping_ageI <- update(freqOfAsking_numRecentTimesDidNotHelpI, .~ Past.Frequency.of.Helping.Accurately:Age + .)
# anova(freqOfAsking_numRecentTimesDidNotHelpI, freqOfHelping_ageI)

individualModel <- glmer(Human.Response ~ (1 | UUID), data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
contextualModel <- glm(Human.Response ~ Busyness.Numeric + Busyness.Numeric:Past.Frequency.of.Asking, data = data, family = binomial(link="logit"))

# Check whether we should add a random slope with busyness
busyness_random_slope <- update(busyness_freqOfAskingI, .~ (Busyness.Numeric | UUID) + .)
anova(busyness_freqOfAskingI, busyness_random_slope)
summary(busyness_random_slope)

# The busyness random slope model failed to converge, so we won't consider it.
# Nothing achieved significance (although freqOfAsking_numRecentTimesDidNotHelpI got close) so we will use that as our final model
finalModel <- busyness_freqOfAskingI
summary(finalModel)
Anova(finalModel)
fixParam <- fixef(finalModel)
ranParam <- ranef(finalModel)$UUID
n <- nrow(ranParam[1])
replicatedFixParam <- data.frame(matrix(rep(t(as.matrix(fixParam)),each=n),nrow=n))
params<-cbind(ranParam[1], replicatedFixParam)
colnames(params) <- append("(Intercept).Random.Effects", names(fixParam))
write.csv(setDT(params, keep.rownames="UUID")[], "/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/processedData/finalModel.csv", row.names=FALSE)

prosocialityModel <- update(busyness_freqOfAskingI, .~ Prosociality + .)
summary(prosocialityModel)

# plot(allEffects(model))
# plotLMER.fnc(model,linecolor="red",
#              lwd=4,
#              ylabel="Probability of Helping Accurately",
#              fun=plogis,
#              # pred="Past.Frequency.of.Asking",
#              # intr=list("Busyness.Numeric", sort(unique(data$Busyness.Numeric)), "beg",
#              #           list(c("green", "blue", "red"), rep(1,3))),
#              # intr=list("Busyness.Numeric", c(0.0, 0.05, 0.15, 0.33, 1.0), "beg",
#              #           list(c("green", "blue", "red", "yellow", "purple"), rep(1,5))),
#              pred="Busyness.Numeric",
#              intr=list("Past.Frequency.of.Asking", c(0.2, 0.4, 0.6, 0.8, 1.0), "mid",
#                        list(c("green", "blue", "red", "yellow", "purple"), rep(1,5))),
#              )

# print the mod results
summary(finalModel)
# get the model fixed and random effects
coef(summary(finalModel))
coef(finalModel)$UUID
fixParam <- fixef(finalModel)
ranParam <- ranef(finalModel)$UUID
summary(ranParam)
boxplot(ranParam)
summary(ranParam$`(Intercept)`)
quantile(ranParam$`(Intercept)`, c(0,.2,.4,.6,.8,1))
quantile(ranParam$`(Intercept)`, c(1/12,3/12,5/12,7/12,9/12,11/12))
h <- hist(ranParam$`(Intercept)`)
xfit <- seq(min(ranParam$`(Intercept)`), max(ranParam$`(Intercept)`), length = 40) 
yfit <- dnorm(xfit, mean = 0.0, sd = attr(summary(finalModel)$varcor$UUID, "stddev"))
yfit <- yfit * diff(h$mids[1:2]) * length(ranParam$`(Intercept)`) 
lines(xfit, yfit, col = "black", lwd = 2)
h <- hist(ranParam$`(Intercept)`, breaks=quantile(ranParam$`(Intercept)`, c(0/6,1/6,2/6,3/6,4/6,5/6,6/6)))
# curve(dnorm(x, mean=0.0, sd=1.65), 
#       col="darkblue", lwd=2, add=TRUE, yaxt="n")
print(fixParam)
print(ranParam)
params<-cbind(fixParam[1]+ranParam[1],fixParam[2], fixParam[3], fixParam[4])
print(params)

# Get the residuals
# summary(finalModel)
# predictions <- as.vector(predict(finalModel, type="response"))
# summary(contextualModel)
# predictions <- as.vector(predict(contextualModel, type="response"))
summary(individualModel)
predictions <- as.vector(predict(individualModel, type="response"))
responses <- as.integer(data$Human.Response) - 1 # minus one due to the one-indexed factors
residuals <- responses-predictions
sd(residuals)

h <- hist(residuals, breaks = 10, density = 10,
          col = "lightgray", xlab = "Accuracy", main = "Overall") 
xfit <- seq(min(residuals), max(residuals), length = 40) 
yfit <- dnorm(xfit, mean = mean(residuals), sd = sd(residuals)) 
yfit <- yfit * diff(h$mids[1:2]) * length(residuals) 
lines(xfit, yfit, col = "black", lwd = 2)

# Compute the correlation between prosociality and the random effect
ranParamDataframe <- setDT(ranParam, keep.rownames = TRUE)
colnames(ranParamDataframe)[1] <- "UUID"
mergedData <- merge(data, ranParamDataframe)
uniqueMergedData <- mergedData[!duplicated(mergedData$UUID),]
cor.test(uniqueMergedData$`(Intercept)`, uniqueMergedData$Prosociality, method="pearson", alternative="two.sided")
cor.test(uniqueMergedData$`(Intercept)`, uniqueMergedData$Navigational.Ability, method="pearson", alternative="two.sided")

# Get the random effect bucket prior distribution
prior <- c(
  sum(ranParam$`(Intercept)` <= -1.6*attr(summary(finalModel)$varcor$UUID, "stddev")),
  sum(ranParam$`(Intercept)` > -1.6*attr(summary(finalModel)$varcor$UUID, "stddev") & ranParam$`(Intercept)` <= -0.8*attr(summary(finalModel)$varcor$UUID, "stddev")),
  sum(ranParam$`(Intercept)` > -0.8*attr(summary(finalModel)$varcor$UUID, "stddev") & ranParam$`(Intercept)` <= 0.0*attr(summary(finalModel)$varcor$UUID, "stddev")),
  sum(ranParam$`(Intercept)` > 0.0*attr(summary(finalModel)$varcor$UUID, "stddev") & ranParam$`(Intercept)` <= 0.8*attr(summary(finalModel)$varcor$UUID, "stddev")),
  sum(ranParam$`(Intercept)` > 0.8*attr(summary(finalModel)$varcor$UUID, "stddev") & ranParam$`(Intercept)` <= 1.6*attr(summary(finalModel)$varcor$UUID, "stddev")),
  sum(ranParam$`(Intercept)` > 1.6*attr(summary(finalModel)$varcor$UUID, "stddev"))
)
prior <- prior# + 14 # exploration epsilon
prior/sum(prior)
ranParam_baseline <- ranef(baseline)$UUID
prior <- c(
  sum(ranParam_baseline$`(Intercept)` <= -1.6*attr(summary(baseline)$varcor$UUID, "stddev")),
  sum(ranParam_baseline$`(Intercept)` > -1.6*attr(summary(baseline)$varcor$UUID, "stddev") & ranParam_baseline$`(Intercept)` <= -0.8*attr(summary(baseline)$varcor$UUID, "stddev")),
  sum(ranParam_baseline$`(Intercept)` > -0.8*attr(summary(baseline)$varcor$UUID, "stddev") & ranParam_baseline$`(Intercept)` <= 0.0*attr(summary(baseline)$varcor$UUID, "stddev")),
  sum(ranParam_baseline$`(Intercept)` > 0.0*attr(summary(baseline)$varcor$UUID, "stddev") & ranParam_baseline$`(Intercept)` <= 0.8*attr(summary(baseline)$varcor$UUID, "stddev")),
  sum(ranParam_baseline$`(Intercept)` > 0.8*attr(summary(baseline)$varcor$UUID, "stddev") & ranParam_baseline$`(Intercept)` <= 1.6*attr(summary(baseline)$varcor$UUID, "stddev")),
  sum(ranParam_baseline$`(Intercept)` > 1.6*attr(summary(baseline)$varcor$UUID, "stddev"))
)
prior <- prior# + 14 # exploration epsilon
prior/sum(prior)

# Plot busyness v likelihood of helping, partitioned by user ID
indices <- which(!duplicated(data$UUID))
frequencies <- data$Past.Frequency.of.Asking[indices]
frequencies_matrix <- matrix(data=frequencies, ncol=length(frequencies), nrow=1)
uuid_to_frequencies <- data.frame(frequencies_matrix)
colnames(uuid_to_frequencies) <- as.character(data$UUID[indices])

busyness_range <- seq(from=0.0, to=1.0, by=.01)

# Get the average curves per frequency
unique_frequencies <- unique(data$Past.Frequency.of.Asking)
frequency_average_output <- matrix(ncol=length(unique_frequencies)+1, nrow=length(busyness_range))
frequency_average_output[, length(unique_frequencies)+1] = busyness_range

j <- 0
for (frequency in unique_frequencies) {
  print(frequency)
  j <- j + 1
  num_recent_times_did_not_help <- mean(data$Num.Recent.Times.Did.Not.Help[which(data$Past.Frequency.of.Asking[indices] == frequency)])
  
  logits <- fixParam[1] + fixParam[2]*num_recent_times_did_not_help + fixParam[3]*busyness_range + fixParam[4]*busyness_range*frequency
  # print(logits)
  
  probs <- exp(logits)/(1 + exp(logits))
  print(probs)
  frequency_average_output[, j] = probs
}
print(frequency_average_output)
frequency_average_data <- data.frame(frequency_average_output)
colnames(frequency_average_data) <- append(as.character(unique_frequencies), "Busyness.Numeric")
print(frequency_average_data)
frequency_data_to_graph <- gather(frequency_average_data, key=frequency, value=Probability, 1:length(unique_frequencies))
print(frequency_data_to_graph)

# Get the lines for every user
all_users_output <- matrix(ncol=length(indices)+1, nrow=length(busyness_range))
all_users_output[, length(indices)+1] = busyness_range

j <- 0
for (i in indices) {
  j <- j + 1
  uuid <- data$UUID[i]
  print(uuid)
  frequency <- data$Past.Frequency.of.Asking[i]
  # prosociality <- data$Prosociality[i]
  num_recent_times_did_not_help <- mean(data$Num.Recent.Times.Did.Not.Help[which(data$UUID == uuid)])
  
  print(params[uuid, 1])
  print(fixParam[2])
  print(fixParam[3])
  print(fixParam[4])
  
  logits <- params[uuid, 1] + fixParam[2]*num_recent_times_did_not_help + fixParam[3]*busyness_range + fixParam[4]*busyness_range*frequency
  # print(logits)
  
  probs <- exp(logits)/(1 + exp(logits))
  all_users_output[, j] = probs
}
print(all_users_output)
per_user_data <- data.frame(all_users_output)
colnames(per_user_data) <- append(as.character(data$UUID[indices]), "Busyness.Numeric")
print(per_user_data)
data_to_graph <- gather(per_user_data, key=UUID, value=Probability, 1:length(indices))
data_to_graph$frequency <- as.numeric(uuid_to_frequencies[, data_to_graph$UUID])
print(data_to_graph)

ggplot() +
  geom_line(data=data_to_graph, aes(x=Busyness.Numeric, y=Probability, group=UUID, color=as.factor(frequency)), lwd=1, lty=2, alpha=0.2) +
  geom_line(data=frequency_data_to_graph, aes(x=Busyness.Numeric, y=Probability, color=as.factor(frequency)), lwd=1) +
  scale_color_manual(breaks = c("0.2", "0.4", "0.6", "0.8", "1"),
                   values=c("red", "blue", "green", "orange", "cyan")) +
  labs(x="Busyness.Numeric", y="Probability of Helping Accurately", title="Probability of Helping Accurately by Busyness")


ggplot() +
  geom_line(data=data_to_graph, aes(x=Busyness.Numeric, y=Probability, group=UUID), lwd=1, lty=2, alpha=0.25, color="black") +
  labs(x="Busyness.Numeric", y="Probability of Helping Accurately", title="Probability of Helping Accurately by Busyness")

frequency_range <- seq(from=0.0, to=1.0, by=.01)

# Get the lines for every user where the x axis is frequency for a fixed busyness
all_users_output_freq <- matrix(ncol=length(indices)+1, nrow=length(frequency_range))
all_users_output_freq[, length(indices)+1] = frequency_range

j <- 0
for (i in indices) {
  j <- j + 1
  uuid <- data$UUID[i]
  # print(uuid)
  busyness <- mean(data$Busyness.Numeric[which(data$UUID == uuid)])
  num_recent_times_did_not_help <- mean(data$Num.Recent.Times.Did.Not.Help[which(data$UUID == uuid)])
  
  
  logits <- params[uuid, 1] + fixParam[3]*busyness + fixParam[2]*num_recent_times_did_not_help + fixParam[4]*busyness*frequency_range
  # print(logits)
  
  probs <- exp(logits)/(1 + exp(logits))
  all_users_output_freq[, j] = probs
}
print(all_users_output_freq)
per_user_data_freq <- data.frame(all_users_output_freq)
colnames(per_user_data_freq) <- append(as.character(data$UUID[indices]), "Past.Frequency.of.Asking")
print(per_user_data_freq)
data_to_graph_freq <- gather(per_user_data_freq, key=UUID, value=Probability, 1:length(indices))
print(data_to_graph_freq)

ggplot() +
  geom_line(data=data_to_graph_freq, aes(x=Past.Frequency.of.Asking, y=Probability, group=UUID), lwd=1, lty=2, alpha=0.25, color="black") +
  labs(x="Past.Frequency.of.Asking", y="Probability of Helping Accurately", title="Probability of Helping Accurately by Frequency of Asking")

# Get the lines for each busyness where the x axis is frequency
busyness_to_test <- c(0.0, 1.0/7, 1.0/3)
per_busyness_users_output_freq <- matrix(ncol=length(busyness_to_test)+1, nrow=length(frequency_range))
per_busyness_users_output_freq[, length(busyness_to_test)+1] = frequency_range

j <- 0
for (busyness in busyness_to_test) {
  j <- j + 1
  # uuid <- data$UUID[i]
  # print(uuid)
  num_recent_times_did_not_help <- mean(data$Num.Recent.Times.Did.Not.Help[which(data$Busyness.Numeric == busyness)])

  # logits <- fixParam[1] + fixParam[3]*busyness + fixParam[2]*frequency_range + fixParam[4]*prosociality + fixParam[5]*busyness*frequency_range
  logits <- fixParam[1] + fixParam[3]*busyness + fixParam[2]*num_recent_times_did_not_help + fixParam[4]*busyness*frequency_range
  # print(logits)
  
  probs <- exp(logits)/(1 + exp(logits))
  per_busyness_users_output_freq[, j] = probs
}
print(per_busyness_users_output_freq)
per_user_data_freq <- data.frame(per_busyness_users_output_freq)
colnames(per_user_data_freq) <- append(as.character(busyness_to_test), "Past.Frequency.of.Asking")
print(per_user_data_freq)
data_to_graph_freq <- gather(per_user_data_freq, key=Busyness.Numeric, value=Probability, 1:length(busyness_to_test))
# data_to_graph_freq$frequency <- as.numeric(uuid_to_frequencies[, data_to_graph_freq$UUID])
print(data_to_graph_freq)

ggplot() +
  geom_line(data=data_to_graph_freq, aes(x=Past.Frequency.of.Asking, y=Probability, color=as.factor(Busyness.Numeric)), lwd=1, lty=2) +
  labs(x="Past.Frequency.of.Asking", y="Probability of Helping Accurately", title="Average Probability of Helping Accurately by Frequency")

num_recent_times_range <- seq(from=0, to=19, by=1)
# Get the lines for each busyness where the x axis is num recent times
busyness_to_test <- c(0.0, 1.0/7, 1.0/3)
per_busyness_users_output_num <- matrix(ncol=length(busyness_to_test)+1, nrow=length(num_recent_times_range))
per_busyness_users_output_num[, length(busyness_to_test)+1] = num_recent_times_range

j <- 0
for (busyness in busyness_to_test) {
  j <- j + 1
  # uuid <- data$UUID[i]
  # print(uuid)
  num_recent_times_did_not_help <- mean(data$Num.Recent.Times.Did.Not.Help[which(data$Busyness.Numeric == busyness)])
  frequency <- 0.6
  
  # logits <- fixParam[1] + fixParam[3]*busyness + fixParam[2]*frequency_range + fixParam[4]*prosociality + fixParam[5]*busyness*frequency_range
  logits <- fixParam[1] + fixParam[3]*busyness + fixParam[2]*num_recent_times_range + fixParam[4]*busyness*frequency
  # print(logits)
  
  probs <- exp(logits)/(1 + exp(logits))
  per_busyness_users_output_num[, j] = probs
}
print(per_busyness_users_output_num)
per_user_data_num <- data.frame(per_busyness_users_output_num)
colnames(per_user_data_num) <- append(as.character(busyness_to_test), "Num.Recent.Times.Did.Not.Help")
print(per_user_data_num)
data_to_graph_num <- gather(per_user_data_num, key=Busyness.Numeric, value=Probability, 1:length(busyness_to_test))
# data_to_graph_freq$frequency <- as.numeric(uuid_to_frequencies[, data_to_graph_freq$UUID])
print(data_to_graph_num)

ggplot() +
  geom_line(data=data_to_graph_num, aes(x= Num.Recent.Times.Did.Not.Help, y=Probability, color=as.factor(Busyness.Numeric)), lwd=1, lty=2) +
  labs(x="Num.Recent.Times.Did.Not.Help", y="Probability of Helping Accurately", title="Average Probability of Helping Accurately by Num.Recent.Times.Did.Not.Help")

# Get the lines for each frequency where the x axis is num recent times
frequency_to_test <- c(0.2,0.4,0.6,0.8,1.0)
per_busyness_users_output_num <- matrix(ncol=length(frequency_to_test)+1, nrow=length(num_recent_times_range))
per_busyness_users_output_num[, length(frequency_to_test)+1] = num_recent_times_range

j <- 0
for (frequency in frequency_to_test) {
  j <- j + 1
  # uuid <- data$UUID[i]
  # print(uuid)
  num_recent_times_did_not_help <- mean(data$Num.Recent.Times.Did.Not.Help[which(data$Busyness.Numeric == busyness)])
  busyness <- 1.0/7
  
  # logits <- fixParam[1] + fixParam[3]*busyness + fixParam[2]*frequency_range + fixParam[4]*prosociality + fixParam[5]*busyness*frequency_range
  logits <- fixParam[1] + fixParam[3]*busyness + fixParam[2]*num_recent_times_range + fixParam[4]*busyness*frequency
  # print(logits)
  
  probs <- exp(logits)/(1 + exp(logits))
  per_busyness_users_output_num[, j] = probs
}
print(per_busyness_users_output_num)
per_user_data_num <- data.frame(per_busyness_users_output_num)
colnames(per_user_data_num) <- append(as.character(frequency_to_test), "Num.Recent.Times.Did.Not.Help")
print(per_user_data_num)
data_to_graph_num <- gather(per_user_data_num, key=Past.Frequency.of.Asking, value=Probability, 1:length(frequency_to_test))
# data_to_graph_freq$frequency <- as.numeric(uuid_to_frequencies[, data_to_graph_freq$UUID])
print(data_to_graph_num)

ggplot() +
  geom_line(data=data_to_graph_num, aes(x= Num.Recent.Times.Did.Not.Help, y=Probability, color=as.factor(Past.Frequency.of.Asking)), lwd=1, lty=2) +
  labs(x="Num.Recent.Times.Did.Not.Help", y="Probability of Helping Accurately", title="Average Probability of Helping Accurately by Num.Recent.Times.Did.Not.Help")

# # Get the past freq of helping for each busyness where the x axis is frequency
# per_busyness_users_output_freq_of_helping <- matrix(ncol=length(busyness_to_test)+1, nrow=length(frequency_range))
# per_busyness_users_output_freq_of_helping[, length(busyness_to_test)+1] = frequency_range
# 
# j <- 0
# for (busyness in busyness_to_test) {
#   j <- j + 1
#   # uuid <- data$UUID[i]
#   # print(uuid)
#   pastFreqOfAsking <- 0.5
#   prosociality <- mean(data$Prosociality[which(data$Busyness.Numeric[indices] == busyness)])
#   
#   # logits <- fixParam[1] + fixParam[2]*busyness + fixParam[3]*frequency_range + fixParam[4]*prosociality + fixParam[5]*busyness*frequency_range
#   logits <- fixParam[1] + fixParam[2]*busyness + fixParam[3]*pastFreqOfAsking + fixParam[4]*frequency_range + fixParam[5]*prosociality
#   # print(logits)
#   
#   probs <- exp(logits)/(1 + exp(logits))
#   per_busyness_users_output_freq_of_helping[, j] = probs
# }
# print(per_busyness_users_output_freq_of_helping)
# per_user_data_freq_helping <- data.frame(per_busyness_users_output_freq_of_helping)
# colnames(per_user_data_freq_helping) <- append(as.character(busyness_to_test), "Past.Frequency.of.Helping")
# print(per_user_data_freq_helping)
# data_to_graph_freq_helping <- gather(per_user_data_freq_helping, key=Busyness.Numeric, value=Probability, 1:length(busyness_to_test))
# # data_to_graph_freq$frequency <- as.numeric(uuid_to_frequencies[, data_to_graph_freq$UUID])
# print(data_to_graph_freq_helping)
# 
# ggplot() +
#   geom_line(data=data_to_graph_freq_helping, aes(x=Past.Frequency.of.Helping, y=Probability, color=as.factor(Busyness.Numeric)), lwd=1, lty=2) +
#   labs(x="Past.Frequency.of.Helping", y="Probability of Helping Accurately", title="Probability of Helping Accurately by Frequency")
# 
# # Get the past freq of helping for each busyness where the x axis is frequency
# frequency_of_asking_to_test <- c(0.2, 0.4, 0.6, 0.8, 1.0)
# per_busyness_users_output_freq_of_helping <- matrix(ncol=length(frequency_of_asking_to_test)+1, nrow=length(frequency_range))
# per_busyness_users_output_freq_of_helping[, length(frequency_of_asking_to_test)+1] = frequency_range
# 
# j <- 0
# for (pastFreqOfAsking in frequency_of_asking_to_test) {
#   j <- j + 1
#   # uuid <- data$UUID[i]
#   # print(uuid)
#   busyness <- 1.0/7
#   prosociality <- mean(data$Prosociality[which(data$Past.Frequency.of.Asking[indices] == pastFreqOfAsking)])
#   
#   # logits <- fixParam[1] + fixParam[2]*busyness + fixParam[3]*frequency_range + fixParam[4]*prosociality + fixParam[5]*busyness*frequency_range
#   logits <- fixParam[1] + fixParam[2]*busyness + fixParam[3]*pastFreqOfAsking + fixParam[4]*prosociality + fixParam[5]*pastFreqOfAsking*frequency_range
#   # print(logits)
#   
#   probs <- exp(logits)/(1 + exp(logits))
#   per_busyness_users_output_freq_of_helping[, j] = probs
# }
# print(per_busyness_users_output_freq_of_helping)
# per_user_data_freq_helping <- data.frame(per_busyness_users_output_freq_of_helping)
# colnames(per_user_data_freq_helping) <- append(as.character(frequency_of_asking_to_test), "Past.Frequency.of.Helping")
# print(per_user_data_freq_helping)
# data_to_graph_freq_helping <- gather(per_user_data_freq_helping, key=Past.Frequency.of.Asking, value=Probability, 1:length(frequency_of_asking_to_test))
# # data_to_graph_freq$frequency <- as.numeric(uuid_to_frequencies[, data_to_graph_freq$UUID])
# print(data_to_graph_freq_helping)
# 
# ggplot() +
#   geom_line(data=data_to_graph_freq_helping, aes(x=Past.Frequency.of.Helping, y=Probability, color=as.factor(Past.Frequency.of.Asking)), lwd=1, lty=2) +
#   labs(x="Past.Frequency.of.Helping", y="Probability of Helping Accurately", title="Probability of Helping Accurately by Frequency")

# Get the model prediction accuracy
p <- as.numeric(predict(finalModel, type="response")>0.5)
sum(predict(finalModel, type="response") > 0.5)
table(p,data$Human.Response)

# Get standard errors and confidence intervals
se <- sqrt(diag(vcov(finalModel)))
# table of estimates with 95% CI
(tab <- cbind(Est = fixef(finalModel), LL = fixef(finalModel) - 1.96 * se, UL = fixef(finalModel) + 1.96 * se))
# odds ratios
exp(tab)
# probability
exp(tab)/(1+exp(tab))

# busynessFrequencyPostHoc <- emmeans(model, ~Busyness.Numeric*Past.Frequency.of.Asking)
# # pairs(busynessPostHoc, simple="Busyness.Numeric")
# # pairs(busynessPostHoc, simple="Past.Frequency.of.Asking")
# # contrast(busynessFrequencyPostHoc, "poly")
# # contrast(busynessFrequencyPostHoc, "trt.vs.ctrl", by="Busyness.Numeric")
# 
# busynessPostHoc <- emmeans(model, "Busyness.Numeric")
# pairs(busynessPostHoc)  
# 
# frequencyOfAskingPostHoc <- emmeans(model, "Past.Frequency.of.Asking")
# pairs(frequencyOfAskingPostHoc)
# contrast(frequencyOfAskingPostHoc, "consec")
# # contrast(frequencyOfAskingPostHoc, "poly")

# Fit the Baseline Models (and the proposed as a sanity check)
model <- glmer(Human.Response ~ Busyness.Numeric + Busyness.Numeric:Past.Frequency.of.Asking + (1 | UUID), data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
summary(model)

model_only_fixed <- glm(Human.Response ~ Busyness.Numeric + Busyness.Numeric:Past.Frequency.of.Asking, data = data, family = binomial(link="logit"))
coef(model_only_fixed)

model_only_random <- glmer(Human.Response ~ (1 | UUID), data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
summary(model_only_random)
attr(summary(model_only_random)$varcor$UUID, "stddev")

model_only_intercept <- glm(Human.Response ~ 1, data = data, family = binomial(link="logit"))
summary(model_only_intercept)

# Analysis as factors

dataAsFactors <- read.csv("/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/humanHelpUserStudyPerResponseData.csv")

dataAsFactors <- within(dataAsFactors, {
  UUID <- factor(UUID)
  TaskI <- factor(TaskI)
  Busyness <- factor(Busyness, levels = c("free time", "medium", "high"))
  Past.Frequency.of.Asking <- factor(Past.Frequency.of.Asking)
  # Past.Frequency.of.Asking <- as.numeric(Past.Frequency.of.Asking)
  # Past.Frequency.of.Helping.Accurately <- factor(Past.Frequency.of.Helping.Accurately)
  Past.Frequency.of.Helping.Accurately <- as.numeric(Past.Frequency.of.Helping.Accurately)
  Human.Response <- factor(Human.Response)
  Prosociality <- as.numeric(Prosociality)
  Slowness <- as.numeric(Slowness)
  # Busyness.Numeric <- factor(Busyness.Numeric)
  Busyness.Numeric <- as.numeric(Busyness.Numeric)
  Num.Recent.Times.Did.Not.Help <- as.integer(Num.Recent.Times.Did.Not.Help)
  Age <- as.integer(Age)
})

print(dataAsFactors)

modelAsFactors <- glmer(Human.Response ~ Busyness + Past.Frequency.of.Asking + Prosociality + (1 | UUID), data = dataAsFactors, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
summary(modelAsFactors)
contrast(emmeans(modelAsFactors, ~ Past.Frequency.of.Asking))

# Model the Errors
data$data_ID <- seq.int(nrow(data))
print(data)
model_width_errors <- glmer(Human.Response ~ Busyness.Numeric + Busyness.Numeric:Past.Frequency.of.Asking + (1 | UUID) + (1 | data_ID), data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))

#########################################################################################################################
evaluation_data <- read.csv("/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs_evaluation/humanHelpUserStudyDataWithExclusionAskingData.csv")

evaluation_data <- within(evaluation_data, {
  User.ID <- factor(User.ID)
  Policy <- factor(Policy)
  Busyness <- as.numeric(Busyness)
  Frequency <- as.numeric(Frequency)
  Human.Response <- factor(Human.Response)
})

print(evaluation_data)
evaluation_model <- glmer(Human.Response ~ Busyness + Busyness:Frequency + (1 | User.ID), data = evaluation_data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
summary(evaluation_model)
