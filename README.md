Aeroport
========

***This preview is pre-beta, pre-alpha, pre-anything, so its completely unsuseful in real projects. 
More work is on the way.*** 

Organize hub for data arrival / departures

Idea is to build server for running scraping jobs from multiple sources and input formats (web sites,
data feeds, etc...), adapt data and deliver it further to destinations (e. g. processing queues).

So it's like an airport where each airline "declares" its own arrivals, destinations and transport,
while using common hub insfrastructure.

Quick commands
--------------

```
aeroport airlines  # which airlines are installed

aeroport process  
aeroport process -d [DESTINATION_NAME] AIRLINE_NAME ORIGIN_NAME
```
