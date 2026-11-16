"""Additional wording sections (LD004-LD011): claims guides, endorsements, settlement tables, word lists.

Everything here is generic contract wording. It deliberately states no amounts, periods or other
product parameters: excesses, limits and notification conditions live only in the sections the
placements name (see wordings.py).

Block grammar (shared with wording_en/no/sv_da):
    ("h2", text) ("h3", text) ("p", text) ("def", term, text) ("ul", [items]) ("ol", [items])
    ("table", title, rows, widths_mm) ("pb",)
"""
from __future__ import annotations

# =============================================================================================
# English (UK) wordings
# =============================================================================================

EN_HOW_TO_CLAIM = [
    ("p", "This part of the booklet explains, step by step, what happens when you tell us about a loss. It does "
          "not change the claims conditions, which you must still follow."),
    ("h2", "Step 1 – Make things safe"),
    ("p", "Take any reasonable steps to stop the loss or damage getting worse. This might mean turning off the water "
          "supply, arranging a temporary covering for a broken window or moving undamaged property to a safe place. "
          "We will pay the reasonable cost of emergency measures taken to protect property that is insured."),
    ("h2", "Step 2 – Give us notification of loss"),
    ("p", "Contact our claims line using the telephone number shown in your schedule, or write to us at the "
          "address in your schedule. Please have your policy number ready. If you are unable to contact us "
          "yourself, someone else may give notification of loss on your behalf."),
    ("ul", ["your name, address and policy number;",
            "the date, time and place of the incident;",
            "what happened and what has been lost or damaged;",
            "the names and addresses of any other people involved and of any witnesses;",
            "the crime reference number, if the police have been told."]),
    ("h2", "Step 3 – We register your claim"),
    ("p", "We will give you a claim number, which you should quote whenever you contact us. We will explain what "
          "happens next, what information we need from you and who will be dealing with your claim."),
    ("h2", "Step 4 – Inspection"),
    ("p", "For some claims we will ask a member of our own staff to visit you. For larger or more complex claims we "
          "may appoint a loss adjuster, who is an independent specialist acting on our behalf. The loss adjuster "
          "or Claims Assessor will inspect the damage, discuss the claim with you and report to us."),
    ("p", "Please do not carry out permanent repairs before the inspection unless we have agreed. You may carry out "
          "emergency repairs, but keep any damaged parts and take photographs before and after the work."),
    ("h2", "Step 5 – Our decision"),
    ("p", "When we have the information we need, we will tell you whether your claim is covered and how we propose "
          "to settle it. If we cannot accept all or part of your claim, we will explain why in writing and tell you "
          "how to ask us to review our decision."),
    ("h2", "Step 6 – Settlement"),
    ("p", "We may settle your claim by repairing, reinstating or replacing the damaged property, or by making a "
          "payment. Where we can offer a repair or replacement through one of our suppliers, we may limit any cash "
          "payment to the amount we would have paid our supplier. Any excess will be deducted from the settlement."),
    ("h2", "Step 7 – Recovering our costs"),
    ("p", "If someone else was responsible for the loss, we may take action in your name to recover what we have "
          "paid. We will also try to recover any uninsured losses you ask us to, such as your excess, but we cannot "
          "guarantee that these will be recovered."),
]

EN_FRAUD_SANCTIONS = [
    ("h2", "Fraudulent claims"),
    ("p", "If you or anyone acting on your behalf makes a claim which is fraudulent or false in any way, or supports "
          "a claim with false or forged documents, we will not pay the claim and we may cancel this policy from the "
          "date of the fraudulent act. We may also keep any premium you have paid and recover from you any sums we "
          "have already paid in respect of the claim, together with our costs."),
    ("p", "We may share information with other insurers, fraud prevention agencies and the police. If false or "
          "inaccurate information is provided and fraud is identified, details may be recorded to prevent fraud and "
          "money laundering."),
    ("h2", "Misrepresentation"),
    ("p", "You must take reasonable care to answer all our questions honestly and to the best of your knowledge. If "
          "you deliberately or recklessly give us false information, we may treat this policy as if it never "
          "existed and decline all claims. If you carelessly give us false information, we may change the terms of "
          "the policy or reduce the amount we pay for a claim in proportion to the premium you would have paid."),
    ("h2", "Financial sanctions"),
    ("p", "We will not provide cover, pay any claim or provide any benefit under this policy to the extent that "
          "doing so would expose us to any sanction, prohibition or restriction under United Nations resolutions or "
          "the trade or economic sanctions, laws or regulations of the United Kingdom or the European Union."),
    ("h2", "Rights of third parties"),
    ("p", "A person who is not a party to this policy has no right to enforce any of its terms, except where the "
          "policy says otherwise. This does not affect any right or remedy of a third party which exists apart "
          "from that legislation."),
]

