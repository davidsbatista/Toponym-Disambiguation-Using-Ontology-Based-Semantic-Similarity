#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, codecs, fileinput, psycopg2, fileinput
from xml.dom import minidom
from collections import defaultdict

originals_dir = "corpus/articles-with-geo-scope-in-title/"
documents = {}

class Entity(object):
    
    f_id = None
    t_id = None
    title = None
        
    def __init__(self,f_id,t_id,title):         
        self.f_id = f_id
        self.t_id = t_id
        self.title = title
        
    def __eq__(self,anEntity):
                        
        if self.f_id == anEntity.f_id and self.t_id == anEntity.t_id and self.title == anEntity.title:
            return True
        
        else:
            return False
    
    def __str__(self):
        return str(self.title) + ' ' + str(self.t_id)

class Relation(object):
    descendents = None
    adjacents = None

    def __init__(self):
        self.descendents = set()
        self.adjacents = set()

class TermRank(object):
    term = None
    desc = None
    level = None
    rank = None
    
    def __init__(self,term,desc,level):
        self.term = term
        self.desc = desc
        self.level = level
        
    def __rank__(self):
        if (self.level > 0):
            self.rank = float(self.desc) / float(self.level)
        else:
            self.rank = 0
            
    def __str__(self):
        return "Term: " + str(self.term) + "\n" + "Rank: " + str(self.rank)

class Document(object):

    title = None
    subtitle = None
    text = None
    filename = None
    resolved = None
    relations_graph = None
    ranks = None
    distance = None
        
    def __init__(self,newFilename):
        self.filename = newFilename
        self.title = list()
        self.subtitle = list()
        self.text = list()
        self.resolved = set()
        relation = Relation()
        self.relations_graph = defaultdict(Relation)
        self.ranks = list()
        self.distance = -1
        
    def _str_(self):
        return str(filename) + str(title) + str(subtitle) + str(text)


def get_locais_resolved(document):
    
    for line in fileinput.input(document.filename):
        if line[0] == "(":
            line_parts = line.split("#")
            document.resolved.add(int(line_parts[1].split(")")[0]))


def get_descendents(f_id,cursor):
    SQL = "SELECT f_id2 FROM adm_feature_relationship WHERE frt_id='PRT' and f_id1 = \'%s\';" % f_id
    cursor.execute(SQL)
    return cursor.fetchall()


def get_adjacents(f_id,cursor):
    SQL = "SELECT f_id2 FROM adm_feature_relationship WHERE frt_id='ADJ' and f_id1 = \'%s\';" % f_id
    cursor.execute(SQL)
    return cursor.fetchall()


def get_term(f_id,cursor):
    SQL = "SELECT n_cap_name, t_id FROM adm_name, adm_feature WHERE adm_name.n_id = adm_feature.n_id and f_id = \'%s\';" % f_id
    cursor.execute(SQL)
    return cursor.fetchall()


def number_levels(relations_graph,id,level):
    if len(relations_graph[id].descendents) == 0:
        return 0 
    else:        
        for d in relations_graph[id].descendents:
           return 1 + number_levels(relations_graph,d,level)


def number_descendants(relations_graph,id,counted):
    counted = counted + len(relations_graph[id].descendents)
    for d in relations_graph[id].descendents:
        counted = number_descendants(relations_graph,d,counted)
    return counted


def rank_measure(document,id): 
    desc = number_descendants(document.relations_graph,id,0)
    level = number_levels(document.relations_graph, id, 0)
    term_rank = TermRank(id,desc,level)
    term_rank.__rank__()
    document.ranks.append(term_rank)


def get_locais(filename,document):

    xmldoc = minidom.parse(filename)
    title = xmldoc.getElementsByTagName('title')
    subtitle = xmldoc.getElementsByTagName('subtitle')
    text = xmldoc.getElementsByTagName('text')
    
    locais_title = None
    locais_subtitle = None
    locais = None
    
    try:
        locais_title = title[0].getElementsByTagName('LOCAL_GeoNetPT02')
        
    except:
        print "<LOCAL_GeoNetPT02> not found in title"

    try:
        locais_subtitle = subtitle[0].getElementsByTagName('LOCAL_GeoNetPT02')
    except:
        print "<LOCAL_GeoNetPT02> not found in subtitle"

        
    try:
        locais = text[0].getElementsByTagName('LOCAL_GeoNetPT02')
    except:
        print "<LOCAL_GeoNetPT02> not found in text"

    
    if locais_title > 0:
        for local in locais_title:
                    t_id = local.getAttribute("t_id")                                
                    f_id = local.getAttribute("f_id")
                    title = local.firstChild.nodeValue.encode("utf-8")
                    document.title.append(Entity(f_id, t_id, title))
                    
    if locais_subtitle > 0:
        for local in locais_subtitle:
                t_id = local.getAttribute("t_id")                                
                f_id = local.getAttribute("f_id")
                subtitle = local.firstChild.nodeValue.encode("utf-8")
                document.subtitle.append(Entity(f_id, t_id, subtitle))

    if locais > 0:
        for local in locais:
            t_id = local.getAttribute("t_id")
            f_id = local.getAttribute("f_id")
            placename = local.firstChild.nodeValue.encode("utf-8")
            document.text.append(Entity(f_id, t_id, placename))


