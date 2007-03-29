# kooklibrary voor piet, bevat de volgende functies:
#
#   kookbalans
#     - geeft een saldolijst
#   gekookt [voor <naam> [<naam> ...]] [door <naam>] [tegen|kosten <naam>] [namelijk <omschrijving ...>]
#     - boekt een kookactie
#   undo
#     - boekt een inverse kookactie van de laatste kookactie
#
# Gebruikt tabellen: kookbalans_balans, kookbalans_mutaties
#
# Tabellen worden indien nodig geinitialiseerd bij aanroep van balansfuncties.
#

import piet
import pietlib
import random
import traceback


def cmd_kookbalans(channel, nick, auth, params):
  if not init_tables(channel):
    return "ACTION kan geen tabellen aanmaken"

  saldos = None

  try:
    saldos = piet.db("SELECT nick, saldo, COUNT(*) from kookbalans_mutaties LEFT JOIN kookbalans_balans ON kookbalans_mutaties.koker = kookbalans_balans.nick GROUP BY nick ORDER BY saldo")

  except:
    return format_exception("probleem met database")

  if saldos == None:
    return "geen informatie"

  # delete column headers
  del saldos[0]

  zegdit = []
  for saldo in saldos:
    zegdit.append("het saldo van %s is %.2f (uit %d keer koken)" % (saldo[0], float(saldo[1]), int(saldo[2])))

  return '\n'.join(zegdit)


def cmd_gekookt(channel, nick, auth, params):
  if not init_tables(channel):
    return "ACTION kan geen tabellen aanmaken"

  if params == "":
    return print_kookgeschiedenis(channel,5)

  stopwoorden = [ "", "credits", "gulden", "euro", "florijnen", "florijn", "dildos", "vuile", "zwarte", "witte", "witgewassen", "is", "en" ]

  keys_kokert = [ "door" ]
  keys_eters = [ "voor" ]
  keys_kosten = [ "tegen", "kost", "kosten", "prijs" ]
  keys_voedsel = [ "namelijk" ]

  for teken in ",.;:!?()[]":
    params = params.replace(teken,"")

  cmd = params.split(" ")

  kokert = nick
  eters = []
  kosten = float(1)
  voedsel = []

  status = None

  for woord in cmd:
    if woord in stopwoorden:
      pass
    elif status == keys_voedsel:
      voedsel.append(woord)

    elif woord in keys_kokert:
      status = keys_kokert
    elif woord in keys_eters:
      status = keys_eters
    elif woord in keys_kosten:
      status = keys_kosten
    elif woord in keys_voedsel:
      status = keys_voedsel

    elif status == keys_kokert:
      kokert = woord
      status = None
    elif status == keys_eters:
      eters.append(woord)
    elif status == keys_kosten:
      kosten = float(woord)
      status = None

    else:
      return "geen idee wat je bedoelt met '%s'" % woord

  if kokert not in eters:
    eters.append(kokert)

  kosten *= len(eters)

  return mutatie (nick, kokert, eters, kosten, ' '.join(voedsel))


def cmd_undo(channel, nick, auth, params):
  if not init_tables(channel):
    return "ACTION kan geen tabellen aanmaken"

  return mutatie_inverteren(nick)


def format_exception(s):
  return s+": "+traceback.format_exc(0).split("\n")[1]


def init_tables(channel):
#
# volgens sqlite-handleiding moet IF NOT EXISTS werken
# --> SQL error: near "NOT": syntax error
#
  try:
    piet.db("CREATE TABLE kookbalans_mutaties (" +
      "tijdstip TIMESTAMP NOT NULL," +
      "muteerder VARCHAR(255) NOT NULL," +
      "koker VARCHAR(255) NOT NULL," +
      "eters VARCHAR(255) NOT NULL," +
      "kosten FLOAT NOT NULL," +
      "commentaar TEXT NULL)")

    piet.db("CREATE TABLE kookbalans_balans (" +
      "nick VARCHAR(255) PRIMARY KEY NOT NULL," +
      "saldo FLOAT NOT NULL DEFAULT 0)")

    piet.send(channel, "nieuwe tabellen aangemaakt")
  except:
    pass

  return True


def print_kookgeschiedenis(channel, nrecords):
  try:
    records = piet.db("SELECT tijdstip,koker,eters,kosten,commentaar FROM kookbalans_mutaties ORDER BY tijdstip DESC LIMIT %d" % nrecords)

  except:
    return format_exception("probleem met database")

  if records == None or len(records) < 2:
    return "geen informatie"

  del records[0]

  for rec in records:
    tijdstip = rec[0]
    koker = rec[1]
    eters = rec[2].strip().split(" ")
    kosten = float(rec[3])
    commentaar = rec[4]

    piet.send(channel, "%s: %s" % (tijdstip, kookmelding(koker, eters, kosten, commentaar)))

  return ""


