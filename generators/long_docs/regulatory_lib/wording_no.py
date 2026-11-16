"""Norwegian (bokmål) policy wording content: LD009 motor 2015, LD011 home 2017."""
from __future__ import annotations

FELLES_INNLEDNING = [
    ("h2", "Om forsikringsavtalen"),
    ("p", "Forsikringsavtalen består av forsikringsbeviset, disse forsikringsvilkårene og eventuelle særvilkår. Dersom "
          "det er motstrid mellom dokumentene, gjelder forsikringsbeviset foran særvilkårene, og særvilkårene foran "
          "disse vilkårene. For øvrig gjelder lov om forsikringsavtaler (forsikringsavtaleloven) og annen lovgivning."),
    ("p", "Forsikringsgiver er Corvane Mutual Norge, filial av Corvane Mutual Insurance Society Limited, "
          "Fjordporten 4, 0150 Oslo. Selskapet er et gjensidig forsikringsselskap som eies av medlemmene, og står "
          "under tilsyn av National Insurance Supervisory Authority (NISA)."),
    ("h2", "Slik leser du vilkårene"),
    ("p", "Vilkårene er delt inn i dekningsavsnitt og felles bestemmelser. Hvert dekningsavsnitt beskriver hva "
          "forsikringen dekker, og hva den ikke dekker. Felles bestemmelser, sikkerhetsforskrifter og regler om "
          "skadeoppgjør gjelder for alle dekningsavsnitt."),
    ("p", "Ord som er definert i avsnittet «Definisjoner», har samme betydning overalt i vilkårene."),
]

FELLES_DEF = [
    ("Forsikringstaker", "Den som har inngått forsikringsavtalen med selskapet, og som er medlem av Corvane Mutual."),
    ("Sikrede", "Den som har krav på erstatning etter forsikringsavtalen."),
    ("Forsikringsbevis", "Dokumentet som angir hvem som er forsikret, hva som er forsikret, forsikringssummer, "
                         "egenandeler og forsikringstiden."),
    ("Forsikringstid", "Tidsrommet som er angitt i forsikringsbeviset. Forsikringen fornyes for ett år om gangen "
                       "dersom den ikke sies opp."),
    ("Egenandel", "Den delen av et erstatningsbeløp som sikrede selv må bære ved hver skade."),
    ("Skadetakstmann", "Den person selskapet utpeker til å besiktige skaden, fastsette årsaken og beregne "
                       "erstatningen."),
    ("Skjønn", "Fastsettelse av erstatningsbeløpet ved uavhengige skjønnsmenn når partene ikke blir enige."),
    ("Regress", "Selskapets rett til å kreve tilbake utbetalt erstatning fra den som er ansvarlig for skaden."),
    ("Skademelding", "Den skriftlige eller elektroniske meldingen sikrede gir selskapet om en skade."),
]

FELLES_UNNTAK = [
    "Krig, krigslignende handlinger, borgerkrig, revolusjon, opprør eller oppløp.",
    "Atomkjernereaksjon, atomkjernestråling eller radioaktiv forurensning.",
    "Terrorhandling, med de unntak som følger av lov om obligatorisk ansvarsforsikring.",
    "Skade som er voldt forsettlig av sikrede eller noen som handler på sikredes vegne.",
    "Skade som har oppstått før forsikringen trådte i kraft.",
    "Indirekte tap, driftstap og andre følgeskader, med mindre dette er særskilt nevnt.",
    "Bøter, gebyrer og lignende ilagt sikrede.",
    "Tap som følge av at sikrede ikke kan disponere tingen, med mindre annet er avtalt.",
]

