#GEORGE NAKHLEH
#ECT 584 Final Project

#Performing clustering and markov chains on clickstream

#Uses a pre-prepped dataset
#Records are supposed to be strings appearing as lists of format: "session_id, url1, url2, ..."

setwd("C://Users//gnakhleh//Documents//ECT584")

install.packages("clickstream")
library("clickstream")
library("dplyr", lib.loc="C:/Program Files/R/R-3.3.1/library")

clickstreams <- read.csv("data_for_clickpathR.csv")
clickstreams$sessionid_and_clickpath <- as.character(clickstreams$sessionid_and_clickpath)


#remove outliers and bouncers
install.packages("outliers")
library("outliers")
class(clickstreams$session_total_pages)

#what # of pages is beyond the 95% when the values are normalized?
min(clickstreams$session_total_pages[scores(clickstreams$session_total_pages, type="z", prob=0.95)]) #so we'll cap at 9

#well, maybe that's too extreme, we'd be left with only a bit more than 30% of all our data at that point

clickstreams <- filter(clickstreams, session_total_pages < 15 & session_total_pages > 1)  #now down to 1535 rows

clickstreams_list <- clickstreams$sessionid_and_clickpath

#this is the format we want, lists of strings, where the strings are the session (string that looks like a list)
clickstreams_list[1:2]

clickstreams_list[1][1]  #string that looks like a list. this is how we want it

#this package has a special datatype: Clickstreams
csf <- tempfile()
writeLines(clickstreams_list, csf)
cls <- readClickstreams(csf, header = TRUE)

mc <- fitMarkovChain(cls, order=1, verbose = FALSE)  #if we don't remove bounces, can't make a 1st-order model
show(mc)  #unreadable

print(summary(mc))

#create every state frequency for each session
#will be useful for clustering?
frequency_df <- frequencies(cls)

#we can now generate something really useful
#give the beginning of a path, and we can predict the sequence
startPattern <- new("Pattern", sequence = c(" dataiku.com/products/trynow/"))
predict(mc, startPattern)

#lets try k-means clustering
clusters5 <- clusterClickstreams(cls, order=0, centers=5)
print(clusters5)
clusters5$centers

clusters5$withinss
clusters5$betweenss #doing a good job, but the within distance of cluster5 isn't much better than between distance
clusters5$tot.withinss

clusters7 <- clusterClickstreams(cls, order=0, centers=7)
clusters7$betweenss
clusters7$withinss

clusters10 <- clusterClickstreams(cls, order=0, centers=10)
clusters10$betweenss
clusters10$withinss

#doesn't have a size function...

summary(clusters10)

plot(clusters)

clusters10[1]


#Not crazy about the output of this package
#Something easier to interpret would be nice

#Lets experiment w/ the markovchain package
install.packages("markovchain")
library("markovchain", lib.loc="C:/Program Files/R/R-3.3.1/library")

dat<-data.frame(replicate(20,sample(c("A", "B", "C","D"), size = 100, replace=TRUE)))
dat

trans.matrix <- function(X, prob=T){
  tt <- table( c(X[, -ncol(X)]), c(X[,-1]) )
  if(prob) tt <- tt / rowSums(tt)
  tt
}

trans.matrix(as.matrix(dat))

#a pre-munged set: rows are sessions, columns are each pg. 
#only sessions with between 2 and 14 clicks (no bounces, no outliers (outliers has loose def. here) )
#when someone ends their session, the rest of the column values are "(EXIT)"
clickstream_4transitions <- read.csv("data_for_transition_mat_munged.csv")
head(clickstream_4transitions)

clickstream_transmat <- trans.matrix(as.matrix(clickstream_4transitions))
head(clickstream_transmat)

#sanity check of these holds up

#lets use this transition matrix for the markovchain package
pages <- colnames(clickstream_transmat)

dtmcA <- as(clickstream_transmat, "markovchain")

energyStates <- c("pg1", "pg2")
byRow <- TRUE
gen <- matrix(data = c(4, 2, 
                       8, 12), nrow = 2,
              byrow = byRow, dimnames = list(energyStates, energyStates))
generatorToTransitionMatrix(gen)


ref_to_loc <- read.csv("data4transmat_locandref.csv")
head(ref_to_loc)
columnnamez <- colnames(ref_to_loc)
ref_to_loc <- as.matrix(ref_to_loc)
rownames(ref_to_loc) <- columnnamez

transition <- ref_to_loc / rowSums(ref_to_loc)
head(transition)
transition = round(transition, 3)

transmat_markov <- as(transition, "markovchain")
summary(transmat_markov)


transition.matrix <- new("markovchain", transitionMatrix = transition)
markov_plot <- plot(transition.matrix, edge.arrow.size = 0.3)


transition.matrix

install.packages("diagram")
install.packages("pracma")
library("igraph", lib.loc="C:/Program Files/R/R-3.3.1/library")
library(diagram)
library(pracma)
library(igraph)

layout <- layout.reingold.tilford(markov_plot, circular=T)

install.packages("Gmisc")
library("Gmisc", lib.loc="C:/Program Files/R/R-3.3.1/library")
library("ggplot2", lib.loc="C:/Program Files/R/R-3.3.1/library")

htmlTable(transition, ctable=TRUE)
transitionPlot(transition)
library(RColorBrewer)
jBuPuFun <- colorRampPalette(brewer.pal(n = 6, "BuPu"))
paletteSize <- 256
jBuPuPalette <- jBuPuFun(paletteSize)
heatmap_absolute <- heatmap(ref_to_loc, Rowv = NA, Colv = NA, scale = "none", col = jBuPuPalette)
heatmap_probs <- heatmap(transition, Rowv = NA, Colv = NA, scale = "none", col = jBuPuPalette)