def kookmelding(kokert, eters, kosten, commentaar):
  eters_subj = eters[:]
  eters_obj = eters[:]
  if eters[-1] == kokert:
    eters_subj[-1] = "hijzelf"
    eters_obj[-1] = "hemzelf"

  if commentaar == None or commentaar == "":
    commentaar = [ "het eten", "vergiftigde slangen", "geperforeerde paashaas", "argelose asperges", "verteerde veterknopen", "aangeslagen aardbeien", "vergeelde krantekoppen" ]
  else:
    commentaar = [ commentaar ]

  grammatica = {
    "%alt%"             : [ "%kok% -> %obj_eters% (%np_eten%)" ],
    "%s%"               : [ "%pp_value% %s_kookt_voor_inv%",
                            "%pp_value% %s_kookt_inv% %pp_eters%",
                            "%pp_eters% %s_kookt_inv% %pp_value%",
                            "%pp_value% %s_kookt_inv% en %vp_eters%",
                            "%pp_eters% %s_kookt_inv% en %vp_value%",
                            "%s_kookt_voor% %pp_value%",
                            "%s_kookt% %pp_eters% %pp_value%",
                            "%s_kookt% %pp_value% %pp_eters%",
                            "%s_kookt%, %vp_value% en %vp_eters%",
                            "%s_kookt%, %vp_eters% en %vp_value%",
                            "%s_kookt%, %s_eters% en %s_value%",
                            "%s_kookt% %pp_eters% en %vp_value%",
                            "%s_kookt% %pp_value% en %vp_eters%",
                            "%s_kookt% en %vp_eters% %pp_value%",
                            "%s_kookt% en %vp_value% %pp_eters%" ],
    "%s_kookt%"         : [ "%kok% kookt %np_eten%",
                            "%kok% maakt %np_eten% klaar",
                            "%kok% pruttelt in de keuken",
                            "%kok% roept dat %np_eten% klaar is",
                            "%kok% vangt een slak" ],
    "%s_kookt_voor%"    : [ "%kok% voedert %obj_eters% %np_eten%",
                            "%kok% probeert %obj_eters% te behagen met %np_eten%",
                            "%kok% bedient %obj_eters%",
                            "%kok% geeft %obj_eters% %np_eten% te eten" ],
    "%s_kookt_inv%"     : [ "kookt %kok% %np_eten%",
                            "maakt %kok% %np_eten% klaar",
                            "pruttelt %kok% in de keuken",
                            "roept %kok% dat %np_eten% klaar is" ],
    "%s_kookt_voor_inv%": [ "voedert %kok% %obj_eters%",
                            "probeert %kok% %obj_eters% te behagen met %np_eten%",
                            "bedient %kok% %obj_eters% met %np_eten%",
                            "geeft %kok% %obj_eters% %np_eten% te eten" ],
    "%pp_eters%"        : [ "voor %obj_eters%",
                            "teneinde %obj_eters% te behagen",
                            "om %obj_eters% langzaam te laten afsterven",
                            "omwille van het welzijn van %obj_eters%" ],
    "%s_eters%"         : [ "%subj_eters% krijgen te eten",
                            "%subj_eters% worden onderworpen aan een sadistisch experiment" ],
    "%vp_eters%"        : [ "geeft %obj_eters% te eten",
                            "voert %obj_eters%",
                            "schuift %obj_eters% een pan toe",
                            "helpt %obj_eters% de dag door" ],
    "%pp_value%"        : [ "voor %np_value%",
                            "tegen %np_value%",
                            "om %np_value% binnen te slepen" ],
    "%s_value%"         : [ "%kok% %vp_value%" ],
    "%vp_value%"        : [ "%v_krijgt% %np_value%",
                            "%v_krijgt% daarmee %np_value%",
                            "%v_krijgt% daarvoor %np_value%",
                            "%v_krijgt% zo %np_value%",
                            "%v_krijgt% op die manier %np_value%",
                            "strijkt %np_value% op" ],
    "%v_krijgt%"        : [ "krijgt", "beurt", "verdient", "incasseert" ],
    "%np_value%"        : [ "%pre_multiplier% %n_quantity_pp% %np_quantity%",
                            "%n_quantity_pp% %np_quantity% %post_multiplier%",
                            "%n_quantity_pp% %np_quantity%",
                            "%pre_sum% %n_quantity_sum% %np_quantity%",
                            "%n_quantity_sum% %np_quantity% %post_sum%",
                            "%n_quantity_sum% %np_quantity%" ],
    "%np_quantity%"     : [ "%n_unit%",
                            "%adj_locality% %n_unit%",
                            "%adj_qual% %n_unit%",
                            "%adj_qual% %adj_locality% %n_unit%" ],
    "%n_unit%"          : [ "florijnen", "guldens", "euros", "goudstukken", "stuivers", "cavias", "gedichten", "zwerfkeien", "sexbeurten" ],
    "%adj_qual%"        : [ "zwartverdiende", "zuurverdiende", "ongeldige", "waardeloze", "virtuele", "virtuose", "uitgepoepte", "goddelijke" ],
    "%adj_locality%"    : [ "armeense", "vogonese", "drentse", "aramese", "joodse", "nigeriaanse", "friese", "cypriotische", "japanse", "hemelse" ],
    "%pre_multiplier%"  : [ "van iedereen", "per persoon", "ongeveer" ],
    "%post_multiplier%" : [ "elk", "per persoon", "de man", "pp" ],
    "%pre_sum%"         : [ "in totaal", "totaal" ],
    "%post_sum%"        : [ "in totaal", "bruto", "(subtotaal)" ],

    "%n_quantity_pp%"   : [ "%.2f" % (kosten/len(eters)),
                            ("%f" % (kosten/len(eters))).strip("0").strip("."),
                            "0x%x cent in" % int(100*kosten/len(eters)),
                            "ongeveer 0x%x.%02x" % (int(kosten/len(eters)), 0xff & int(0x100*kosten/len(eters))) ],
    "%n_quantity_sum%"  : [ "%.2f" % kosten,
                            ("%f" % kosten).strip("0").strip("."),
                            "0x%x cent in" % int(100*kosten),
                            "ongeveer 0x%x.%02x" % (int(kosten), 0xff & int(0x100*kosten)) ],
    "%np_eten%"         : commentaar,
    "%kok%"             : [ kokert ],
    "%subj_eters%"      : [ pietlib.make_list(eters_subj) ],
    "%obj_eters%"       : [ pietlib.make_list(eters_obj) ]
  }

  melding = "%alt%"

  while "%" in melding:
    melding_subst = melding
    for k in grammatica.keys():
      melding_subst = melding_subst.replace(k,random.choice(grammatica[k]))

    if melding == melding_subst:
      break
    else:
      melding = melding_subst

  return melding


