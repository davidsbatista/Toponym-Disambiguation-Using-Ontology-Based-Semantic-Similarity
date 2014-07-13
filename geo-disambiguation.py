#!/usr/bin/env python
# -*- coding: utf8 -*-

# standard stuff
import sys
import os
import time

# to make HTTP requests
import base64
import httplib
import urllib
import urllib2

# to make a deep copy of objects
import copy

from xml.dom import minidom
from collections import defaultdict


"""
class for representing an annotated entity found in a news text
"""

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
		if self.t_id and self.f_id:
			return self.title.encode("utf8") + ' ' + self.f_id.encode("utf8").split("#")[1] + ' ' + self.t_id.encode("utf8")
		else:
			return self.title.encode("utf8")

"""
class for representing a SSM score between two entities
"""

class Score(object):
	
	entity1 = None 
	entity2 = None
	score = None
	
	def __init__(self,newEntity1,newEntity2,newScore):
		self.entity1 = newEntity1
		self.entity2 = newEntity2
		self.score = newScore
		
	
	def __eq__(self,another):
				
		if self.entity1 == another.entity1 and self.entity2 == another.entity2:
			return True
		
		elif self.entity1 == another.entity2 and self.entity2 == another.entity1:
			return True 

		else:
			 return False

	def __str__(self):
		return '(' + str(self.entity1) + ',' + str(self.entity2) + ') = ' + str(self.score)
	
"""
this class holds information about the geographic entities and the geographic disambiguation process of a news text document:

- annotations: a list with Entity objects representing the entities annotated;
- filename: the name of the file;
- identifiers: dict to store the identifier of a given name+geographic type;
- uniqueScores: since SSM(x,y) == SSM(y,x) only the unique score for a given document are keep;
- highestScores: for each possible SSM pair between two entities, we will only keep the one(s) with the highest SSM
- precision: the mean precision of the whole document, that is, the sum of all the ssm scores divided by the number of 
annotations for which a geographic concept was found;
"""
class Document(object):

	annotations = None
	filename = None
	identifiers = None
	disambiguationBranches = None
	totalScore = 0.0
	bestBranch = None
	
	def __init__(self,newFilename):
		self.filename = newFilename
		self.annotations = list()
		self.identifiers = defaultdict()
		self.disambiguationBranches = list()


def printDocument(document):

		print "annotations found: "

		for entity in document.annotations:
			print entity

		print "\nnumber of branches found: ", len(document.disambiguationBranches)
		
		print "best branch: \n"
		for branch in document.disambiguationBranches:
			for entity in branch:
				print entity
			print "----\n"


"""
- parses an annotated XML document extracting the placenames whose country is Portugal
- each of those properties is stored in a Entity object.
"""
def parseDocument(document):
	
	xmldoc = minidom.parse(document.filename)
	locais = xmldoc.getElementsByTagName('LOCAL')
		
	for local in locais:
		if local.firstChild.nodeType == 3:
			if local.getAttribute("country")=='Portugal':
				entity = Entity(None, None, local.firstChild.toxml().strip())
				document.annotations.append(entity)



