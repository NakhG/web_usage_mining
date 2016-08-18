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

#this is the format we want, lists of strings, where the strings are the session
clickstreams_list[1:2]

clickstreams_list[1][1]

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
startPattern <- new("Pattern", sequence = c(" dataiku.com/"))
predict(mc, startPattern)

#lets try k-means clustering
clusters <- clusterClickstreams(cls, order=0, centers=5)
print(clusters)

plot(clusters)
