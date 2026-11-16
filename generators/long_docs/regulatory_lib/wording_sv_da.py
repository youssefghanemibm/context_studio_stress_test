"""Swedish (LD008 Hem Sverige 2016) and Danish (LD010 Hjem Danmark 2016) policy wording content."""
from __future__ import annotations

# =========================================================================================
# Swedish
# =========================================================================================

SV_INLEDNING = [
    ("h2", "Om försäkringsavtalet"),
    ("p", "Försäkringsavtalet består av försäkringsbrevet, dessa försäkringsvillkor och eventuella särskilda villkor. "
          "Om dokumenten innehåller motstridiga uppgifter gäller i första hand försäkringsbrevet, därefter de "
          "särskilda villkoren och sist dessa villkor. I övrigt gäller försäkringsavtalslagen (2005:104) och annan "
          "svensk lag."),
    ("p", "Försäkringsgivare är Corvane Mutual Sverige, filial till Corvane Mutual Insurance Society Limited. "
          "Bolaget är ett ömsesidigt försäkringsbolag som ägs av sina medlemmar och står under tillsyn av National "
          "Insurance Supervisory Authority (NISA)."),
    ("h2", "Så läser du villkoren"),
    ("p", "Villkoren är indelade i moment. Varje moment beskriver vad försäkringen gäller för och vilka undantag "
          "som gäller. Säkerhetsföreskrifterna, reglerna om självrisk och reglerna om skadevärdering gäller för "
          "samtliga moment om inget annat anges."),
]

SV_DEF = [
    ("Försäkringstagare", "Den som har ingått avtalet med bolaget och som är medlem i Corvane Mutual."),
    ("Den försäkrade", "Den vars intresse är försäkrat, det vill säga försäkringstagaren och de personer som "
                       "anges i momentet Vem försäkringen gäller för."),
    ("Försäkringsbrev", "Det dokument som anger vad som är försäkrat, försäkringsbelopp, självrisk och "
                        "försäkringstid."),
    ("Lösegendom", "Lös egendom som den försäkrade äger, hyr eller lånar för privat bruk, till exempel möbler, "
                   "kläder, hemelektronik och husgeråd."),
    ("Byggnad", "Byggnad som anges i försäkringsbrevet, med fast inredning och fast installationer."),
    ("Stöldbegärlig egendom", "Egendom som är särskilt attraktiv för tjuvar, till exempel smycken, klockor, "
                              "datorer, mobiltelefoner, kameror och konst."),
    ("Självrisk", "Den del av skadan som den försäkrade själv står för vid varje skadetillfälle."),
    ("Besiktningsman", "Den person som bolaget utser för att besiktiga skadan, fastställa orsaken och värdera "
                       "skadan."),
    ("Regress", "Bolagets rätt att kräva tillbaka utbetald ersättning av den som är ansvarig för skadan."),
]