"""
this function is applied to the two first starting toponyms in the text
"""
def SimilarityEntityEntity(firstItem,secondItem):
		
	print "\nSSM between: " , firstItem.title + ',' + secondItem.title
			
	"""		
	calculate the SSM scores between all the possible geographic concepts for each annotation
	"""
	
	placenames = ''
	placenames = firstItem.title.lower().encode("utf8")+'/'
	placenames += secondItem.title.lower().encode("utf8")
	
	params = urllib.urlencode({"icTable": infotable, 
							   "geonames": placenames, 
							   "termsPerName": termsPerName, 
							   "ssmMeasure": ssm_measure,
							   "type": 0})

	data = urllib2.urlopen('http://xldb.di.fc.ul.pt/geossm/ssm.php', params).read()
	
	xmldoc = minidom.parseString(data)
	pairs = xmldoc.getElementsByTagName('ssm:Pair')
			
	bestSSMScore = 0.0
	bestScores = []

	for pair in pairs:
		entity1 = pair.getElementsByTagName('ssm:entity1')
		entity2 = pair.getElementsByTagName('ssm:entity2')

		f_id1 = entity1.item(0).getElementsByTagName('gnpt02:term').item(0).getAttribute('rdf:about').encode('utf-8')
		t_id1 = entity1.item(0).getElementsByTagName('gnpt02:type').item(0).firstChild.toxml().encode('utf-8')
		title1 = entity1.item(0).getElementsByTagName('dcterms:title').item(0).firstChild.toxml().encode('utf-8')
			
		f_id2 = entity2.item(0).getElementsByTagName('gnpt02:term').item(0).getAttribute('rdf:about').encode('utf-8')
		t_id2 = entity2.item(0).getElementsByTagName('gnpt02:type').item(0).firstChild.toxml().encode('utf-8')
		title2 = entity2.item(0).getElementsByTagName('dcterms:title').item(0).firstChild.toxml().encode('utf-8')
					
		if f_id1 == f_id2 or title1 == title2:
			continue
					
		else:
			score = float(pair.getElementsByTagName('ssm:score').item(0).firstChild.toxml())
			print title1+t_id1, title2+t_id2, score
			
			#if it's a best score, create new list with the new high Score
			#else if it's a equal to the best score, append to the list with the highest scores
	
			if score > bestSSMScore:						
				bestSSMScore = score
				entity1 = Entity(f_id1, t_id1, title1)
				entity2 = Entity(f_id2, t_id2, title2) 
				bestScores = [] 
				bestScores.append(Score(entity1,entity2,score))
			
			elif score == bestSSMScore:
				entity1 = Entity(f_id1, t_id1, title1)
				entity2 = Entity(f_id2, t_id2, title2) 
				bestScores.append(Score(entity1,entity2,score))
				
	return bestScores


"""
general case function, to calculate the similarity between an identifier and an Entity
"""
def SimilarityIdentifierEntity(id,entity):

	# first lets get all the possible ids for entity
	secondItemEntities = []
		
	placename = entity.title.lower()
	params = urllib.urlencode({"icTable": infotable, "geonames": placename.encode("utf8"), "termsPerName": termsPerName, "type": 2})
	
	data = urllib2.urlopen('http://xldb.di.fc.ul.pt/geossm/ssm.php', params).read()
	
	xmldoc = minidom.parseString(data)
	
	"""parse the xml output with the identifiers"""
	xmldoc = minidom.parseString(data)
	identifiers = xmldoc.getElementsByTagName('gnpt02:entity')
						
	for identifier in identifiers:
		term = identifier.getElementsByTagName('gnpt02:term')
		f_id = term.item(0).getAttribute('rdf:about').encode('utf-8')
		t_id = term.item(0).getElementsByTagName('gnpt02:type')[0].firstChild.toxml().encode('utf-8')
		title = term.item(0).getElementsByTagName('dcterms:title')[0].firstChild.toxml().encode('utf-8')
		entity = Entity(f_id,t_id,title)
		secondItemEntities.append(entity)


	"""
	calculate the SSM between the fixed identifier and all other possible geographic concepts
	"""	
	print "\nSSM between: ", str(id) + ',' + str(entity.title)
	
	bestScore = 0.0
	bestEntities = []
			
	for el in secondItemEntities:
		f_id2 = el.f_id.rsplit('#')[1]
		score = callJavaTerms(id,f_id2)
		print id, el, score
		
		if score > bestScore:
			bestScore = score
			bestEntities = []
			bestEntities.append(el)
			
		elif score == bestScore:
			bestEntities.append(el)

	return bestEntities


