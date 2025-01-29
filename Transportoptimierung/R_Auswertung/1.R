# init ----

library(readxl)
library(ggplot2)
library(dplyr)
library(tidyverse)

raw <- read_excel("C:/Users/lgehl/Documents/GitHub/SPP24/Transportoptimierung/tasks_metrics.xlsx")



Leerdistanz <- raw %>% mutate(rel = global_empty_distance/global_total_distance)

Leerdistanz$task_id <- factor(Leerdistanz$task_id) %>% 
  fct_reorder(Leerdistanz$rel)

Wartezeit <- raw %>% rename(wt = `global_mean_waiting_time (mins)`)

Wartezeit$task_id <- factor(Wartezeit$task_id) %>% 
  fct_reorder(Wartezeit$wt)

# wartezeit plots ----
ggplot(Wartezeit, aes(task_id, wt, fill=a)) +
  geom_col() +
  scale_fill_continuous(name = "Präferiere das\nnächste FFZ") +
  theme_minimal() +
  ylab("mittlere Wartezeit der Chargen")

ggplot(Wartezeit, aes(task_id, wt, fill=b)) +
  geom_col() +
  scale_fill_continuous(name = "Präferiere das FFZ mit\nden wenigsten Aufträgen") +
  theme_minimal() +
  ylab("mittlere Wartezeit der Chargen")

ggplot(Wartezeit, aes(task_id, wt, fill=d)) +
  geom_col() +
  scale_fill_continuous(name = "Präferiere das\nschnellste FFZ") +
  theme_minimal() +
  ylab("mittlere Wartezeit der Chargen")


# leerdistanz plot2 ----
ggplot(Leerdistanz, aes(task_id, rel, fill=a)) +
  geom_col() +
  scale_fill_continuous(name = "Präferiere das\nnächste FFZ") +
  theme_minimal() +
  ylab("gefahrene relative Leerdistanz")
  


ggplot(Leerdistanz, aes(task_id, rel, fill=b)) +
  geom_col() +
  scale_fill_continuous(name = "Präferiere das FFZ mit\nden wenigsten Aufträgen") +
  theme_minimal() +
  ylab("gefahrene relative Leerdistanz")


  
ggplot(Leerdistanz, aes(task_id, rel, fill=d)) +
  geom_col() +
  scale_fill_continuous(name = "Präferiere das\nschnellste FFZ") +
  theme_minimal() +
  ylab("gefahrene relative Leerdistanz")

