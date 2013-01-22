#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import string, random, os, math, re, datetime
import pietlib

def addcalc(param_org):
  param_org=string.strip(param_org)
  if (param_org[:1]>="0" and param_org[:1]<="9") or (param_org[:1]=="(") or (param_org[:1]=="[") or (param_org[:1]=="-") or (param_org[:1]=="|") or (param_org[:4]=="det(")  or (param_org[:5]=="sqrt(") or (param_org[:5]=="ceil(") or (param_org[:4]=="abs(") or (param_org[:6]=="floor(") or (param_org[:4]=="exp(") or (param_org[:4]=="log(") or (param_org[:6]=="log10(") or (param_org[:5]=="acos(") or (param_org[:5]=="asin(") or (param_org[:5]=="atan(") or (param_org[:4]=="cos(") or (param_org[:4]=="sin(") or (param_org[:4]=="tan(") or (param_org[:1]=="I" and param_org[1:2]>="0" and param_org[1:2]<="9") or (param_org[:6]=="gauss("):
    param_org="calc "+param_org;
  return param_org

def unitinvertcheck(unit1,unit2):
  for i in ["1","2","3","4","5","6","7","8","9"]:
    unit1=string.replace(unit1,"^"+i,"^+"+i)
  unit1=string.replace(unit1,"^-","^")
  unit1=string.replace(unit1,"^+","^-")
  return unit1==unit2

def calcS(param):
  # Subtract and Add rule
  (error,(result,imag),param,unit,dimx,dimy)=calcD(param)
  if (error!=""):
    return (error,(result,0),param,unit,1,1)
  while ((error=="") and (param!="") and ((param[0]=="-") or (param[0]=="+"))):
    if (dimx>1 and unit[:1]==["D^1"]):
      sign=param[0]
      # date format, look if we can add anything to it
      (error,(result2,imag),param,unit2,dimx2,dimy2)=calcD(param[1:])
      if (error!=""):
        return(error,(0,0),"","",1,1)
      if (dimx2>1 and unit2[:1]==["D^1"]):
        if (sign=="+"):
          return ("Adding on dates is not allowed",(0,0),"","",1,1)
        date1=datetime.date(result[0],result[1],result[2])
        date2=datetime.date(result2[0],result2[1],result2[2])
        difference=date1-date2
        if (dimx==3):
          sec1=0
        else:
          sec1=result[3]
        if (dimx2==3):
          sec2=0
        else:
          sec2=result2[3]
        return ("",((difference.days*86400)+difference.seconds+(difference.microseconds*1e-6)+(sec1-sec2),0),param,"s^1",1,1)
      if (dimx2!=1 or dimy2!=1 or unit2!="s^1"):
        return("Can only add time to a date",(0,0),"","",1,1)
      thisdate=datetime.date(result[0],result[1],result[2])
      if (len(result)>3):
        offset=datetime.timedelta(seconds=(result2+result[3]))
        reminder=(result2+result[3])%86400
      else:
        offset=datetime.timedelta(seconds=result2)
        reminder=result2%86400
          
      if (sign=="-"):
        try:
          thisdate-=offset
          if reminder!=0:
            thisdate-=datetime.timedelta(seconds=86400)
            reminder=86400-reminder
        except:
          return("Year underflow error",(0,0),"","",1,1)
      else:
        try:
          thisdate+=offset
        except:
          return("Year overflow error",(0,0),"","",1,1)
      result[0]=thisdate.year
      result[1]=thisdate.month
      result[2]=thisdate.day
      if reminder!=0:
        if (len(result)>3):
          result[3]=reminder
        else:
          result+=[reminder]
        unit=["D^1","D^1","D^1","s^1"]
        dimx=4
        continue
      unit=["D^1","D^1","D^1"]
      dimx=3
      continue
    op=param[0]
    (error,(result2,imag),param,unit2,dimx2,dimy2)=calcD(param[1:])
    if (dimx!=dimx2) or (dimy!=dimy2):
      return("adding matrix: matrices do not have the same dimension",(0,0),"","",1,1)
    if (dimx==1) and (dimx2==1) and (dimy==1) and (dimy2==1):
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
          result+=result2
    else:
      for x in range(dimx*dimy):
        if op=="+":
          result[x]=result[x]+result2[x]
        else:
          result[x]=result[x]-result2[x]
        if unit[x]!=unit2[x]:
          unit[x]="W"
  return (error,(result,imag),param,unit,dimx,dimy)