"""
is called recursively until the end of all anotations in text	
"""
def calculate(bestEntity,resolvedAnnotations, document, currentAnnotation):
	
	if bestEntity != None:
		resolvedAnnotations.append(bestEntity)
		currentAnnotation += 1

	#print "resolvedAnnotations: "
	#for el in resolvedAnnotations:
	#	print el
	
	print "currentAnnotations: ", currentAnnotation
		
	if len(resolvedAnnotations) < len(document.annotations):

		firstItem = resolvedAnnotations[-1]
		identifier = firstItem.f_id.rsplit('#')[1]
		entity = document.annotations[currentAnnotation]
		
		#print "Identifier,Entity",identifier,entity
						
		bestEntities = SimilarityIdentifierEntity(identifier,entity)
			
		if len(bestEntities)>1:
			print "\nMore than one best pairs found:"
			for entity in bestEntities:
				print entity	
			
			for entity in bestEntities:
				print "\nCalculating branch for: ", entity
				"""
				let's keep copy of the already disambiguated toponyms which are stored
				in _resolvedAnnotations_, and also of the current annotations, _currentAnnotation_  
				"""
				resolvedAnnotationsCopy = copy.deepcopy(resolvedAnnotations) 
				currentAnnotationCopy = currentAnnotation
				calculate(entity,resolvedAnnotationsCopy, document, currentAnnotationCopy)
				document.disambiguationBranches.append(resolvedAnnotationsCopy)
				print "finished calculating branch"
					
		else:
			print "\nBest score found:", bestEntities[0]			
			calculate(bestEntities[0],resolvedAnnotations, document, currentAnnotation)
			document.disambiguationBranches.append(resolvedAnnotations)

	else:
				
		"""
		base-case, send the branch to calculateScore() along with the document
		but first lets see if there were same toponyms occurring at the beginning of the text
		"""
		differentToponymsAtPosition = 0
		i = 0
				
		while isinstance( resolvedAnnotations[i], int ):
			i += 1
		
		differentToponymsAtPosition = i
		
		#print "differentToponymsAtPosition: ", differentToponymsAtPosition
		
		#print "resolvedAnnotations :"
		#for el in resolvedAnnotations:
		#	print el
		
		if differentToponymsAtPosition != 0:
			for i in range( differentToponymsAtPosition, -1, -1 ):
				resolvedAnnotations[i] = resolvedAnnotations[differentToponymsAtPosition]
		
		print "resolvedAnnotations :"
		for el in resolvedAnnotations:
			print el


def byOrderOfOccurence(document):

	print "\nAnnotations found: "
	for el in document.annotations:
		print el
		
	resolvedAnnotations = []
	
	ToponymA = document.annotations[0]
	ToponymB = document.annotations[1]
	
	currentAnnotation = 1
	differentToponymsAtPosition = -1
	
	"""
	first case, apply ssm to the first two annotations
	"""
	
	if len(resolvedAnnotations) == 0:
		
		"""
		if the two first toponyms are the same, keep shifting one
		to the right until a pair of different toponyms is found
		then asign the same geographic concept to all that are equal from
		this position until the beginning of the text, e.g:
		
		[Braga, Braga, Braga, Braga, Lisboa]
		calculate: SimilarityEntityEntity(Braga, Lisboa) and we have a geo-concept for the 
		last Braga and Lisboa, then we assign the same geo-concept for all the toponyms "Braga"
		"""
				
		while ToponymA.title == ToponymB.title:
			ToponymA = document.annotations[currentAnnotation]
			ToponymB = document.annotations[currentAnnotation+1]
			resolvedAnnotations.append(-1)
			currentAnnotation += 1

		#print "resolvedAnnotations: "
		
		#for el in resolvedAnnotations:
		#	print el
	
		#print "currentAnnotations: ", currentAnnotation
		
		scores = SimilarityEntityEntity(ToponymA,ToponymB);

		if len(scores)>1:
			print "\nMore than one best pairs found:"
			for el in scores:
				print el

			for el in scores:
				print "\nCalculating branch for pair: "
				print el.entity1, el.entity2, el.score
				
				resolvedAnnotationsCopy = copy.deepcopy(resolvedAnnotations)
				currentAnnotationCopy = currentAnnotation
				
				if el.entity1.title == ToponymA.title:
					resolvedAnnotationsCopy.append(el.entity1)
					resolvedAnnotationsCopy.append(el.entity2)
					
				elif el.entity1.title == ToponymB.title:
					resolvedAnnotationsCopy.append(el.entity2)
					resolvedAnnotationsCopy.append(el.entity1)

				print "resolvedAnnotationsCopy: "
				for el in resolvedAnnotationsCopy:
					print el
				
				currentAnnotationCopy += 1
				calculate(None,resolvedAnnotationsCopy,document,currentAnnotationCopy)
				print "the end1"

		elif len(scores) == 1:
			print "\nBest score found:", scores[0]
			
			if scores[0].entity1.title == ToponymA.title:
				resolvedAnnotations.append(scores[0].entity1)
				resolvedAnnotations.append(scores[0].entity2)
			
			elif scores[0].entity1.title == ToponymB.title:
				resolvedAnnotations.append(scores[0].entity2)
				resolvedAnnotations.append(scores[0].entity1)
			
			currentAnnotation += 1						
			calculate(None,resolvedAnnotations, document, currentAnnotation)
			print "the end2"
			
		elif len(scores) == 0:
			print "Toponym string matching with Geo-Net-PT failed"