_EN_ENDORSE = {
    "motor": [
        ("Endorsement 01 – Named drivers only", "Cover applies only while your car is being driven by you or by a "
         "person named in your certificate of motor insurance. All other drivers are excluded."),
        ("Endorsement 02 – Social, domestic and pleasure use only", "Your car is not insured while it is used for "
         "commuting or for any business purpose, even if such use is shown elsewhere in your schedule."),
        ("Endorsement 03 – Approved immobiliser", "We will not pay for loss or damage caused by theft or attempted "
         "theft unless the immobiliser fitted to your car was set and in full working order at the time."),
        ("Endorsement 04 – Interested party", "We have noted the interest of the finance company named in your "
         "schedule. We will pay any claim for the total loss of your car to the finance company first, and any "
         "balance to you."),
        ("Endorsement 05 – Protected no claim discount", "Your no claim discount will not be reduced following a "
         "claim, within the limits set out in your schedule. Protection does not prevent your premium from "
         "increasing for other reasons."),
        ("Endorsement 06 – Third party, fire and theft only", "Section 2 of this policy applies only to loss or "
         "damage caused by fire, lightning, explosion, theft or attempted theft. Section 3 and Section 4 do not "
         "apply."),
        ("Endorsement 07 – Garaging", "Loss or damage caused by theft or attempted theft between the hours shown in "
         "your schedule is covered only if your car was kept in a locked private garage at the time."),
        ("Endorsement 08 – Additional excess for young or inexperienced drivers", "An additional excess applies to "
         "every claim under Section 2 while your car is being driven by a person in the category shown in your "
         "schedule. This additional excess is payable on top of every other excess."),
        ("Endorsement 09 – Trade plates and motor trade use", "No cover applies while your car is being used under "
         "trade plates or while it is in the custody of a member of the motor trade, other than for servicing or "
         "repair."),
    ],
    "home": [
        ("Endorsement H1 – Interested party (mortgagee)", "We have noted the interest of the lender named in your "
         "schedule. Any payment for damage to the buildings may be made to the lender, or jointly to you and the "
         "lender."),
        ("Endorsement H2 – Minimum security", "Cover for theft or attempted theft applies only if all external doors "
         "are fitted with the locks described in your schedule and all accessible windows have key-operated locks, "
         "and these are in use when your home is left unattended."),
        ("Endorsement H3 – Intruder alarm", "The intruder alarm described in your schedule must be set whenever your "
         "home is left unattended and must be maintained under a contract with an approved installer."),
        ("Endorsement H4 – Flood exclusion", "Section 1 and Section 2 do not cover loss or damage caused by flood. "
         "All other causes remain covered."),
        ("Endorsement H5 – Subsidence exclusion", "Section 1 does not cover damage caused by subsidence, heave or "
         "landslip. This endorsement applies where we were told of previous movement at your home."),
        ("Endorsement H6 – Listed building", "Reinstatement will be carried out using materials and methods "
         "required by the planning authority. You must tell us of any change in the listing status of your home."),
        ("Endorsement H7 – Lodgers", "Theft is covered only if it involves forcible and violent entry to or exit "
         "from your home. Theft by lodgers or paying guests is not covered."),
        ("Endorsement H8 – Business use", "Business equipment kept in your home is covered within the limit shown in "
         "your schedule. Stock, goods held in trust and money belonging to the business are not covered."),
        ("Endorsement H9 – Non-standard construction", "Your home is of the construction described in your "
         "schedule. Cover is provided on the basis of that description, and you must tell us of any alteration."),
    ],
    "commercial": [
        ("Clause C1 – Sprinkler installation", "The automatic sprinkler installation must be maintained in full "
         "working order and inspected under a contract with a competent engineer. You must tell us immediately of "
         "any impairment or shut-down."),
        ("Clause C2 – Intruder alarm", "The intruder alarm must be set whenever the premises are closed for business "
         "and must be connected to a monitoring centre approved by us."),
        ("Clause C3 – Hot work", "Where any process involving welding, flame cutting or the use of blow lamps or "
         "angle grinders is carried out at the premises, a hot work permit system acceptable to us must be in "
         "operation and a fire watch maintained after the work stops."),
        ("Clause C4 – Unoccupied buildings", "If any building becomes unoccupied you must tell us, inspect the "
         "building weekly, remove combustible waste, turn off utilities other than those needed for fire "
         "protection and secure all doors and windows."),
        ("Clause C5 – Waste control", "Trade waste must be removed from the buildings at the end of each working day "
         "and kept in metal containers with close-fitting lids, positioned away from the buildings."),
        ("Clause C6 – Electrical installation", "The electrical installation must be inspected and tested by a "
         "qualified electrician at the intervals recommended by the electrician, and any defects corrected "
         "promptly."),
        ("Clause C7 – Day one reinstatement", "Where the schedule shows a declared value, the sums insured for "
         "buildings and machinery will be adjusted at the end of the period of insurance in line with the declared "
         "value and any inflation provision shown."),
        ("Clause C8 – Composite panels", "Where the buildings include insulated composite panels, any panels that are "
         "not certified to an appropriate fire standard must be identified in a schedule supplied to us."),
        ("Clause C9 – Cooking ranges and ducting", "Grease filters and extraction ducting must be cleaned at regular "
         "intervals by a specialist contractor and records of cleaning kept for our inspection."),
    ],
    "liability": [
        ("Clause L1 – Heat application", "Where work involving the application of heat is carried out away from your "
         "premises, the area must be cleared of combustible materials, suitable fire extinguishers must be "
         "available and the area must be inspected after the work is completed."),
        ("Clause L2 – Work at height", "This policy does not cover liability arising from work at a height greater "
         "than that shown in your schedule unless we have agreed in writing."),
        ("Clause L3 – Work below ground", "This policy does not cover liability arising from work below ground deeper "
         "than that shown in your schedule unless we have agreed in writing."),
        ("Clause L4 – Underground services", "Before any excavation you must obtain plans of underground services "
         "from the relevant utility companies and use detection equipment to locate them."),
        ("Clause L5 – Indemnity to principals", "Where a contract requires it, we will indemnify the principal for "
         "whom you are carrying out work, as if the principal were insured under this policy, but only for "
         "liability arising from your work."),
        ("Clause L6 – Cross liabilities", "Where more than one party is insured, this policy applies as if a separate "
         "policy had been issued to each, but our total liability will not exceed the limit of indemnity."),
        ("Clause L7 – Contractual liability", "We will not indemnify you for liability you have accepted under a "
         "contract which would not have attached in the absence of that contract, unless we have agreed."),
        ("Clause L8 – Products supplied overseas", "Products exported to the territories shown in your schedule are "
         "covered only where the products were exported without your knowledge or where we have agreed."),
        ("Clause L9 – Sudden and accidental pollution", "Liability for pollution or contamination is covered only "
         "where it is caused by a sudden, identifiable, unintended and unexpected incident at a specific time and "
         "place."),
    ],
}

_EN_CARE = {
    "motor": ("Looking after your car", [
        ("p", "Most claims could not have been prevented, but some simple precautions reduce the risk of theft and "
              "damage and help to keep your premium down."),
        ("ul", ["Always remove the keys and lock your car when you leave it, even for a short time.",
                "Never leave the keys or the vehicle documents inside the car.",
                "Keep valuables out of sight, preferably in a locked boot.",
                "Have your car serviced regularly and keep the tyres, lights and brakes in good condition.",
                "Repair chips in the windscreen promptly: a small chip can quickly spread into a crack.",
                "Park in a garage or in a well-lit area wherever possible."]),
        ("h2", "After an accident"),
        ("ol", ["Stop and stay at the scene.",
                "Check whether anyone is injured and call the emergency services if needed.",
                "Exchange names, addresses and insurance details with the other driver.",
                "Take photographs of the scene and the vehicles.",
                "Write down the names and addresses of any witnesses.",
                "Do not admit fault or offer to pay for damage.",
                "Give us notification of loss as soon as you can."]),
    ]),
    "home": ("Looking after your home", [
        ("p", "Taking care of your home reduces the chance of a claim and can prevent a small problem becoming a "
              "large one."),
        ("h2", "Preventing water damage"),
        ("ul", ["Know where your stopcock is and check that it turns.",
                "Lag pipes and water tanks in the loft and in unheated areas.",
                "Keep your heating on a low setting during cold weather, even when you are away.",
                "Replace worn seals around baths and showers, and repair dripping taps promptly.",
                "Check flexible hoses on washing machines and dishwashers for wear."]),
        ("h2", "Preventing fire"),
        ("ul", ["Fit smoke alarms on every floor and test them regularly.",
                "Do not leave cooking unattended.",
                "Have chimneys swept regularly if you use an open fire or wood-burning stove.",
                "Do not overload electrical sockets."]),
        ("h2", "Preventing theft"),
        ("ul", ["Lock all doors and windows whenever you go out.",
                "Use timer switches for lights when you are away.",
                "Keep ladders and tools locked away.",
                "Mark valuable items with your postcode and keep receipts and photographs."]),
        ("h2", "Keeping your home in good repair"),
        ("p", "Inspect your roof, gutters and drains regularly. Damage caused by wear and tear or by gradual "
              "deterioration is not covered, so routine maintenance is important."),
    ]),
    "commercial": ("Risk management guidance", [
        ("p", "This guidance is provided to help you manage the risks to your business. It does not form part of the "
              "policy conditions, but following it may help to prevent a loss and to speed up the handling of any "
              "claim."),
        ("h2", "Fire safety"),
        ("ul", ["Carry out and record a fire risk assessment and review it whenever the premises change.",
                "Keep escape routes clear and fire doors closed.",
                "Store flammable liquids in approved containers and in a designated area.",
                "Train staff in the use of fire extinguishers and in the evacuation procedure."]),
        ("h2", "Security"),
        ("ul", ["Check that all doors and windows are secured at the end of each day.",
                "Control the issue of keys and alarm codes and change codes when staff leave.",
                "Keep stock of high value in a secure area."]),
        ("h2", "Business continuity"),
        ("p", "A written business continuity plan, tested at regular intervals, will help you to resume trading after "
              "a loss. Keep copies of important records off site and agree arrangements with key suppliers in "
              "advance."),
        ("h2", "Escape of water"),
        ("p", "Escape of water is a frequent cause of loss in commercial premises, particularly when they are closed "
              "over weekends and holiday periods. Maintain heating in cold weather, know where stopcocks are and "
              "consider fitting leak detection equipment."),
    ]),
    "liability": ("Health and safety guidance", [
        ("p", "Good health and safety management protects your employees and the public, and helps you to defend "
              "claims. The following guidance does not form part of the policy conditions."),
        ("h2", "Risk assessment"),
        ("p", "Identify the hazards in your work, decide who might be harmed and how, evaluate the risks and decide on "
              "precautions. Record your findings and review them regularly."),
        ("h2", "Accident reporting"),
        ("ul", ["Keep an accident book and record every accident, however minor.",
                "Investigate accidents and near misses and record what was done to prevent a recurrence.",
                "Keep copies of training records, maintenance records and safety inspections.",
                "Tell us about any accident which might lead to a claim."]),
        ("h2", "Defending a claim"),
        ("p", "The success of a defence often depends on the records you keep. Please send us all relevant documents "
              "promptly when we ask for them, including risk assessments, training records, maintenance records and "
              "the accident book entry."),
        ("h2", "Contractors and subcontractors"),
        ("p", "Check that any contractors you engage hold appropriate insurance and are competent to carry out the "
              "work. Keep evidence of the checks you have made."),
    ]),
}