SV_MOMENT = [
    ("Vem och var försäkringen gäller", [
        ("h2", "Vem försäkringen gäller för"),
        ("p", "Försäkringen gäller för försäkringstagaren och de personer som är folkbokförda på och stadigvarande "
              "bor på samma adress som försäkringstagaren."),
        ("p", "Barn som studerar på annan ort och har eget boende omfattas av försäkringen för sin lösegendom "
              "i den bostad där de bor under studietiden."),
        ("h2", "Var försäkringen gäller"),
        ("p", "Försäkringen gäller i bostaden på den adress som anges i försäkringsbrevet. Lösegendom som "
              "tillfälligt finns utanför bostaden omfattas i hela världen med de begränsningar som anges i "
              "villkoren."),
    ]),
    ("Egendomsskydd", [
        ("h2", "Brand"),
        ("p", "Försäkringen gäller för skada genom brand, det vill säga eld som kommit lös, samt skada genom "
              "blixtnedslag, explosion och sot som plötsligt strömmat ut från eldstad."),
        ("ul", ["Försäkringen gäller inte för skada genom sotning eller rök från tobak eller levande ljus.",
                "Försäkringen gäller inte för skada på egendom som avsiktligt utsatts för eld eller värme."]),
        ("h2", "Vattenskada"),
        ("p", "Försäkringen gäller för skada genom vätska som oberäknat strömmat ut från ledningssystem för vatten, "
              "avlopp eller värme, eller från anslutna anordningar som tvättmaskin och diskmaskin, samt från "
              "akvarium och vattensäng."),
        ("ul", ["Försäkringen gäller inte för skada genom vatten som trängt in genom tak, fönster eller ytterväggar.",
                "Försäkringen gäller inte för skada som uppkommit successivt genom läckage under lång tid.",
                "Försäkringen gäller inte för kostnad för att reparera själva ledningen eller anordningen."]),
        ("h2", "Frostskada"),
        ("p", "Försäkringen gäller för frostskada på ledningssystem och anslutna anordningar i byggnaden, samt "
              "för vattenskada som uppkommer när vattnet tinar."),
        ("ul", ["Försäkringen gäller inte om byggnaden inte hållits tillräckligt uppvärmd eller om vattnet inte "
                "stängts av och ledningarna tömts när byggnaden lämnats utan tillsyn."]),
        ("h2", "Inbrott och stöld"),
        ("p", "Försäkringen gäller för stöld av lösegendom ur bostaden efter inbrott, det vill säga när någon "
              "olovligen tagit sig in i bostaden genom att bryta sig in, samt för skadegörelse i samband med "
              "inbrott."),
        ("ul", ["Försäkringen gäller inte för stöld ur ofullständigt låst bostad.",
                "Stöldbegärlig egendom är försäkrad till det belopp som anges i försäkringsbrevet."]),
        ("h2", "Naturskador"),
        ("p", "Försäkringen gäller för skada genom storm, hagel, snötryck, översvämning och jordskred, enligt "
              "de närmare bestämmelser som anges i försäkringsbrevet."),
        ("p", "Snötryck på byggnad är försäkrat när tak eller bärande konstruktion ger vika för tyngden av snö eller "
              "is."),
        ("h2", "Skadegörelse"),
        ("p", "Försäkringen gäller för skadegörelse på lösegendom och byggnad som orsakats av någon som olovligen "
              "tagit sig in i bostaden."),
        ("h2", "Allrisk (tillägg)"),
        ("p", "Om det framgår av försäkringsbrevet gäller försäkringen även för plötslig och oförutsedd skada på "
              "lösegendom, till exempel när en sak tappas eller välts omkull."),
    ]),
    ("Ansvarsskydd, rättsskydd och överfallsskydd", [
        ("h2", "Ansvarsskydd"),
        ("p", "Försäkringen gäller när den försäkrade i egenskap av privatperson krävs på skadestånd för person- "
              "eller sakskada. Bolaget utreder om skadeståndsskyldighet föreligger, förhandlar med den som kräver "
              "skadestånd och betalar det skadestånd som den försäkrade är skyldig att betala."),
        ("ul", ["Ansvarsskyddet gäller inte för skada på egendom som den försäkrade äger, hyr eller lånar.",
                "Ansvarsskyddet gäller inte för skada i samband med yrkesutövning eller näringsverksamhet.",
                "Ansvarsskyddet gäller inte för skada genom motordrivet fordon."]),
        ("h2", "Rättsskydd"),
        ("p", "Försäkringen gäller för ombudskostnader vid tvist som kan prövas av tingsrätt, och som uppkommit "
              "under försäkringstiden, med de begränsningar som anges i försäkringsbrevet."),
        ("h2", "Överfallsskydd"),
        ("p", "Försäkringen gäller med skadestånd beräknat enligt skadeståndslagen om den försäkrade utsätts för "
              "uppsåtlig misshandel, våldtäkt eller rån."),
    ]),
    ("Reseskydd och extra kostnader", [
        ("h2", "Reseskydd"),
        ("p", "Reseskyddet gäller under resa utanför Sverige i högst den tid som anges i försäkringsbrevet och "
              "omfattar sjuk- och olycksfallskostnader, hemtransport och kostnader för avbruten resa."),
        ("h2", "Merkostnader vid skada"),
        ("p", "Om bostaden blir obeboelig efter en skada som omfattas av försäkringen, ersätter bolaget skäliga "
              "merkostnader för tillfälligt boende under den tid det tar att återställa bostaden."),
    ]),
]

