require(lme4)
require(data.table)

write_params <- function(model, filepath) {
  # Get the parameters
  if (grepl("glmer", class(model)[1])) {
    fixParam <- fixef(model)
    ranParam <- ranef(model)$UUID
    n <- nrow(ranParam[1])
    replicatedFixParam <- data.frame(matrix(rep(t(as.matrix(fixParam)),each=n),nrow=n))
    params<-cbind(ranParam[1], replicatedFixParam)
    colnames(params) <- append("(Intercept).Random.Effects", names(fixParam))
    # print(fixParam)
    # print(ranParam)
    # print(params)
    write.csv(setDT(params, keep.rownames="UUID")[], filepath, row.names=FALSE)
  } else {
    coefs = coef(model)
    params <- cbind(matrix(c(0,0), nrow = 1, ncol = 2),t(coefs))
    colnames(params) <- append(c("UUID", "(Intercept).Random.Effects"), names(coefs))
    write.csv(params, filepath, row.names=FALSE)
  }
}

fit_model <- function(i, in_filepath, out_filepath, out_only_fixed, out_only_random, out_only_intercept) {
  # Read the Data
  data <- read.csv(sprintf(in_filepath, i))
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
  })
  
  # Fit the Model
  model <- glmer(Human.Response ~ Busyness.Numeric + Busyness.Numeric:Past.Frequency.of.Asking + (1 | UUID), data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
  write_params(model, sprintf(out_filepath, i))
  
  # # Get the model prediction accuracy
  # p <- as.numeric(predict(model, type="response")>0.5)
  # print(sum(predict(model, type="response") > 0.5))
  # print(prop.table(table(p,data$Human.Response), 2))
  
  model_only_fixed <- glm(Human.Response ~ Busyness.Numeric + Busyness.Numeric:Past.Frequency.of.Asking, data = data, family = binomial(link="logit"))
  write_params(model_only_fixed, sprintf(out_only_fixed, i))
  
  model_only_random <- glmer(Human.Response ~ (1 | UUID), data = data, family = binomial(link="logit"), control = glmerControl(optimizer = "bobyqa", optCtrl=list(maxfun=100000)))
  write_params(model_only_random, sprintf(out_only_random, i))
  
  model_only_intercept <- glm(Human.Response ~ 1, data = data, family = binomial(link="logit"))
  write_params(model_only_intercept, sprintf(out_only_intercept, i))
}

base_dir <- "/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/processedData/80-20/"
num_partitions <- 5

# base_dir <- "/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/processedData/hold-one-out/"
# num_partitions <- 140

in_filepath <- paste(base_dir, "%d_train.csv", sep="")
out_filepath <- paste(base_dir, "%d_model.csv", sep="")
out_only_fixed <- paste(base_dir, "%d_model_only_fixed.csv", sep="")
out_only_random <- paste(base_dir, "%d_model_only_random.csv", sep="")
out_only_intercept <- paste(base_dir, "%d_model_only_intercept.csv", sep="")

for (i in 0:(num_partitions-1)) {
  fit_model(i, in_filepath, out_filepath, out_only_fixed, out_only_random, out_only_intercept)
}
