require(lme4)
require(data.table)
require(ez)
require(car)

analyze_experiment <- function(in_filepath) {
  
  # Read the Data
  data <- read.csv(in_filepath)
  data <- within(data, {
    User.ID <- factor(User.ID)
    First.GID <- factor(First.GID) # Order
    Which.robot.was.more.annoying. <- as.numeric(Which.robot.was.more.annoying.)
    Which.robot.would.you.be.more.willing.to.help.in.the.future. <- as.numeric(Which.robot.would.you.be.more.willing.to.help.in.the.future.)
    Which.robot.was.better.at.adapting.its.behavior.to.you.as.an.individual. <- as.numeric(Which.robot.was.better.at.adapting.its.behavior.to.you.as.an.individual.)
    Which.robot.inconvenienced.you.more. <- as.numeric(Which.robot.inconvenienced.you.more.)
  })
  
  print(data)
  
  # My hypothesis is that the mean of "Which.robot.inconvenienced.you.more." is non-zero. The t-test tests that.
  inconvenienceModel <- t.test(data$Which.robot.inconvenienced.you.more., mu = 0, alternative = "two.sided")
  print(inconvenienceModel)
  
  # However, I also want to control for ordering effects, since which condition users got first could also affect their perceived inconvenience. 
  # Although I tried the below ANOVA, it does not test what I want -- it tests whether there are significant ordering effects (there are),
  # but not whether the mean is significantly non-zero while controlling for ordering effects.
  inconvenienceModelANOVA <- lm(Which.robot.inconvenienced.you.more. ~ First.GID + 1, data = data)
  print(summary(inconvenienceModelANOVA))
  print(inconvenienceModelANOVA$coefficients)
  print(mean(data$Which.robot.inconvenienced.you.more.))
  print(sd(data$Which.robot.inconvenienced.you.more.))
  
  # If you would like to play around with more data, the below variables are all of the same type, and I want to 
  # test the same hypothesis with them. That hypothesis is: controlling for ordering effects, the mean of ______ will
  # will be significantly non-zero.
  
  # model <- t.test(data$Which.robot.was.more.annoying., mu = 0, alternative = "two.sided")
  # print(model)
  # 
  # model <- t.test(data$Which.robot.would.you.be.more.willing.to.help.in.the.future., mu = 0, alternative = "two.sided")
  # print(model)
  # 
  # model <- t.test(data$Which.robot.was.better.at.adapting.its.behavior.to.you.as.an.individual., mu = 0, alternative = "two.sided")
  # print(model)
}

in_filepath <- "/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs_evaluation_2021_hybrid_v_contextual/humanHelpUserStudyDataHybrid_vs_Contextual.csv"

analyze_experiment(in_filepath)