def en_extra(kind: str) -> dict:
    """Extra English sections keyed by where they are inserted."""
    endorse = [("p", "The following endorsements apply only where the endorsement number is shown in your "
                     "schedule. Where an endorsement applies, it overrides any other term of this policy to the "
                     "extent that they conflict.")]
    for title, text in _EN_ENDORSE[kind]:
        endorse += [("h3", title), ("p", text)]
    care_title, care = _EN_CARE[kind]
    return {"endorsements": ("Endorsements", endorse),
            "how_to_claim": ("How to make a claim – step by step", EN_HOW_TO_CLAIM),
            "fraud": ("Fraud, misrepresentation and sanctions", EN_FRAUD_SANCTIONS),
            "care": (care_title, care)}


# =============================================================================================
# Norwegian (bokmål)
# =============================================================================================

NO_PREMIE = [
    ("h2", "Betaling av premie"),
    ("p", "Premien forfaller til betaling ved forsikringstidens begynnelse og deretter ved hver fornyelse. Selskapet "
          "sender premievarsel med opplysning om beløp, forfallsdato og hvilke forsikringer varselet gjelder. "
          "Forsikringstakeren kan avtale å betale premien i terminer. Det kan da påløpe et termingebyr, som "
          "fremgår av premievarselet."),
    ("h2", "Følger av manglende betaling"),
    ("p", "Betales ikke premien innen forfall, sender selskapet et skriftlig varsel med en ny betalingsfrist. "
          "Varselet opplyser om at forsikringen opphører dersom premien ikke betales innen den nye fristen. "
          "Fristen er ikke kortere enn det forsikringsavtaleloven krever. Skader som inntreffer etter at "
          "forsikringen er opphørt, dekkes ikke."),
    ("h2", "Endring av premie og vilkår"),
    ("p", "Selskapet kan endre premie og vilkår med virkning fra hovedforfall. Endringene varsles skriftlig sammen "
          "med premievarselet for den nye forsikringsperioden. Godtar forsikringstakeren ikke endringene, kan "
          "forsikringen sies opp med virkning fra hovedforfall."),
    ("h2", "Tilbakebetaling ved opphør"),
    ("p", "Opphører forsikringen før forsikringstiden er ute, har forsikringstakeren krav på å få tilbake premien "
          "for den gjenværende delen av forsikringstiden. Selskapet kan trekke fra et administrasjonsgebyr etter "
          "de satser som gjelder på opphørstidspunktet."),
    ("h2", "Medlemskap"),
    ("p", "Forsikringstakeren blir medlem av Corvane Mutual når avtalen inngås. Medlemskapet gir rett til å delta i "
          "selskapets medlemsdemokrati i samsvar med vedtektene, men innebærer ikke plikt til å betale noe utover "
          "avtalt premie. Medlemskapet opphører når forsikringsforholdet opphører."),
]

NO_OPPLYSNING = [
    ("h2", "Forsikringstakerens opplysningsplikt"),
    ("p", "Forsikringstakeren skal gi riktige og fullstendige svar på selskapets spørsmål ved inngåelse og "
          "fornyelse av avtalen. Forsikringstakeren skal også av eget tiltak opplyse om særlige forhold som han "
          "eller hun må forstå er av vesentlig betydning for selskapets vurdering av risikoen."),
    ("p", "Er opplysningsplikten forsømt, kan selskapets ansvar bli redusert eller falle bort etter reglene i "
          "forsikringsavtaleloven. Selskapet kan også si opp forsikringen."),
    ("h2", "Endring av risiko"),
    ("p", "Forsikringstakeren skal straks melde fra til selskapet om endringer i forhold som er angitt i "
          "forsikringsbeviset, eller som forsikringstakeren har opplyst om ved inngåelsen, når endringen øker "
          "risikoen for skade."),
    ("h2", "Fremkallelse av forsikringstilfellet"),
    ("p", "Har sikrede forsettlig fremkalt forsikringstilfellet, svarer ikke selskapet. Har sikrede ved grov "
          "uaktsomhet fremkalt forsikringstilfellet, kan selskapets ansvar settes ned eller falle bort. Ved "
          "avgjørelsen legges det vekt på graden av skyld, skadeforløpet og omstendighetene ellers."),
    ("h2", "Identifikasjon"),
    ("p", "Ved anvendelse av reglene om opplysningsplikt, sikkerhetsforskrifter og fremkallelse av "
          "forsikringstilfellet identifiseres sikrede med den som med sikredes samtykke har ansvar for det "
          "forsikrede, i den utstrekning loven tillater det."),
    ("h2", "Svik"),
    ("p", "Har sikrede svikaktig fremkalt et forsikringstilfelle, eller gitt uriktige eller ufullstendige "
          "opplysninger for å oppnå en erstatning sikrede vet eller må forstå at han eller hun ikke har krav på, "
          "mister sikrede retten til erstatning for den aktuelle skaden. Selskapet kan i tillegg si opp alle "
          "avtaler med forsikringstakeren og kreve dekket sine utgifter til utredning av saken."),
    ("p", "Forhold som gir grunn til mistanke om svik, kan bli anmeldt til politiet. Selskapet kan registrere "
          "opplysninger om skaden i bransjens felles skaderegister."),
    ("h2", "Dobbeltforsikring"),
    ("p", "Er det samme interesse forsikret mot den samme faren i flere selskaper, kan sikrede velge hvilket "
          "selskap som skal benyttes. Selskapene fordeler erstatningen seg imellom etter reglene i "
          "forsikringsavtaleloven."),
]

NO_TRINN = [
    ("p", "Denne veiledningen viser hva du bør gjøre når en skade har skjedd. Den erstatter ikke reglene i "
          "avsnittene om skademelding og skadeoppgjør, som gjelder fullt ut."),
    ("ol", ["Begrens skaden. Steng vannet, dekk til åpninger og flytt uskadde gjenstander i sikkerhet, dersom det "
            "kan gjøres uten fare.",
            "Kontakt politiet straks ved tyveri, innbrudd, hærverk eller trafikkuhell med personskade, og noter "
            "saksnummeret.",
            "Dokumenter skaden. Ta bilder av skadestedet og av skadde gjenstander før noe ryddes bort eller "
            "repareres.",
            "Send skademelding til selskapet på nett, per telefon eller på selskapets skjema.",
            "Avtal besiktigelse. Ved større skader sender selskapet normalt en skadetakstmann, som avtaler tid for "
            "besøk med deg.",
            "Vent med reparasjon. Utfør bare nødvendige midlertidige reparasjoner til selskapet har godkjent "
            "reparasjonen.",
            "Ta imot oppgjøret. Selskapet sender et skriftlig oppgjør som viser hvordan erstatningen er beregnet "
            "og hvilken egenandel som er trukket fra.",
            "Klag om du er uenig. Se avsnittet om klage under «Andre bestemmelser»."]),
    ("h2", "Hva skademeldingen bør inneholde"),
    ("ul", ["Navn, adresse og polisenummer.",
            "Tidspunkt og sted for skaden.",
            "En kort beskrivelse av hvordan skaden skjedde.",
            "Hva som er skadet eller stjålet, med anslått verdi og kjøpsår.",
            "Navn og adresse til eventuelle vitner og andre involverte.",
            "Kontonummer for utbetaling av erstatning."]),
    ("h2", "Hvordan selskapet behandler saken"),
    ("p", "Selskapet registrerer skaden og gir sikrede et skadenummer, som skal oppgis ved all kontakt. Selskapet "
          "skal behandle saken så raskt som mulig, og gi beskjed dersom det trengs flere opplysninger. Når "
          "selskapet har fått de opplysningene som er nødvendige for å vurdere saken, gir selskapet skriftlig "
          "beskjed om erstatningsspørsmålet er avgjort."),
]