FELLES_SLUTT = [
    ("h2", "Fornyelse og oppsigelse"),
    ("p", "Forsikringen fornyes automatisk for ett år av gangen med de vilkår og priser som selskapet da benytter, "
          "med mindre forsikringstakeren eller selskapet har sagt opp forsikringen etter reglene i "
          "forsikringsavtaleloven."),
    ("p", "Forsikringstakeren kan si opp forsikringen i forsikringstiden dersom det foreligger særlige grunner, for "
          "eksempel ved salg av den forsikrede tingen, eller ved flytting av forsikringen til et annet selskap."),
    ("h2", "Personopplysninger"),
    ("p", "Selskapet behandler personopplysninger for å administrere forsikringsavtalen, behandle skader og "
          "forebygge og avdekke svindel. Opplysningene behandles i samsvar med personopplysningsloven. Sikrede har "
          "rett til innsyn i og retting av egne opplysninger."),
    ("h2", "Klage"),
    ("p", "Dersom sikrede ikke er fornøyd med selskapets avgjørelse, kan saken tas opp med saksbehandler eller "
          "dennes leder. Sikrede kan deretter klage skriftlig til selskapets klageansvarlige i Oslo. Dersom saken "
          "fortsatt ikke løses, kan den bringes inn for en uavhengig klagenemnd for forsikring. Opplysninger om "
          "dette gis i selskapets endelige svar."),
    ("h2", "Foreldelse"),
    ("p", "Krav om erstatning foreldes etter reglene i forsikringsavtaleloven. Sikrede mister retten til "
          "erstatning dersom kravet ikke er meldt til selskapet innen ett år etter at sikrede fikk kunnskap om de "
          "forhold som begrunner kravet."),
    ("h2", "Lovvalg og verneting"),
    ("p", "Forsikringsavtalen reguleres av norsk lov. Tvister avgjøres ved norske domstoler."),
]

SKADEMELDING = [
    "Gi selskapet de opplysninger og dokumenter som er nødvendige for å behandle saken, herunder kvitteringer, "
    "garantibevis og bilder av skaden.",
    "Melde tyveri, innbrudd og hærverk til politiet straks, og sende kopi av anmeldelsen til selskapet.",
    "Ta vare på skadde gjenstander inntil selskapet har besiktiget dem eller samtykket i at de kan kastes.",
    "Ikke vedta ansvar, inngå forlik eller betale erstatning til tredjemann uten selskapets samtykke.",
    "Gi skadetakstmannen adgang til skadestedet og de skadde gjenstandene.",
    "Sette i verk rimelige tiltak for å avverge eller begrense skaden, så langt det er mulig.",
]


