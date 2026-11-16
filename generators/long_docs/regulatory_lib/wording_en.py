"""English (UK) policy wording content for LD004-LD007.

Blocks: ("h1", text) section heading on a new page; ("h2", text); ("h3", text); ("p", text);
("ul", [items]); ("ol", [items]); ("table", title, rows, widths_mm); ("pb",).
No amounts appear here except those passed in from the world model (excesses, limits).
"""
from __future__ import annotations

INTRO = [
    ("h2", "Welcome"),
    ("p", "Thank you for choosing Corvane Mutual. As a mutual insurer we are owned by our members, and we aim to "
          "deal with every claim fairly, promptly and in plain language. This booklet is your policy wording. "
          "Please read it together with your schedule and any endorsements, because together they form your "
          "contract of insurance with us."),
    ("p", "Keep this booklet in a safe place. If you need to make a claim, the section headed 'Claims conditions' "
          "explains what you need to do and what you can expect from us."),
    ("h2", "Your contract with us"),
    ("p", "In return for your payment of the premium, we will provide the cover described in this policy wording "
          "for loss, damage, injury or liability occurring during the period of insurance, subject to the terms, "
          "conditions, limits and exclusions set out in it."),
    ("p", "The information you gave us when you applied for this insurance, and when it was renewed or changed, "
          "forms the basis of this contract. If any of that information is incorrect or incomplete it may affect "
          "the cover we provide or the premium you pay."),
    ("h2", "How to read this policy"),
    ("p", "Certain words and phrases have a specific meaning wherever they appear in this policy. They are listed in "
          "the section headed 'Definitions' and are printed in bold type where they are used in the cover sections."),
    ("p", "Each section of cover tells you what is covered and what is not covered. The general exclusions and "
          "general conditions apply to every section of this policy."),
    ("p", "Headings are included for ease of reference only and do not affect the meaning of the policy."),
]

GENERAL_DEFS = [
    ("Endorsement", "A change to the terms of this policy, shown in your schedule or issued to you in writing."),
    ("Excess", "The amount you must pay towards each claim. The excesses that apply are set out in this policy and in "
               "your schedule."),
    ("Period of insurance", "The period shown in your schedule for which we have accepted your premium."),
    ("Schedule", "The document that gives details of you, the cover you have chosen, the period of insurance and any "
                 "endorsements. It forms part of this policy."),
    ("We, us, our", "Corvane Mutual Insurance Society Limited."),
    ("You, your", "The person or business named as the policyholder in the schedule, who is a member of Corvane Mutual."),
    ("Member", "A policyholder of Corvane Mutual. Membership begins when your first policy with us starts and ends "
               "when you no longer hold a policy with us."),
    ("Terrorism", "Any act of any person or organisation, involving the causing or threatening of harm, or putting the "
                  "public or any section of the public in fear, if it is reasonable to conclude that the purpose is "
                  "of a political, religious, ideological or similar nature."),
    ("Unoccupied", "Not lived in or used for the normal purposes of the insured activity for more than the number of "
                   "consecutive days stated in the relevant section."),
]

GENERAL_EXCLUSIONS = [
    ("War", "Any consequence of war, invasion, act of foreign enemy, hostilities or warlike operations (whether war "
            "is declared or not), civil war, rebellion, revolution, insurrection, military force or coup, or "
            "confiscation, nationalisation or requisition by any government or public authority."),
    ("Terrorism", "Any loss, damage, cost or expense of any kind directly or indirectly caused by, resulting from or "
                  "in connection with terrorism, regardless of any other cause contributing at the same time or in "
                  "any other sequence, except where cover is compulsory under road traffic or other legislation."),
    ("Radioactive contamination", "Ionising radiation or contamination by radioactivity from any nuclear fuel or "
                                  "nuclear waste, or the radioactive, toxic, explosive or other hazardous properties "
                                  "of any nuclear assembly or component."),
    ("Pressure waves", "Pressure waves caused by aircraft or other aerial devices travelling at sonic or supersonic "
                       "speeds."),
    ("Pollution", "Pollution or contamination, unless caused by a sudden, identifiable, unintended and unexpected "
                  "incident which happens in its entirety at a specific time and place during the period of "
                  "insurance."),
    ("Date recognition", "Failure of any computer or other equipment to recognise or process a date correctly, unless "
                         "this results in damage that is otherwise covered by this policy."),
    ("Deliberate acts", "Any loss, damage or liability arising from a deliberate act by you or by anyone acting on "
                        "your behalf, or with your knowledge or consent."),
    ("Existing damage", "Loss or damage that happened before the start of the period of insurance."),
    ("Indirect loss", "Any loss or expense that is not directly covered by this policy, unless the policy says "
                      "otherwise."),
    ("Sanctions", "We will not provide any cover or pay any claim where doing so would expose us to any sanction, "
                  "prohibition or restriction under United Nations resolutions or the trade or economic sanctions, "
                  "laws or regulations of the United Kingdom, the European Union or the United States of America."),
]

