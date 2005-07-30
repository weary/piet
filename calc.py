#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import string,random,os,math,re;

def unitinvertcheck(unit1,unit2):
  for i in ["1","2","3","4","5","6","7","8","9"]:
    unit1=string.replace(unit1,"^"+i,"^+"+i)
  unit1=string.replace(unit1,"^-","^")
  unit1=string.replace(unit1,"^+","^-")
  return unit1==unit2

def calcS(param):
  # Subtract adn Add rule
  (error,result,param,unit)=calcD(param)
  if (error>0):
    return (1,result,param,unit)
  while ((error==0) and (param!="") and ((param[0]=="-") or (param[0]=="+"))):
    op=param[0]
    (error,result2,param,unit2)=calcD(param[1:])
    if unit!="" and unitinvertcheck(unit,unit2):
      if op=="-":
        result-=(1/result2)
      else:
        result+=(1/result2)
    else:
      if (unit2!=unit) and (unit!="W"):
        unit="W"
      if op=="-":
        result-=result2
      else:
        result+=result2;
  return (error,result,param,unit)

def calcD(param):
  # Divide and Multiply rule
  (error,result,param,unit)=calcP(param)
  if (error>0):
    return (1,result,param,"")
  while ((error==0) and (param!="") and ((param[0]=="/") or (param[0]=="*"))):
    op=param[0]
    (error,result2,param,unit2)=calcP(param[1:])
    #unify units for dividing
    if unit2=="W":
      unit="W"
    if op=="/":
      result/=result2
      #unify units too
      if unit!="W" and unit2!="":
        unitlist1=[]
        unitlist2=[]
        newunitlist=[]
        if unit!="":
          for item in string.split(unit,"*"):
            i=string.find(item,"^")
            unitlist1+=[(item[:i],int(item[i+1:]))]
        for item in string.split(unit2,"*"):
          i=string.find(item,"^")
          unitlist2+=[(item[:i],int(item[i+1:]))]
        for (unit1,value1) in unitlist1:
          i=-1
          t=0
          for (unit2,value2) in unitlist2:
            if unit1==unit2:
              i=t
            t+=1
          value2=0
          if i>=0:
            (_,value2)=unitlist2[i]
            unitlist2[i]=('',0)
          if (value1-value2)!=0:
            newunitlist+=[unit1+"^"+str(value1-value2)]
        for (unit2,value2) in unitlist2:
          if value2!=0:
            newunitlist+=[unit2+"^"+str(-value2)]
        newunitlist.sort(lambda x,y: cmp(x,y))
        unit=string.join(newunitlist,"*")
      elif unit=="":
        unit=unit2;
    else:
      result*=result2
      #unify units too
      if unit!="W" and unit2!="":
        unitlist1=[]
        unitlist2=[]
        newunitlist=[]
        if unit!="":
          for item in string.split(unit,"*"):
            i=string.find(item,"^")
            unitlist1+=[(item[:i],int(item[i+1:]))]
        for item in string.split(unit2,"*"):
          i=string.find(item,"^")
          unitlist2+=[(item[:i],int(item[i+1:]))]
        for (unit1,value1) in unitlist1:
          i=-1
          t=0
          for (unit2,value2) in unitlist2:
            if unit1==unit2:
              i=t
            t+=1
          value2=0
          if i>=0:
            (_,value2)=unitlist2[i]
            unitlist2[i]=('',0)
          if (value1+value2)!=0:
            newunitlist+=[unit1+"^"+str(value1+value2)]
        for (unit2,value2) in unitlist2:
          if value2!=0:
            newunitlist+=[unit2+"^"+str(value2)]
        newunitlist.sort(lambda x,y: cmp(x,y))
        unit=string.join(newunitlist,"*")
      elif unit=="":
        unit=unit2;
  return (error,result,param,unit)

def calcP(param):
  # Power rule
  (error,result,param,unit)=calcM(param)
  if (error>0):
    return (1,result,param,unit)
  while ((error==0) and (param!="") and (param[0]=="^")):
    (error,result2,param,unit2)=calcM(param[1:])
    #update unit
    if unit!="W" and unit!="":
      if unit2!="":
        unit="W"
      else:
        if math.floor(abs(result2))==abs(result2):
          i=string.find(unit,"^")
          while i>=0:
            n=string.find(unit,"*",i)
            if n<0:
              n=len(unit)
            value=int(unit[i+1:n])*int(result2)
            unit=unit[:i+1]+str(value)+unit[n:]
            i=string.find(unit,"^",i+1)
        else:
          unit="W"
    result**=result2
  return (error,result,param,unit)