NO_INNBO_TABELL = [
    ("p", "Tabellen viser hvordan selskapet normalt gjør opp skade på innbo og løsøre. Fradrag for alder og slit "
          "fastsettes etter selskapets aldersfradragstabeller, som sikrede kan få på forespørsel."),
    ("table", "Oppgjørsform for innbo og løsøre", [
        ("Gjenstandsgruppe", "Oppgjørsform", "Merknad"),
        ("Møbler og tekstiler", "Reparasjon eller gjenanskaffelse", "Fradrag for slit og elde"),
        ("Klær og sko", "Kontantoppgjør", "Aldersfradrag etter tabell"),
        ("Elektronikk og mobiltelefon", "Gjenanskaffelse gjennom selskapets leverandør", "Aldersfradrag etter tabell"),
        ("Smykker og ur", "Gjenanskaffelse eller kontantoppgjør", "Særskilt sumgrense i forsikringsbeviset"),
        ("Sykler og elsykler", "Gjenanskaffelse", "Kvittering og rammenummer kreves"),
        ("Briller og høreapparater", "Gjenanskaffelse", "Dokumentasjon fra optiker eller audiograf"),
        ("Kunst og antikviteter", "Markedsverdi på skadedagen", "Takst kan kreves"),
        ("Penger og verdipapirer", "Dokumentert tap", "Særskilt sumgrense"),
        ("Verktøy og hageredskap", "Gjenanskaffelse", "Fradrag for slit og elde"),
        ("Mat og drikkevarer", "Kontantoppgjør", "Ingen"),
    ], [36, 44, 34]),
    ("h2", "Gjenstander som ikke gjenanskaffes"),
    ("p", "Gjenanskaffes ikke en gjenstand, beregnes erstatningen ut fra gjenstandens verdi på skadedagen. "
          "Selskapet kan i slike tilfeller begrense erstatningen til det beløpet selskapet ville ha betalt sin "
          "leverandør for en tilsvarende gjenstand."),
    ("h2", "Delvis skadde gjenstander"),
    ("p", "Kan en gjenstand repareres, erstattes reparasjonskostnadene. Erstatningen kan likevel ikke overstige det "
          "selskapet ville ha betalt om gjenstanden var totalskadet. Verdiforringelse etter reparasjon erstattes "
          "ikke."),
]

NO_KJORETOY_TABELL = [
    ("p", "Tabellen viser hvordan selskapet normalt gjør opp skader på kjøretøyet. Reglene i avsnittet "
          "«Skadeoppgjør» gjelder fullt ut."),
    ("table", "Oppgjørsform for kjøretøy", [
        ("Situasjon", "Oppgjørsform", "Merknad"),
        ("Reparerbar skade", "Reparasjon", "Verksted godkjent av selskapet"),
        ("Totalskade", "Kontantoppgjør", "Etter markedsverdi på skadedagen"),
        ("Tyveri, kjøretøyet ikke funnet", "Kontantoppgjør", "Når kjøretøyet regnes som tapt"),
        ("Glasskade – reparasjon", "Reparasjon", "Ingen egenandel"),
        ("Glasskade – utskifting", "Utskifting", "Egenandel ved glasskade"),
        ("Ekstrautstyr", "Gjenanskaffelse", "Fradrag for slit og elde"),
        ("Bagasje", "Kontantoppgjør", "Aldersfradrag etter tabell"),
        ("Redning", "Dekkes direkte", "Til nærmeste egnede verksted"),
        ("Leiebil", "Dekkes etter avsnittet «Leiebil»", "Kun når leiebil er avtalt"),
    ], [38, 36, 40]),
    ("h2", "Verditap etter reparasjon"),
    ("p", "Selskapet erstatter ikke verditap etter at en skade er reparert, og heller ikke tap ved at kjøretøyet "
          "ikke kan brukes, med mindre leiebildekning er avtalt."),
    ("h2", "Kondemnering"),
    ("p", "Er kjøretøyet totalskadet, kan selskapet overta vraket. Selskapet sørger for at kjøretøyet blir avregistrert "
          "og levert til godkjent mottak."),
]

NO_ORDLISTE = [
    ("p", "Ordlisten gir en kort forklaring av sentrale begreper i vilkårene, med engelsk oversettelse. Den er "
          "ment som en hjelp for kunder som ikke har norsk som morsmål. Ordlisten er ikke en del av "
          "forsikringsavtalen."),
    ("table", "Ordliste", [
        ("Norsk", "Engelsk", "Forklaring"),
        ("Egenandel", "Excess", "Den delen av skaden sikrede selv betaler"),
        ("Skadetakstmann", "Claims Assessor (loss adjuster)", "Besiktiger skaden for selskapet"),
        ("Regress", "Subrogation / recovery", "Selskapet krever utbetalingen tilbake fra den ansvarlige"),
        ("Skademelding", "Notification of loss", "Melding om en skade til selskapet"),
        ("Forsikringsbevis", "Policy schedule", "Viser hva som er forsikret"),
        ("Forsikringstaker", "Policyholder", "Den som har inngått avtalen"),
        ("Sikrede", "Insured person", "Den som har krav på erstatning"),
        ("Skjønn", "Appraisal", "Uavhengig fastsettelse av erstatningen"),
        ("Aldersfradrag", "Deduction for age", "Fradrag for slit og elde"),
        ("Foreldelse", "Time bar / limitation", "Bortfall av krav etter en viss tid"),
        ("Sikkerhetsforskrift", "Safety condition", "Plikt til å forebygge skade"),
        ("Hovedforfall", "Renewal date", "Dato for fornyelse"),
    ], [32, 38, 44]),
]

NO_MOTOR_EXTRA = [
    ("h2", "Veihjelp"),
    ("p", "Er veihjelp avtalt, dekker forsikringen assistanse ved driftsstans, punktering, tom batteri og "
          "lignende, og om nødvendig berging av kjøretøyet til nærmeste verksted. Veihjelp bestilles gjennom "
          "selskapets alarmtelefon, som er åpen hele døgnet."),
    ("h2", "Bagasje og fører- og passasjerutstyr"),
    ("p", "Forsikringen dekker skade på eller tyveri av bagasje som fraktes i kjøretøyet, når skaden er en direkte "
          "følge av en skade som er dekket under kasko eller delkasko. Tyveri av bagasje fra kjøretøy dekkes bare "
          "når bagasjen var innelåst og ikke synlig fra utsiden."),
    ("h2", "Kjøring i utlandet"),
    ("p", "Forsikringen gjelder i de nordiske land og i land som er tilsluttet grønt kort-ordningen. Ved kjøring "
          "utenfor disse landene må sikrede selv sørge for nødvendig ansvarsforsikring."),
    ("h2", "Bonus"),
    ("p", "Bonus opptjenes for hvert skadefritt år etter selskapets bonusregler. Ved skade som selskapet utbetaler "
          "erstatning for under kasko, reduseres bonusen. Skade som bare gjelder glass, brann eller tyveri, påvirker "
          "ikke bonusen. Selskapets bonusregler sendes på forespørsel."),
]