def calcD(param):
  # Divide and Multiply rule
  (error,(result,imag),param,unit,dimx,dimy)=calcP(param)
  if (error!=""):
    return (error,(result,0),param,"",1,1)
  
  while ((error=="") and (param!="") and ((param[0]=="/") or (param[0]=="*"))):
    if (dimx>1 and unit[:1]==["D^1"]):
      return ("Multiplication and dividing not allowed on dates",(0,0),"","",1,1)
    op=param[0]
    (error,(result2,imag2),param,unit2,dimx2,dimy2)=calcP(param[1:])
    if (dimx==1) and (dimy==1) and (dimx2==1) and (dimy2==1):
      unit=unifyunits(unit,unit2,op)
      if op=="/":
        if (imag==0 and imag2==0):
          result/=result2
        else:
          newresult=((result*result2)+(imag*imag2))/((result2*result2)+(imag2*imag2))
          imag=((imag*result2)-(result*imag2))/((imag2*imag2)+(result2*result2))
          result=newresult
      else:
        newresult=(result*result2)-(imag*imag2)
        imag=(result*imag2)+(imag*result2)
        result=newresult
    else:
      #matrix multiplication
      if op=="/":
        #invert matrix is not yet supported
        if dimx2!=1 and dimy2!=1:
          return ("Matrix dividing is not supported",(0,0),"","",1,1)
        #but it is for scalars now
        newresult=[]
        for x in result:
          newresult+=[x/result2]
        newunit=[]
        for x in unit:
          newunit+=[unifyunits(x,unit2,"/")]
        return ("",(newresult,0),param,newunit,dimx,dimy)
      if (dimx==1) and (dimy==1):
        #scalar
        for x in range(dimx2):
          for y in range(dimy2):
            result2[x+(y*dimx2)]=result*result2[x+(y*dimx2)]
            unit2[x+(y*dimx2)]=unifyunits(unit,unit2[x+(y*dimx2)],"*")
        return (error,(result2,0),param,unit2,dimx2,dimy2)
      elif (dimx2==1) and (dimy2==1):
        #scalar
        for x in range(dimx):
          for y in range(dimy):
            result[x+(y*dimx)]=result2*result[x+(y*dimx)]
            unit[x+(y*dimx)]=unifyunits(unit2,unit[x+(y*dimx)],"*")
        return (error,(result,0),param,unit,dimx,dimy)
      elif (dimx==dimy2):
        newunit=[]
        newresults=[]
        newdimx=dimx2
        newdimy=dimy
        for y in range(newdimy):
          for x in range(newdimx):
            resultitem=0
            unititem=unifyunits(unit[y*dimx],unit2[x],"*")
            for t in range(dimx):
              if unititem!=unifyunits(unit[t+(y*dimx)],unit2[x+(t*dimx2)],"*"):
                unititem="W"
              resultitem+=result[t+(y*dimx)]*result2[x+(t*dimx2)]
            newresults+=[resultitem]
            newunit+=[unititem]
        if newdimx==1 and newdimy==1:
          result=newresults[0]
          unit=newunit[0]
          dimx=1
          dimy=1
        else:
          result=newresults
          unit=newunit
          unit=newunit
          dimx=newdimx
          dimy=newdimy
      else:
        return("Cannot multiply "+str(dimx)+"x"+str(dimy)+" matrix with "+str(dimx2)+"x"+str(dimy2)+" matrix",(0,0),"","",1,1)
  while ((error=="") and (param[:1]==".")):
  #vector cross product
    (error,(result2,imag),param,unit2,dimx2,dimy2)=calcP(param[1:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (dimx!=3 or dimy!=1 or dimx2!=3 or dimy2!=1) and (dimx!=1 or dimy!=3 or dimx2!=1 or dimy2!=3):
       return("Crossproduct is defined in R3 only",(0,0),"","",1,1)
    newmatrix=[result[1]*result2[2]-result[2]*result2[1],-result[0]*result2[2]+result[2]*result2[0],result[0]*result2[1]-result[1]*result2[0]]
    return("",(newmatrix,0),param,["","",""],dimx,dimy)

  return (error,(result,imag),param,unit,dimx,dimy)

def unifyunits(unit,unit2,op):
  #unify units for dividing
  if unit2=="W":
    unit="W"
  if op=="/":
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
    #unify units for multiplying
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
  return unit
#  return (error,(result,0),param,unit,dimx,dimy)

def calcP(param):
  # Power rule
  (error,(result,imag),param,unit,dimx,dimy)=calcT(param)
  if (error!=""):
    return (error,(result,0),param,unit,1,1)
  while ((error=="") and (param!="") and (param[0]=="^")):
    if (dimx!=1) or (dimy!=1):
    # matrix to a power something? not defined
      return("Cannot raise matrix to powers (yet)",(0,0),"","",1,1)
    (error,(result2,imag),param,unit2,dimx,dimy)=calcT(param[1:])
    if (dimx!=1) or (dimy!=1):
    # something to a power matrix? not defined
      return("Cannot raise things to power of matrix",(0,0),"","",1,1)
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
  return (error,(result,imag),param,unit,dimx,dimy)

def factorial(x):
    if x == 0:
        return 1
    else:
        return x * factorial(x-1)

def calcT(param):
  #rule for transposing matrices
  (error,(value,imag),param,unit,dimx,dimy)=calcM(param)
  while param[:1]=="!":
    if error!="":
      return(error,(value,0),param,unit,dimx,dimy)
    if dimx!=1 or dimy!=1:
      return("Parse error factorial expects non matrix type",(0,0),"","",1,1)
    value=factorial(value)
    param=param[1:]
  if param[:2]=="*t":
    param=param[1:]
  while param[:1]=="t":
    param=param[1:]
    if (dimx>1) or (dimy>1):
      newmatrixvalues=[]
      newmatrixunits=[]
      for x in range(dimx):
        for y in range(dimy):
          newmatrixvalues+=[value[x+(y*dimx)]]
          newmatrixunits+=[unit[x+(y*dimx)]]
      i=dimx
      dimx=dimy
      dimy=i
      value=newmatrixvalues
      unit=newmatrixunits
   
  return (error,(value,imag),param,unit,dimx,dimy)


#gaus functie
def gauss(value,unit,dimx,dimy):
  newmatrix=[]
  for y in range(dimy):
    newline=value[y*dimx:(y+1)*dimx]
    for i in range(y):
      x=0
      while x<dimx and newline[x]==0:
        x+=1
      if x<dimx:
        if newmatrix[i*dimx+x]!=0:
          factor=newline[x]/newmatrix[i*dimx+x]
          for t in range(dimx):
            newline[t]=(factor*newmatrix[i*dimx+t])-newline[t]
    
    #now insert the row at the right position
    nonzeroline=0
    while nonzeroline<dimx and newline[nonzeroline]==0:
      nonzeroline+=1
    added=0
    x=0
    while x<len(newmatrix) and added==0:
      nonzeromatrix=0
      while nonzeromatrix<dimx and newmatrix[x+nonzeromatrix]==0:
        nonzeromatrix+=1
      if nonzeromatrix>nonzeroline:
        added=1
        newmatrix=newmatrix[:x]+newline+newmatrix[x:]
      x+=dimx
    if added==0:
      newmatrix+=newline
  
  newunit=[]
  for x in range(dimx):
    thisunit=unit[x]
    for y in range(dimy):
      if thisunit!=unit[x+(y*dimx)]:
        thisunit="W"
    newunit+=[thisunit]
  unit=[]
  for y in range(dimy):
    unit+=newunit
  return(newmatrix,unit)

def det(value,unit,dim):
  if dim==1:
    return(value,unit)
  if dim==2:
    # nee het is niet efficient maar wel makkelijk om de eenheden goed te houden
    value=value[0]*value[3]-value[1]*value[2]
    newunit=unifyunits(unit[0],unit[3],"*")
    if newunit!=unifyunits(unit[1],unit[2],"*"):
      unit="W"
    else:
      unit=newunit
    return(value,unit)
  # nee, leibniz zou efficienter zijn, maar who cares...
  newvalue=0
  newunit="UNDEFINED"
  for x in range(dim):
    smallermatrixvalue=[]
    smallermatrixunit=[]
    for y in range(dim):
      if y!=x:
        smallermatrixvalue+=value[y*dim+1:(y+1)*dim]
        smallermatrixunit+=unit[y*dim+1:(y+1)*dim]
    (smallermatrixvalue,smallermatrixunit)=det(smallermatrixvalue,smallermatrixunit,dim-1)
    newvalue+=value[y*(dim)]*smallermatrixvalue
    smallermatrixunit=unifyunits(unit[y*dim],smallermatrixunit,"*")
    if newunit=="UNDEFINED":
      newunit=smallermatrixunit
    else:
      if newunit!=smallermatrixunit:
        newunit="W"
    
  return (newvalue,newunit)

def calcM(param):
  functions=[
  ("ceil", math.ceil), ("abs", math.fabs), ("floor", math.floor),
  ("exp", math.exp), ("log", math.log), ("log10", math.log10),
  ("sqrt", math.sqrt), ("acos", math.acos), ("asin", math.asin),
  ("atan", math.atan), ("cos", math.cos), ("sin", math.sin), ("tan", math.tan),
  ("cosh", math.cosh), ("sinh", math.sinh), ("tan", math.tanh)]
  for (funcname,func) in functions:
    funcname+='('
    if param[:len(funcname)]==funcname:
      (error,(value,imag),param,unit,dimx,dimy)=calcS(param[len(funcname):])
      if (dimx!=1) or (dimy!=1):
        return("Function does not work on a matrix",(0,0),"","",1,1)
      if (error!=""):
        return(error,(0,0),"","",1,1)
      if (param[:1]!=")"):
        if error=="":
          return("Missing )",(0,0),"","",1,1)
        else:
          return(error,(0,0),"","",1,1)
      chars=re.compile('[a-z]')
      if chars.match(param[1:]):
        (error,(result,imag),param,unit,dimx,dimy)=calcM(param[1:])
        return (error,(func.__call__(value)*result,0),param,"",1,1)

      return(error,(func.__call__(value),0),param[1:],"",1,1)
# special matrix
  if (param[:1]=="i" and param[1:2]>="0" and  param[1:2]<="9"):
    (error,(value,imag),param,unit,dimx,dimy)=calcM(param[1:])
    if error!="" and error!="t unknown":
      return (error,(0,0),"","",1,1)
    if dimx!=1 or dimy!=1 or value!=math.floor(value):
      return ("identity matrix must have simply number",(0,0),"","",1,1)
    value=int(value)
    matrixvalue=[]
    matrixunit=[]
    for x in range(value):
      matrixline=[]
      unitline=[]
      for y in range(value):
        unitline+=[""]
        if x==y:
          matrixline+=[1]
        else:
          matrixline+=[0]
      matrixvalue+=matrixline
      matrixunit+=unitline
    if value==1:
      return("",(matrixvalue[0],0),param,matrixunit[0],1,1)
    return("",(matrixvalue,0),param,matrixunit,value,value)

# date function
  if param[:10]=="dayofweek(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[10:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (dimx<3 or unit[:1]!=["D^1"]):
      return("DayOfWeek function works on dates only",(0,0),"","",1,1)
    if (param[:1]!=")"):
      return("Missing )",(0,0),"","",1,1)
    thisday=datetime.date(value[0],value[1],value[2])
    return("",(thisday.weekday(),0),param[1:],"DW^1",1,1)
  if param[:8]=="weekday(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[8:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (dimx<3 or unit[:1]!=["D^1"]):
      return("DayOfWeek function works on dates only",(0,0),"","",1,1)
    if (param[:1]!=")"):
      return("Missing )",(0,0),"","",1,1)
    thisday=datetime.date(value[0],value[1],value[2])
    return("",(thisday.weekday(),0),param[1:],"DW^1",1,1)
  if param[:4]=="dow(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[4:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (dimx<3 or unit[:1]!=["D^1"]):
      return("DayOfWeek function works on dates only",(0,0),"","",1,1)
    if (param[:1]!=")"):
      return("Missing )",(0,0),"","",1,1)
    thisday=datetime.date(value[0],value[1],value[2])
    return("",(thisday.weekday(),0),param[1:],"DW^1",1,1)
  if param[:4]=="day(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[4:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (dimx<3 or unit[:1]!=["D^1"]):
      return("DayOfWeek function works on dates only",(0,0),"","",1,1)
    if (param[:1]!=")"):
      return("Missing )",(0,0),"","",1,1)
    thisday=datetime.date(value[0],value[1],value[2])
    return("",(thisday.weekday(),0),param[1:],"DW^1",1,1)
  if param[:8]=="weekdag(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[8:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (dimx<3 or unit[:1]!=["D^1"]):
      return("DayOfWeek function works on dates only",(0,0),"","",1,1)
    if (param[:1]!=")"):
      return("Missing )",(0,0),"","",1,1)
    thisday=datetime.date(value[0],value[1],value[2])
    return("",(thisday.weekday()+7,0),param[1:],"DW^1",1,1)
  if param[:4]=="dag(":
    language="nl"
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[4:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (dimx<3 or unit[:1]!=["D^1"]):
      return("DayOfWeek function works on dates only",(0,0),"","",1,1)
    if (param[:1]!=")"):
      return("Missing )",(0,0),"","",1,1)
    thisday=datetime.date(value[0],value[1],value[2])
    return("",(thisday.weekday()+7,0),param[1:],"DW^1",1,1)

# matrix functions
  if param[:4]=="det(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[4:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (param[:1]!=")"):
      return("Missing )",(0,0),"","",1,1)

    if dimx!=dimy:
      return("det() expects a square matrix",(0,0),"","",1,1)
    (value,unit)=det(value,unit,dimx)
    return (error,(value,0),param[1:],unit,1,1)

  if param[:6]=="gauss(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[6:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (param[:1]!=")"):
      if error=="":
        return("missing )",(0,0),"","",1,1)
      else:
        return(error,(0,0),"","",1,1)
    (value,unit)=gauss(value,unit,dimx,dimy)
    return (error,(value,0),param[1:],unit,dimx,dimy)
  if param[:4]=="len(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[4:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (param[:1]!=")"):
      return("missing )",(0,0),"","",1,1)
    if (dimx!=1) and (dimy!=1):
      return("length only works on vectors",(0,0),"","",1,1)
    result=0
    for i in value:
      result+=i*i
    return("",(math.sqrt(result),0),param[1:],"",1,1)
  if param[:1]=="|":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[1:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (param[:1]!="|"):
      return("missing close |",(0,0),"","",1,1)
    if (dimx!=1) and (dimy!=1):
      return("length only works on vectors",(0,0),"","",1,1)
    if (dimx==1) and (dimy==1):
      return ("",(value,0),param[1:],unit,1,1)
    result=0
    for i in value:
      result+=i*i
    return("",(math.sqrt(result),0),param[1:],"",1,1)
  if param[:5]=="rank(":
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[5:])
    if error!="":
      return(error,(0,0),"","",1,1)
    if (param[:1]!=")"):
      if error=="":
        return("missing )",(0,0),"","",1,1)
      else:
        return(error,(0,0),"","",1,1)
    (value,unit)=gauss(value,unit,dimx,dimy)
    rank=0
    for y in range(dimy):
      x=0
      while x<dimx:
        if value[x+(y*dimx)]!=0:
          rank+=1
          x=dimx
        else:
          x+=1
    return (error,(rank,0),param[1:],"",1,1)

  #date and time format
  date=0
  digits=re.compile('[0-9]+\-?'+months+'\-?[0-9]+')
  digitscheck = digits.match(param)
  if digitscheck:
    date=1
    datestring=digitscheck.group()
    day=int(re.compile('[0-9]+').match(datestring).group())
    month=re.compile(months).search(param).group()
    i=string.find(param,month)
    year=int(re.compile('[0-9]+').search(datestring[i:]).group())
    month=monthmap[month]
    try:
      datetime.date(year,month,day)
    except:
      return("Invalide date type",(0,0),"","",1,1)
    param=param[digitscheck.end():]
    if (param[:1]!="_" or param[:3]=="_in"):
      return("",([year,month,day],0),param,["D^1","D^1","D^1"],3,1)
    param=param[1:]
  complexnumber=re.compile('-?((0x[0-9a-f]+(\.[0-9a-f]+)?)|([0-9]+(\.[0-9]+)?))(\+|-)((0x[0-9a-f]+(\.[0-9a-f]+)?)|([0-9]+(\.[0-9]+)?))?i')
  complexcheck=complexnumber.match(param)
  if complexcheck:
    l=len(complexcheck.group())
    if ((param[l:l+1]=="") or (param[l:l+1]=="_") or (param[l:l+1]=="*") or (param[l:l+1]=="/") or (param[l:l+1]=="+") or (param[l:l+1]=="-") or (param[l:l+1]=="^")):
      sign=1
      if param[:1]=="-":
        sign=-1
        param=param[1:]
      #if I is follwed by a number it's the identity matrix
      realpart=re.match('((0x[0-9a-f]+(\.[0-9a-f]+)?)|([0-9]+(\.[0-9]+)?))',param).group()
      (_,(realvalue,_),_,_,_,_)=calcP(realpart)
      realvalue*=sign
      param=param[len(realpart):]
      sign=1
      if param[:1]=="-":
        sign=-1
      param=param[1:]
      if re.match('((0x[0-9a-f]+(\.[0-9a-f]+)?)|([0-9]+(\.[0-9]+)?))',param):
        complexpart=re.match('((0x[0-9a-f]+(\.[0-9a-f]+)?)|([0-9]+(\.[0-9]+)?))',param).group()
        (_,(complexvalue,_),_,_,_,_)=calcP(complexpart)
      else:
        complexvalue=1
        complexpart=""
      complexvalue*=sign
      param=param[len(complexpart)+1:]
      if param[:1]=="_":
        param=param[1:]
      return ("",(realvalue,complexvalue),param,"",1,1)
  complexnumber=re.compile('-?((0x[0-9a-f]+(\.[0-9a-f]+)?)|([0-9]+(\.[0-9]+)?))?i')
  complexcheck=complexnumber.match(param)
  if complexcheck:
    l=len(complexcheck.group())
    if ((param[l:l+1]=="") or (param[l:l+1]=="_") or (param[l:l+1]=="*") or (param[l:l+1]=="/") or (param[l:l+1]=="+") or (param[l:l+1]=="-") or (param[l:l+1]=="^")):
      sign=1
      if param[:1]=="-":
        sign=-1
        param=param[1:]
      #if I is follwed by a number it's the identity matrix
      if re.match('((0x[0-9a-f]+(\.[0-9a-f]+)?)|([0-9]+(\.[0-9]+)?))',param):
        complexpart=re.match('((0x[0-9a-f]+(\.[0-9a-f]+)?)|([0-9]+(\.[0-9]+)?))',param).group()
        (_,(complexvalue,_),_,_,_,_)=calcP(complexpart)
      else:
        complexvalue=1
        complexpart=""
      complexvalue*=sign
      param=param[len(complexpart)+1:]
      if param[:1]=="_":
        param=param[1:]
      print param
      return ("",(0,complexvalue),param,"",1,1)
  digits=re.compile('[0-9]+\:[0-9]+(\:[0-9]+(\.[0-9]+)?)?') # time format
  digitscheck= digits.match(param)
  if digitscheck:
    value=0.0
    # in time format... parse that
    timestring=digitscheck.group()
    i1=string.find(timestring,":")
    value+=int(timestring[:i1])*60
    i2=string.find(timestring,":",i1+1)
    if (i2>0):
      value+=int(timestring[i1+1:i2])
      value*=60
      i1=i2
      value+=float(timestring[i1+1:])
    else:
      value+=float(timestring[i1+1:])
      value*=60      
    if (date==1):
      return("",([year,month,day,value],0),param[len(timestring):],["D^1","D^1","D^1","s^1"],4,1)
    return("",(value,0),param[len(timestring):],"s^1",1,1)

