#!/usr/bin/python
#
# functie: bash
# autheur: Eelco Jepkema
# omschrijving: haalt de bash quote op die gevraagd wordt, of een random bashquote als er geen nummer meegegeven wordt.
# syntax: pistes [<quotenmr>]
# changelog:
#   2006-06-29:
#		- eerste versie
#

import string,os

def bash(quote=0):
	if(quote):
		cmd = "lynx -dump --width 1000 http://www.bash.org/?" + str(quote);
	else:
		cmd = "lynx -dump --width 1000 http://www.bash.org/?random";
	
	inp,outp,stderr = os.popen3(cmd);
	result = outp.read();
	inp.close();
	outp.close();
	stderr.close();
	i = string.find(result, "[16][X]");

	if(i == -1):
		result = "Bash quote #" + str(quote) + " niet gevonden\n";
	else:
		i = i + 7;
		
		j=string.find(result, "[17]", i);
		lines = string.split(string.strip(result[i:j]), '\n');

		k = string.find(result, "[13]");
		l = string.find(result, "14", k);
		mynumber = string.split(string.strip(result[k+4:l-1]), '\n');
		for thenumber in mynumber:
			thisnumber = thenumber;
			
		result = "bash quote: " + thisnumber + "\n";
		for mystr in lines:
			result+=string.strip(mystr)+"\n";
			if len(mystr)<2:
				result+='\n';
	return string.strip(result);
