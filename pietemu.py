from pysqlite2 import dbapi2 as sqlite;
import string;

pietdbpath="/home/weary/piet/piet.db"

def db(query):
  con = sqlite.connect(pietdbpath, isolation_level=None)
  cur = con.cursor()
  cur.execute(query)
  r=cur.fetchall()
  
  if len(r)==0:
    return None;

  return [[a[0] for a in cur.description]]+[[str(b) for b in c] for c in r];

def send(channel, msg):
    for m in msg.split('\n'):
        if m[0:7]=="ACTION ":
            print channel+": iemand "+m[7:];
        elif m[0:5]=="NICK ":
            print "will try to change nick to \""+m[5:]+"\"";
        elif len(m)>0:
            print channel+": "+m;

def names(a):
    print "niet geimplementeerd";

internalnick="piet";

def nick(newnick=""):
    oldnick=internalnick;
    if len(newnick)>0:
        internalnick=newnick;
    return oldnick;

def thread(a,b,c):
    print "niet geimplementeerd";

def op(channel, names):
    while len(names)>0:
        nm=names[0:3];
        names=names[3:];
        nm2=["+o" for i in nm];
        nm=string.join(nm, " ");
        nm2=string.join(nm2, "");
        print channel+": MODE "+nm2+" "+nm;        
    
#send("channel", "hallo hoe\nis het\nmet jou\n\n");
#send("channel", "NICK fropsel");
#send("channel", "ACTION eet uit je hand\nACTION eet je hand op");
#op("channel", ["aap", "noot", "mies", "wim"]);