def calcM(param):
  digits=re.compile('(\-)?[0-9]+(\.[0-9]+)?((e\+[0-9]+)|(e\-[0-9]+))?')
  digitscheck= digits.match(param)
  if digitscheck:
    value=float(digitscheck.group())
    param=string.strip(param[digitscheck.end():])
    chars=re.compile('[a-z]|\(|[0-9]|\$')
    if chars.match(param):
      return (0,value,"*"+param,"")
    return (0,value,param,"")
  if (param[:1]=="("):
    (error,value,param,unit)=calcS(param[1:])
    if param[:1]!=")":
      return(0,0,"","");
    chars=re.compile('[a-z]|\(|[0-9]|\$')
    if chars.match(param[1:]):
      return(error,value,"*"+param[1:],unit)
    return(error,value,param[1:],unit)

  #prefixes
  prefix=[("yotta",1e24),("zetta",1e21),("exa",1e18),("peta",1e15),("tera",1e12),("giga",1e9),("mega",1e6),("kilo",1e3),("hecto",1e2),("deca",1e1),("deci",1e-1),("centi",1e-2),("milli",1e-3),("micro",1e-6),("nano",1e-9),("pico",1e-12),("femto",1e-15),("atto",1e-18),("zepto",1e-21),("yocto",1e-24)]
  for(thisprefix,power) in prefix:
    if param[:len(thisprefix)]==thisprefix:
      (error,value,param,unit)=calcM(param[len(thisprefix):])
      return (error,value*power,param,unit)

  #SI length
  units=[("meter",1.0,"m^1")]

  #SI weight
  
  units+=[("gram",1.0,"g^1"),("ton",1e+6,"g^1")]

  # volume

  units+=[("liter",1e-3,"m^3")]

  #time

  units+=[("minute",6.0e+1,"s^1"),("hour",3.6e+3,"s^1"),("day",8.64e+4,"s^1"),("week",6.048e+5,"s^1"),("fortnight",1.2096e+6,"s^1"),("month",2.6298e+6,"s^1"),("year",3.15576e+7,"s^1"),("lustrum",1.57788e+8,"s^1"),("lustra",1.15576e+8,"s^1"),("decade",3.15576e+8,"s^1"),("century",3.15576e+9,"s^1"),("centuries",3.15576e+9,"s^1"),("millenium",3.15576e+10,"s^1"),("millenia",3.15576e+10,"s^1")]
  
  #tijd

  units+=[("seconde",1.0,"s^1"),("second",1.0,"s^1"),("sec",1.0,"s^1"),("minuut",6.0e+1,"s^1"),("minuten",6.0e+1,"s^1"),("uur",3.6e+3,"s^1"),("uren",3.6e+2,"s^1"),("dag",8.64e+4,"s^1"),("dagen",8.64e+4,"s^1"),("maand",2.6298e+6,"s^1"),("maanden",2.6298e+6,"s^1"),("jaar",3.15576e+7,"s^1"),("jaren",3.15576e+7,"s^1"),("eeuw",3.15576e+9,"s^1"),("eeuwen",3.15576e+9,"s^1")]

  #pressure
  units+=[("bar",1.0e+8,"g^1*m^-1*s^-2"),("psi",6.8947529e+6,"g^1*m^-1*s^-2"),("barye",1.0e+2,"g^1*m^-1*s^-2"),("atmosphere",1.01325e+8,"g^1*m^-1*s^-2")]

  #force
 
  units+=[("newton",1.0e+3,"g^1*m^1*s^-2"),("dyne",1.0e-2,"g^1*m^1*s^-2"),("pascal",1.0e+3,"g^1*m^-1*s^-2")]

  #degree/rad

  units+=[("degree",0.01745329251994329,"r^1"),("graad",0.01745329251994329,"r^1"),("graden",0.017453292519943299,"r^1"),("radian",1,"r^1"),("rad",1,"r^1")]

  #area

  units+=[("acre",4.0468564224e+3,"m^2"),("are",1.0e+2,"m^2"),("hectare",1.0e+2,"m^2"),("rood",1.011714105e+3,"m^2")]

  #electricity

  units+=[("volt",1.0e+3,"g^1*m^2*s^-3*a^-1"),("ampere",1.0,"a^1"),("coulomb",1.0,"a^1*s^1"),("ohm",1.0e+3,"g^1*m^2*s^-3*a^-2"),("farad",1.0e-3,"a^2*g^-1*m^-2*s^4"),("tesla",1.0e+3,"a^-1*g^1*s^-2"),("weber",1.0e+3,"a^-1*g^1*m^2*s^-2"),("henry",1.0e+3,"a^-2*g^1*m^2*s^-2")] 

  #energy
  units+=[("joule",1.0e+3,"g^1*m^2*s^-2"),("calorie",4.184e+3,"g^1*m^2*s^-2"),("watt",1.0e+3,"g^1*m^2*s^-3")]
    
  # imperial volume
  units+=[("gallon",3.785411784e-3,"m^3"),("usgallon",3.785411784e-3,"m^3"),("fluidgallon",3.785411784e-3,"m^3"),("drygallon",4.4048428032e-3,"m^3"),("imperialgallon",4.54609e-3,"m^3"),("fluidounce",2.84130625e-5,"m^3"),("oz",2.84130625e-5,"m^3"),("fl.oz",2.84130625e-5,"m^3"),("gill",1.420653125e-4,"m^3"),("pint",5.6826125e-4,"m^3"),("peck",9.09218e-3,"m^3"),("kenning",1.818436e-2,"m^3"),("bucket",1.818436e-2,"m^3"),("bushel",3.636872e-2,"m^3"),("strike",7.273744e-2,"m^3"),("quarter",0.29094976,"m^3"),("pail",0.2909497,"m^3"),("chaldron",1.16379904,"m^3"),("last",2.9094976,"m^3"),("firkin",4.091481e-2,"m^3"),("kilderkin",8.182962e-2,"m^3"),("barrel",0.16365924,"m^3"),("hogshead",0.24548886,"m^3")]

  # imperial length

  units+=[("inch",2.54e-2,"m^1"),("foot",3.048e-1,"m^1"),("feet",3.048e-1,"m^1"),("yard",9.144e-1,"m^1"),("rod",5.0292,"m^1"),("pole",5.0292,"m^1"),("perch",5.0292,"m^1"),("chain",20.1168,"m^1"),("furlong",2.01168e+2,"m^1"),("mile",1.609344e+3,"m^1"),("mijl",1.609344e+3,"m^1"),("mijlen",1.609344e+3,"m^1"),("league",4.828032e+3,"m^1"),("nauticalmile",1.852e+3,"m^1"),("zeemijl",1.852e+3,"m^1"),("zeemijlen",1.852e+3,"m^1")]

  # imperial speed

  units+=[("knot",5.14444444444,"m^1*s^-1"),("knoop",5.14444444444,"m^1*s^-1"),("knopen",5.14444444444,"m^1*s^-1")]

  # Herz
  units+=[("herz",1.0,"s^-1"),("hz",1.0,"s^-1")]

  # light
 
  units+=[("candela",1.0,"cd^1"),("lumen",1.0,"cd^1"),("lux",1.0,"cd^1*s^-2"),("iluminance",1.0,"cd^1*s^-2")]

  # galaxy 

  units+=[("parsec",3.08568e+16,"m^1"),("lightyear",9.460730472580800e+15,"m^1"),("light-year",9.460730472580800e+15,"m^1"),("lichtjaar",9.460730472580800e+15,"m^1"),("licht-jaar",9.460730472580800e+15,"m^1"),("lightspeed",2.99792458e+8,"m^1*s^-1"),("light-speed",2.99792458e+8,"m^1*s^-1"),("lichtsnelheid",2.99792458e+8,"m^1*s^-1"),("licht-snelheid",2.99792458e+8,"m^1*s^-1")]

  #imperial weight and mass

  units+=[("mite",3.2399455e-3,"g^1"),("grain",6.479891e-2,"g^1"),("drachm",1.7718451953125,"g^1"),("ounce",2.8349523123e+1,"g^1"),("pound",4.5359237e+2,"g^1"),("stone",6.35029318e+3,"g^1"),("quarter",1.270058636e+4,"g^1"),("hundredweight",5.080234544e+4,"g^1"),("imperialton",1.0160469088e+6,"g^1"),("britishton",1.0160469088e+6,"g^1"),("slug",1.45939e+4,"g^1")]

  units+=[("joule",1.0,"j^1"),("calorie",4.184,"j^1"),("watt",1.0,"j^1*s^-1")]

  # cooking volume

  units+=[("teaspoon",5e-6,"m^3"),("theelepel",5e-6,"m^3"),("dessertspoon",10e-6,"m^3"),("tablespoon",1.5e-5,"m^3"),("eetlepel",1.5e-5,"m^3"),("lepel",1.5e-5,"m^3"),("cup",2.5e-4,"m^3"),("kopje",2.5e-4,"m^3"),("mug",3.0e-4,"m^3"),("mok",3.0e-4,"m^3"),("mokken",3.0e-4,"m^3"),("jigger",4.436e-5,"m^3"),("drop",8.33333333333333333333e-8,"m^3"),("druppel",8.33333333333333333333e-8,"m^3")]

  # abbreviations, must be at the end of the list otherwise the m of meter would match with mile for example
  units+=[("mm",1.0e-3,"m^1"),("dm",1e-1,"m^1"),("cm",1e-2,"m^1"),("m",1.0,"m^1"),("km",1e+3,"m^1"),("ft",3.048e-1,"m^1"),("lb",4.5359237e+3,"g^1"),("l",1e-3,"m^1"),("dl",1e-4,"m^3"),("cl",1e-5,"m^1"),("ml",1e-6,"^1"),("kg",1.0e+3,"g^1"),("cc",1.0e-6,"m^3"),("cl",1.0e-5,"m^3"),("nm",1.0e-9,"m^1"),("l",0.001,"m^3"),("s",1.0,"s^1"),("amp",1.0,"a^1"),("min",6.0e+1,"s^1")]

  for (thisunit,convertrate,siunit) in units:
    if param[:len(thisunit)]==thisunit:
      #check for plural
      endpos=len(thisunit)
      if param[endpos:endpos+1]=="s":
        endpos+=1
      if param[endpos:endpos+2]=="es":
        endpos+=1
      return(0,convertrate,param[endpos:],siunit)

  a=math.sqrt
  functions=[("ceil",math.ceil),("abs",math.fabs),("floor",math.floor),("exp",math.exp),("log",math.log),("log10",math.log10),("sqrt",math.sqrt),("acos",math.acos),("asin",math.asin),("atan",math.atan),("cos",math.cos),("sin",math.sin),("tan",math.tan),("cosh",math.cosh),("sinh",math.sinh),("tan",math.tanh)]
  for (funcname,func) in functions:
    funcname+='('
    if param[:len(funcname)]==funcname:
      (error,value,param,unit)=calcS(param[len(funcname):])
      if (param[:1]!=")"):
        return(0,0,"","")
      chars=re.compile('[a-z]')
      if chars.match(param[1:]):
        (error,result,param,unit)=calcM(param[1:])
        return (error,func.__call__(value)*result,param,"")

      return(error,func.__call__(value),param[1:],"");

  #check for money currency
  
  money=[("euro","EUR"),("dollar","USD"),("pond","GBP"),("britsepond","GBP"),("britishpound","GBP"),("eur","EUR"),("usd","usd"),("gbp","GBP"),("a$","AUD"),("$a","AUD"),("aud","AUD"),("australischedollar","AUD"),("$c","CAD"),("c$","CAD"),("canadiandollar","CAD"),("canadeesedollar","CAD"),("cad","CAD"),("ukp","GBP"),("yen","JPY"),("jpy","JPY"),("$nz","NZD"),("nz$","NZD"),("newzealanddollar","NZD"),("nieuwzeeuwsedollar","NZD"),("nieuwzeelandsedollar","NZD"),("nzd","NZD"),("chf","CHF"),("zwitsersefrank","CHF"),("switzerlandfranc","CHF"),("swissfranc","CHF"),("franc","CHF"),("$","USD")]

  for (currency,name) in money:
    if  param[:len(currency)]==currency:
      endpos=len(currency)
      if param[endpos:endpos+1]=="s":
        endpos+=1
      if name=="EUR":
        return(0,1,param[endpos:],"e^1")
      cmd = "echo -e \"Amount=1&From=EUR&To="+name+"\"";
      cmd += " | lynx -post_data http://www.xe.com/ucc/convert.cgi";
      inp,outp,stderr = os.popen3(cmd);
      result = outp.read();
      outp.close();
      inp.close();
      stderr.close();
      i1=string.find(result,"Euro = ")+7;
      i2=string.find(result," ",i1)
      return(0,1/float(result[i1:i2]),param[endpos:],"e^1")

  unit=""

  if param[:2]=="pi":
    chars=re.compile('[a-z]')
    if chars.match(param[2:]):
      (error,result,param,unit)=calcM(param[2:])
      return (error,3.1415926535897932384*result,param,unit)

    return (0,3.14159265358979323846,param[2:],"")

  if param[:1]=="e":
    chars=re.compile('[a-z]')
    if chars.match(param[1:]):
      (error,result,param,unit)=calcM(param[1:])
      return (error,2.7182818284590452353602874713*result,param,unit)
    return (0,2.7182818284590452353602874713,param[1:],"")

  if param[:5]=="dozen":
    chars=re.compile('[a-z]')
    if chars.match(param[5:]):
      (error,result,param,unit)=calcM(param[5:])
      return (error,12*result,param,unit)
    return (0,12,param[5:],unit)

  if param[:6]=="dozijn":
    chars=re.compile('[a-z]')
    if chars.match(param[6:]):
      (error,result,param,unit)=calcM(param[6:])
      return (error,12*result,param,unit)

    return (0,12,param[6:],unit)

  if param[:5]=="gross":
    chars=re.compile('[a-z]')
    if chars.match(param[5:]):
      (error,result,param,unit)=calcM(param[5:])
      return (error,144*result,param,unit)

    return (0,144,param[5:],unit)

  return (1,1,param,unit)