SV_SAKERHET = [
    "Dörrar och fönster ska vara låsta och stängda när bostaden lämnas utan tillsyn.",
    "Nycklar får inte förvaras så att obehöriga kan få tillgång till dem.",
    "Byggnaden ska hållas tillräckligt uppvärmd för att förhindra frostskada. När byggnaden lämnas utan tillsyn "
    "under den kalla årstiden ska vattnet stängas av och ledningarna tömmas.",
    "Ledningssystem och anslutna anordningar ska vara installerade fackmässigt och underhållas.",
    "Tvättmaskin och diskmaskin får inte lämnas igång utan tillsyn.",
    "Levande ljus får inte lämnas utan tillsyn.",
    "Bostaden ska vara försedd med fungerande brandvarnare.",
]

SV_SKADEVARDERING = [
    ("h2", "Besiktning"),
    ("p", "Bolaget har rätt att besiktiga skadad egendom och kan utse en besiktningsman för detta. Den försäkrade "
          "ska ge besiktningsmannen tillträde till skadeplatsen och lämna de uppgifter som behövs."),
    ("h2", "Värdering av lösegendom"),
    ("p", "Lösegendom värderas till vad det på skadedagen kostar att köpa ny likvärdig egendom, med avdrag för "
          "ålder, slitage, omodernitet och minskad användbarhet. Bolaget har rätt att välja om skadan ska "
          "ersättas genom reparation, ersättningsegendom eller kontant ersättning."),
    ("h2", "Värdering av byggnad"),
    ("p", "Skada på byggnad ersätts med kostnaden för reparation eller återuppbyggnad med samma material och "
          "standard, med avdrag för ålder och slitage enligt de regler som anges i försäkringsbrevet."),
    ("h2", "Regress"),
    ("p", "Bolaget övertar den försäkrades rätt till skadestånd i den mån bolaget betalat ersättning för skadan "
          "(regress). Den försäkrade får inte avstå från sin rätt till skadestånd utan bolagets medgivande."),
    ("h2", "Om vi inte kommer överens"),
    ("p", "Är den försäkrade inte nöjd med bolagets beslut kan ärendet omprövas av bolagets kundombudsman. "
          "Den försäkrade kan även vända sig till en oberoende nämnd för prövning av försäkringstvister eller till "
          "allmän domstol."),
]

SV_ALLMANT = [
    ("h2", "Preskription"),
    ("p", "Den som vill ha ersättning ska väcka talan mot bolaget inom den tid som anges i "
          "försäkringsavtalslagen."),
    ("h2", "Personuppgifter"),
    ("p", "Bolaget behandlar personuppgifter för att administrera försäkringen och reglera skador, samt för att "
          "förebygga och upptäcka bedrägerier, i enlighet med gällande dataskyddslagstiftning."),
    ("h2", "Dubbelförsäkring"),
    ("p", "Om samma intresse är försäkrat hos flera försäkringsgivare gäller reglerna i försäkringsavtalslagen om "
          "fördelning av ansvaret mellan dem."),
    ("h2", "Force majeure"),
    ("p", "Bolaget ansvarar inte för förlust som beror på att skadeutredning, värdering eller utbetalning "
          "fördröjs till följd av krig, terrorhandling, myndighetsåtgärd, strejk eller annan liknande händelse."),
]

SV_ENGLISH = [
    ("p", "This page is an English summary of the Swedish home insurance terms (Hem Sverige). It is provided for "
          "information only. In the event of any difference, the Swedish text prevails."),
    ("ul", ["The policy covers household contents (lösegendom) and, where shown in the policy certificate "
            "(försäkringsbrev), the building.",
            "Cover includes property cover, liability, legal expenses, assault cover and travel cover, each "
            "described in its own section (moment).",
            "The excess (självrisk) is set out in the section 'Självrisk'.",
            "Claims must be reported to the company as soon as possible (snarast). The company may appoint an "
            "assessor (besiktningsman).",
            "Safety regulations (säkerhetsföreskrifter) apply; failure to follow them may reduce the payment.",
            "The company may recover its outlay from a responsible party (regress)."]),
]

