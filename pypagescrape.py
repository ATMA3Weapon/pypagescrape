import lxml
from lxml.html.diff import htmldiff, html_annotate
import bs4
from bs4 import BeautifulSoup
import difflib
import ast
from collections import OrderedDict

def depth(node):
    d = 0
    while node is not None:
        d += 1
        node = node.getparent()
    return (d-1)

def html_compare(threshold, html1, html2):
	html1 = str(html1)
	html2 = str(html2)
	
	s = difflib.SequenceMatcher(None, html1+";", html2+";") 
	rat = s.ratio()
	
	#print (rat)
	
	if rat >= threshold: return [True, rat]
	else: return [False, rat]

def html_profiler(depth, html, charset):
	#html = str(html)
	html = BeautifulSoup(html, "html5lib")
	
	striped_away = ['a', 'img', 'link', 'meta', 'script', 'form', 'noscript', 'ul', 'li', 'style']
	
	# find and remove all text
	for textelement in html.findAll(text=True):
		textelement.extract()
	
	# remove unwanted tags
	for tagstriped in html(striped_away):
		tagstriped.extract()

	# remove all tags past the desired depth
	#soup = BeautifulSoup(data)
	for tag in html.find_all():		
		if len(list(tag.parents)) >= depth:
			tag.extract()
	
	# remove all contents of attributes 
	for tag2 in html.findAll(True):
		for testtt in tag2.attrs:
			if testtt is not None: 
				tag2[testtt] = ""
								
	rest = str(html.prettify(charset))
	
	return rest