def supercalc(toparse):
  if toparse[:4]=="uit ":
    toparse=toparse[4:];
  elif toparse[len(toparse)-4:]==" uit":
    toparse=toparse[:len(toparse)-4];
  toparse=string.lower(toparse)
  toparse=string.strip(string.replace(toparse," in ","_in_"))
  toparse=string.replace(toparse," per ","/")
  toparse=string.replace(toparse," ","")
  toparse=string.replace(toparse,"kilo)","kg)")
  toparse=string.replace(toparse,"kilo_","kg_")
  if toparse[len(toparse)-4:]=="kilo":
    toparse=toparse[:len(toparse)-4]+"kg"
  (error,result,left,unit)= calcS(toparse)
  if left[:7]=="celsius":
    left=left[7:]
    result+=273.15
  elif left[:6]=="kelvin":
    left=left[6:]
  elif left[:10]=="fahrenheit":
    left=left[10:]
    result=(result+459.67)*(5.0/9.0)
  elif (error>0):
    return "Parse Error!"
  if left[:11]=="_in_celsius":
    result-=273.15
    left=left[11:]
  elif left[:11]=="_in_fahrenheit":
    result=((result*9)/5)-459.67
    left=left[11:]
  elif left[:11]=="_in_kelvin":
    left=left[11:]
  if left[:4]=="_in_":
    backupunit=left[4:]
    (error,result2,left,unit2)=calcS(left[4:])
    if (error>0):
      return "Parse Error!"
    if (left!=""):
      return "Parse Error!"
    if result2!=0:
      if unitinvertcheck(unit,unit2):
        result=(1/result)/result2
        unit=backupunit
        result=str(result)
        if result[len(result)-2:]==".0":
          result=result[:len(result)-2]
        return result+" "+unit
      if (unit==unit2):
        unit=backupunit
        result/=result2
        result=str(result)
        if result[len(result)-2:]==".0":
          result=result[:len(result)-2]
        return result+" "+unit
      unit="W"
      result/=result2 
  if left!="":
    return "Parse Error!"
  result=str(result)
  if result[len(result)-2:]==".0":
    result=result[:len(result)-2]
  if unit=="W":
    unit=random.choice(["Quantum fluctuations","Random distortions","Hyper Wave-entanglements","Chrono particle inductions","Parallel Chi","meta Universe inhibitors","Semi Nuclear Helices","Thaume bubbles"])
  else:
    unit=string.replace(unit,"s^","sec^")
    unit=string.replace(unit,"j^","joule^")
    unit=string.replace(unit,"m^","meter^")
    unit=string.replace(unit,"g^","gram^")
    unit=string.replace(unit,"e^","Euro^")
    unit=string.replace(unit,"a^","Ampere^")
    unit=string.replace(unit,"cd^","candela^")
  unit=string.replace(unit,"^1","")
  result+=" "+unit
  return result