GENERAL_CONDITIONS = [
    ("Taking reasonable care", "You must take all reasonable steps to prevent loss, damage, accident or injury and "
                               "keep the insured property in a good state of repair. You must also take reasonable "
                               "care to give complete and accurate answers to the questions we ask."),
    ("Changes you must tell us about", "You must tell us as soon as possible about any change in circumstances that "
                                       "may affect your cover, including a change of address, a change in the use "
                                       "of the insured property, or any conviction or pending prosecution."),
    ("Other insurance", "If any loss, damage or liability covered by this policy is also covered by another "
                        "insurance, we will only pay our proportionate share, unless the policy says otherwise."),
    ("Fraud", "If you or anyone acting for you makes a claim that is fraudulent or exaggerated in any respect, or "
              "supports a claim with a false document or statement, we will not pay the claim, we may cancel this "
              "policy from the date of the fraudulent act and keep the premium, and we may recover from you any "
              "amount we have already paid. We may also inform the police."),
    ("Rights of other people", "No person other than you and us has any right to enforce any term of this policy "
                               "under the Contracts (Rights of Third Parties) Act 1999."),
    ("Recoveries", "We may take over and conduct in your name the defence or settlement of any claim, or take "
                   "proceedings in your name for our own benefit to recover any payment we have made under this "
                   "policy. You must give us all the information and assistance we reasonably need."),
    ("Observance of terms", "We will only provide the cover described in this policy if you, and any person "
                            "insured, have complied with its terms and conditions so far as they are relevant."),
    ("Arbitration", "If we accept a claim but there is a dispute about the amount to be paid, the dispute may be "
                    "referred to an arbitrator appointed jointly by you and us in accordance with the law at the "
                    "time. You may not take legal action against us over that dispute before the arbitrator has "
                    "made a decision."),
]

CANCELLATION = [
    ("h2", "Your right to cancel"),
    ("p", "You may cancel this policy within the cooling-off period shown in your schedule, starting on the day you "
          "receive the policy documents. We will refund the premium in full provided no claim has been made."),
    ("p", "After this cooling-off period you may cancel at any time by contacting us. We will refund a proportion of "
          "the premium for the unexpired period of insurance, less a charge for the time you have been covered, "
          "provided no claim has been made during the current period of insurance."),
    ("h2", "Our right to cancel"),
    ("p", "We may cancel this policy by giving you reasonable notice in writing to your last known address where "
          "there is a valid reason for doing so. Valid reasons include non-payment of premium, a change in risk "
          "which means we can no longer provide cover, or your failure to co-operate with us or provide information "
          "we have reasonably requested."),
    ("p", "If we cancel the policy we will refund any premium you have paid for the remainder of the period of "
          "insurance, unless the cancellation is because of fraud."),
]

COMPLAINTS = [
    ("h2", "Our commitment to you"),
    ("p", "We aim to provide a high standard of service to every member. If you are unhappy with any aspect of the "
          "service you have received, please tell us so that we can put things right."),
    ("h2", "How to complain"),
    ("p", "Please contact the person or team who dealt with you first. Most complaints can be resolved quickly at "
          "this stage. If you remain unhappy, please write to the Customer Relations Manager, Corvane Mutual, "
          "Corvane House, 14 Tallowgate, London EC3N 9ZZ."),
    ("p", "We will acknowledge your complaint promptly, keep you informed of our progress and do everything we can "
          "to resolve it. When we have completed our investigation we will send you a final response in writing."),
    ("h2", "If you are still not satisfied"),
    ("p", "If you are not satisfied with our final response, you may be able to refer your complaint to an "
          "independent dispute resolution service. Details of how to do so will be included in our final response. "
          "Using this service does not affect your right to take legal action."),
]

DATA = [
    ("h2", "How we use your information"),
    ("p", "We collect and use information about you and anyone else insured under this policy to provide insurance "
          "and handle claims, to prevent and detect fraud, and to meet our legal and regulatory obligations. We "
          "process this information in accordance with the Data Protection Act 1998."),
    ("p", "We may share your information with other insurers, loss adjusters, repairers, solicitors and service "
          "providers who help us administer your policy and handle claims, and with fraud prevention agencies. We "
          "will only share it where it is necessary to do so and we will take steps to keep it secure."),
    ("p", "You have the right to ask for a copy of the information we hold about you and to ask us to correct any "
          "inaccurate information. Please write to the Data Protection Officer at our registered office."),
    ("h2", "Telephone calls"),
    ("p", "Telephone calls may be recorded and monitored for training, quality and fraud prevention purposes."),
]

LAW = [
    ("h2", "Law and language"),
    ("p", "You and we are free to choose the law that applies to this contract. Unless we agree otherwise, the law of "
          "the part of the United Kingdom in which you live, or in which your business is based, will apply. This "
          "policy and all communications about it will be in English."),
    ("h2", "Regulation"),
    ("p", "Corvane Mutual Insurance Society Limited is supervised by the National Insurance Supervisory Authority. "
          "Our registered office is Corvane House, 14 Tallowgate, London EC3N 9ZZ."),
]

CLAIMS_COMMON = [
    "Give us full details of the loss, damage, injury or incident and any information or documents we reasonably ask for.",
    "Do not admit liability or offer, promise or make any payment without our written consent.",
    "Send us, unopened, every letter, claim form, writ, summons or other legal document you receive in connection with the claim.",
    "Tell the police as soon as possible if the loss or damage is caused by theft, attempted theft, malicious damage or vandalism, and obtain a crime reference number.",
    "Keep any damaged items so that we or our representative can inspect them, and do not dispose of them without our agreement.",
    "Allow us, or any loss adjuster, Claims Assessor or other expert we appoint, access to inspect the damage and to take photographs.",
    "Take all reasonable steps to recover lost or stolen property and to prevent further loss or damage.",
]

CLAIMS_HANDLING_PROMISES = [
    "explain how your claim will be handled and who will be dealing with it",
    "tell you if we need a loss adjuster or Claims Assessor to inspect the damage",
    "keep you informed about the progress of your claim",
    "explain clearly how we have calculated any payment and any excess deducted",
    "tell you in writing if we cannot accept your claim, and why",
]