def parse_document(filename,cursor):
    
    print filename
    
    # create the Document object
    document = Document(filename)
    
    # extract the  <LOCAL_GeoNet-PT02> tags from original's title/subtitle
    get_locais(originals_dir+filename.split("/")[1],document)
    
    # extract the identifiers from the file with the disambiguated information
    get_locais_resolved(document)
    
    # calculate ranks for each term
    calculate_ranks(document,cursor)
    
    # add do the documents dict
    documents[document.filename] = document
    
def calculate_ranks(document,cursor):
         
    for id in document.resolved:
        descendents = get_descendents(id,cursor)
        adjacents = get_adjacents(id,cursor)
        
        for d in descendents:
            if int(d[0]) in document.resolved:
                document.relations_graph[id].descendents.add(int(d[0]))
    
        for a in adjacents:
            if int(a[0]) in document.resolved:
                document.relations_graph[id].adjacents.add(int(a[0]))

    for d in document.resolved: 
        rank_measure(document,d)
 
def check_rank(document,cursor):
    
    """
    returns the distance from the geo-concept defined as geo-scope to the geo-concept in the title,
    possible values are:
    
        -1 no path in the graph connecting the two
        0 same concept
        >0 number of nodes in distance 
    """
    
    distance = None
    baseline = None
    
    if len(document.title) == 1:
        baseline = document.title[0].f_id
    
    elif len(document.title) == 0:
        baseline = document.subtitle[0].f_id
        
    if baseline != None:
        
        if int(baseline) == int(document.ranks[0].term):
            distance = 0
            
        else:        
            # see the distance in the graph between the LOCAL in title and the generated geo-scope
            SQL = "SELECT f_id1, f_id2, distance FROM ssm_graphpath WHERE (f_id1 = \'%s\' AND f_id2 = \'%s\') OR (f_id1 = \'%s\' AND f_id2 = \'%s\')" % (document.ranks[0].term, baseline, baseline, document.ranks[0].term)            
            cursor.execute(SQL)
            rows =  cursor.fetchall()
            
            # see if highest ranked term is part of the children, if so, at which distance
            
            if len(rows) != 0:
                for row in rows:
                    f_id1 = get_term(int(row[0]), cursor)
                    f_id2 = get_term(int(row[1]), cursor)
                    #print "\t ",f_id1[0], f_id2[0], row[2]
                    return int(row[2])
                
            else: distance = -1
                
    return distance
    
def main():
    
    connection_string = "dbname='' user='' host='' password=''"
    
    connection = psycopg2.connect(connection_string)    
    cursor = connection.cursor()

    if os.path.isdir(sys.argv[1]):
        dirList = os.listdir(sys.argv[1])
        print len(dirList) , "files to process"
        for f in dirList:
            if f.startswith("PUBLICO"):
                parse_document(sys.argv[1]+f,cursor)
            
    else:
        parse_document(sys.argv[1],cursor)
    
    
    print "\nCalculating Document Ranks "
    
    for k in documents:    
        best_rank_score = 0
        best_term = None
        
        for identifier in documents[k].ranks:
            if identifier.rank > best_rank_score:
                best_rank_score = identifier.rank
                best_term = identifier.term
    
        #sorts the ranks list by the value of rank, in reverse, higher to lower
        documents[k].ranks.sort(key=lambda identifier: identifier.rank, reverse=True)
    
    print"\nDocuments Ranks:"
    
    for k in documents:
        print "\n",k
        
        print "\t identifiers: ", documents[k].resolved
        for id in documents[k].relations_graph:
            row = get_term(id, cursor)
            print "\t\t", id, row[0][0], row[0][1] 
            print "\t\t\t descendents: ", documents[k].relations_graph[id].descendents
            print "\t\t\t adjacents: ", documents[k].relations_graph[id].adjacents
         
        print "\t title: ", 
        for t in documents[k].title:
               print str(t),
        
        print "\n\t subtitle: ",
        for s in documents[k].subtitle:
               print str(s),
               
        print "\n\t nº unique identifers: ", len(documents[k].resolved),
               
        if documents[k].ranks[0].rank > 0:
            row = get_term(documents[k].ranks[0].term, cursor)
            print "\n\t geo-scope(rank#1): ", row[0][0], row[0][1]
            print "\t distance :", check_rank(documents[k],cursor)
        else:
            print "\n\t geo-scope(rank#1): -"
            print "\t distance : - "            
        print "\n"

    print "Total number of documents: ", len(documents)
    
    connection.close()
    
if __name__ == "__main__":
    main()

