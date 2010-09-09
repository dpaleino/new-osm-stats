#!/bin/bash

DUMPDIR=/home/vezzo/Desktop/OSM/italy/download.gfoss.it/osm/osm/

for i in `ls ${DUMPDIR}/*.bz2.*`; do
   echo ${i}
   echo bunzip ${i}
   echo ./fast_stats ${i:56:28}.out
   echo rm ${i:56:28}.out
   read;
done