def scrape_by_template_page(site, page, templatexml, charset, html):

	# open XML data
	open_scrapey_template_file = open(templatexml) # open the XML file 
	profiles_file_output = open_scrapey_template_file.read()  # read from the XML file 

	template = BeautifulSoup(profiles_file_output, features="xml")  # stored XML template file as BS use XML prasing with it

	html_soup = BeautifulSoup(html, "html5lib", from_encoding=charset) # BS the incoming HTML
	html_pretty_charset = str(html_soup.prettify(charset))

	output = {} # set up our output list dictionary for adding stuff to
	
	foundsite = template.find("website", {"name": site}) # search for it
	if foundsite is not None: # check if site template exists in the file
		
		foundpage = foundsite.find("webpage", {"name": page}) # search for it
		if foundpage is not None: # check if the page template for this site exists
			
			pageprofile = foundpage.find("pageprofile")  # find the page profile section
			variables   = foundpage.find("variables")    # find the variables section
			searchforvar   = foundpage.find("scrapepage")    # find the search section
			filterspage = foundpage.find("filters")      # find the filters section
		
			pagethreshold = float(pageprofile.profiledata.get("threshold"))
			pagedepth     = int(pageprofile.profiledata.get("depth"))
			
			profiled_page = pageprofile.profilehtml.html #.prettifty() # get the profile saved from the XML file
			profiled_page = profiled_page.prettify()
			profiled_html = html_profiler(pagedepth, html_pretty_charset, charset) # create a profile of incoming HTML
			
			compare_html = html_compare(pagethreshold, profiled_page, profiled_html) # check if the HTML is comparable to a degree.

			# create dictionary of variables'
			for temp in variables.findAll("var"):
				varname = str(temp['name']);
				output[varname] = None

			if compare_html[0] is True: # check if comparison meet threshold for continueing and begin stripping data. 
				
				
				tree = lxml.etree.XML(searchforvar.prettify())
				
				rents = [] # eg: rents[2] = [find, bs4.element.tag], rents[3] = [findall, bs4.element.listoftagsorw/ethehellitis]
				
				lastlevel = 1
				levelcount = 0
				
				for test in tree.iterdescendants():
					level = depth(test)
					
					if lastlevel > level:
						diff = lastlevel - level
						del rents[diff:-1] # remove the old data from the stack. so were back at the reference we want.
					
					# get the last parent from the rents.
					lastrent = None
					flippedrents = rents[::-1]
					for rentlist in flippedrents:
						if isinstance(rentlist, list):
							#if rentlist[2] is (bs4.element.Tag, bs4.element.ResultSet): #"soup":
							lastrent = rentlist[2]
							break
					
					if test.tag in "find":
						# get the attributes
						attrtypes = test.attrib.keys()
						tag = None
						context = None
						textput = None
						findoutput = None
						
						if "tag" in attrtypes:
							tag = test.attrib.get("tag")
						
						if "attribute" in attrtypes:
							attr = test.attrib.get("attribute")
							context = ast.literal_eval(attr)
						
						if "text" in attrtypes:
							textput = test.attrib.get("text")
				
						# are we on the first level? use the base soup.
						if level == 1:
							findoutput = html_soup.find(tag, attrs=context, text=textput)
						
						# are we abpve the first level? then we use the last known find or findall parent in the stack.
						elif level > 1:
							#print "ya", level, tag, textput, type(lastrent), rents
							
							if isinstance(lastrent, bs4.element.Tag):
								findoutput = lastrent.find(tag, attrs=context, text=textput)
					
							elif isinstance(lastrent, list):
								#print "eh", level, textput
								for found in lastrent:
									findoutput = found.find(tag, attrs=context, text=textput)
									if findoutput is not None:
										break
					
						rents.append(["soup", level, findoutput]) # save the output to rents stack
					
					elif test.tag in "findall":
						# get the attributes
						attrtypes = test.attrib.keys()
						tag = None
						context = None
						textput = None
						findoutput = None
						
						if "tag" in attrtypes:
							tag = test.attrib.get("tag")
						
						if "attribute" in attrtypes:
							attr = test.attrib.get("attribute")
							context = ast.literal_eval(attr)
						
						if "text" in attrtypes:
							textput = test.attrib.get("text")
					
						# are we on the first level? use the base soup.
						if level == 1:
							findoutput = souped.findAll(tag, attrs=context, text=textput)
						
						elif level > 1:
							if isinstance(lastrent, bs4.element.Tag):
								findoutput = lastrent.findAll(tag, attrs=context, text=textput)
						
						rents.append(["soup", level, findoutput]) # save the output to rents stack
					
					# direct the tree
					elif test.tag in "parent":
						#print lastrent
						if isinstance(lastrent, bs4.element.Tag):
							findoutput = lastrent.parent
							
						rents.append(["soup", level, findoutput])
					
					elif test.tag in "child":
						if isinstance(lastrent, bs4.element.Tag):
							findoutput = lastrent.child
							
						rents.append(["soup", level, findoutput])
					
					elif test.tag in "string":
						rents.append(level)
					
					# call from the tree
					elif test.tag in "get_text":
						rents.append(level)
						
					elif test.tag in "innertext":
						if isinstance(lastrent, bs4.element.Tag):
							findoutput = lastrent.text
							
						elif isinstance(lastrent, list):
							findoutput = []
							for fo in lastrent:
								findoutput.append(fo.text)
					
						rents.append(["text", level, findoutput])
					
					# outputting data through savetovar
					elif test.tag in "savetovar":
						# get all the keys of text
						attrtypes = test.attrib.keys()
						
						if "location" in attrtypes:
							location = test.attrib.get("location") # save the location were saving the BS data to
					
							output[location] = lastrent
						
						rents.append(level)
					
					
					lastlevel = level
				
				# lets filter that shit
				filtertree = lxml.etree.XML(filterspage.prettify())
				
				rents = [] # eg: rents[2] = [find, bs4.element.tag], rents[3] = [findall, bs4.element.listoftagsorw/ethehellitis]
				
				lastlevel = 1
				levelcount = 0
				
				for commands in filtertree.iterdescendants():
					level = depth(commands)
					
					if lastlevel > level:
						diff = lastlevel - level
						del rents[diff:-1] # remove the old data from the stack. so were back at the reference we want.
					
					# get the last parent from the rents.
					lastrent = None
					flippedrents = rents[::-1]
					for rentlist in flippedrents:
						if isinstance(rentlist, list):
							#if rentlist[2] is (bs4.element.Tag, bs4.element.ResultSet): #"soup":
							lastrent = rentlist[2]
							break
					
					#newoutput = ""
					
					if commands.tag in "clearwhitespace":
						outputvar = commands.attrib.get("var")
						if outputvar in output:
							if output[outputvar] is not None:  
								newoutput = output[outputvar].strip()
								newoutput = newoutput.replace("\n", "")
							
								output[outputvar]  = newoutput
					
					elif commands.tag in "remove":
						outputvar = commands.attrib.get("var")
						outputtext = commands.attrib.get("text")
					
						if outputtext in output[outputvar]:
							if output[outputvar] is not None: 
								newoutput = output[outputvar].replace(outputtext, "")
								output[outputvar]  = newoutput
							
				#print output
				return output	
	return False


#openpage = open("B000M5U6CU.html") # open the XML file 
#readpage = openpage.read() 
#souped = BeautifulSoup(readpage, "html5lib")
#
#html_soup1 = souped.prettify()
#
#scrapey_file = "template.xml"
#charset = "ISO-8859-1"
#
#print scrape_by_template_page("amazon.com", "productpage-general", scrapey_file, charset, readpage)