def motor(egenandel, egenandel_glass, notify):
    defs = FELLES_DEF + [
        ("Kjøretøyet", "Det motorvogn som er angitt i forsikringsbeviset, med fast montert utstyr og ett sett "
                       "hjul i tillegg til de som sitter på kjøretøyet."),
        ("Kasko", "Dekning for skade på kjøretøyet ved kollisjon, velt, utforkjøring og annen plutselig og uforutsett "
                  "ytre hendelse."),
        ("Delkasko", "Dekning for brann, tyveri, glasskade og redning."),
        ("Fører", "Den som kjører kjøretøyet med eiers samtykke og har gyldig førerkort for kjøretøyet."),
        ("Markedsverdi", "Det beløp det på skadedagen ville kostet å kjøpe et tilsvarende kjøretøy av samme merke, "
                         "modell, årsmodell, kjørelengde og stand."),
        ("Bonus", "Prisreduksjon som opptjenes ved skadefrie år, i samsvar med selskapets bonusregler."),
    ]
    sections = [
        ("Ansvar – lovpålagt trafikkforsikring", [
            ("h2", "Hva forsikringen dekker"),
            ("p", "Forsikringen dekker erstatningsansvar etter lov om ansvar for skade som motorvogner gjer "
                  "(bilansvarslova) for skade på person og ting som kjøretøyet volder ved trafikkuhell."),
            ("p", "Ansvarsdekningen gjelder også for skade kjøretøyet volder på annen manns eiendom, for eksempel på "
                  "bygninger, gjerder og andre kjøretøy, i den utstrekning sikrede er ansvarlig etter loven."),
            ("h2", "Hva forsikringen ikke dekker"),
            ("ul", ["Skade på kjøretøyet selv, med mindre kaskodekning er avtalt.",
                    "Skade på gods som transporteres med kjøretøyet, med mindre annet følger av loven.",
                    "Skade som skjer under motorsportløp eller trening til slike."]),
        ]),
        ("Delkasko – brann, tyveri, glass og redning", [
            ("h2", "Brann"),
            ("p", "Forsikringen dekker skade på kjøretøyet ved brann, lynnedslag og eksplosjon. Skade på elektriske "
                  "ledninger som følge av kortslutning dekkes dersom brann oppstår."),
            ("h2", "Tyveri og tyveriforsøk"),
            ("p", "Forsikringen dekker tyveri av kjøretøyet og skade ved tyveriforsøk, samt tyveri av fast montert "
                  "utstyr fra låst kjøretøy. Dersom kjøretøyet ikke er kommet til rette innen rimelig tid etter at "
                  "skaden ble meldt, regnes det som tapt."),
            ("ul", ["Selskapet dekker ikke tyveri dersom nøkkelen var etterlatt i eller på kjøretøyet.",
                    "Selskapet dekker ikke tyveri fra ulåst kjøretøy.",
                    "Selskapet dekker ikke tap av løse gjenstander, mobiltelefoner eller penger."]),
            ("h2", "Glasskade"),
            ("p", "Forsikringen dekker knusing av og sprekker i frontrute, sideruter og bakrute. Er ruten reparert i "
                  "stedet for skiftet, betaler sikrede ingen egenandel for reparasjonen."),
            ("h2", "Redning"),
            ("p", "Forsikringen dekker nødvendig redning av kjøretøyet til nærmeste verksted som kan utføre "
                  "reparasjonen, når kjøretøyet ikke kan kjøres etter en skade som er dekket av forsikringen, eller "
                  "etter driftsstopp."),
        ]),
        ("Kasko – skade på eget kjøretøy", [
            ("h2", "Hva forsikringen dekker"),
            ("p", "Forsikringen dekker skade på kjøretøyet ved kollisjon, velt, utforkjøring og annen plutselig og "
                  "uforutsett ytre hendelse, herunder hærverk."),
            ("p", "Ved skade velger selskapet om kjøretøyet skal repareres, erstattes med et tilsvarende kjøretøy, "
                  "eller om skaden skal erstattes kontant. Erstatningen kan ikke overstige kjøretøyets markedsverdi."),
            ("h2", "Hva forsikringen ikke dekker"),
            ("ul", ["Skade som skyldes slitasje, rust, frost, materialfeil, konstruksjonsfeil eller feil ved "
                    "montering.",
                    "Skade på dekk og felger alene, med mindre skaden er voldt ved hærverk eller kollisjon.",
                    "Verdiforringelse etter reparasjon.",
                    "Skade som oppstår når kjøretøyet brukes av noen som ikke har gyldig førerkort.",
                    "Skade som oppstår når føreren er påvirket av alkohol eller andre berusende eller bedøvende midler."]),
        ]),
        ("Fører- og passasjerulykke", [
            ("p", "Forsikringen dekker ulykkesskade på fører og passasjerer i kjøretøyet med de beløp som er angitt i "
                  "forsikringsbeviset, i tillegg til erstatning etter bilansvarslova."),
            ("p", "Erstatningen utbetales ved dødsfall eller varig medisinsk invaliditet som følge av ulykken. "
                  "Invaliditetsgraden fastsettes etter de til enhver tid gjeldende tabeller."),
        ]),
        ("Leiebil", [
            ("p", "Dersom leiebil er avtalt og angitt i forsikringsbeviset, dekker forsikringen leie av bil i "
                  "reparasjonstiden etter en skade som er dekket under kasko eller delkasko, i det antall dager som "
                  "fremgår av forsikringsbeviset."),
            ("p", "Selskapet dekker ikke drivstoff, bompenger eller andre driftsutgifter for leiebilen."),
        ]),
    ]
    egenandel_avsnitt = [
        ("p", f"Ordinær egenandel ved skade på kjøretøyet er NOK {egenandel:,}".replace(",", " ") +
              " for hver skade under kasko og delkasko, med mindre en annen egenandel er avtalt og angitt i "
              "forsikringsbeviset."),
        ("p", f"Egenandel ved glasskade er NOK {egenandel_glass:,}".replace(",", " ") +
              " når ruten skiftes. Ved reparasjon av rute trekkes ingen egenandel."),
        ("p", "Ved tyveri av kjøretøyet trekkes i tillegg en egenandel dersom kjøretøyet ikke var utstyrt med "
              "godkjent elektronisk startsperre."),
        ("p", "Det trekkes ingen egenandel under ansvarsdekningen når skaden er voldt av kjøretøyet i trafikk."),
        ("p", "Inntreffer flere skader ved samme hendelse, trekkes bare én egenandel, og da den høyeste."),
    ]
    sikkerhet = [
        "Kjøretøyet skal være låst og vinduer lukket når det forlates. Nøkler skal oppbevares slik at "
        "uvedkommende ikke får tilgang til dem.",
        "Føreren skal ha gyldig førerkort for kjøretøyet og må ikke være påvirket av alkohol eller andre berusende "
        "eller bedøvende midler.",
        "Kjøretøyet skal ha godkjent periodisk kjøretøykontroll og være i forskriftsmessig stand.",
        "Kjøretøyet skal ikke brukes til utleie eller persontransport mot betaling, med mindre dette er avtalt.",
        "Fast montert tilleggsutstyr skal være forsvarlig festet.",
    ]
    return defs, sections, egenandel_avsnitt, sikkerhet, notify