# hex check
  if re.match("(\-)?0x([0-9]|[a-f])+",param):
    digits=re.match("(\-)?0x([0-9]|[a-f])+",param).group()
    param=param[len(digits):]
    if param[:1]!=".":
      chars=re.compile('[a-z]|\(|[0-9]|\$')
      if chars.match(param):
        (error,(value2,imag),left,unit,dimx,dimy)=calcP(param)
        return (error,(int(digits,16)*value2,0),left,unit,1,1)

      return("",(int(digits,16),0),param,"",1,1)
    value=1.0*int(digits,16)
    if re.match("([0-9]|[a-f])+",param[1:]):
      digits=re.match("([0-9]|[a-f])+",param[1:]).group()
      value+=(int(digits,16))/math.pow(16,len(digits))
      param=param[len(digits)+1:]
      chars=re.compile('[a-z]|\(|[0-9]|\$')
      if chars.match(param):
        (error,(value2,imag),left,unit,dimx,dimy)=calcP(param)
        return (error,(value*value2,0),left,unit,1,1)
      return ("",(value,0),param,"",1,1)
    else:
      return("Reached end of line, could not parse: "+param,0,"","",1,1)
      
  digits=re.compile('(\-)?[0-9]+(\.[0-9]+)?((e\+[0-9]+)|(e\-[0-9]+)|(e[0-9]+))?')
  digitscheck= digits.match(param)
  if digitscheck:
    value=float(digitscheck.group())
    param=string.strip(param[digitscheck.end():])
    chars=re.compile('[a-z]|\(|[0-9]|\$')
    if chars.match(param):
      (error,(value2,imag),left,unit,dimx,dimy)=calcP(param)
      if (dimx==1 and dimy==1):
        return (error,(value*value2,0),left,unit,1,1)
      return(error,(value,0),"*"+param,"",1,1)
    return ("",(value,0),param,"",1,1)