# ------------------------------------------------------------------------------------------
# Product-specific content
# ------------------------------------------------------------------------------------------

def motor(excess_std, excess_ws, notify, ack):
    defs = [
        ("Accessories", "Parts or products specifically designed to be fitted to your car, and spare parts for your car."),
        ("Car", "Any motor vehicle described in the schedule, including its accessories, for which a current certificate of motor insurance has been issued."),
        ("Certificate of motor insurance", "The document which is evidence of the insurance required by the Road Traffic Act 1988. It shows who may drive your car and the purposes for which it may be used."),
        ("Compulsory excess", "The excess which applies to every claim for loss of or damage to your car, whoever is driving."),
        ("Insured person", "You, and any person permitted to drive your car under your certificate of motor insurance."),
        ("Market value", "The cost of replacing your car with one of the same make, model, specification, age, mileage and condition, immediately before the loss or damage."),
        ("Windscreen", "The windscreen, windows and sunroof glass of your car, and any scratching of the bodywork caused solely by their breakage."),
        ("Road", "Any road or other public place to which the public has access."),
        ("Total loss", "Damage to your car which we consider is not economical to repair, or theft of your car where it is not recovered."),
        ("Voluntary excess", "An additional excess that you have chosen to pay and which is shown in your schedule."),
    ]
    sections = [
        ("Section 1 – Liability to third parties", [
            ("h2", "What is covered"),
            ("p", "We will cover you for your legal liability for death of or bodily injury to any person, and for damage "
                  "to their property, arising from an accident caused by, or in connection with, your car or a trailer "
                  "or caravan attached to it."),
            ("p", "We will provide the same cover for any person who is driving your car with your permission, provided "
                  "the certificate of motor insurance allows them to drive and they hold a valid licence; any passenger "
                  "travelling in or getting into or out of your car; and the employer or business partner of an insured "
                  "person while your car is being used for business purposes allowed by the certificate."),
            ("h2", "Legal costs"),
            ("p", "If there is an accident which may give rise to a claim under this section, we will also pay the cost "
                  "of legal representation at any coroner's inquest or fatal accident inquiry, the cost of defending a "
                  "charge of manslaughter or causing death by dangerous or careless driving, and any other costs and "
                  "expenses we agree to in writing."),
            ("h2", "What is not covered"),
            ("ul", ["Death of or bodily injury to any person driving your car, or in charge of it.",
                    "Damage to property belonging to, or in the care of, the insured person who is claiming.",
                    "Damage to your car or to any trailer or caravan attached to it.",
                    "Any liability arising while your car is being driven by a person not permitted by the certificate of motor insurance, except where we must provide cover under road traffic law.",
                    "Liability arising from use of your car in or on any part of an airport or airfield used for aircraft, except where required by law."]),
        ]),
        ("Section 2 – Loss of or damage to your car", [
            ("h2", "What is covered"),
            ("p", "If your car is lost or damaged we will at our option repair it, replace it, or pay the cost of the "
                  "loss or damage up to the market value of your car. This cover applies to accidental damage, "
                  "malicious damage, fire, lightning, explosion, theft and attempted theft."),
            ("p", "If your car cannot be driven because of the loss or damage, we will pay the reasonable cost of "
                  "protecting it and moving it to the nearest suitable repairer, and of delivering it to your home "
                  "address in the United Kingdom after repair."),
            ("h2", "Repairs"),
            ("p", "You may choose your own repairer or use one of our approved repairers. If you use an approved "
                  "repairer we will guarantee the workmanship of the repair for as long as you own the car. If you "
                  "choose your own repairer we may ask for two estimates before work begins."),
            ("h2", "Total loss"),
            ("p", "If your car is a total loss, we will pay you the market value of your car at the time of the loss. "
                  "Once we have paid your claim, your car will become our property. If your car is subject to a hire "
                  "purchase or leasing agreement we will pay the finance company first."),
            ("h2", "New car replacement"),
            ("p", "If your schedule shows that new car replacement applies, you are the first registered keeper, and your "
                  "car is stolen and not recovered or damaged by an insured cause to the extent shown in your schedule, "
                  "we will replace it with a new car of the same make, model and specification if one "
                  "is available in the United Kingdom."),
            ("h2", "What is not covered"),
            ("ul", ["The excesses shown in the Schedule of excesses and in your schedule.",
                    "Loss of use of your car, or any other indirect loss.",
                    "Wear and tear, depreciation, or mechanical, electrical, electronic or computer failures or breakdowns.",
                    "Damage to tyres caused by braking, punctures, cuts or bursts.",
                    "Loss or damage caused by theft or attempted theft if the keys were left in or on the car, or if the car was left unlocked or with a window or roof open.",
                    "Loss or damage arising from the car being taken by a member of your family or household without your permission, unless they are reported to the police.",
                    "Loss of or damage to your car caused by deception by someone claiming to be a buyer or agent.",
                    "Any reduction in the market value of your car after it has been repaired."]),
        ]),
        ("Section 3 – Windscreen and glass", [
            ("h2", "What is covered"),
            ("p", "We will pay for the repair or replacement of broken glass in the windscreen, windows or sunroof of "
                  "your car, and for any scratching of the bodywork caused solely by the breakage."),
            ("p", "You can arrange the repair or replacement through our windscreen helpline. If you use our approved "
                  "glass repairer you will not need to pay for the work at the time; we will settle the account "
                  "directly, less the windscreen excess."),
            ("p", "A claim under this section only will not affect your no claim discount."),
            ("h2", "What is not covered"),
            ("ul", ["The windscreen excess shown in the Schedule of excesses.",
                    "Repair or replacement of any hood made of plastic or other flexible material.",
                    "Replacement of glass in lights, mirrors or panoramic roofs unless shown as covered in your schedule."]),
        ]),
        ("Section 4 – Personal accident and medical expenses", [
            ("h2", "Personal accident"),
            ("p", "If you or your spouse or civil partner are accidentally injured while travelling in or getting into or "
                  "out of any private car, and the injury results within the period stated in your schedule in death, loss of sight in one or "
                  "both eyes, or loss of a limb, we will pay the benefit shown in your schedule."),
            ("p", "We will not pay more than one benefit for any one person, and we will not pay benefit for death or "
                  "injury caused by suicide or attempted suicide, or by driving under the influence of alcohol or drugs."),
            ("h2", "Medical expenses"),
            ("p", "If anyone is injured while travelling in your car following an accident, we will pay the medical "
                  "expenses for each injured person up to the limit shown in your schedule."),
            ("h2", "Personal belongings"),
            ("p", "We will pay for personal belongings in your car which are lost or damaged by accident, fire, theft or "
                  "attempted theft, up to the limit shown in your schedule. We will not pay for money, credit cards, "
                  "tickets, documents, mobile telephones, goods or samples carried in connection with any business, or "
                  "property insured under any other policy."),
        ]),
        ("Section 5 – Using your car abroad", [
            ("h2", "Minimum cover required by law"),
            ("p", "This policy gives you the minimum cover you need by law to use your car in any country which is a "
                  "member of the European Union, and in any other country which has agreed to meet the minimum "
                  "insurance requirements set by the European Union."),
            ("h2", "Full policy cover abroad"),
            ("p", "We will also provide the full cover shown in your schedule while your car is used in those countries "
                  "for trips of no more than the number of days shown in your schedule, provided the main purpose of "
                  "the trip is social, domestic or pleasure and you normally live in the United Kingdom."),
            ("p", "We will also cover your car while it is being transported by a recognised sea, air or rail route "
                  "between the countries where you have cover, including loading and unloading."),
        ]),
        ("Section 6 – No claim discount", [
            ("p", "If no claim is made under this policy during a period of insurance, we will give you a discount "
                  "when you renew your policy, in line with our scale of discounts at the time."),
            ("p", "If a claim is made, your no claim discount will be reduced at your next renewal unless the claim is "
                  "for windscreen or glass only, or we have recovered all of our outlay from the person responsible."),
            ("p", "Your no claim discount cannot be transferred to another person. If you have chosen to protect your "
                  "no claim discount, the protection applies only as described in your schedule."),
        ]),
    ]
    excess_table = [["Excess", "Amount", "Applies to"],
                    ["Compulsory excess", f"£{excess_std:,} each claim", "Section 2 – every claim for loss of or damage to your car"],
                    ["Windscreen excess", f"£{excess_ws:,} each replacement", "Section 3 – each replacement of broken glass"],
                    ["Voluntary excess", "As shown in your schedule", "Section 2, in addition to the compulsory excess"],
                    ["Young or inexperienced driver excess", "As shown in your schedule", "Section 2, drivers named in your schedule"]]
    schedule = [
        ("p", "The excesses below apply to claims under this policy. Any additional excess shown in your schedule or "
              "endorsements will also apply."),
        ("table", "Schedule of excesses", excess_table, [42, 30, 50]),
        ("p", "Where more than one excess applies to the same claim, the excesses are added together. We will deduct "
              "the excesses from any payment we make, or ask you to pay them to the repairer directly."),
    ]
    claims = [
        ("h2", "Telling us about a claim"),
        ("p", f"If you need to make a claim, you must {notify}. You can tell us by telephone, at any time of day or "
              "night, using the claims number shown on your certificate of motor insurance, or by writing to us."),
        ("h2", "What we will do"),
        ("p", f"When you tell us about a claim, {ack}. We will also:"),
        ("ul", CLAIMS_HANDLING_PROMISES),
        ("h2", "What you must do"),
        ("ul", CLAIMS_COMMON + ["Tell us immediately if you become aware of any prosecution, inquest or fatal accident inquiry in connection with an accident."]),
        ("h2", "Paying claims"),
        ("p", "We will deduct any excess and any amount you owe us from the payment we make. If your car is the subject "
              "of a finance agreement we may make the payment to the finance company."),
    ]
    return defs, sections, schedule, claims


