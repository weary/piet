-- special functions: send(..), split(string,key)

leave_time={};
in_netsplit={}; -- per nick "weg", "terug" of "op"

function printtable(a,b)
  print("table "..b..": ",a);
  for k,v in a do
    print(k,v);
  end;
  print("end of table "..b);
end

function maketimestring(verschil)
  dagen=math.floor(verschil/(3600*24)); verschil=verschil-(dagen*24*3600);
  uren=math.floor(verschil/3600); verschil=verschil-(uren*3600);
  minuten=math.floor(verschil/60); verschil=verschil-(minuten*60);

  result="";
  if (dagen>1) then result=dagen.." dagen, ";
  elseif (dagen==1) then result="1 dag, "; end

  if (uren>1) then result=result..uren.." uren, ";
  elseif (uren==1) then result=result.."1 uur, "; end

  if (minuten>1) then result=result..minuten.." minuten en ";
  elseif (minuten==1) then result=result.."1 minuut en "; end

  if (verschil>1) then result=result..verschil.." seconden";
  elseif (verschil==1) then result=result.."1 seconde";
    else result=result.."geen seconden"; end
  return result;
end

function servermsg(nick, auth, channel, msg)
  --nick=string.gsub(nick, "`", "'");
  print("servermsg("..nick..", "..auth..", "..channel..", "..msg.."), msg splitted:");
  a=split(msg, " ");
  printtable(a, "msg-splitted");

  if (a[1]=="JOIN") then 
    servermsg_join(nick, auth, channel, msg);
  elseif ((a[1]=="PART") or (a[1]=="QUIT")) then
    netsplit_begin,netsplit_end=string.find(msg, "QUIT :[%w%.]+ [%w%.%*]+");
    if ((netsplit_begin~=nil) and (netsplit_begin==1) and (netsplit_end==string.len(msg))) then
      print(nick.." gaat in netsplit mode\n");
      in_netsplit[nick]="weg";
    else
      nu=tonumber(os.date("%s"));
      leave_time[nick]=nu;
      send("doei! kom nog eens weer!\n");
    end;
  elseif (a[1]=="KICK") then
    nu=tonumber(os.date("%s"));
    leave_time[a[3]]=nu;
    send("en waag het niet om weer te komen, jij vuile "..a[3].."!\n");
  elseif (a[1]=="MODE") then
    servermsg_mode(nick, auth, channel, msg, a);
  elseif (a[1]=="437") then
     send("bah, die nick is even niet beschikbaar\n");
  end
end

function checkgemiddelde(naam, verschil)
  filename=string.gsub(naam, "`", "-").."_offlinetijd.txt";

  -- output new value to file
  handle=io.open(filename, "a");
  oldoutput=io.output();
  io.output(handle);
  io.write(verschil);
  io.write("\n");
  io.output(oldoutput);
  io.close(handle);

  -- iterate over file and calculate new average
  totaal = {0,0,0,0};
  count= {0,0,0,0};
  for line in io.lines(filename)
  do
    val=tonumber(line);
    if (val<3600) then
      duur=1;
    elseif (val<4*3600) then
      duur=2;
    elseif (val<20*3600) then
      duur=3;
    else
      duur=4;
    end

    totaal[duur]=totaal[duur]+val;
    count[duur]=count[duur]+1;
  end;

  if ((count[duur]) and (count[duur]>1)) then
    gem=math.floor(totaal[duur]/count[duur]+0.5);
    send("dat brengt het gemiddelde voor "..naam.." op "..maketimestring(gem).."\n");
  end;
end

-- function called when received "JOIN" from server
function servermsg_join(nick, auth, channel, msg)
  --nick=string.gsub(nick, "`", "'");
  if (in_netsplit[nick]=="weg") then
    print(nick.." komt terug uit een netsplit");
    in_netsplit[nick]="terug";
    return;
  end;

  if (auth>150) then
    sendspecial("MODE "..channel.." +o "..nick);
  end;
    
  if (leave_time[nick]) then
    print("ja! die zit er in! met "..leave_time[nick]);
    nu=tonumber(os.date("%s"));
    verschil=nu-leave_time[nick];
    if (verschil>0) then
      result=maketimestring(verschil);
      send("Welkom "..nick..", wist je dat je hier "..result.." geleden ook al was?\n");
      checkgemiddelde(nick, verschil);
    else
      send("Blijkbaar is "..nick.." aan het fietsen\n");
    end;
  else
    send("Welkom "..nick.."!\n");
  end
end

function servermsg_mode(nick, auth, channel, msg, a)
  local _,ocount=string.find(a[3], "%+o+");
  if (ocount==nil) then
    ocount=0;
  else
    ocount=ocount-1;
  end;
  if (nick=="piet") then
    if (ocount==1) then
      send("alsjeblieft, ik heb je maar een @tje gegeven..\n");
    elseif (ocount>1) then
      send("alsjeblieft, ik heb jullie maar een @tje gegeven..\n");
    end;
  else
    local nameslist={};
    for tellertje=1,ocount do
      local nick2=a[3+tellertje];
      -- nick2 krijgt een @ van nick
      nick2=string.gsub(nick2, "`", "'");
      print("\""..nick2.."\" krijgt een @'tje van \""..nick.."\"\n");
      print("in_netsplit: ");
      for k,v in in_netsplit do print("\""..k.."\": \""..v.."\"\n"); end;
      print("<einde netsplit table>\n");

      local state=in_netsplit[nick2];
      if (state~=nil) then
        print("\""..nick2.."\" is in state \""..state.."\"\n");
      else
        print("\""..nick2.."\" is in state nil\n");
      end;
      if ((string.find(nick, "%.")~=nil) and (state=="terug")) then
        print("server geeft apestaart na netsplit aan "..nick.."\n");
        --send("en dan ga ik ook nog spammen als "..nick.." een @ krijgt\n");
        in_netsplit[a[4]]="op";
      elseif (nick2=="piet") then
        send("dank je\n");
      else
        table.insert(nameslist, nick2);
      end;
    end;
    local listlen; listlen=table.getn(nameslist);
    if (table.getn(nameslist)>0) then
      local result="ah, "..table.concat(nameslist, ", ");
      if (listlen>1) then
        result=result.." krijgen";
      else
        result=result.." krijgt";
      end;
      
      send(result.." een atje\n");
    end;
  end;
end