def home(egenandel, notify):
    defs = FELLES_DEF + [
        ("Bygning", "Den bygning som er angitt i forsikringsbeviset, med fast inventar og fast utstyr som er "
                    "montert for bygningens varige bruk."),
        ("Innbo", "Løsøre som tilhører sikrede og som hører til en privat husholdning, herunder klær, møbler og "
                  "husholdningsartikler."),
        ("Vannskade", "Skade ved utstrømning av vann fra rør, sanitærinstallasjoner, varmeanlegg og tilknyttede "
                      "apparater."),
        ("Frostskade", "Skade på bygning og innbo som skyldes at vann i rør, installasjoner eller apparater har "
                       "frosset."),
        ("Naturskade", "Skade som direkte skyldes naturulykke som skred, storm, flom, stormflo, jordskjelv eller "
                       "vulkanutbrudd, jf. lov om naturskadeforsikring."),
        ("Snølast", "Skade på bygning ved at tak eller bærende konstruksjoner gir etter for vekten av snø eller is."),
        ("Uhellsskade", "Plutselig og uforutsett skade på innbo som ikke er dekket av andre dekningsavsnitt."),
    ]
    sections = [
        ("Hvem og hva forsikringen gjelder for", [
            ("h2", "Hvem forsikringen gjelder for"),
            ("p", "Forsikringen gjelder for forsikringstakeren og medlemmer av forsikringstakerens husstand som bor "
                  "fast sammen med forsikringstakeren."),
            ("p", "Barn under utdanning som midlertidig bor utenfor hjemmet, omfattes av forsikringen for innbo "
                  "som de har med seg."),
            ("h2", "Hvor forsikringen gjelder"),
            ("p", "Forsikringen gjelder på forsikringsstedet som er angitt i forsikringsbeviset. For innbo som "
                  "midlertidig er utenfor forsikringsstedet, gjelder forsikringen i Norden med de begrensninger som "
                  "fremgår av vilkårene."),
            ("h2", "Hva forsikringen omfatter"),
            ("p", "Forsikringen omfatter bygning og innbo i den utstrekning dette fremgår av forsikringsbeviset."),
        ]),
        ("Dekning", [
            ("h2", "Brannskade"),
            ("p", "Forsikringen dekker skade ved brann, det vil si ild som er kommet løs, samt lynnedslag, "
                  "eksplosjon og plutselig utslipp av røyk eller sot fra fyringsanlegg."),
            ("ul", ["Selskapet dekker ikke skade på ting som er utsatt for nyttebrann, for eksempel i peis eller ovn.",
                    "Selskapet dekker ikke svimerker eller sengebrann uten at det har oppstått flamme."]),
            ("h2", "Vannskade"),
            ("p", "Forsikringen dekker vannskade ved plutselig og uforutsett utstrømning av vann fra rør, sanitær- "
                  "og varmeanlegg og tilknyttede apparater, akvarier og vannsenger."),
            ("ul", ["Selskapet dekker ikke skade som skyldes vann som siver langsomt over tid, eller fuktighet og "
                    "kondens.",
                    "Selskapet dekker ikke utbedring av selve røret eller installasjonen som vannet strømmet ut fra.",
                    "Selskapet dekker ikke skade som skyldes vann fra tak, takrenner eller nedløpsrør."]),
            ("h2", "Frostskade"),
            ("p", "Forsikringen dekker frostskade på bygning og innbo, herunder skade på rør, installasjoner og "
                  "tilknyttede apparater som følge av at vann har frosset, samt vannskade som oppstår når det "
                  "frosne vannet tiner."),
            ("ul", ["Frostskade dekkes ikke dersom sikkerhetsforskriften om oppvarming og tømming av vannførende "
                    "installasjoner ikke er overholdt, jf. forsikringsavtaleloven.",
                    "Frostskade på hageanlegg, utvendige vannkraner og svømmebasseng dekkes ikke."]),
            ("h2", "Naturskade"),
            ("p", "Forsikringen dekker naturskade på bygning og innbo i samsvar med lov om naturskadeforsikring. "
                  "Skaden må skyldes naturulykke som skred, storm, flom, stormflo, jordskjelv eller vulkanutbrudd."),
            ("h2", "Storm og snølast"),
            ("p", "Forsikringen dekker skade ved storm, det vil si vind med middelhastighet som i forsikringsvilkårenes "
                  "forstand regnes som storm, samt skade ved snølast når tak eller bærende konstruksjon gir etter."),
            ("h2", "Tyveri og hærverk"),
            ("p", "Forsikringen dekker tyveri av innbo fra låst bolig og hærverk på bygning og innbo, når noen "
                  "har tatt seg inn i boligen ved bruk av makt, eller når tyveriet eller hærverket er begått av "
                  "person som har lovlig adgang til boligen og som ikke tilhører husstanden."),
            ("ul", ["Selskapet dekker ikke tyveri fra ulåst bolig eller fra fellesarealer som ikke er låst.",
                    "Selskapet dekker ikke tyveri av penger utover det beløp som fremgår av forsikringsbeviset."]),
            ("h2", "Glass og sanitærutstyr"),
            ("p", "Forsikringen dekker brudd på glass i vinduer og dører, servant, toalettskål og badekar, samt "
                  "keramiske koketopper, når glasset eller utstyret er fast montert i bygningen."),
            ("h2", "Uhellsskade (tilleggsdekning)"),
            ("p", "Dersom det fremgår av forsikringsbeviset, dekker forsikringen plutselig og uforutsett skade på "
                  "innbo som ikke dekkes av andre dekningsavsnitt, for eksempel når en gjenstand mistes i gulvet."),
        ]),
        ("Ansvar og rettshjelp", [
            ("h2", "Ansvar"),
            ("p", "Forsikringen dekker sikredes erstatningsansvar som privatperson og som eier eller bruker av den "
                  "forsikrede boligen, for skade på person og ting, med den forsikringssum som fremgår av "
                  "forsikringsbeviset."),
            ("ul", ["Selskapet dekker ikke ansvar for skade på ting som sikrede eier, leier eller låner.",
                    "Selskapet dekker ikke ansvar i forbindelse med yrkesutøvelse eller næringsvirksomhet.",
                    "Selskapet dekker ikke ansvar som skyldes bruk av motorvogn, båt eller luftfartøy."]),
            ("h2", "Rettshjelp"),
            ("p", "Forsikringen dekker sikredes nødvendige og rimelige utgifter til advokat og sakkyndige ved tvist "
                  "som kan bringes inn for domstolene, og som har oppstått i forsikringstiden, med de begrensninger "
                  "som fremgår av forsikringsbeviset."),
        ]),
        ("Ekstrautgifter og husleietap", [
            ("p", "Er boligen ubeboelig etter en skade som er dekket av forsikringen, dekker selskapet nødvendige og "
                  "dokumenterte merutgifter til midlertidig bolig i den tid det tar å sette boligen i stand igjen, "
                  "begrenset til det som fremgår av forsikringsbeviset."),
            ("p", "Ved utleie av del av bygningen dekker forsikringen tap av husleie i reparasjonstiden, når "
                  "utleiedelen er ubeboelig etter en dekket skade."),
            ("p", "Selskapet dekker også nødvendige utgifter til opprydding og riving etter en dekket skade."),
        ]),
    ]
    egenandel_avsnitt = [
        ("p", f"Ordinær egenandel for skade på bygning og innbo er NOK {egenandel:,}".replace(",", " ") +
              " for hver skade, med mindre en annen egenandel er avtalt og angitt i forsikringsbeviset."),
        ("p", "Ved naturskade gjelder den egenandel som er fastsatt i medhold av lov om naturskadeforsikring."),
        ("p", "Rammes både bygning og innbo av samme skadetilfelle, trekkes bare én egenandel."),
        ("p", "Er en sikkerhetsforskrift ikke overholdt, kan selskapet i tillegg redusere erstatningen etter reglene "
              "i forsikringsavtaleloven."),
    ]
    sikkerhet = [
        "Bygningen skal holdes tilstrekkelig oppvarmet til å hindre frostskade. Er bygningen ikke i bruk, skal "
        "vannet stenges og vannførende installasjoner tømmes.",
        "Vannførende installasjoner skal være montert av fagkyndig og vedlikeholdes slik at lekkasje unngås.",
        "Boligen skal ha røykvarsler i hver etasje og godkjent slokkeutstyr i samsvar med gjeldende forskrifter.",
        "Dører og vinduer skal være låst og lukket når boligen forlates.",
        "Snø og is skal fjernes fra taket når snømengden er så stor at det er fare for skade på bygningen.",
        "Levende lys skal ikke etterlates uten tilsyn.",
    ]
    return defs, sections, egenandel_avsnitt, sikkerhet, notify