def home(excess_std, excess_eow, excess_sub, notify):
    defs = [
        ("Buildings", "The structure of your home, including its fixtures and fittings, garages and outbuildings, "
                      "walls, gates, fences, drives, paths, patios and swimming pools, all within the boundaries of the "
                      "premises."),
        ("Contents", "Household goods and personal belongings which you own or for which you are legally responsible, "
                     "kept within your home."),
        ("Escape of water", "Water escaping from any fixed water installation, washing machine, dishwasher, fish tank, "
                            "or from a fixed heating installation."),
        ("Heave", "Upward movement of the ground beneath the buildings as a result of the soil expanding."),
        ("Home", "The private dwelling at the address shown in your schedule."),
        ("Landslip", "Downward movement of sloping ground."),
        ("Subsidence", "Downward movement of the ground beneath the buildings, other than by settlement."),
        ("Settlement", "Normal downward movement of new buildings or extensions as the soil adjusts to the load."),
        ("Storm", "Strong winds, with or without rain, hail or snow, or exceptionally heavy rainfall or snowfall."),
        ("Flood", "Water entering your home from outside, from rivers, the sea, surface water or burst water mains."),
        ("Accidental damage", "Sudden and unexpected physical damage which happens at a specific time and was not "
                              "deliberately caused."),
        ("Valuables", "Jewellery, watches, items of gold, silver or other precious metals, works of art, collections "
                      "of stamps, coins or medals, and furs."),
    ]
    perils = [
        ("Fire, smoke, explosion, lightning and earthquake", "Damage caused by fire, smoke, explosion, lightning or earthquake.",
         ["Damage caused by smoke from fireplaces or agricultural or industrial operations.",
          "Scorching, melting or warping unless accompanied by flames."]),
        ("Storm and flood", "Damage caused by storm or flood.",
         ["Damage to gates, hedges and fences.",
          "Damage caused by frost or by a gradual rise in the water table.",
          "Damage which happens gradually or is caused by wear and tear."]),
        ("Escape of water", "Damage caused by escape of water from any fixed water or heating installation.",
         ["Damage caused by water escaping gradually over a period of time, including damage caused by failed seals or grouting.",
          "Damage to the installation from which the water escaped, other than the cost of tracing and accessing the leak described below.",
          "Damage while your home is unoccupied for longer than the period shown in your schedule.",
          "The escape of water excess."]),
        ("Theft or attempted theft", "Loss or damage caused by theft or attempted theft.",
         ["Theft while your home is lent, let or sublet, unless force was used to enter or leave.",
          "Theft by any person lawfully in your home.",
          "Theft while your home is unoccupied for longer than the period shown in your schedule."]),
        ("Malicious damage and vandalism", "Damage caused by malicious people or vandals.",
         ["Damage caused by you, your family or anyone lawfully in your home.",
          "Damage while your home is unoccupied for longer than the period shown in your schedule."]),
        ("Subsidence, heave and landslip", "Damage to the buildings caused by subsidence or heave of the site on which the "
                                           "buildings stand, or by landslip.",
         ["Damage caused by settlement, shrinkage or expansion of new structures.",
          "Damage to solid floors unless the foundations beneath the external walls are damaged at the same time.",
          "Damage to drives, paths, patios, walls, gates and fences unless the main building is damaged by the same cause at the same time.",
          "Damage caused by coastal or river erosion.",
          "The subsidence excess."]),
        ("Impact", "Damage caused by impact by any aircraft or other flying object, vehicle, animal, falling tree or "
                   "branch, or falling aerial or satellite dish.",
         ["Damage caused by domestic pets.",
          "The cost of removing fallen trees which have not damaged the buildings."]),
    ]
    sec1 = [("h2", "What is covered"),
            ("p", "We will cover the buildings against loss or damage caused by any of the following causes during the "
                  "period of insurance.")]
    for name, cover, nots in perils:
        sec1 += [("h3", name), ("p", cover), ("p", "We will not pay for:"), ("ul", nots)]
    sec1 += [
        ("h2", "Additional cover for buildings"),
        ("h3", "Trace and access"),
        ("p", "If there is an escape of water from any fixed water installation in your home, we will pay the cost of "
              "removing and replacing any part of the buildings necessary to find the source of the escape and to "
              "make good, up to the limit shown in your schedule."),
        ("h3", "Alternative accommodation"),
        ("p", "If your home cannot be lived in because of damage covered by this section, we will pay the reasonable "
              "cost of comparable alternative accommodation for you, your family and your domestic pets until your "
              "home is fit to live in again, up to the limit shown in your schedule."),
        ("h3", "Underground services"),
        ("p", "We will pay for accidental damage to underground drains, pipes, cables and tanks serving your home for "
              "which you are legally responsible."),
        ("h3", "Glass and sanitaryware"),
        ("p", "We will pay for accidental breakage of fixed glass in windows, doors and skylights, and of fixed "
              "sanitaryware, ceramic hobs and solar panels forming part of the buildings."),
        ("h2", "Section 1 excesses"),
        ("p", f"The following excesses apply to each claim under Section 1 – Buildings: the standard excess of "
              f"£{excess_std:,} for each claim; an escape of water excess of £{excess_eow:,} for each claim "
              f"caused by escape of water; and a subsidence excess of £{excess_sub:,} for each claim for damage "
              "caused by subsidence, heave or landslip. Only one excess applies to each claim: where the escape of "
              "water or subsidence excess applies, it replaces the standard excess."),
        ("h2", "How we settle claims"),
        ("p", "We will pay the cost of repairing or rebuilding the damaged part of the buildings to the same condition "
              "as when new, provided the buildings have been kept in a good state of repair. We may choose to "
              "arrange the repair ourselves through our approved contractors."),
        ("p", "If the buildings are not kept in a good state of repair, or the repair or rebuilding is not carried out, "
              "we will make a deduction for wear and tear. We will not pay more than the sum insured shown in your "
              "schedule for any one claim."),
    ]
    sec2 = [("h2", "What is covered"),
            ("p", "We will cover your contents against loss or damage caused by any of the causes listed in Section 1 "
                  "(other than subsidence, heave and landslip, which are covered only where the buildings are "
                  "damaged by the same cause), and by the additional causes below.")]
    sec2 += [
        ("h3", "Contents temporarily removed"),
        ("p", "We will cover your contents while temporarily removed from your home to any other building in the "
              "United Kingdom where you or your family are staying or working, against the causes listed in Section 1."),
        ("h3", "Freezer contents"),
        ("p", "We will pay for loss of food in any freezer in your home caused by a rise or fall in temperature, or by "
              "contamination by refrigerant fumes."),
        ("h3", "Theft of keys"),
        ("p", "If the keys to the external doors or windows of your home are stolen, we will pay the cost of replacing "
              "the locks or lock mechanisms."),
        ("h3", "Students' possessions"),
        ("p", "We will cover the personal possessions of any member of your family who is a full-time student and "
              "living away from home, against the causes listed in Section 1, up to the limit shown in your schedule."),
        ("h2", "What is not covered"),
        ("ul", ["Valuables above the single article limit shown in your schedule unless specified.",
                "Money and credit cards unless shown as covered in your schedule.",
                "Motor vehicles, caravans, trailers, boats and their accessories.",
                "Any living creature.",
                "Property used for business purposes.",
                "Loss or damage caused by moth, vermin, wear and tear or any gradually operating cause.",
                "The excess shown in your schedule for contents claims."]),
        ("h2", "How we settle claims"),
        ("p", "We will repair or replace the damaged items with new items of the same quality, or pay the cost of "
              "doing so. For clothing and household linen we will make a deduction for wear and tear. We may choose "
              "to replace items through one of our suppliers."),
    ]
    sec3 = [("h2", "Accidental damage"),
            ("p", "If your schedule shows that accidental damage cover applies, we will cover the buildings and "
                  "contents against accidental damage in addition to the causes listed in Sections 1 and 2."),
            ("p", "We will not pay for damage caused by pets, damage caused by chewing, scratching, tearing or fouling, "
                  "damage caused by building work, damage to items in the open, or mechanical or electrical faults."),
            ("h2", "Personal possessions away from the home"),
            ("p", "If your schedule shows that personal possessions cover applies, we will cover personal belongings "
                  "which you or your family normally wear or carry, against loss, theft or accidental damage anywhere "
                  "in the world, up to the limits shown in your schedule.")]
    sec4 = [("h2", "Liability as owner of the buildings"),
            ("p", "We will cover your legal liability as owner of the buildings to pay damages and costs for accidental "
                  "death of or bodily injury to any person, or accidental damage to property, happening during the "
                  "period of insurance, up to the limit shown in your schedule."),
            ("h2", "Liability as occupier"),
            ("p", "We will cover your legal liability as occupier of your home, and as a private individual, to pay "
                  "damages and costs for accidental death of or bodily injury to any person, or accidental damage to "
                  "property, happening during the period of insurance."),
            ("h2", "What is not covered"),
            ("ul", ["Liability arising from any business, trade or profession.",
                    "Liability for injury to you or to any member of your family or household.",
                    "Liability arising from the ownership or use of any motorised vehicle, aircraft or watercraft.",
                    "Liability arising from any dangerous dog.",
                    "Liability you have agreed to accept under a contract which you would not otherwise have."])]
    sections = [("Section 1 – Buildings", sec1), ("Section 2 – Contents", sec2),
                ("Section 3 – Optional covers", sec3), ("Section 4 – Liability to the public", sec4)]
    claims = [("h2", "Telling us about a claim"),
              ("p", f"If anything happens which may lead to a claim, you must {notify}. Please telephone our claims "
                    "line or write to us. Tell the police immediately about any loss caused by theft, attempted theft, "
                    "malicious damage or vandalism."),
              ("h2", "What we will do"),
              ("p", "When you tell us about a claim we will:"),
              ("ul", CLAIMS_HANDLING_PROMISES),
              ("h2", "What you must do"),
              ("ul", CLAIMS_COMMON),
              ("h2", "Emergency repairs"),
              ("p", "You may carry out emergency repairs needed to prevent further damage without our agreement. Please "
                    "keep receipts and photographs of the damage before repair.")]
    return defs, sections, None, claims