def mutatie(afzender, kokert, eters, kosten, commentaar):
  try:
    for eter in eters:
      result = piet.db("SELECT COUNT(*) FROM auth WHERE name = '%s'" % eter.replace("'","''"))
      if int(result[1][0]) == 0:
        result = piet.db("SELECT COUNT(*) FROM kookbalans_balans WHERE nick = '%s'" % eter.replace("'","''"))
      if int(result[1][0]) == 0:
        return "%s ken ik niet" % eter

  except:
    return format_exception("probleem met de database")

  q_log = "INSERT INTO kookbalans_mutaties(tijdstip,muteerder,koker,eters,kosten,commentaar) VALUES (datetime('now'), '%s', '%s', ' %s ', %f, '%s')"
  try:
    piet.db("BEGIN")

    piet.db(q_log % (afzender.replace("'","''"),
      kokert.replace("'","''"),
      ' '.join(eters).replace("'","''"),
      kosten,
      commentaar.replace("'","''")))

  except:
    try:
      piet.db("ROLLBACK")
    except:
      pass
    return format_exception("ACTION kan geen log entry toevoegen")

  err = balans_bijwerken(kokert,eters,kosten)
  if err != None:
    try:
      piet.db("ROLLBACK")
    except:
      pass
    return err

  try:
    piet.db("COMMIT")
  except:
    return format_exception("ACTION kan de database niet wijzigen")

  return kookmelding(kokert, eters, kosten, commentaar)


def mutatie_inverteren(afzender):
  q_last = "FROM kookbalans_mutaties WHERE muteerder = '%s' ORDER BY tijdstip DESC LIMIT 1" % afzender.replace("'","''")

  try:
    q_results = piet.db("SELECT koker,eters,kosten " + q_last);

  except:
    return format_exception("probleem met database")

  if q_results == None or len(q_results) < 2:
    return "geen laatste log entry gevonden"

  kokert = q_results[1][0]
  eters = q_results[1][1].strip().split(" ")
  kosten = float(q_results[1][2])

  return mutatie(afzender, kokert, eters, -kosten)


def balans_bijwerken(kokert, eters, kosten):
  try:
    for eter in eters:
      piet.db("INSERT OR IGNORE INTO kookbalans_balans(nick) VALUES('%s')" % eter.replace("'","''"))

  except:
    return format_exception("probleem met het toevoegen van eters")

  q_mutatie = "UPDATE kookbalans_balans SET saldo = saldo + %f WHERE nick = '%s'"

  try:
    piet.db(q_mutatie % (kosten, kokert.replace("'","''")))
  except:
    return format_exception("probleem met saldo update van kok")

  try:
    for eter in eters:
      piet.db(q_mutatie % (-kosten/len(eters), eter.replace("'","''")))

  except:
    return format_exception("probleem met saldo update van eters")

  return None