#matrix
  if (param[:1]=="["):
    x1=param[1:].find("]")
    x2=param[1:].find("[")
    if x1 < 0:
      return("Missing ]",(0,0),"","",1,1)
    if ((x2>0) and (x1<x2)) or (x2<0):
      matrixelements=param[1:x1+1].split(",")
      dimx=len(matrixelements)
      matrixvalues=[]
      matrixunits=[]
      error=""
      for matrixel in matrixelements:
        (error1,(value,imag),left,unit,_,_)=calcS(matrixel)
        if (error1!="") or (left!=""):
          error="Error reading matrix elements"
        matrixvalues+=[value]
        matrixunits+=[unit]
      if dimx==1:
        if param[x1+2:x1+3]=="t":
          x1+=1
        return(error,(matrixvalues[0],0),param[x1+2:],matrixunits[0],1,1)
      return (error,(matrixvalues,0),param[x1+2:],matrixunits,dimx,1)
    if (x2>=0) and (x2<x1):
      dimx=0
      error=""
      matrixvalues=[]
      matrixunits=[]
      x2=param[1:].find("]]")
      if x2 < 0:
        return ("Error reading matrix elements",(0,0),"","",1,1)
      rows=param[2:x2+1].split("],[")
      dimy=len(rows)
      for row in rows:
        matrixelements=row.split(",")
        if dimx==0:
          dimx=len(matrixelements)
        elif dimx!=len(matrixelements):
          return("Error reading matrix elements",(0,0),"","",1,1)
        for matrixel in matrixelements:
          (error1,(value,imag),left,unit,_,_)=calcS(matrixel)
          if (error1!="") or (left!=""):
            error=error1
          matrixvalues+=[value]
          matrixunits+=[unit]
      if dimx==1 and dimy==1:
        if param[x2+3:x2+4]=="t":
          x2+=1
        return(error,(matrixvalues[0],0),param[x2+3:],matrixunits[0],1,1)
      return (error,(matrixvalues,0),param[x2+3:],matrixunits,dimx,dimy)
      
    return ("Matrix format error",(0,0),"","",1,1)

  if (param[:1]=="("):
    (error,(value,imag),param,unit,dimx,dimy)=calcS(param[1:])
    if param[:1]!=")":
      if error=="":
        return("missing )",(0,0),"","",1,1)
      else:
        return(error,(0,0),"","",1,1)
    chars=re.compile('[a-z]|\(|[0-9]|\$')
    if chars.match(param[1:]):
      return(error,(value,0),"*"+param[1:],unit,dimx,dimy)
    return(error,(value,0),param[1:],unit,dimx,dimy)

  #2 based prefixes
  prefix=[("kilob",1024), ("megab",1048576), ("gigab",1073741824),
  ("terrab",1099511627776), ("petab",1125899906842624),
  ("exab",1152921504606846976), ("zettab",1180591620717411303424),
  ("yottab",1208925819614629174706176), ("millib",1.0/1024),
  ("microb",1.0/1048576), ("nanob",1.0/1073741824),
  ("picob",1.0/1099511627776), ("femtob",1.0/1125899906842624),
  ("attob",1.0/1152921504606846976), ("zeptob",1.0/1180591620717411303424),
  ("yoctob",1.0/1208925819614629174706176)]

  for(thisprefix,power) in prefix:
    if param[:len(thisprefix)]==thisprefix:
      (error_p,(value_p,imag),param_p,unit_p,dimx_p,dimy_p)=calcM(param[len(thisprefix)-1:])
      if (unit_p[:2]=="b^"):
        return (error_p,(value_p*power,0),param_p,unit_p,1,1)


  #prefixes
  prefix=[("yotta",1e24), ("zetta",1e21), ("exa",1e18), ("peta",1e15),
  ("tera",1e12), ("giga",1e9), ("mega",1e6), ("kilo",1e3), ("hecto",1e2),
  ("deca",1e1), ("deci",1e-1), ("centi",1e-2), ("milli",1e-3), ("micro",1e-6),
  ("nano",1e-9), ("pico",1e-12), ("femto",1e-15), ("atto",1e-18),
  ("zepto",1e-21), ("yocto",1e-24)]
  for(thisprefix,power) in prefix:
    if param[:len(thisprefix)]==thisprefix:
      (error,(value,imag),param,unit,dimx,dimy)=calcM(param[len(thisprefix):])
      return (error,(value*power,0),param,unit,1,1)

  for (thisunit,convertrate,siunit) in units:
    if param[:len(thisunit)]==thisunit:
      #check for plural
      endpos=len(thisunit)
      if param[endpos:endpos+1]=="s":
        endpos+=1
      if param[endpos:endpos+2]=="es":
        endpos+=1
      return("",(convertrate,0),param[endpos:],siunit,1,1)

  #check for money currency
  money=[("euro","EUR"), ("dollar","USD"), ("pond","GBP"), ("gbp","GBP"),
  ("britsepond","GBP"), ("britishpound","GBP"), ("eur","EUR"), ("usd","usd"),
  ("gbp","GBP"), ("a$","AUD"), ("$a","AUD"), ("aud","AUD"),
  ("$sg","SGD"), # singaporese dollar
  ("cur_bzd","BZD"),
  ("colones", "CRC"), ("colon", "CRC"),
  ("australischedollar","AUD"), ("$c","CAD"), ("c$","CAD"),
  ("canadiandollar","CAD"), ("canadeesedollar","CAD"), ("cad","CAD"),
  ("ukp","GBP"), ("yen","JPY"), ("jpy","JPY"), ("$nz","NZD"), ("nz$","NZD"),
  ("newzealanddollar","NZD"), ("nieuwzeeuwsedollar","NZD"),
  ("nieuwzeelandsedollar","NZD"), ("nzd","NZD"), ("chf","CHF"),
  ("zwitsersefrank","CHF"), ("switzerlandfranc","CHF"), ("swissfranc","CHF"),
  ("franc","CHF"), ("$","USD"), ("dkk","DKK"), ("deensekronen","DKK"),
  ("deensekroon","DKK"), ("danishkronor","DKK"), ("nok","NOK"),
  ("noorsekronen","NOK"), ("noorsekroon","NOK"), ("norwegiankronor","NOK"),
  ("noorweegsekronen","NOK"), ("noorweegsekroon","NOK"), ("sek","SEK"),
  ("zweedsekronen","SEK"), ("zweedsekroon","SEK"), ("swedishkroner","SEK"),
  ("hkd","HKD"), ("hongkongdollar","HKD"), ("cur_hkd","HKD"),
  ("yuan","CNY"), ("cny","CNY"), ("cedi","GHC"), ("turkselire", "TRL")]

  for (currency,name) in money:
    if  param[:len(currency)]==currency:
      endpos=len(currency)
      if param[endpos:endpos+1]=="s":
        endpos+=1
      if name=="EUR":
        return("",(1,0),param[endpos:],"$^1",1,1)
      page = pietlib.get_url('http://www.xe.com/ucc/convert.cgi', postdata={
        'Amount':1, 'From':'EUR', 'To':name})
      result = re.subn('<[^>]*>', '', page)[0].replace('&nbsp;', ' ')
      val = float(re.findall("1 EUR = ([0-9.]+)", result)[0])
      return("",(1/val,0),param[endpos:],"$^1",1,1)

  unit=""

  if param[:2]=="pi":
    chars=re.compile('[a-z]')
    if chars.match(param[2:]):
      (error,(result,imag),param,unit,dimx,dimy)=calcM(param[2:])
      return (error,(3.1415926535897932384*result,0),param,unit,1,1)

    return ("",(3.14159265358979323846,0),param[2:],"",1,1)

  if param[:1]=="e":
    chars=re.compile('[a-z]')
    if chars.match(param[1:]):
      (error,(result,imag),param,unit,dimx,dimy)=calcM(param[1:])
      return (error,(2.7182818284590452353602874713*result,0),param,unit,1,1)
    return ("",(2.7182818284590452353602874713,0),param[1:],"",1,1)

  if param[:5]=="dozen":
    chars=re.compile('[a-z]')
    if chars.match(param[5:]):
      (error,(result,imag),param,unit,dimx,dimy)=calcM(param[5:])
      return (error,(12*result,0),param,unit,1,1)
    return ("",(12,0),param[5:],unit,1,1)

  if param[:6]=="dozijn":
    chars=re.compile('[a-z]')
    if chars.match(param[6:]):
      (error,(result,imag),param,unit,dimx,dimy)=calcM(param[6:])
      return (error,(12*result,0),param,unit,1,1)

    return ("",(12,0),param[6:],unit,1,1)

  if param[:5]=="gross":
    chars=re.compile('[a-z]')
    if chars.match(param[5:]):
      (error,(result,imag),param,unit,dimx,dimy)=calcM(param[5:])
      return (error,(144*result,0),param,unit,1,1)

    return ("",(144,0),param[5:],unit,1,1)

  nametype=re.compile('[a-z]*')
  nametype=nametype.match(param)
  nametype=nametype.group()
  if nametype=="":
    return ("Parse Error",(1,0),"","",1,1)
  return (nametype+" unknown",(1,0),param,unit,1,1)