def commercial(excess_std, bi_months, notify):
    defs = [
        ("Business", "The business activities described in the schedule, carried on at the premises."),
        ("Buildings", "The buildings at the premises, including landlord's fixtures and fittings, outbuildings, walls, "
                      "gates, fences, yards and car parks."),
        ("Damage", "Accidental loss or destruction of or damage to property."),
        ("Gross profit", "The amount by which the turnover of the business and the value of closing stock exceed the "
                         "value of opening stock and the specified working expenses."),
        ("Indemnity period", "The period beginning with the occurrence of the damage and ending not later than the "
                             "maximum indemnity period, during which the results of the business are affected by the damage."),
        ("Insurer", "Corvane Mutual Insurance Society Limited."),
        ("Insured", "The person, firm or company named in the schedule as the insured."),
        ("Premises", "The premises described in the schedule."),
        ("Stock", "Stock and materials in trade, including work in progress and finished goods."),
        ("Turnover", "The money paid or payable to the Insured for goods sold and delivered and for services rendered "
                     "in the course of the business at the premises."),
    ]
    perils = ["fire, lightning, explosion and aircraft", "riot, civil commotion, strikers and malicious persons",
              "earthquake", "storm and flood", "escape of water from any tank, apparatus or pipe",
              "impact by any road vehicle or animal", "subterranean fire", "theft involving forcible and violent entry",
              "accidental escape of water from any automatic sprinkler installation"]
    sec1 = [("h2", "Insured events"),
            ("p", "The Insurer will indemnify the Insured in respect of Damage to the property described in the schedule "
                  "caused by any of the following events occurring during the period of insurance:"),
            ("ol", [p[0].upper() + p[1:] + "." for p in perils]),
            ("h2", "Basis of settlement"),
            ("p", "The basis upon which the amount payable is to be calculated is the reinstatement of the property "
                  "destroyed or damaged, meaning the rebuilding or replacement of property lost or destroyed in a "
                  "condition equal to, but not better or more extensive than, its condition when new."),
            ("h2", "Exclusions to Section 1"),
            ("ul", ["Damage caused by the property's own faulty or defective design, materials or workmanship.",
                    "Damage caused by wear and tear, gradual deterioration, rust, corrosion, frost or atmospheric conditions.",
                    "Damage to property in the open, other than buildings and fixed plant, caused by storm or flood.",
                    "Theft or attempted theft unless involving forcible and violent entry to or exit from the buildings.",
                    "Damage occurring while the buildings are unoccupied, other than by fire, lightning or explosion.",
                    "The excess shown in the schedule."])]
    sec2 = [("h2", "Cover"),
            ("p", "If any building or other property used by the Insured at the premises for the purpose of the business "
                  "suffers Damage by an event insured under Section 1, and the business is in consequence interrupted "
                  "or interfered with, the Insurer will pay to the Insured the amount of loss resulting from the "
                  "interruption or interference."),
            ("h2", "Measure of indemnity"),
            ("p", "The insurance is limited to loss of gross profit due to reduction in turnover and increase in cost of "
                  "working, and the amount payable as indemnity shall be calculated over the indemnity period."),
            ("p", f"The maximum indemnity period under this policy is {bi_months} months unless a different period is "
                  "shown in the schedule."),
            ("h2", "Extensions"),
            ("ul", ["Damage at the premises of the Insured's suppliers in the United Kingdom.",
                    "Prevention of access to the premises by the order of a public authority following damage in the vicinity.",
                    "Failure of the public supply of electricity, gas or water at the terminal ends of the supply undertaking's feed to the premises.",
                    "Book debts outstanding which cannot be traced as a result of damage to records."])]
    sec3 = [("h2", "Money"),
            ("p", "The Insurer will indemnify the Insured for loss of money belonging to the Insured or for which the "
                  "Insured is responsible, in the course of the business, up to the limits shown in the schedule."),
            ("h2", "Glass"),
            ("p", "The Insurer will pay for breakage of fixed glass at the premises, including the cost of boarding up "
                  "and temporary repairs."),
            ("h2", "Goods in transit"),
            ("p", "The Insurer will indemnify the Insured for damage to goods in transit in the Insured's own vehicles "
                  "within the United Kingdom, up to the limit shown in the schedule.")]
    sections = [("Section 1 – Material damage", sec1), ("Section 2 – Business interruption", sec2),
                ("Section 3 – Additional covers", sec3)]
    gen_extra = [
        ("Claims – notification", f"On the happening of any Damage or event which may give rise to a claim under "
                                       f"this policy the Insured shall {notify} of its occurrence, and shall within a "
                                       "reasonable time deliver to the Insurer a claim in writing with full particulars."),
        ("Business interruption – indemnity period", f"For the purposes of Section 2 the maximum indemnity period is "
                                                          f"{bi_months} months beginning with the occurrence of the Damage, "
                                                          "unless the schedule states otherwise."),
        ("Alteration", "The Insured shall notify the Insurer of any alteration to the business, the premises or the "
                       "property insured which increases the risk of Damage."),
        ("Inspection", "The Insurer may at all reasonable times inspect the premises and the property insured."),
        ("Security", "All protections and security devices shall be maintained in efficient working order and put "
                     "into full operation whenever the premises are closed for business."),
    ]
    schedule_rows = [["Item", "Detail"],
                     ["Policy wording", "Commercial Property Policy Wording 2011"],
                     ["Excess (Section 1)", f"£{excess_std:,} each and every loss"],
                     ["Sums insured", "As stated in the schedule for each item"],
                     ["Basis of cover", "Reinstatement"]]
    schedule = [("table", "Policy summary", schedule_rows, [45, 75])]
    claims = [("h2", "Procedure in the event of a claim"),
              ("p", "The Insured shall, at their own expense, produce and give to the Insurer all such books of account "
                    "and other business books, vouchers, invoices, balance sheets and other documents, proofs, "
                    "information, explanation and other evidence as the Insurer may reasonably require."),
              ("ul", CLAIMS_COMMON)]
    return defs, sections, schedule, claims, gen_extra