SKADEOPPGJOR = [
    ("h2", "Skadetakstmann og besiktigelse"),
    ("p", "Selskapet kan utpeke en skadetakstmann til å besiktige skaden og beregne erstatningen. Sikrede skal gi "
          "skadetakstmannen adgang til skadestedet og legge frem de opplysninger som er nødvendige."),
    ("p", "Selskapet har rett til å kreve at skaden repareres av fagfolk som selskapet anviser, eller at "
          "skadde gjenstander erstattes gjennom selskapets leverandører."),
    ("h2", "Hvordan erstatningen beregnes"),
    ("p", "Erstatningen beregnes på grunnlag av hva det på skadedagen ville koste å reparere eller gjenskaffe den "
          "skadde tingen med tilsvarende ting av samme type og kvalitet. Det gjøres fradrag for verdiforringelse "
          "på grunn av alder, bruk og slitasje der dette fremgår av vilkårene."),
    ("p", "Dersom reparasjon eller gjenskaffelse ikke foretas, er selskapet ikke forpliktet til å betale mer enn "
          "tingens omsetningsverdi."),
    ("h2", "Skjønn"),
    ("p", "Dersom sikrede og selskapet ikke blir enige om erstatningens størrelse, kan hver av partene kreve at "
          "erstatningen fastsettes ved skjønn. Hver av partene velger en skjønnsmann, og skjønnsmennene velger en "
          "oppmann før skjønnet begynner."),
    ("h2", "Renter"),
    ("p", "Selskapet betaler renter av erstatningen etter reglene i forsikringsavtaleloven."),
    ("h2", "Regress"),
    ("p", "Selskapet har regress mot den som er erstatningsansvarlig for skaden, i den utstrekning loven gir "
          "adgang til det. Når selskapet har betalt erstatning, overtar selskapet sikredes krav mot skadevolderen "
          "(regressfordring). Sikrede må ikke gi avkall på retten til erstatning fra skadevolderen uten selskapets "
          "samtykke."),
]