NO_HOME_EXTRA = [
    ("h2", "Naturskade"),
    ("p", "Forsikringen dekker naturskade etter lov om naturskadeforsikring, det vil si skade som direkte skyldes "
          "naturulykke som skred, storm, flom, stormflo, jordskjelv eller vulkanutbrudd. Erstatningen fastsettes "
          "etter de regler som gjelder for den lovpålagte naturskadeordningen."),
    ("h2", "Lovpålagte utbedringer"),
    ("p", "Ved skade på bygning dekker forsikringen merutgifter til utbedringer som offentlige myndigheter krever "
          "når bygningen repareres eller gjenoppføres, dersom kravet er stilt i medhold av plan- og "
          "bygningsloven."),
    ("h2", "Opprydding og riving"),
    ("p", "Forsikringen dekker nødvendige utgifter til opprydding, riving og bortkjøring av skadde rester etter en "
          "skade som er dekket av forsikringen."),
    ("h2", "Midlertidig bolig"),
    ("p", "Blir boligen ubeboelig etter en skade som er dekket, dekker forsikringen nødvendige og dokumenterte "
          "merutgifter til midlertidig bolig til boligen igjen er beboelig, innenfor den tid som er nødvendig "
          "for reparasjon."),
    ("h2", "Fritidsbåt, campingvogn og motorvogn"),
    ("p", "Innboforsikringen omfatter ikke motorvogn, campingvogn, tilhenger, båt eller luftfartøy med tilbehør. "
          "Slike gjenstander må forsikres særskilt."),
]

# =============================================================================================
# Swedish
# =============================================================================================

SV_PREMIE = [
    ("h2", "Betalning av premie"),
    ("p", "Premien ska betalas senast på den dag som anges i premieavin. Försäkringstagaren kan välja att betala "
          "premien vid flera tillfällen under försäkringsperioden. Bolaget kan då ta ut en avgift för "
          "delbetalning, vilken framgår av premieavin."),
    ("h2", "Om premien inte betalas i tid"),
    ("p", "Betalas premien inte i rätt tid får bolaget säga upp försäkringen. Uppsägningen får verkan den dag som "
          "anges i bolagets meddelande, dock tidigast vid den tidpunkt som följer av försäkringsavtalslagen. Betalas "
          "premien inom den tiden upphör uppsägningen att gälla."),
    ("h2", "Ändring av premie och villkor"),
    ("p", "Bolaget har rätt att ändra premie och villkor i samband med att försäkringen förnyas. Ändringarna "
          "meddelas skriftligen tillsammans med premieavin för den nya perioden. Den som inte godtar ändringarna kan "
          "säga upp försäkringen till förnyelsedagen."),
    ("h2", "Återbetalning av premie"),
    ("p", "Upphör försäkringen innan försäkringsperioden har löpt ut har försäkringstagaren rätt att få tillbaka "
          "premie för den återstående tiden. Bolaget får göra avdrag för en administrationsavgift."),
    ("h2", "Medlemskap"),
    ("p", "Försäkringstagaren blir medlem i Corvane Mutual när avtalet ingås. Medlemskapet ger rätt att delta i "
          "bolagets medlemsdemokrati enligt stadgarna, men medför ingen skyldighet att betala något utöver den "
          "avtalade premien."),
]

SV_OREDLIGHET = [
    ("h2", "Upplysningsplikt"),
    ("p", "Försäkringstagaren ska lämna riktiga och fullständiga svar på bolagets frågor när försäkringen tecknas "
          "och förnyas. Har försäkringstagaren lämnat oriktiga eller ofullständiga uppgifter kan ersättningen sättas "
          "ned eller helt utebli enligt försäkringsavtalslagen."),
    ("h2", "Riskökning"),
    ("p", "Försäkringstagaren ska utan dröjsmål meddela bolaget om förhållanden som angetts i försäkringsbrevet "
          "ändras på ett sätt som innebär att risken för skada ökar, till exempel om bostaden byggs om eller "
          "används för annat ändamål."),
    ("h2", "Framkallande av försäkringsfall"),
    ("p", "Har den försäkrade uppsåtligen framkallat försäkringsfallet lämnas ingen ersättning. Har den försäkrade "
          "framkallat försäkringsfallet genom grov vårdslöshet kan ersättningen sättas ned. Vid bedömningen tas "
          "hänsyn till graden av vårdslöshet och omständigheterna i övrigt."),
    ("h2", "Oredlighet"),
    ("p", "Har den försäkrade efter ett försäkringsfall uppsåtligen eller av grov vårdslöshet lämnat oriktiga "
          "uppgifter eller förtigit något av betydelse för bedömningen av rätten till ersättning, kan ersättningen "
          "sättas ned efter vad som är skäligt. Bolaget kan också säga upp försäkringen med omedelbar verkan."),
    ("p", "Misstänkta fall av försäkringsbedrägeri kan polisanmälas. Bolaget kan registrera uppgifter om skadan i "
          "ett gemensamt skadeanmälningsregister som används av försäkringsbranschen."),
    ("h2", "Identifikation"),
    ("p", "Vid tillämpning av reglerna om säkerhetsföreskrifter och framkallande av försäkringsfall jämställs den "
          "försäkrade med den som med den försäkrades samtycke har hand om den försäkrade egendomen, i den "
          "utsträckning som lagen medger."),
]

SV_STEG = [
    ("p", "Här beskrivs vad du ska göra när en skada har inträffat. Beskrivningen ersätter inte reglerna om "
          "anmälan av skada och skadevärdering, som gäller fullt ut."),
    ("ol", ["Begränsa skadan. Stäng av vattnet, täck över öppningar och flytta oskadad egendom i säkerhet om det "
            "kan ske utan fara.",
            "Polisanmäl stöld, inbrott, rån och skadegörelse och skicka en kopia av anmälan till bolaget.",
            "Dokumentera skadan. Fotografera skadeplatsen och skadad egendom innan något städas bort eller lagas.",
            "Anmäl skadan till bolaget via webben, per telefon eller på bolagets blankett.",
            "Kom överens om besiktning. Vid större skador skickar bolaget i regel en besiktningsman som kontaktar "
            "dig.",
            "Vänta med reparation. Gör endast nödvändiga tillfälliga åtgärder tills bolaget har godkänt "
            "reparationen.",
            "Ta emot ersättningsbeskedet. Bolaget skickar ett skriftligt besked som visar hur ersättningen har "
            "beräknats och vilken självrisk som har dragits av.",
            "Begär omprövning om du inte är nöjd. Se avsnittet «Om vi inte kommer överens»."]),
    ("h2", "Det här behöver bolaget veta"),
    ("ul", ["Namn, adress och försäkringsnummer.",
            "När och var skadan inträffade.",
            "Hur skadan gick till.",
            "Vad som har skadats eller stulits, med uppgift om ålder och anskaffningsvärde.",
            "Namn på vittnen och andra inblandade.",
            "Kontonummer för utbetalning."]),
    ("h2", "Så handläggs ärendet"),
    ("p", "Bolaget registrerar skadan och ger den försäkrade ett skadenummer som ska anges vid all kontakt. "
          "Ersättning betalas ut snarast efter det att den försäkrade har gjort vad som åligger honom eller henne "
          "och bolaget har kunnat fastställa ersättningens storlek."),
]