"""
returns the similarity between two identifiers
"""
def callJavaTerms(id1,id2):

	if id1 == id2:
		return float(1.0)

	ids = id1+'/'+id2
		
	params = urllib.urlencode({"icTable": infotable, 
							   "geonames": ids, 
							   "termsPerName": termsPerName,
							   "ssmMeasure": ssm_measure, 
							   "type": 1})
	
	data = urllib2.urlopen('http://xldb.di.fc.ul.pt/geossm/ssm.php', params).read()	
	xmldoc = minidom.parseString(data)
		
	#get all the results for all possible pairs	
	pairs = xmldoc.getElementsByTagName('ssm:Pair')
	
	for pair in pairs:
	
		entity1 = pair.getElementsByTagName('ssm:entity1')
		entity2 = pair.getElementsByTagName('ssm:entity2')
		f_id1 = entity1.item(0).getElementsByTagName('gnpt02:term').item(0).getAttribute('rdf:about')
		f_id2 = entity2.item(0).getElementsByTagName('gnpt02:term').item(0).getAttribute('rdf:about')
		
		if f_id1 == f_id2:
			continue
		
		else:
			score = pair.getElementsByTagName('ssm:score').item(0).firstChild.toxml()			
			break
		
	return float(score)
	
"""
processes a file
"""
def desambiguate(filename):
	
	document = Document(filename)
	
	"""find all the annotations regarding placenames"""
	parseDocument(document)
			
	if len(document.annotations) > 1:
		begin = time.time()
		
		byOrderOfOccurence(document)
		
		printDocument(document)

		secs = time.time() - begin
		hours, remainder = divmod(secs, 3600)
		minutes, seconds = divmod(remainder, 60)
				
		print "%02.0f:%02.0f:%02.2f hh:mm:ss.ss"  % (hours, minutes, seconds)
		

def main():	
	start = time.time()
	
	global ssm_measure, termsPerName, infotable
	
	file = sys.stdin
	ssm_measure = "JG"
	termsPerName = 2
	infotable = "ssm_adm_name_term_freq_n_cap_name"

	desambiguate(file)
	
	secs = time.time() - start
	hours, remainder = divmod(secs, 3600)
	minutes, seconds = divmod(remainder, 60)
	print "\nTotal running time was %02.0f:%02.0f:%02.2f hh:mm:ss.ss"  % (hours, minutes, seconds)

if __name__ == "__main__":
	main()
	