def supercalc(toparse):
  if string.find(toparse.lower()," celcius")>0:
    return "/nick Anders_Celsius; Heet geen Celcius!;/nick piet"
  if toparse[:4]=="help":
    x1=toparse[4:].find(" ")
    if x1<0:
      return "help available on arithmetic, convert, currency, matrix, units"
    toparse=toparse[x1+5:]
    if toparse=="arithmetic":
      return "supported operators: * / - + ^\nsupported functions: abs,ceil,exp,floor,log,log10,sqrt\nsupported goniometric functions acos,asin,atan,cos,sin,tan,cosh,sinh,tanh\nsyntax <expression> <operator> <expression> or <function>(<expression>) for example: 1+2, ceil(sin(3))"
    if toparse=="currency":
      return "syntax: <value> <currency> for example 2.5 euro\ncurrencies are known my their full name, their 3 letter abbreviation, or a shorthand ($a for australian dollar)\nknown currencies: (American, Australian, Canadian, New Zealand)dollar, Britisch Pound, Euro, Swiss Franc, Japanese Yen\nconversion example: 1 euro in yen"
    if toparse=="convert":
      return "converts one unit in another\nsyntax: <expression> <unit> in <expression> <unit>\nfor example: 1 feet*1 acre in liter\nconversion only supported on simple expression i.e. not on matrices"
    if toparse=="matrix":
      return "syntax: [[<e>,<e>,....,<e>],[<e>,<e>,....,<e>],....,[<e>,<e>,....,<e>]]\nfor example [[1,2,3],[4,5,6],[7,8,9]] is a 3x3 matrix\nspecial matrix: I<n> (for example I7) indicates the identity matrix of nxn\nsupported matrix suffix: T (transposes the matrix [[1],[2],[3]]T = [1,2,3]T)\nsupported matrix operators: * - +\nsupported matrix functions: det gauss rank"
    if toparse=="units":
      return "each expression is allowed to be followed by a unit of physics, most units are supported and are by default calculated back to SI units\nsyntax: <expression> <unit>\nfor example: 10 mile\nunits can be prefixed by the SI prefixes ranging from yotta till yocto in steps of 1e3 and kilo till milli in steps of 10\nfor example: 1 nanometer"
    return "topic not found"


  if toparse[:4]=="uit ":
    toparse=toparse[4:];
  elif toparse[len(toparse)-4:]==" uit":
    toparse=toparse[:len(toparse)-4];
  toparse=string.lower(string.strip(toparse))
  toparse=string.replace(toparse," aud"," $a")
  toparse=string.replace(toparse,"$hk"," cur_hkd")
  toparse=string.replace(toparse,"hk$"," cur_hkd")
  toparse=string.replace(toparse,"gbp"," ukp")
  toparse=string.replace(toparse," a$"," $a")
  toparse=string.replace(toparse," b$"," cur_bzd")
  toparse=string.replace(toparse," $b"," cur_bzd")
  toparse=string.replace(toparse," in ","_in_")
  toparse=string.replace(toparse,"\\bi ","i_")

  # if time after date change space to _ so it doesn't get lost
  digits=re.compile('[0-9]+(\-|\ )?'+months+'(\-|\ )?[0-9]+(\ )+[0-9]+\:')
  digitscheck= digits.search(toparse)
  while digitscheck:
    i=string.rfind(toparse[:digitscheck.end()-1]," ")
    toparse=toparse[:i]+"_"+toparse[i+1:]
    digitscheck= digits.search(toparse)

  toparse=string.replace(toparse," per ","/")
  toparse=string.replace(toparse," ","")
  toparse=string.replace(toparse,"kilo)","kg)")
  toparse=string.replace(toparse,"kilo_","kg_")
  if toparse[len(toparse)-4:]=="kilo":
    toparse=toparse[:len(toparse)-4]+"kg"
  (error,(result,imag),left,unit,dimx,dimy)= calcS(toparse)
  if dimx==1 and dimy==1:
    if left[:7]=="celsius":
      left=left[7:]
      result+=273.15
    elif left[:6]=="kelvin":
      left=left[6:]
    elif left[:10]=="fahrenheit":
      left=left[10:]
      result=(result+459.67)*(5.0/9.0)
    elif (error!=""):
      return error
    if left[:11]=="_in_celsius":
      result-=273.15
      left=left[11:]
    elif left[:14]=="_in_fahrenheit":
      result=((result*9)/5)-459.67
      left=left[14:]
    elif left[:10]=="_in_kelvin":
      left=left[10:]
    if left[:4]=="_in_":
      backupunit=left[4:]
      (error,(result2,imag),left,unit2,dimx,dimy)=calcS(left[4:])
      if (error!=""):
        return error
      if (left!=""):
        return "Reached end of line, could not parse: "+left
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
      return "Reached end of line, could not parse: "+left
    if unit=="s^1":
      if result < 0:
        pref="-"
        result=-result
      else:
        pref=""
      s100=str(result)
      if string.find(s100,"e-")>0:
        return pref+s100+" sec"
      if string.find(s100,"e")>0:
        s100=""
      else:
        s100=s100[string.find(s100,".")+1:]
      hours=math.floor(result/3600)
      result-=hours*3600
      hours=string.replace(str(hours),".0","")
      min=math.floor(result/60)
      result-=min*60
      min=string.replace(str(min),".0","")
      sec=math.floor(result)
      sec=string.replace(str(sec),".0","")
      if s100=="0":
        s100=""
      else:
        s100="."+s100;
      result=""
      if (hours!="0"):
        if len(min)==1:
          min="0"+min
        if len(sec)==1:
          sec="0"+sec
        return pref+hours+":"+min+":"+sec+s100    
      if (min!="0"):
        if len(sec)==1:
          sec="0"+sec
        if len(min)==1:
          min="0"+min
        return pref+"00:"+min+":"+sec+s100        
      else:
        return pref+sec+s100+" sec"
    result=str(result)
    imag=str(imag)
    if (string.find(unit,"DW^")>=0 and unit!="DW^1"):
      return "Operations on days of week are not allowed"
    if unit=="DW^1":
      try:
        return daysofweek[int(result)]
      except:
        return "Operations on days of week are not allowed"

    if result[len(result)-2:]==".0":
      result=result[:len(result)-2]
    if imag[len(imag)-2:]==".0":
      imag=imag[:len(imag)-2]
    if unit=="W":
      unit=random.choice(["Quantum fluctuations","Random distortions","Hyper Wave-entanglements","Chrono particle inductions","Parallel Chi","meta Universe inhibitors","Semi Nuclear Helices","Thaume bubbles"])
    else:
      unit=string.replace(unit,"s^","sec^")
      unit=string.replace(unit,"m^","meter^")
      unit=string.replace(unit,"g^","gram^")
      unit=string.replace(unit,"$^","Euro^")
      unit=string.replace(unit,"a^","Ampere^")
      unit=string.replace(unit,"b^","byte^")
      unit=string.replace(unit,"cd^","candela^")
    unit=string.replace(unit,"^1","")
    if imag!="0":
      if result=="0":
        result=""
      if imag[:1]=="-":
        result+=imag+"i"
      else:
        if result!="":
          result+="+"+imag+"i"
        else:
          result=imag+"i"
          if imag=="1":
             result="i"
    result+=" "+unit
    result=string.replace(result,"+1i","+i")
    result=string.replace(result,"-1i","-i")
    return result
  else:
    if (unit[0]=="D^1"):