SV_LOS_TABELL = [
    ("p", "Tabellen visar hur bolaget normalt värderar och ersätter lösegendom. Avdrag för ålder och slitage görs "
          "enligt bolagets åldersavdragstabeller, som den försäkrade kan få på begäran."),
    ("table", "Värdering av lösegendom", [
        ("Egendomsgrupp", "Ersättningsform", "Anmärkning"),
        ("Möbler och textilier", "Reparation eller nyanskaffning", "Avdrag för ålder och slitage"),
        ("Kläder och skor", "Kontant ersättning", "Åldersavdrag enligt tabell"),
        ("Hemelektronik och mobiltelefon", "Ersättning i form av ny egendom", "Åldersavdrag enligt tabell"),
        ("Smycken och ur", "Nyanskaffning eller kontant ersättning", "Särskild beloppsgräns i försäkringsbrevet"),
        ("Cyklar och elcyklar", "Nyanskaffning", "Kvitto och ramnummer krävs"),
        ("Glasögon", "Nyanskaffning", "Intyg från optiker"),
        ("Konst och antikviteter", "Marknadsvärde", "Värdering kan krävas"),
        ("Pengar och värdehandlingar", "Styrkt förlust", "Särskild beloppsgräns"),
        ("Verktyg och trädgårdsredskap", "Nyanskaffning", "Avdrag för ålder och slitage"),
        ("Livsmedel", "Kontant ersättning", "Inget"),
    ], [36, 42, 36]),
    ("h2", "Egendom som inte anskaffas på nytt"),
    ("p", "Anskaffas inte ny egendom ersätts egendomens marknadsvärde omedelbart före skadan. Bolaget kan begränsa "
          "ersättningen till vad bolaget skulle ha betalat sin leverantör för likvärdig egendom."),
    ("h2", "Delvis skadad egendom"),
    ("p", "Kan egendomen repareras ersätts reparationskostnaden, dock högst vad det skulle ha kostat att ersätta "
          "egendomen om den hade förstörts helt. Värdeminskning efter reparation ersätts inte."),
]

SV_ORDLISTA = [
    ("p", "Ordlistan förklarar några viktiga begrepp i villkoren och ger en engelsk översättning. Den är ett stöd "
          "för kunder som inte har svenska som modersmål och ingår inte i försäkringsavtalet."),
    ("table", "Ordlista", [
        ("Svenska", "Engelska", "Förklaring"),
        ("Självrisk", "Excess", "Den del av skadan den försäkrade själv står för"),
        ("Besiktningsman", "Claims Assessor (loss adjuster)", "Besiktigar skadan för bolaget"),
        ("Regress", "Subrogation / recovery", "Bolaget kräver tillbaka ersättning av den ansvarige"),
        ("Skadeanmälan", "Notification of loss", "Anmälan av en skada till bolaget"),
        ("Försäkringsbrev", "Policy schedule", "Visar vad som är försäkrat"),
        ("Försäkringstagare", "Policyholder", "Den som har ingått avtalet"),
        ("Lösegendom", "Contents", "Hemmets lösa saker"),
        ("Åldersavdrag", "Deduction for age", "Avdrag för ålder och slitage"),
        ("Preskription", "Time bar / limitation", "Rätten till ersättning går förlorad"),
        ("Säkerhetsföreskrift", "Safety condition", "Regel för att förebygga skada"),
        ("Allrisk", "Accidental damage", "Plötslig och oförutsedd skada"),
    ], [32, 38, 44]),
]

SV_EXTRA = [
    ("h2", "ID-skydd"),
    ("p", "Försäkringen ger hjälp om någon obehörigen har använt den försäkrades identitetsuppgifter, till exempel "
          "för att ta lån eller handla på kredit. Bolaget hjälper till att spärra kort och handlingar och att "
          "bestrida krav som den försäkrade inte har orsakat."),
    ("h2", "Krisskydd"),
    ("p", "Försäkringen ersätter kostnader för krisbehandling hos psykolog efter en traumatisk händelse som till "
          "exempel inbrott i bostaden, rån eller brand. Behandlingen ska vara godkänd av bolaget i förväg."),
    ("h2", "Hyresgästens ansvar"),
    ("p", "Bor den försäkrade i hyreslägenhet omfattar försäkringen det ansvar som den försäkrade har som "
          "hyresgäst enligt hyreslagen för skada på lägenheten och fast inredning, om skadan har orsakats av en "
          "händelse som omfattas av egendomsskyddet."),
    ("h2", "Bostadsrättstillägg"),
    ("p", "För den som äger en bostadsrätt kan försäkringen utökas med ett bostadsrättstillägg. Tillägget omfattar "
          "lägenhetens fasta inredning och ytskikt i den utsträckning som bostadsrättshavaren svarar för enligt "
          "föreningens stadgar."),
]

# =============================================================================================
# Danish
# =============================================================================================

DA_PRAEMIE = [
    ("h2", "Betaling af præmie"),
    ("p", "Præmien betales forud ved forsikringens begyndelse og derefter ved hver forfaldsdag. Selskabet sender "
          "en opkrævning, som viser beløbet og den sidste rettidige betalingsdag. Betales præmien i rater, kan der "
          "tillægges et gebyr, som fremgår af opkrævningen."),
    ("h2", "Hvis præmien ikke betales"),
    ("p", "Betales præmien ikke rettidigt, sender selskabet en påmindelse med en ny betalingsfrist. Påmindelsen "
          "oplyser, at forsikringen ophører, hvis præmien ikke betales inden den nye frist. Fristen er ikke kortere, "
          "end forsikringsaftaleloven kræver."),
    ("h2", "Ændring af præmie og betingelser"),
    ("p", "Selskabet kan ændre præmie og betingelser med virkning fra den årlige hovedforfaldsdag. Ændringer "
          "meddeles skriftligt sammen med opkrævningen for den nye periode. Accepterer forsikringstageren ikke "
          "ændringerne, kan forsikringen opsiges til hovedforfaldsdagen."),
    ("h2", "Tilbagebetaling af præmie"),
    ("p", "Ophører forsikringen, før forsikringsperioden er udløbet, tilbagebetales præmien for den resterende "
          "periode. Selskabet kan fratrække et administrationsgebyr."),
    ("h2", "Medlemskab"),
    ("p", "Forsikringstageren bliver medlem af Corvane Mutual, når aftalen indgås. Medlemskabet giver ret til at "
          "deltage i selskabets medlemsdemokrati efter vedtægterne, men medfører ingen pligt til at betale ud over "
          "den aftalte præmie."),
]