SV_ANMALAN = [
    "Lämna de upplysningar och handlingar som bolaget behöver för att reglera skadan, till exempel kvitton, "
    "garantibevis och fotografier.",
    "Polisanmäla inbrott, stöld, rån och skadegörelse och skicka en kopia av anmälan till bolaget.",
    "Spara skadad egendom tills bolaget har besiktigat den eller medgett att den får kastas.",
    "Inte medge skadeståndsskyldighet eller betala skadestånd utan bolagets medgivande.",
    "Försöka begränsa skadan så långt det är möjligt.",
]

# =========================================================================================
# Danish
# =========================================================================================

DA_INDLEDNING = [
    ("h2", "Om forsikringsaftalen"),
    ("p", "Forsikringsaftalen består af policen, disse forsikringsbetingelser og eventuelle særlige betingelser. "
          "Er der uoverensstemmelse mellem dokumenterne, gælder policen forud for de særlige betingelser, og de "
          "særlige betingelser forud for disse betingelser. I øvrigt gælder lov om forsikringsaftaler "
          "(forsikringsaftaleloven)."),
    ("p", "Forsikringsgiver er Corvane Mutual Danmark, filial af Corvane Mutual Insurance Society Limited. "
          "Selskabet er et gensidigt forsikringsselskab, som ejes af medlemmerne, og er under tilsyn af National "
          "Insurance Supervisory Authority (NISA)."),
    ("h2", "Sådan læser du betingelserne"),
    ("p", "Betingelserne er opdelt i dækninger og fælles bestemmelser. Under hver dækning står, hvad forsikringen "
          "dækker, og hvad den ikke dækker. Reglerne om selvrisiko, sikkerhedsforskrifter og skadeopgørelse gælder "
          "for alle dækninger, medmindre andet er nævnt."),
]

DA_DEF = [
    ("Forsikringstager", "Den, der har indgået aftalen med selskabet, og som er medlem af Corvane Mutual."),
    ("Sikrede", "De personer, der er dækket af forsikringen, jf. afsnittet Hvem er dækket."),
    ("Police", "Det dokument, der angiver, hvad der er forsikret, forsikringssummer, selvrisiko og "
               "forsikringsperiode."),
    ("Indbo", "Almindeligt privat løsøre, som tilhører sikrede, for eksempel møbler, tøj, elektronik og "
              "husgeråd."),
    ("Bygning", "Den bygning, der er nævnt i policen, med fast inventar og faste installationer."),
    ("Selvrisiko", "Den del af skaden, som sikrede selv skal betale ved hver skade."),
    ("Taksator", "Den person, som selskabet udpeger til at besigtige skaden og opgøre erstatningen."),
    ("Regres", "Selskabets ret til at kræve udbetalt erstatning tilbage fra den, der er ansvarlig for skaden."),
    ("Pludselig skade", "En skade, der sker uventet og på én gang, og som ikke skyldes slid eller gradvis "
                        "påvirkning."),
]