#Date format
      if left!="":
        return "Reached end of line, could not parse: "+left
      try:
        reply=str(result[2])+" "+selectmonth[result[1]]+" "+str(result[0])
      except:
        return "Year underflow error"
      if (len(result)>3):
        result=result[3]
        s100=str(result)
        if string.find(s100,"e-")>0:
          return s100+" sec"
        if string.find(s100,"e")>0:
          s100=""
        else:
          s100=s100[string.find(s100,".")+1:]
        hours=math.floor(result/3600)
        result-=hours*3600
        hours=string.replace(str(hours),".0","")
        min=math.floor(result/60)
        result-=min*60
        min=string.replace(str(min),".0","")
        sec=math.floor(result)
        sec=string.replace(str(sec),".0","")
        if s100=="0":
          s100=""
        else:
          s100="."+s100;
        result=""
        if (hours!="0"):
          if len(min)==1:
            min="0"+min
          if len(sec)==1:
            sec="0"+sec
          return reply+" "+hours+":"+min+":"+sec+s100    
        if (min!="0"):
          if len(sec)==1:
            sec="0"+sec
          if len(min)==1:
            min="0"+min
          return reply+" 0:"+min+":"+sec+s100        
        else:
          if (len(sec)<2):
            return reply+" 0:00:0"+sec+s100
          return reply+" 0:00:"+sec+s100

      return reply
