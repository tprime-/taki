#!/usr/bin/python

# DNS zone transfer waterfall
# TODO:
# dont use system DNS for lookups

import dns.query
import dns.zone
import dns.resolver
import argparse

#nameserver = 'ns1.tld.sy'
#target = 'gov.sy'

def getNS( domain ):
	print "Attempting to find nameservers for: " + domain
	answers = dns.resolver.query(domain, 'NS', raise_on_no_answer=False)
	if answers:
			print "Nameservers for " + domain + " are:"
			for nameserver in answers.rrset.items:
					print nameserver
			return answers.rrset.items
	else:
			print " Unable to retrieve nameservers for " + domain

			return

def attemptXfr( nameserver, target ):
	try:
		print "Attempting zone transfer for: " + target + " with " + nameserver
		z = dns.zone.from_xfr(dns.query.xfr(nameserver, target, timeout=timeout))
		for node in z.nodes.keys():
			# get rid of all NSEC3 records
			if "NSEC3" in z[node].to_text(node):
				del z[node]
		names = z.nodes.keys()
		names.sort()
		
		return names
		
	except Exception:
		print " Zone transfer failed for: " + target + " with " + nameserver

def iterateResults( domains ):
	results = []
	for domain in domains:
			try:
				nameservers = getNS(domain)
				for nameserver in nameservers:
					result = attemptXfr(nameserver.to_text(), domain)
					if result != None:
						for r in result:
							r = r.to_text()
							if r != "*" and r != "@" and r != ".":
								r += "." + domain
								results.append(r)
							else:
								pass
	# pythondns throws an error if all nameservers failed to answer the query. ignore this
			except Exception:
				continue

	return results

# convert a zone object into a list of DNS names	
def zoneToNames( zone, tld ):
	names = []
	for name in zone:
		name = name.to_text()
		name += "." + tld
		# reject origin and wildcard records
		if name[:1] != "@" and name[:1] != "*" and name[:1] != ".":
			names.append(name)

	return names
	
def sortResults( results ):
	# [::-1] for reversing name
	unique_results = [ result[::-1] for result in list(set(results))]
	unique_results.sort()
	unique_results = [ result[::-1] for result in unique_results]

	return unique_results
	
def startTaki( args ):
	try:
		global timeout
		timeout = args.timeout
		final_results = []
		temp_results = []
		zone = attemptXfr(args.nameserver, args.target)
		# make sure the initial zone transfer succeeds
		if zone != None:
			temp_results = zoneToNames(zone, args.target)
			for result in temp_results:
				final_results.append(result)
		else:
			pass
			
		while True:
			temp_results = iterateResults(temp_results)
			for result in temp_results:
				final_results.append(result)
			if not temp_results:
				print "All done. Identified domains are:"
				print(sortResults(final_results))
				break
				
	except KeyboardInterrupt:
		print "User Interrupt - ending."

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		description='taki - zone transfer waterfall',
		usage='Usage: ./taki.py [-n nameserver] [-z zone] [-t timeout]',
	)
	parser.add_argument('-v', '--version',
		action='version',
		version='taki version 0.1',
	)
	parser.add_argument('-t',
		dest='timeout',
		help='Zone transfer timeout in seconds',
		default=10
		#required=True,
	)
	parser.add_argument('-n',
		dest='nameserver',
		help='Nameserver to use',
		required=True,
	)
	parser.add_argument('-z',
		dest='target',
		help='Target zone',
		required=True,
	)
	args = parser.parse_args()
				
startTaki(args)