ENGLISH_SUMMARY_MOTOR = [
    ("p", "This page is an English summary of the Norwegian policy terms for private motor insurance (Motor Privat "
          "Norge). It is provided for information only. In the event of any difference, the Norwegian text prevails."),
    ("ul", ["The policy combines compulsory motor liability (ansvar) with optional partial cover (delkasko: fire, "
            "theft, glass and recovery) and comprehensive cover (kasko).",
            "The excess (egenandel) for each claim is set out in the section 'Egenandel'. Glass replacement has a "
            "separate excess; glass repairs carry no excess.",
            "Claims must be reported to the company without undue delay (uten ugrunnet opphold).",
            "The company may appoint an assessor (skadetakstmann) to inspect the damage.",
            "Safety regulations (sikkerhetsforskrifter) apply, for example locking the vehicle and keeping keys safe. "
            "Breach may reduce the claim payment.",
            "The company may recover its outlay from a responsible third party (regress).",
            "Complaints are first handled by the company in Oslo and may then be referred to an independent "
            "complaints board."]),
]

ENGLISH_SUMMARY_HOME = [
    ("p", "This page is an English summary of the Norwegian policy terms for home insurance (Hjem Norge). It is "
          "provided for information only. In the event of any difference, the Norwegian text prevails."),
    ("ul", ["The policy covers the building and household contents (bygning og innbo) as shown in the policy "
            "certificate (forsikringsbevis).",
            "Covered perils are listed in the section 'Dekning'; please read that section for the full scope of "
            "cover and the exclusions that apply.",
            "The excess (egenandel) is set out in the section 'Egenandel'.",
            "Claims must be reported without undue delay (uten ugrunnet opphold). The company may appoint an "
            "assessor (skadetakstmann).",
            "Safety regulations (sikkerhetsforskrifter), such as keeping the building heated, must be followed.",
            "The company may recover its outlay from a responsible third party (regress)."]),
]