#Matrix format
    if left!="":
      return "Reached end of line, could not parse: "+left
    lens = []
    for x in range(dimx):
      maxlen=0
      for y in range(dimy):
        if unit[x+(y*dimx)]=="W":
          unit[x+(y*dimx)]="Weird"
        else:
          unit[x+(y*dimx)]=string.replace(unit[x+(y*dimx)],"s^","sec^")
          unit[x+(y*dimx)]=string.replace(unit[x+(y*dimx)],"m^","meter^")
          unit[x+(y*dimx)]=string.replace(unit[x+(y*dimx)],"g^","gram^")
          unit[x+(y*dimx)]=string.replace(unit[x+(y*dimx)],"$^","Euro^")
          unit[x+(y*dimx)]=string.replace(unit[x+(y*dimx)],"a^","Ampere^")
          unit[x+(y*dimx)]=string.replace(unit[x+(y*dimx)],"b^","byte^")
          unit[x+(y*dimx)]=string.replace(unit[x+(y*dimx)],"cd^","candela^")
          unit[x+(y*dimx)]=string.replace(unit[x+(y*dimx)],"^1","")
        if (len((str(result[x+(y*dimx)])+" ").replace(".0 "," "))-1+len(unit[x+(y*dimx)]) > maxlen):
          maxlen=len((str(result[x+(y*dimx)])+" ").replace(".0 "," "))-1+len(unit[x+(y*dimx)])

      lens+=[maxlen+2]
    returnline=""
    for y in range(dimy):
      returnline+="[ "
      for x in range(dimx):
        item=str(result[x+(y*dimx)])
        item+=" "+unit[x+(y*dimx)]
        item=item.replace(".0 "," ").ljust(lens[x])
        returnline+=item
      returnline+="]\n"
    return returnline.strip()


#SI length
global units
units=[("meter",1.0,"m^1")]

#SI weight
  
units+=[("g",1.0,"g^1"),("gram",1.0,"g^1"),("ton",1e+6,"g^1")]

# volume

units+=[("liter",1e-3,"m^3")]

#airspeed

units+=[("mach",340.277777777,"m^1*s^-1")]

#tijd

units+=[("seconde",1.0,"s^1"),("second",1.0,"s^1"),("sec",1.0,"s^1"),("minuut",6.0e+1,"s^1"),("minuten",6.0e+1,"s^1"),("uur",3.6e+3,"s^1"),("uren",3.6e+3,"s^1"),("dag",8.64e+4,"s^1"),("dagen",8.64e+4,"s^1"),("maand",2.6298e+6,"s^1"),("maanden",2.6298e+6,"s^1"),("jaar",3.15576e+7,"s^1"),("jaren",3.15576e+7,"s^1"),("eeuw",3.15576e+9,"s^1"),("eeuwen",3.15576e+9,"s^1")]

#time

units+=[("minute",6.0e+1,"s^1"),("hour",3.6e+3,"s^1"),("day",8.64e+4,"s^1"),("week",6.048e+5,"s^1"),("weken",6.048e+5,"s^1"),("fortnight",1.2096e+6,"s^1"),("month",2.6298e+6,"s^1"),("year",3.15576e+7,"s^1"),("lustrum",1.57788e+8,"s^1"),("lustra",1.15576e+8,"s^1"),("decade",3.15576e+8,"s^1"),("century",3.15576e+9,"s^1"),("centuries",3.15576e+9,"s^1"),("millenium",3.15576e+10,"s^1"),("millenia",3.15576e+10,"s^1")]

#pressure
units+=[("bar",1.0e+8,"g^1*m^-1*s^-2"),("psi",6.8947529e+6,"g^1*m^-1*s^-2"),("barye",1.0e+2,"g^1*m^-1*s^-2"),("atmosphere",1.01325e+8,"g^1*m^-1*s^-2")]

#force
 
units+=[("newton",1.0e+3,"g^1*m^1*s^-2"),("dyne",1.0e-2,"g^1*m^1*s^-2"),("pascal",1.0e+3,"g^1*m^-1*s^-2")]

#degree/rad

units+=[("degree",0.01745329251994329,"r^1"),("graad",0.01745329251994329,"r^1"),("graden",0.017453292519943299,"r^1"),("radian",1,"r^1"),("rad",1,"r^1")]

#area

units+=[("acre",4.0468564224e+3,"m^2"),("are",1.0e+2,"m^2"),("hectare",1.0e+2,"m^2"),("rood",1.011714105e+3,"m^2")]

#electricity

units+=[("volt",1.0e+3,"a^-1*g^1*m^2*s^-3"),("ampere",1.0,"a^1"),("a",1.0,"a^1"),("coulomb",1.0,"a^1*s^1"),("ohm",1.0e+3,"g^1*m^2*s^-3*a^-2"),("farad",1.0e-3,"a^2*g^-1*m^-2*s^4"),("tesla",1.0e+3,"a^-1*g^1*s^-2"),("weber",1.0e+3,"a^-1*g^1*m^2*s^-2"),("henry",1.0e+3,"a^-2*g^1*m^2*s^-2")] 

#energy
units+=[("joule",1.0e+3,"g^1*m^2*s^-2"),("calorie",4.184e+3,"g^1*m^2*s^-2"),("watt",1.0e+3,"g^1*m^2*s^-3")]
   
# imperial volume
units+=[("gallon",3.785411784e-3,"m^3"),("usgallon",3.785411784e-3,"m^3"),("fluidgallon",3.785411784e-3,"m^3"),("drygallon",4.4048428032e-3,"m^3"),("imperialgallon",4.54609e-3,"m^3"),("fluidounce",2.84130625e-5,"m^3"),("oz",2.84130625e-5,"m^3"),("fl.oz",2.84130625e-5,"m^3"),("gill",1.420653125e-4,"m^3"),("schooner",4.25e-4,"m^3"),("pint",5.6826125e-4,"m^3"),("peck",9.09218e-3,"m^3"),("kenning",1.818436e-2,"m^3"),("bucket",1.818436e-2,"m^3"),("bushel",3.636872e-2,"m^3"),("strike",7.273744e-2,"m^3"),("quarter",0.29094976,"m^3"),("pail",0.2909497,"m^3"),("chaldron",1.16379904,"m^3"),("last",2.9094976,"m^3"),("firkin",4.091481e-2,"m^3"),("kilderkin",8.182962e-2,"m^3"),("barrel",0.158987294928,"m^3"),("hogshead",0.24548886,"m^3")]