def liability(pl_limit, el_limit, excess_pd, notify):
    defs = [
        ("Bodily injury", "Death, injury, illness or disease of any person."),
        ("Business", "The business described in the schedule, conducted by the Insured."),
        ("Damage", "Physical loss of or damage to tangible property."),
        ("Employee", "Any person under a contract of service or apprenticeship with the Insured, and any person "
                     "supplied to or hired by the Insured, while working for the Insured in connection with the business."),
        ("Insured", "The person, firm or company named in the schedule."),
        ("Insurer", "Corvane Mutual Insurance Society Limited."),
        ("Limit of indemnity", "The maximum amount the Insurer will pay as stated in the schedule."),
        ("Products", "Any goods or property, after they have ceased to be in the Insured's possession or control, "
                     "which were sold, supplied, repaired, serviced or installed by the Insured in connection with the business."),
        ("Territorial limits", "Great Britain, Northern Ireland, the Channel Islands and the Isle of Man."),
    ]
    sec1 = [("h2", "Employers' liability"),
            ("p", "The Insurer will indemnify the Insured against all sums which the Insured is legally liable to pay "
                  "as compensation for bodily injury caused to any employee arising out of and in the course of their "
                  "employment by the Insured in the business, within the territorial limits."),
            ("p", "This section of the policy complies with the Employers' Liability (Compulsory Insurance) Act 1969 "
                  "and any law which amends or replaces it."),
            ("h2", "Exclusions to Section 1"),
            ("ul", ["Bodily injury arising out of the use of a vehicle where compulsory motor insurance is required.",
                    "Liability arising from offshore work.",
                    "Any amount above the limit of indemnity stated in the schedule."])]
    sec2 = [("h2", "Public liability"),
            ("p", "The Insurer will indemnify the Insured against all sums which the Insured is legally liable to pay "
                  "as compensation for accidental bodily injury to any person other than an employee, and accidental "
                  "damage to property, happening within the territorial limits during the period of insurance in "
                  "connection with the business."),
            ("h2", "Products liability"),
            ("p", "The Insurer will indemnify the Insured against all sums which the Insured is legally liable to pay "
                  "as compensation for accidental bodily injury or damage caused by any products, happening during the "
                  "period of insurance, provided the products were supplied from within the territorial limits."),
            ("h2", "Exclusions to Section 2"),
            ("ul", ["Liability for damage to property owned by, or in the custody or control of, the Insured.",
                    "Liability arising from the ownership or use of any mechanically propelled vehicle, aircraft or watercraft.",
                    "Liability arising from professional advice or design given for a fee.",
                    "The cost of recalling, repairing or replacing any products.",
                    "Liability arising from pollution unless caused by a sudden, identifiable, unintended and unexpected incident.",
                    "Fines, penalties, punitive or exemplary damages.",
                    "The excess shown in the schedule for property damage claims."])]
    sec3 = [("h2", "Legal defence costs"),
            ("p", "The Insurer will pay the costs of legal representation at any coroner's inquest or fatal accident "
                  "inquiry, and in defending proceedings in any court of summary jurisdiction, arising from any event "
                  "which may be the subject of indemnity under this policy."),
            ("h2", "Cross liabilities"),
            ("p", "Where more than one party is named as the Insured, this policy will apply as though a separate policy "
                  "had been issued to each, provided the total amount payable does not exceed the limit of indemnity.")]
    sections = [("Section 1 – Employers' liability", sec1), ("Section 2 – Public and products liability", sec2),
                ("Section 3 – Extensions", sec3)]
    schedule_rows = [["Section", "Limit of indemnity", "Excess"],
                     ["Section 1 – Employers' liability", f"£{el_limit:,} any one occurrence", "Nil"],
                     ["Section 2 – Public liability", f"£{pl_limit:,} any one occurrence",
                      f"£{excess_pd:,} each claim for damage to property"],
                     ["Section 2 – Products liability", "As public liability, in the aggregate for the period",
                      f"£{excess_pd:,} each claim for damage to property"]]
    schedule = [("p", "The limits of indemnity below include all costs and expenses recoverable by any claimant, unless "
                      "the schedule states otherwise."),
                ("table", "Schedule – limits of indemnity", schedule_rows, [42, 44, 36])]
    claims = [("h2", "Claims procedure"),
              ("p", f"The Insured shall {notify}, and shall give full details in writing as soon as possible. Every "
                    "letter, claim, writ, summons or process shall be forwarded to the Insurer on receipt."),
              ("ul", CLAIMS_COMMON),
              ("p", "The Insurer shall be entitled to take over and conduct in the name of the Insured the defence or "
                    "settlement of any claim, and shall have full discretion in the conduct of any proceedings.")]
    return defs, sections, schedule, claims