DA_DAEKNINGER = [
    ("Hvem og hvor", [
        ("h2", "Hvem er dækket"),
        ("p", "Forsikringen dækker forsikringstageren og de personer, der bor fast på adressen og hører til "
              "husstanden, herunder ægtefælle, samlever og hjemmeboende børn."),
        ("p", "Børn, der er under uddannelse og bor midlertidigt uden for hjemmet, er dækket for deres indbo på "
              "deres midlertidige bopæl."),
        ("h2", "Hvor dækker forsikringen"),
        ("p", "Forsikringen dækker på den adresse, der står i policen. Indbo, der midlertidigt er uden for "
              "boligen, er dækket i hele verden med de begrænsninger, der fremgår af betingelserne."),
    ]),
    ("Dækninger", [
        ("h2", "Brand"),
        ("p", "Forsikringen dækker skade ved brand, det vil sige ild, der har bredt sig, samt lynnedslag, "
              "eksplosion og pludselig udsivning af røg eller sod fra fyringsanlæg."),
        ("ul", ["Forsikringen dækker ikke svidning, smeltning eller forkulning uden at der har været brand.",
                "Forsikringen dækker ikke genstande, der er udsat for ild eller varme med vilje."]),
        ("h2", "Vandskade"),
        ("p", "Forsikringen dækker skade ved udstrømning af vand, olie eller anden væske fra installationer, "
              "akvarier og vandsenge, samt ved udsivning fra skjulte rør."),
        ("ul", ["Forsikringen dækker ikke skade som følge af grundvand, opstigning af kloakvand eller "
                "nedbør, medmindre andet fremgår af policen.",
                "Forsikringen dækker ikke udbedring af selve installationen, som væsken er strømmet ud fra."]),
        ("h2", "Frostskade"),
        ("p", "Forsikringen dækker frostskade på rør og installationer i bygningen samt skade ved udstrømning af "
              "vand, når det frosne vand tør op."),
        ("ul", ["Forsikringen dækker ikke frostskade, hvis bygningen ikke har været tilstrækkeligt opvarmet, eller "
                "hvis vandet ikke er lukket af og installationerne tømt, når bygningen er ubeboet."]),
        ("h2", "Storm og snetryk"),
        ("p", "Forsikringen dækker skade ved storm, skypumpe og snetryk, herunder skade når tag eller bærende "
              "konstruktioner giver efter for vægten af sne eller is."),
        ("h2", "Tyveri og indbrud"),
        ("p", "Forsikringen dækker tyveri af indbo fra aflåst bolig efter indbrud, det vil sige når nogen "
              "uberettiget har skaffet sig adgang ved at bryde døre eller vinduer op, samt hærværk i forbindelse "
              "med indbrud."),
        ("ul", ["Forsikringen dækker ikke tyveri fra ulåst bolig.",
                "Tyveri af penge og smykker er dækket med de beløb, der fremgår af policen."]),
        ("h2", "Hærværk"),
        ("p", "Forsikringen dækker hærværk på indbo og bygning, når det er begået af personer, der uberettiget "
              "har skaffet sig adgang til boligen."),
        ("h2", "Pludselig skade (tilvalg)"),
        ("p", "Har forsikringstageren valgt dækning for pludselig skade, og fremgår det af policen, dækker "
              "forsikringen pludselige skader på indbo, som ikke er dækket af andre dækninger."),
    ]),
    ("Ansvar og retshjælp", [
        ("h2", "Ansvarsforsikring"),
        ("p", "Forsikringen dækker sikredes erstatningsansvar som privatperson for skade på personer og ting, med "
              "den forsikringssum, der fremgår af policen."),
        ("ul", ["Forsikringen dækker ikke skade på ting, som sikrede ejer, lejer eller låner.",
                "Forsikringen dækker ikke ansvar i forbindelse med erhverv.",
                "Forsikringen dækker ikke ansvar for skade forvoldt med motorkøretøj."]),
        ("h2", "Retshjælpsforsikring"),
        ("p", "Forsikringen dækker sikredes udgifter til advokat og sagsomkostninger ved tvister, der kan "
              "behandles ved domstolene, og som er opstået i forsikringsperioden, med de begrænsninger der "
              "fremgår af policen."),
    ]),
    ("Ekstraudgifter", [
        ("p", "Bliver boligen ubeboelig efter en skade, der er dækket af forsikringen, dækker selskabet "
              "rimelige og dokumenterede merudgifter til midlertidig bolig, så længe det er nødvendigt."),
        ("p", "Selskabet dækker også rimelige udgifter til oprydning og flytning af indbo efter en dækket skade."),
    ]),
]

DA_SIKKERHED = [
    "Døre og vinduer skal være låst og lukket, når boligen forlades.",
    "Nøgler må ikke opbevares, så uvedkommende kan få adgang til dem.",
    "Bygningen skal holdes tilstrækkeligt opvarmet, så frostskade undgås. Er bygningen ubeboet i den kolde "
    "årstid, skal vandet lukkes af og installationerne tømmes.",
    "Installationer skal være udført af autoriserede installatører og vedligeholdes.",
    "Levende lys må ikke efterlades uden opsyn.",
    "Boligen skal have en funktionsdygtig røgalarm.",
]