DA_SVIG = [
    ("h2", "Oplysningspligt"),
    ("p", "Forsikringstageren skal give rigtige og fuldstændige svar på selskabets spørgsmål, når forsikringen "
          "tegnes og ændres. Er der givet urigtige eller ufuldstændige oplysninger, kan erstatningen nedsættes "
          "eller bortfalde efter reglerne i forsikringsaftaleloven."),
    ("h2", "Risikoforandring"),
    ("p", "Forsikringstageren skal straks give selskabet besked, hvis forhold, der er nævnt i policen, ændres på "
          "en måde, der øger risikoen for skade, for eksempel ved ombygning eller ændret anvendelse af boligen."),
    ("h2", "Fremkaldelse af forsikringsbegivenheden"),
    ("p", "Har sikrede forsætligt fremkaldt forsikringsbegivenheden, betaler selskabet ikke erstatning. Har sikrede "
          "fremkaldt forsikringsbegivenheden ved grov uagtsomhed, kan erstatningen nedsættes eller bortfalde. Ved "
          "afgørelsen tages hensyn til graden af skyld og omstændighederne i øvrigt."),
    ("h2", "Svig"),
    ("p", "Har sikrede givet urigtige oplysninger eller fortiet forhold af betydning for selskabets bedømmelse af "
          "skaden, kan retten til erstatning bortfalde helt eller delvis. Selskabet kan desuden opsige alle "
          "forsikringer med forsikringstageren med øjeblikkelig virkning."),
    ("p", "Forsøg på forsikringssvig kan blive politianmeldt. Selskabet kan registrere oplysninger om skaden i "
          "forsikringsbranchens fælles skaderegister."),
    ("h2", "Identifikation"),
    ("p", "Ved anvendelse af reglerne om sikkerhedsforskrifter og fremkaldelse af forsikringsbegivenheden "
          "identificeres sikrede med den, der med sikredes samtykke har rådighed over de forsikrede genstande, i "
          "det omfang loven tillader det."),
    ("h2", "Dobbeltforsikring"),
    ("p", "Er der tegnet forsikring mod samme risiko i et andet selskab, dækker denne forsikring kun i det omfang, "
          "den anden forsikring ikke dækker. Selskaberne fordeler erstatningen efter reglerne i "
          "forsikringsaftaleloven."),
]

DA_TRIN = [
    ("p", "Her kan du læse, hvad du skal gøre, når der er sket en skade. Vejledningen erstatter ikke reglerne om "
          "anmeldelse og skadeopgørelse, som gælder fuldt ud."),
    ("ol", ["Begræns skaden. Luk for vandet, dæk åbninger til og flyt ubeskadigede genstande i sikkerhed, hvis det "
            "kan ske uden fare.",
            "Anmeld tyveri, indbrud, røveri og hærværk til politiet og send en kopi af anmeldelsen til selskabet.",
            "Dokumentér skaden. Tag billeder af skadestedet og af beskadigede genstande, før der ryddes op eller "
            "repareres.",
            "Anmeld skaden til selskabet på nettet, pr. telefon eller på selskabets skema.",
            "Aftal besigtigelse. Ved større skader sender selskabet som regel en taksator, som aftaler et besøg "
            "med dig.",
            "Vent med reparation. Udfør kun nødvendige midlertidige foranstaltninger, indtil selskabet har godkendt "
            "reparationen.",
            "Modtag erstatningsopgørelsen. Selskabet sender en skriftlig opgørelse, som viser, hvordan erstatningen "
            "er beregnet, og hvilken selvrisiko der er fratrukket.",
            "Klag, hvis du er uenig. Se afsnittet «Klage» under «Fælles bestemmelser»."]),
    ("h2", "Det skal anmeldelsen indeholde"),
    ("ul", ["Navn, adresse og policenummer.",
            "Tidspunkt og sted for skaden.",
            "En kort beskrivelse af, hvordan skaden skete.",
            "Hvad der er beskadiget eller stjålet, med oplysning om alder og købspris.",
            "Navne på eventuelle vidner og andre involverede.",
            "Kontonummer til udbetaling af erstatning."]),
    ("h2", "Sådan behandles sagen"),
    ("p", "Selskabet registrerer skaden og giver sikrede et skadenummer, som skal oplyses ved al kontakt. "
          "Erstatningen udbetales, når selskabet har modtaget de oplysninger, der er nødvendige for at opgøre "
          "skaden. Selskabet betaler renter efter reglerne i forsikringsaftaleloven."),
]

DA_INDBO_TABEL = [
    ("p", "Tabellen viser, hvordan selskabet normalt opgør skader på indbo. Fradrag for alder, brug og nedsat "
          "anvendelighed sker efter selskabets afskrivningstabeller, som sikrede kan få udleveret."),
    ("table", "Opgørelse af indboskader", [
        ("Genstandsgruppe", "Erstatningsform", "Bemærkning"),
        ("Møbler og tekstiler", "Reparation eller genanskaffelse", "Fradrag for alder og brug"),
        ("Tøj og fodtøj", "Kontant erstatning", "Afskrivning efter tabel"),
        ("Elektronik og mobiltelefon", "Genlevering gennem selskabets leverandør", "Afskrivning efter tabel"),
        ("Smykker og ure", "Genanskaffelse eller kontant erstatning", "Særlig sumgrænse i policen"),
        ("Cykler og elcykler", "Genanskaffelse", "Kvittering og stelnummer kræves"),
        ("Briller", "Genanskaffelse", "Dokumentation fra optiker"),
        ("Kunst og antikviteter", "Handelsværdi", "Vurdering kan kræves"),
        ("Penge og værdipapirer", "Dokumenteret tab", "Særlig sumgrænse"),
        ("Værktøj og haveredskaber", "Genanskaffelse", "Fradrag for alder og brug"),
        ("Fødevarer", "Kontant erstatning", "Ingen"),
    ], [36, 44, 34]),
    ("h2", "Genstande, der ikke genanskaffes"),
    ("p", "Genanskaffes en genstand ikke, opgøres erstatningen til genstandens handelsværdi umiddelbart før skaden. "
          "Selskabet kan begrænse erstatningen til det beløb, selskabet skulle have betalt sin leverandør for en "
          "tilsvarende genstand."),
    ("h2", "Delvist beskadigede genstande"),
    ("p", "Kan en genstand repareres, betaler selskabet reparationsudgiften, dog højst det beløb, som en "
          "totalskade ville have udløst. Værdiforringelse efter reparation erstattes ikke."),
]

DA_ORDLISTE = [
    ("p", "Ordlisten forklarer centrale begreber i betingelserne og giver en engelsk oversættelse. Den er en hjælp "
          "til kunder, der ikke har dansk som modersmål, og er ikke en del af forsikringsaftalen."),
    ("table", "Ordliste", [
        ("Dansk", "Engelsk", "Forklaring"),
        ("Selvrisiko", "Excess", "Den del af skaden, sikrede selv betaler"),
        ("Taksator", "Claims Assessor (loss adjuster)", "Besigtiger skaden for selskabet"),
        ("Regres", "Subrogation / recovery", "Selskabet kræver erstatningen tilbage fra den ansvarlige"),
        ("Skadeanmeldelse", "Notification of loss", "Anmeldelse af en skade til selskabet"),
        ("Police", "Policy schedule", "Viser, hvad der er forsikret"),
        ("Forsikringstager", "Policyholder", "Den, der har indgået aftalen"),
        ("Indbo", "Contents", "Almindeligt privat løsøre"),
        ("Afskrivning", "Deduction for age", "Fradrag for alder og brug"),
        ("Forældelse", "Time bar / limitation", "Kravet bortfalder efter en vis tid"),
        ("Sikkerhedsforskrift", "Safety condition", "Regel, der skal forebygge skade"),
        ("Pludselig skade", "Accidental damage", "Uventet skade, der sker på én gang"),
    ], [32, 38, 44]),
]

DA_EXTRA = [
    ("h2", "Glas- og sanitetsforsikring (tilvalg)"),
    ("p", "Er glas- og sanitetsforsikring valgt, dækker forsikringen brud på bygningens ruder og glas i døre, "
          "glaskeramiske kogeplader samt brud på toiletkummer, cisterner, håndvaske og badekar. Ridser, afskalninger "
          "og skader, der opstår under reparation eller flytning, er ikke dækket."),
    ("h2", "Elskade (tilvalg)"),
    ("p", "Er elskadeforsikring valgt, dækker forsikringen skade på elektriske installationer og apparater, der er "
          "opstået ved kortslutning, induktion eller overspænding. Skader, der skyldes slid, fejlbetjening eller "
          "manglende vedligeholdelse, er ikke dækket."),
    ("h2", "Huslejetab"),
    ("p", "Bliver boligen ubeboelig efter en skade, der er dækket af forsikringen, dækker forsikringen nødvendige "
          "og dokumenterede merudgifter til midlertidig bolig, så længe boligen ikke kan bebos."),
    ("h2", "Retshjælp ved tvister"),
    ("p", "Retshjælpsforsikringen dækker sagsomkostninger ved tvister, som kan indbringes for domstolene, efter "
          "de standardvilkår for retshjælpsforsikring, der gælder på skadetidspunktet. Sagen skal anmeldes af "
          "sikredes advokat."),
]