# Filler clauses used to extend the conditions section (generic, no amounts)
EXTRA_CONDITIONS = [
    ("Premium payment", "If you pay your premium by instalments and an instalment is not paid, we may cancel this policy "
                        "by giving you notice in writing. Any claim we have paid may be deducted from the premium refund."),
    ("Index linking", "Where the schedule shows that sums insured are index linked, they will be adjusted at renewal in "
                      "line with an appropriate index. No charge will be made for the adjustment during the period of insurance."),
    ("Unoccupied premises", "You must tell us if the insured property is to be left unoccupied for longer than the "
                            "period stated in the relevant section, so that we can tell you whether any special terms apply."),
    ("Maintenance", "You must keep the insured property in a good state of repair and take reasonable steps to prevent "
                    "frost damage, including maintaining adequate heating during cold weather."),
    ("Contracts", "You must not enter into any agreement which limits or removes your rights of recovery against "
                  "another party without our agreement."),
    ("Average", "If at the time of any loss the sum insured is less than the full value of the property, the amount we pay "
                "may be reduced in the same proportion. This condition applies only where your schedule says so."),
    ("Joint insureds", "Where more than one person is insured under this policy, the knowledge, act or failure of any "
                       "one of them will be treated as the knowledge, act or failure of all of them."),
    ("Notices", "Any notice we send you will be sent to your last known address. Any notice you send us must be sent to "
                "our registered office or to the address shown in your schedule."),
    ("Waiver", "Our failure to enforce any term of this policy will not prevent us from enforcing it later."),
    ("Mutual membership", "As a member of Corvane Mutual you may be entitled to attend and vote at general meetings of "
                          "the Society in accordance with its rules. Membership does not create any liability to contribute "
                          "to the Society beyond the premium payable under this policy."),
]

IMPORTANT_INFO = [
    ("h2", "Important information"),
    ("p", "This policy is a legal contract. Please check your schedule carefully to make sure the details are correct "
          "and that the cover meets your needs. If anything is wrong, or if you have any questions, please contact us "
          "as soon as possible."),
    ("p", "You must tell us about any changes which may affect your insurance. If you do not, your policy may not "
          "operate fully or at all, or we may reduce the amount we pay in the event of a claim."),
    ("p", "Where we refer to an Act of Parliament or a regulation, we mean that Act or regulation as amended or "
          "replaced from time to time."),
    ("h2", "Large print and other formats"),
    ("p", "This booklet is available on request in large print, Braille and audio formats."),
]