# imperial length

units+=[("inch",2.54e-2,"m^1"),("foot",3.048e-1,"m^1"),("feet",3.048e-1,"m^1"),("yard",9.144e-1,"m^1"),("rod",5.0292,"m^1"),("pole",5.0292,"m^1"),("perch",5.0292,"m^1"),("chain",20.1168,"m^1"),("furlong",2.01168e+2,"m^1"),("mile",1.609344e+3,"m^1"),("mijl",1.609344e+3,"m^1"),("mijlen",1.609344e+3,"m^1"),("league",4.828032e+3,"m^1"),("nauticalmile",1.852e+3,"m^1"),("zeemijl",1.852e+3,"m^1"),("zeemijlen",1.852e+3,"m^1")]

# imperial speed

units+=[("knot",0.514444444444,"m^1*s^-1"),("knoop",0.514444444444,"m^1*s^-1"),("knopen",0.514444444444,"m^1*s^-1")]

# Herz
units+=[("herz",1.0,"s^-1"),("hz",1.0,"s^-1")]

# light
 
units+=[("candela",1.0,"cd^1"),("cd",1.0,"cd^1"),("lumen",1.0,"cd^1"),("lux",1.0,"cd^1*m^-2"),("iluminance",1.0,"cd^1*m^-2")]

#information
units+=[("byte",1.0,"b^1"),("b",1.0,"b^1"),("bit",0.125,"b^1"),("mbit",131072,"b^1")]

#information 2-power-prefixes
units+=[("kb",1024,"b^1"),("mb",1048576,"b^1"),("gb",1073741824,"b^1"),("tb",1099511627776,"b^1"),("pb",1125899906842624,"b^1"),("eb",1152921504606846976,"b^1"),("zb",1180591620717411303424,"b^1"),("yb",1208925819614629174706176,"b^1")]

# galaxy 

units+=[("parsec",3.08568e+16,"m^1"),("lightyear",9.460730472580800e+15,"m^1"),("light-year",9.460730472580800e+15,"m^1"),("ly",9.460730472580800e+15,"m^1"),("lichtjaar",9.460730472580800e+15,"m^1"),("licht-jaar",9.460730472580800e+15,"m^1"),("lightspeed",2.99792458e+8,"m^1*s^-1"),("light-speed",2.99792458e+8,"m^1*s^-1"),("lichtsnelheid",2.99792458e+8,"m^1*s^-1"),("licht-snelheid",2.99792458e+8,"m^1*s^-1"),("astronomicalunit",1.49597870691e+11,"m^1"),("astronomischeeenheid",1.49597870691e+11,"m^1"),("ae",1.49597870691e+11,"m^1"),("au",1.49597870691e+11,"m^1")]

#imperial weight and mass

units+=[("mite",3.2399455e-3,"g^1"),("grain",6.479891e-2,"g^1"),("drachm",1.7718451953125,"g^1"),("ounce",2.8349523123e+1,"g^1"),("pound",4.5359237e+2,"g^1"),("stone",6.35029318e+3,"g^1"),("quarter",1.270058636e+4,"g^1"),("hundredweight",5.080234544e+4,"g^1"),("imperialton",1.0160469088e+6,"g^1"),("britishton",1.0160469088e+6,"g^1"),("slug",1.45939e+4,"g^1")]

units+=[("joule",1.0,"j^1"),("calorie",4.184,"j^1"),("watt",1.0,"j^1*s^-1")]

# cooking volume

units+=[("teaspoon",5e-6,"m^3"),("theelepel",5e-6,"m^3"),("dessertspoon",10e-6,"m^3"),("tablespoon",1.5e-5,"m^3"),("eetlepel",1.5e-5,"m^3"),("lepel",1.5e-5,"m^3"),("cup",2.5e-4,"m^3"),("kopje",2.5e-4,"m^3"),("mug",3.0e-4,"m^3"),("mok",3.0e-4,"m^3"),("mokken",3.0e-4,"m^3"),("jigger",4.436e-5,"m^3"),("drop",8.33333333333333333333e-8,"m^3"),("druppel",8.33333333333333333333e-8,"m^3")]

# thanks to www.unc.edu/~rowlett/units/
units+=[("btuh",2.93071e+2,"g^1*m^2*s^-3"),("btu",2.93071e+2,"g^1*m^2*s^-3"),("bunder",1e3,"m^2"),("horsepower",7.354e+5,"g^1*m^2*s^-3"),("paardekracht",7.354e+5,"g^1*m^2*s^-3"),("pk",7.354e+5,"g^1*m^2*s^-3"),("electronvolt",1.6021765314e-16,"g*m^2*s^-2"),("ev",1.6021765314e-16,"g*m^2*s^-2"),("angstrom",1e-10,"m^1"),("mole",6.02214199e23,""),("bag",0.10910616e-1,"m^3"),("barleycorn",8.4666666666667e-3,"m^3"),("barrel",1.58987294928e-1,"m^3"),("barye",9.997391705,"g^1*m^-1*s^-2"),("box",5.8189952e-2,"m^3"),("faraday",9.64853e+4,"a^1*s^1")]

# abbreviations
units+=[("mm",1.0e-3,"m^1"),("dm",1e-1,"m^1"),("cm",1e-2,"m^1"),("km",1e+3,"m^1"),("ft",3.048e-1,"m^1"),("lb",4.5359237e+2,"g^1"),("l",1e-3,"m^3"),("dl",1e-4,"m^3"),("cl",1e-5,"m^3"),("ml",1e-6,"m^3"),("kg",1.0e+3,"g^1"),("cc",1.0e-6,"m^3"),("cl",1.0e-5,"m^3"),("nm",1.0e-9,"m^1"),("s",1.0,"s^1"),("amp",1.0,"a^1"),("min",6.0e+1,"s^1"),("h",3.6e+3,"s^1"),("m",1.0,"m^1"),("el",1.143,"m^1")]

#depcrecated exchange rates:
units+=[("gulden",0.45378021609,"$^1"),("guldens",0.45378021609,"$^1"),("nlg",0.45378021609,"$^1")]

units.sort(lambda (x1,x2,x3), (y1,y2,y3): cmp(len(y1),len(x1)))

monthmap={
  "jan":1, "januari":1, "january":1, "feb":2, "februari":2, "february":2,
  "mar":3, "mrt":3, "maart":3, "march":3, "apr":4, "april":4,
  "mei":5, "may":5, "jun":6, "juni":6, "june":6,
  "jul":7, "juli":7, "july":7, "aug":8, "augustus":8, "august":8,
  "sep":9, "september":9, "oct":10, "okt":10, "oktober":10, "october":10,
  "nov":11, "november":11, "dec":12, "december":12}
months = '(%s)' % ('|'.join(monthmap.keys()))
selectmonth={1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}
daysofweek=["Monday","Tuesday","Wednesday","Thursday","Friday","Saterday","Sunday"]
daysofweek+=["Maandag","Dinsdag","Woensdag","Donderdag","Vrijdag","Zaterdag","Zondag"]