# Coverage overview tables (no amounts; they point to sections)
_OVERVIEW = {
    ("no", "motor"): ("Oversikt over dekningene", [
        ("Dekning", "Hva den gjelder", "Avsnitt"),
        ("Ansvar", "Skade på person og ting som kjøretøyet volder", "Ansvar"),
        ("Brann", "Brann, lynnedslag og eksplosjon", "Delkasko"),
        ("Tyveri", "Tyveri og tyveriforsøk", "Delkasko"),
        ("Glass", "Frontrute, sideruter og bakrute", "Delkasko"),
        ("Redning", "Berging til verksted", "Delkasko"),
        ("Kasko", "Kollisjon, velt og utforkjøring", "Kasko"),
        ("Fører og passasjer", "Ulykkesforsikring for personer i kjøretøyet", "Fører- og passasjerulykke"),
        ("Leiebil", "Leiebil mens kjøretøyet repareres", "Leiebil"),
        ("Veihjelp", "Assistanse ved driftsstans", "Utvidede dekninger"),
    ], [30, 52, 32]),
    ("no", "home"): ("Oversikt over dekningene", [
        ("Dekning", "Gjelder for", "Avsnitt"),
        ("Brannskade", "Bygning og innbo", "Dekning"),
        ("Vannskade", "Bygning og innbo", "Dekning"),
        ("Naturskade", "Bygning og innbo", "Dekning / Utvidede dekninger"),
        ("Storm og snølast", "Bygning", "Dekning"),
        ("Tyveri og hærverk", "Innbo", "Dekning"),
        ("Glass og sanitærutstyr", "Bygning", "Dekning"),
        ("Uhellsskade", "Innbo (tillegg)", "Dekning"),
        ("Ansvar og rettshjelp", "Sikrede", "Ansvar og rettshjelp"),
        ("Husleietap", "Bygning", "Ekstrautgifter og husleietap"),
    ], [36, 38, 40]),
    ("sv", "home"): ("Översikt över försäkringsskyddet", [
        ("Skydd", "Gäller för", "Avsnitt"),
        ("Brand", "Lösegendom och byggnad", "Egendomsskydd"),
        ("Vattenskada", "Lösegendom och byggnad", "Egendomsskydd"),
        ("Frostskada", "Byggnad", "Egendomsskydd"),
        ("Inbrott och stöld", "Lösegendom", "Egendomsskydd"),
        ("Naturskador", "Lösegendom och byggnad", "Egendomsskydd"),
        ("Allrisk", "Lösegendom (tillägg)", "Egendomsskydd"),
        ("Ansvarsskydd", "Den försäkrade", "Ansvarsskydd, rättsskydd och överfallsskydd"),
        ("Rättsskydd", "Den försäkrade", "Ansvarsskydd, rättsskydd och överfallsskydd"),
        ("Reseskydd", "Den försäkrade", "Reseskydd och extra kostnader"),
        ("ID-skydd och krisskydd", "Den försäkrade", "Utökade skydd"),
    ], [34, 36, 44]),
    ("da", "home"): ("Oversigt over dækninger", [
        ("Dækning", "Gælder for", "Afsnit"),
        ("Brand", "Indbo og bygning", "Dækninger"),
        ("Vandskade", "Indbo og bygning", "Dækninger"),
        ("Frostskade", "Bygning", "Dækninger"),
        ("Storm og snetryk", "Bygning", "Dækninger"),
        ("Tyveri og indbrud", "Indbo", "Dækninger"),
        ("Hærværk", "Indbo og bygning", "Dækninger"),
        ("Pludselig skade", "Indbo (tilvalg)", "Dækninger"),
        ("Ansvar og retshjælp", "Sikrede", "Ansvar og retshjælp"),
        ("Glas og sanitet", "Bygning (tilvalg)", "Udvidede dækninger"),
        ("Elskade", "Bygning (tilvalg)", "Udvidede dækninger"),
    ], [34, 38, 42]),
}

_OVERVIEW_INTRO = {
    "no": "Tabellen gir en oversikt over dekningene i vilkårene og viser hvor de er beskrevet. Hvilke dekninger som "
          "gjelder for den enkelte avtalen, fremgår av forsikringsbeviset.",
    "sv": "Tabellen ger en översikt över försäkringsskydden i villkoren och visar var de beskrivs. Vilka skydd som "
          "gäller för det enskilda avtalet framgår av försäkringsbrevet.",
    "da": "Tabellen giver et overblik over dækningerne i betingelserne og viser, hvor de er beskrevet. Hvilke "
          "dækninger der gælder for den enkelte aftale, fremgår af policen.",
}

_TITLES = {
    "no": {"overview": "Oversikt over dekningene", "premium": "Premie og betaling",
           "duty": "Opplysningsplikt, risikoendring og svik", "steps": "Slik melder du en skade – trinn for trinn",
           "table_home": "Oppgjørsregler for innbo og løsøre", "table_motor": "Oppgjørsregler for kjøretøy",
           "extra": "Utvidede dekninger", "words": "Ordliste – norsk/engelsk"},
    "sv": {"overview": "Översikt över försäkringsskyddet", "premium": "Premie och betalning",
           "duty": "Upplysningsplikt, riskökning och oredlighet", "steps": "Så anmäler du en skada – steg för steg",
           "table_home": "Ersättningsregler för lösegendom", "extra": "Utökade skydd",
           "words": "Ordlista – svenska/engelska"},
    "da": {"overview": "Oversigt over dækninger", "premium": "Præmie og betaling",
           "duty": "Oplysningspligt, risikoforandring og svig", "steps": "Sådan anmelder du en skade – trin for trin",
           "table_home": "Erstatningsregler for indbo", "extra": "Udvidede dækninger",
           "words": "Ordliste – dansk/engelsk"},
}


def nordic_extra(lang: str, kind: str) -> dict:
    """Extra Nordic sections keyed by where they are inserted."""
    t = _TITLES[lang]
    ov_title, ov_rows, ov_w = _OVERVIEW[(lang, kind)]
    overview = [("p", _OVERVIEW_INTRO[lang]), ("table", ov_title, ov_rows, ov_w)]
    if lang == "no":
        premium, duty, steps, words = NO_PREMIE, NO_OPPLYSNING, NO_TRINN, NO_ORDLISTE
        table = (t["table_motor"], NO_KJORETOY_TABELL) if kind == "motor" else (t["table_home"], NO_INNBO_TABELL)
        extra = NO_MOTOR_EXTRA if kind == "motor" else NO_HOME_EXTRA
    elif lang == "sv":
        premium, duty, steps, words = SV_PREMIE, SV_OREDLIGHET, SV_STEG, SV_ORDLISTA
        table, extra = (t["table_home"], SV_LOS_TABELL), SV_EXTRA
    else:
        premium, duty, steps, words = DA_PRAEMIE, DA_SVIG, DA_TRIN, DA_ORDLISTE
        table, extra = (t["table_home"], DA_INDBO_TABEL), DA_EXTRA
    return {"overview": (t["overview"], overview), "premium": (t["premium"], premium),
            "duty": (t["duty"], duty), "steps": (t["steps"], steps), "table": table,
            "extra": (t["extra"], extra), "words": (t["words"], words)}
