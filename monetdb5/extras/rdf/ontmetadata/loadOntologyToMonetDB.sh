#dbpedia3.9
NUMMETADATA=`cat ontMetadata.dbpedia39.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.dbpedia39.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.dbpedia39.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.dbpedia39.csv:g" loadtmp.sql

mclient < loadtmp.sql


NUMMETADATA=`cat ontMetadata.gr.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.gr.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.gr.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.gr.csv:g" loadtmp.sql


mclient < loadtmp.sql

#lubm
NUMMETADATA=`cat ontMetadata.lubm.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.lubm.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.lubm.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.lubm.csv:g" loadtmp.sql


mclient < loadtmp.sql


#eurostat
NUMMETADATA=`cat ontMetadata.eurostat.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.eurostat.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.eurostat.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.eurostat.csv:g" loadtmp.sql


mclient < loadtmp.sql


#swrc
NUMMETADATA=`cat ontMetadata.swrc.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.swrc.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.swrc.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.swrc.csv:g" loadtmp.sql


mclient < loadtmp.sql

#foaf
NUMMETADATA=`cat ontMetadata.foaf.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.foaf.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.foaf.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.foaf.csv:g" loadtmp.sql


mclient < loadtmp.sql

#bsbm
NUMMETADATA=`cat ontMetadata.bsbm.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.bsbm.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.bsbm.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.bsbm.csv:g" loadtmp.sql


mclient < loadtmp.sql

#rdfvocabulary
NUMMETADATA=`cat ontMetadata.rdfvocabulary.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.rdfvocabulary.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.rdfvocabulary.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.rdfvocabulary.csv:g" loadtmp.sql


mclient < loadtmp.sql

#Open Graph Protocol (ogp)
NUMMETADATA=`cat ontMetadata.ogp.csv | wc -l`
NUMATTRIBUTES=`cat ontAttribute.ogp.csv | wc -l`

cp loadOntologySAMPLE.sql loadtmp.sql
sed -i "s:NUMMETADATA:$NUMMETADATA:g" loadtmp.sql
sed -i "s:NUMATTRIBUTES:$NUMATTRIBUTES:g" loadtmp.sql
sed -i "s:MetaFile:${PWD}/ontMetadata.ogp.csv:g" loadtmp.sql
sed -i "s:AttFile:${PWD}/ontAttribute.ogp.csv:g" loadtmp.sql


mclient < loadtmp.sql

#List of possible ontologies
NUMONT=`cat ontList.csv | wc -l`

cp loadOntologyListSAMPLE.sql loadtmp.sql
sed -i "s:NUMONT:$NUMONT:g" loadtmp.sql
sed -i "s:OntListFile:${PWD}/ontList.csv:g" loadtmp.sql


mclient < loadtmp.sql