DA_SKADEOPGORELSE = [
    ("h2", "Taksator og besigtigelse"),
    ("p", "Selskabet kan udpege en taksator til at besigtige skaden og opgøre erstatningen. Sikrede skal give "
          "taksatoren adgang til skadestedet og de nødvendige oplysninger."),
    ("h2", "Opgørelse af indboskader"),
    ("p", "Erstatningen opgøres på grundlag af, hvad det på skadedagen vil koste at genanskaffe tilsvarende "
          "genstande. Der foretages fradrag for værdiforringelse på grund af alder, brug og nedsat anvendelighed. "
          "Selskabet kan vælge at erstatte skaden ved reparation, genlevering eller kontant erstatning."),
    ("h2", "Opgørelse af bygningsskader"),
    ("p", "Bygningsskader erstattes med udgiften til reparation eller genopførelse med samme byggemåde og på samme "
          "sted, med fradrag for slid og ælde efter de regler, der fremgår af policen."),
    ("h2", "Regres"),
    ("p", "Selskabet indtræder i sikredes ret over for den, der er ansvarlig for skaden, i det omfang selskabet "
          "har betalt erstatning (regres). Sikrede må ikke give afkald på sin ret til erstatning uden "
          "selskabets samtykke."),
    ("h2", "Uenighed om erstatningen"),
    ("p", "Er sikrede og selskabet uenige om erstatningens størrelse, kan hver af parterne forlange, at "
          "erstatningen fastsættes af uvildige skønsmænd."),
]

DA_FAELLES = [
    ("h2", "Fornyelse og opsigelse"),
    ("p", "Forsikringen fornyes automatisk for ét år ad gangen, medmindre forsikringstageren eller selskabet "
          "opsiger den efter reglerne i forsikringsaftaleloven."),
    ("h2", "Personoplysninger"),
    ("p", "Selskabet behandler personoplysninger for at administrere forsikringen, behandle skader og forebygge "
          "forsikringssvindel, i overensstemmelse med gældende databeskyttelsesregler."),
    ("h2", "Klage"),
    ("p", "Er sikrede utilfreds med en afgørelse, kan sagen tages op med selskabets kundeansvarlige i København. "
          "Hvis sagen herefter ikke er løst, kan den indbringes for et uafhængigt ankenævn for forsikring. "
          "Oplysning herom gives i selskabets endelige svar."),
    ("h2", "Forældelse"),
    ("p", "Krav mod selskabet forældes efter reglerne i forældelsesloven."),
    ("h2", "Lovvalg og værneting"),
    ("p", "Forsikringsaftalen er underlagt dansk ret. Tvister afgøres ved danske domstole."),
]

DA_ANMELDELSE = [
    "Give selskabet de oplysninger og dokumenter, der er nødvendige for at behandle skaden, for eksempel "
    "kvitteringer og fotos.",
    "Anmelde tyveri, indbrud og hærværk til politiet straks og sende en kopi af anmeldelsen til selskabet.",
    "Opbevare beskadigede genstande, indtil selskabet har set dem eller givet tilladelse til, at de kasseres.",
    "Ikke anerkende erstatningsansvar eller betale erstatning uden selskabets samtykke.",
    "Begrænse skaden mest muligt.",
]

DA_ENGLISH = [
    ("p", "This page is an English summary of the Danish home insurance terms (Hjem Danmark). It is provided for "
          "information only. In the event of any difference, the Danish text prevails."),
    ("ul", ["The policy covers household contents (indbo) and, where shown in the policy (police), the building.",
            "Each cover (dækning) is described with what is and is not covered.",
            "The excess (selvrisiko) is set out in the section 'Selvrisiko'.",
            "Claims must be reported as quickly as possible (hurtigst muligt). The company may appoint an "
            "assessor (taksator).",
            "Safety regulations (sikkerhedsforskrifter) apply.",
            "The company may recover its outlay from a responsible party (regres)."]),
]
