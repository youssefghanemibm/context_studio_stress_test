"""Text content for LD021, the Claims Assessor Field Guide and Photo Atlas (2025 edition).

Values that come from the world (rule parameters, names, system names) are injected by atlas.py
through the ``V`` dict, so this module holds only wording. Exclusive values (the gradual-leak moisture
threshold, the subsidence crack width and the Norrvik fee schedule) are NOT referenced here at all:
atlas.py burns them into specific raster images only.

Plate tuple: (texture, title, burned_caption, options)
    options keys: overlay ("ruler"), meter (LCD reading), marker (label), single (bool: 1-up plate with notes)
"""
from __future__ import annotations


def chapters(V: dict) -> list[dict]:
    return [
        {
            "num": 1, "title": "Introduction", "hero": "plaster",
            "intro": [
                "This field guide sets out how Corvane Mutual expects a Claims Assessor to inspect, record and report "
                "on a loss. It combines practical guidance with a photo atlas of typical damage, so that assessors can "
                "compare what they see on site with reference examples.",
                f"A Claims Assessor is {V['assessor_def']} In this guide, 'loss adjuster' means an external Claims "
                "Assessor appointed from the panel; the same standards apply to internal and external assessors.",
            ],
            "sections": [
                ("Who this guide is for", [
                    ("p", f"The guide is issued to the {V['t06']} and {V['t07']} teams and to the panel firms "
                          f"{V['ven01']} and {V['ven02']}. It replaces the 2022 edition."),
                    ("p", "It is also useful for claims handlers who review assessor reports and for team leaders who "
                          "allocate instructions."),
                ]),
                ("How the assessment process works", [
                    ("p", "Assessment sits between triage and settlement. The main steps are shown in Figure 1.1: "
                          "appoint the Claims Assessor, inspect or desk-assess the loss, report, take the coverage "
                          "decision and record the estimate and any recovery potential."),
                    ("p", f"Instructions are issued and reports returned through the {V['portal']} "
                          f"({V['portal_old']} until {V['portal_rename']}). Photographs and documents are held in "
                          f"{V['vault']}; photographs sent in by customers arrive through the {V['gateway']}."),
                    ("rule", V["r_asm002"]),
                ]),
                ("How to use the photo atlas", [
                    ("p", "Each chapter ends with photo plates. The caption printed on each photograph explains what "
                          "the plate shows and, where relevant, the decision it supports. Plate captions form part of "
                          "this guide and should be read with the chapter text."),
                    ("ul", ["Compare the damage you see with the plates before you form a view on cause.",
                            "Use the same framing and scale references in your own photographs.",
                            "Where the plate caption states a referral or evidence requirement, follow it and record "
                            "that you have done so in your report."]),
                ]),
            ],
            "figures": [("flow", "fig1_1")],
            "plates": [],
        },
        {
            "num": 2, "title": "Health and safety on site", "hero": "debris",
            "intro": [
                "No inspection is so urgent that it justifies putting yourself or others at risk. Before entering any "
                "damaged property, carry out a dynamic risk assessment and decide whether it is safe to proceed.",
            ],
            "sections": [
                ("Before you arrive", [
                    ("ul", ["Check the claim notes for known hazards, such as structural damage, vulnerable occupants "
                            "or dogs.",
                            "Tell your team where you are going and when you expect to finish.",
                            "Carry the personal protective equipment listed in Table 2.1.",
                            "If the customer or a third party has been aggressive, arrange a joint visit."]),
                ]),
                ("On site", [
                    ("p", "Look up before you go in. After fire or water damage, ceilings may be saturated or "
                          "weakened. Do not walk on fire-damaged floors or stairs until you are sure they are sound."),
                    ("p", "Assume that flood water and sewage are contaminated. Wear gloves and wash before eating or "
                          "drinking. Do not touch electrical fittings in wet areas; ask the customer to arrange for the "
                          "supply to be isolated."),
                    ("p", "Do not disturb materials that may contain asbestos, such as old textured ceiling coatings "
                          "or insulation boards. Photograph them from a distance and record your concern."),
                    ("p", "Do not climb onto roofs. Use a pole camera or binoculars, or ask a contractor with the right "
                          "equipment to provide photographs."),
                ]),
                ("If something goes wrong", [
                    ("p", "Leave the property if you feel unsafe. Report any accident or near miss to your team "
                          "leader on the same day."),
                ]),
            ],
            "figures": [("table", "tab2_1")],
            "plates": [
                ("smoke", "Saturated ceiling after fire-fighting water",
                 "Ceiling boards sagging after fire-fighting water. Do not enter until the ceiling has been made safe.",
                 {}),
                ("debris", "Collapsed plaster and debris", "Collapsed plaster in a back bedroom. Debris can hide holes in "
                 "the floor; keep to the edge of the room.", {}),
                ("flood", "Contaminated flood water line", "Flood line on an internal wall. Treat all flood water as "
                 "contaminated and wear gloves.", {}),
                ("fire_char", "Fire-damaged floor joists", "Charred floor structure. Do not walk on fire-damaged floors "
                 "until a contractor has confirmed they are sound.", {"single": True}),
            ],
        },
        {
            "num": 3, "title": "Photographic standards", "hero": "plaster",
            "intro": [
                "Photographs are the main evidence of what the Claims Assessor saw. They are used by claims handlers, "
                "by the recoveries team, by Counter-Fraud & SIU and, if a claim is disputed, by the customer's "
                "representatives and the ombudsman. They must be clear, complete and unedited.",
            ],
            "sections": [
                ("Minimum photo set", [
                    ("rule", V["r_asm004"]),
                    ("p", "Table 3.1 lists the photographs expected for each type of loss. Take more where the damage "
                          "is extensive or the cause is unclear."),
                ]),
                ("Wide, mid and close", [
                    ("p", "For every area of damage, take a wide shot that shows the room or elevation, a mid shot that "
                          "shows the damaged item in context and a close-up that shows the detail (Figure 3.1)."),
                    ("ul", ["Include a scale reference, such as a ruler or tape, in close-ups.",
                            "Photograph the serial plate of damaged appliances and equipment.",
                            "Photograph undamaged areas for comparison where this helps to show cause.",
                            "Do not crop, filter or otherwise edit photographs before upload."]),
                ]),
                ("Uploading", [
                    ("p", f"Upload photographs to {V['vault']} through the {V['portal']} on the day of the inspection. "
                          "Keep the original files and their metadata. Name the files using the claim number and a "
                          "sequence number."),
                    ("rule", V["r_asm008"]),
                ]),
            ],
            "figures": [("table", "tab3_1"), ("flow", "fig3_1")],
            "plates": [
                ("plaster", "Wide shot: room overview", "Wide shot. Show the whole room, including the ceiling and the "
                 "floor, before moving closer.", {}),
                ("water_stain", "Mid shot: damaged item in context", "Mid shot. The stained area is shown with the "
                 "window and the ceiling rose for orientation.", {}),
                ("crack", "Close-up with scale reference", "Close-up with a ruler as scale reference. Keep the camera "
                 "square to the surface.", {"overlay": "ruler"}),
                ("floor", "Poor lighting", "Poor practice: low light hides the staining. Use the flash or a torch at a "
                 "low angle.", {}),
                ("panel", "Annotated close-up", "Annotations may be added to a copy, never to the original image.",
                 {"marker": "A"}),
                ("glass", "Detail of damage origin", "Close-up of the point of impact. Photograph the origin of the "
                 "damage before any temporary repair.", {}),
            ],
        },
        {
            "num": 4, "title": "Escape of water", "hero": "water_stain",
            "intro": [
                "Escape of water is the most frequent cause of loss under household policies. The policy covers sudden "
                "escapes of water from fixed installations. It does not cover damage caused gradually, for example by "
                "a slow leak from a shower tray or a weeping joint that has continued over weeks or months.",
                "The Claims Assessor's main task is therefore to establish whether the escape was sudden or gradual, "
                "using the pattern of damage, the history given by the customer and moisture readings.",
            ],
            "sections": [
                ("Signs of a sudden escape", [
                    ("ul", ["A single, recent event described by the customer, such as a burst pipe in cold weather.",
                            "Fresh staining with a sharp edge and little or no tide marking.",
                            "Damage concentrated below the point of escape.",
                            "No decay, mould or corrosion in adjacent materials."]),
                ]),
                ("Signs of a gradual leak", [
                    ("ul", ["Several tide marks, showing repeated wetting and drying.",
                            "Mould growth, rot or corrosion of fixings.",
                            "Swollen, delaminated or discoloured timber around baths and showers.",
                            "Failed grout or sealant that has allowed water to pass over a long period."]),
                ]),
                ("Moisture readings", [
                    ("p", "Take readings with a calibrated meter at the positions shown in Figure 4.1, working outwards "
                          "from the suspected source. Take a reference reading in unaffected timber of the same type. "
                          "Record and photograph every meter reading, with the meter display legible in the "
                          "photograph."),
                    ("p", "Pin meters give readings in wood moisture equivalent (WME). Pinless meters give relative "
                          "readings and are useful for mapping the extent of wetting, but should be confirmed with a "
                          "pin meter before a conclusion on cause is reached. The interpretation of readings is shown "
                          "on the photo plates at the end of this chapter."),
                    ("rule", V["r_asm019"]),
                ]),
                ("Video assessment", [
                    ("rule", V["r_asm003"]),
                    ("p", "During a video assessment, ask the customer to show the meter display and the source of the "
                          "leak, and capture screenshots for the claim file."),
                ]),
            ],
            "figures": [("wall", "fig4_1"), ("table", "tab4_2")],
            "plates": [
                ("water_stain", "Fresh ceiling stain below a burst pipe", "Fresh stain below a burst pipe in the loft. "
                 "Sharp edge, no tide marks: consistent with a sudden escape.", {}),
                ("water_stain", "Multiple tide marks", "Several tide marks around a shower waste. Repeated wetting over "
                 "a long period.", {}),
                ("water_stain", "Reference reading in unaffected timber", "Reference reading in dry timber of the same "
                 "type, taken away from the affected area.", {"meter": "14.2"}),
                ("water_stain", "GRADUAL_LEAK_PLATE", None, {"meter": "31.8"}),
                ("floor", "Cupped floorboards", "Cupped boards beside a dishwasher. Lift a board to check the joists "
                 "and the void below.", {}),
                ("floor", "Staining under floor covering", "Staining revealed after lifting vinyl. Note the extent and "
                 "the colour of the staining.", {}),
                ("plaster", "Failed sealant at bath edge", "Failed sealant along the bath edge. Water has tracked behind "
                 "the tiles over time.", {"single": True}),
                ("water_stain", "Mould behind kitchen units", "Mould behind kitchen units. Mould takes time to develop and "
                 "points to prolonged wetting.", {}),
                ("smoke", "Drying equipment in place", "Dehumidifier and air movers in place. Record the equipment and "
                 "the start date of drying.", {}),
                ("water_stain", "Pinless meter mapping", "Pinless meter used to map the extent of wetting before "
                 "confirming with a pin meter.", {"meter": "22.4"}),
            ],
        },
        {
            "num": 5, "title": "Fire and smoke", "hero": "fire_char",
            "intro": [
                "Fire losses range from minor kitchen fires to the total loss of a building. The Claims Assessor must "
                "establish the extent of the damage, confirm that the cause is consistent with the customer's account "
                "and identify any recovery potential, for example where an appliance has failed.",
            ],
            "sections": [
                ("Origin and cause", [
                    ("p", "Burn patterns usually point back to the origin of a fire. Look for the lowest point of "
                          "burning and for V-shaped patterns on walls (Figure 5.1). Note the position of electrical "
                          "appliances, sockets and heat sources near the origin."),
                    ("ul", ["Do not move items at the origin until they have been photographed in place.",
                            "Retain failed appliances for examination where a recovery may be possible.",
                            "If the origin cannot be identified, or if there are signs of more than one origin, tell "
                            "the claims handler, who will consider instructing a forensic investigator and whether a "
                            "referral to SIU is appropriate."]),
                ]),
                ("Smoke and soot", [
                    ("p", "Smoke travels well beyond the area of burning. Check rooms and voids that were closed during "
                          "the fire, and the contents of cupboards. Distinguish between dry soot, which can often be "
                          "cleaned, and oily soot from plastics, which is harder to remove."),
                ]),
                ("Contents", [
                    ("p", "Separate contents into items that can be cleaned, items that must be replaced and items "
                          "that need specialist restoration. Photograph each group before it is removed."),
                ]),
            ],
            "figures": [("vpattern", "fig5_1")],
            "plates": [
                ("fire_char", "Alligator charring on timber", "Deep alligator charring on a door lining close to the "
                 "origin of the fire.", {}),
                ("smoke", "Smoke plume on ceiling", "Smoke plume spreading across the ceiling from the kitchen doorway.",
                 {}),
                ("fire_char", "Origin area with appliance remains", "Remains of a tumble dryer at the lowest point of "
                 "burning. Retain for examination.", {}),
                ("smoke", "Joist ghosting", "Soot deposited along the line of the joists (ghosting). Cleaning alone may "
                 "not remove it.", {}),
                ("debris", "Fire debris after clearance", "Debris after clearance. Photograph contents before disposal.",
                 {}),
                ("fire_char", "Heat damage to plaster", "Spalled plaster above the cooker. Heat damage extends further "
                 "than the visible charring.", {"single": True}),
                ("smoke", "Smoke in a closed cupboard", "Light soot inside a closed cupboard. Smoke reaches closed spaces "
                 "through gaps around doors.", {}),
                ("fire_char", "Electrical intake", "Burnt cable at the consumer unit. Ask an electrician to make safe "
                 "before inspection continues.", {}),
            ],
        },
        {
            "num": 6, "title": "Storm and flood", "hero": "roof",
            "intro": [
                "Storm and flood claims often arrive in large numbers after a weather event. Assessors must work "
                "quickly while maintaining the same standard of evidence, because the cause of damage is not always "
                "the weather.",
            ],
            "sections": [
                ("Storm damage", [
                    ("p", "Check the weather records for the date of loss and the location of the property. Storm "
                          "damage is typically sudden and localised: displaced tiles, damaged ridge, fallen fences."),
                    ("ul", ["Wear and tear, such as failed mortar or perished felt, is not storm damage.",
                            "Water entry through a roof in poor repair is usually excluded, even during a storm.",
                            "Look at neighbouring properties: storm damage rarely affects one house alone."]),
                ]),
                ("Flood damage", [
                    ("p", "Record the depth of flood water inside and outside the property, using the tide line on "
                          "the walls. Photograph the tide line with a scale reference. Note the source of the water, "
                          "such as a river, surface water or a drain."),
                    ("p", "Flood water is contaminated. Porous materials that have been in contact with it, such as "
                          "plasterboard and insulation, usually need to be removed."),
                ]),
            ],
            "figures": [("table", "tab6_1")],
            "plates": [
                ("roof", "Displaced tiles after a storm", "Displaced tiles on the windward slope. Fresh breaks and no "
                 "moss on exposed battens.", {}),
                ("roof", "Long-standing slipped tiles", "Slipped tiles with moss on the exposed surfaces. The damage "
                 "predates the storm.", {}),
                ("flood", "Internal flood line", "Internal tide line measured from the finished floor level with a "
                 "ruler.", {"overlay": "ruler"}),
                ("flood", "Silt deposit at skirting", "Silt deposit along the skirting. Remove and photograph a sample "
                 "area.", {}),
                ("debris", "Debris carried by flood water", "Debris carried into the garden by flood water. Record the "
                 "direction of flow.", {}),
                ("brick", "Wall saturated below damp-proof course", "Saturated brickwork below the damp-proof course.",
                 {"single": True}),
                ("floor", "Swollen floor after flood", "Swollen chipboard flooring after flood. Porous materials usually "
                 "need replacement.", {}),
                ("roof", "Ridge damage", "Ridge tiles lifted along their full length. Check the bedding mortar.", {}),
            ],
        },
        {
            "num": 7, "title": "Subsidence and structural movement", "hero": "brick",
            "intro": [
                "Subsidence is the downward movement of the ground beneath a building, other than by settlement of new "
                "construction. It is often linked to clay soils, trees and leaking drains. Subsidence claims are "
                "complex and long-running, and an early, well-evidenced assessment saves time and cost later.",
            ],
            "sections": [
                ("Recognising subsidence", [
                    ("ul", ["Diagonal cracks that taper, often radiating from the corners of doors and windows.",
                            "Cracks visible inside and outside at the same point.",
                            "Doors and windows that stick or no longer close.",
                            "Stepped cracking in external brickwork following the mortar joints."]),
                    ("p", "Other kinds of movement can produce cracks: shrinkage of new plaster, thermal movement and "
                          "the settlement of new extensions. These are not usually covered."),
                ]),
                ("Measuring cracks", [
                    ("p", "Measure every crack with a crack width gauge at its widest point, and record its length and "
                          "direction. Mark the measuring point so that later readings can be taken at the same place. "
                          "Record readings on the crack monitoring record (Table 7.2)."),
                    ("p", "The referral requirement for wide cracks is stated on the photo plates at the end of this "
                          "chapter and must be followed before cover is confirmed."),
                ]),
                ("Trees and drains", [
                    ("p", "Record the species, height and distance from the building of trees and large shrubs, and "
                          "who owns them. Where a leaking drain may be a cause, arrange a drain survey."),
                ]),
            ],
            "figures": [("house", "fig7_1"), ("table", "tab7_2")],
            "plates": [
                ("brick", "Stepped crack in external brickwork", "Stepped crack following the mortar joints below a "
                 "window.", {"overlay": "ruler"}),
                ("crack", "Tapering crack from window corner", "Tapering crack from the corner of a window opening, "
                 "wider at the top.", {}),
                ("crack", "CRACK_REFERRAL_PLATE", None, {"overlay": "ruler"}),
                ("crack", "Hairline shrinkage cracks", "Hairline cracks in new plaster. Shrinkage, not structural "
                 "movement.", {}),
                ("brick", "Crack at extension junction", "Crack where an extension meets the original house. Typical of "
                 "settlement of the extension.", {}),
                ("plaster", "Sticking door with distorted frame", "Door frame out of square. Measure the gap at the top "
                 "and the bottom of the door.", {}),
                ("crack", "Crack monitoring point", "Monitoring point marked beside the crack. Readings must be taken "
                 "at the same point on each visit.", {"single": True}),
                ("brick", "Tree close to the building", "Mature tree close to the front elevation. Record species, "
                 "height and distance.", {}),
                ("crack", "Internal crack matching external crack", "Internal crack in the same position as the "
                 "external crack.", {}),
                ("debris", "Drain survey excavation", "Excavation for a drain survey. Photograph the pipe condition "
                 "and joints.", {}),
            ],
        },
        {
            "num": 8, "title": "Theft, forced entry and malicious damage", "hero": "door",
            "intro": [
                "Theft and malicious damage claims depend on evidence of what happened, how entry was gained and what "
                "was taken. The Claims Assessor should record the physical evidence carefully and check that it is "
                "consistent with the customer's account.",
            ],
            "sections": [
                ("Signs of forced entry", [
                    ("ul", ["Tool marks on door and window frames, with matching damage to the lock or keep.",
                            "Splintered timber at the lock side of a door.",
                            "Broken glass on the inside of the property when entry was made through a window.",
                            "Damage that is consistent with the force needed to open the door or window."]),
                    ("p", "Note where the evidence is inconsistent: for example, damage to the outside of a frame when "
                          "the door opens outwards, or glass broken from the inside."),
                ]),
                ("Proof of ownership", [
                    ("rule", V["r_asm018"]),
                    ("p", "Acceptable evidence includes receipts, bank statements, photographs, manuals and packaging. "
                          "Record what the customer has provided and what remains outstanding."),
                ]),
                ("Police reports", [
                    ("p", "Record the crime reference number and the name of the police force. Ask the customer "
                          "whether the police attended and whether forensic evidence was taken."),
                ]),
            ],
            "figures": [],
            "plates": [
                ("door", "Forced door at lock side", "Splintered lining at the lock side of a back door. Matching marks "
                 "on the keep.", {}),
                ("door", "Tool marks on frame", "Tool marks on the frame. Photograph with a scale reference.",
                 {"overlay": "ruler"}),
                ("glass", "Broken window pane", "Broken pane beside the handle. Glass on the inside floor.", {}),
                ("door", "Inconsistent damage", "Damage on the hinge side only. Inconsistent with the account given.",
                 {"single": True}),
                ("panel", "Malicious scratching to a vehicle", "Deliberate scratching along the side of a vehicle.",
                 {"marker": "B"}),
                ("plaster", "Graffiti on rendered wall", "Graffiti on a rendered wall. Record the area affected.", {}),
            ],
        },
        {
            "num": 9, "title": "Motor vehicle damage", "hero": "panel",
            "intro": [
                "Motor claims are assessed by desk assessment from photographs, by video or by physical inspection. "
                "The aim is the same in each case: to confirm that the damage is consistent with the accident "
                "described, to agree the repair method and cost and to identify total losses early.",
            ],
            "sections": [
                ("Choosing the assessment route", [
                    ("rule", V["r_asm001"]),
                    ("rule", V["r_asm008"]),
                    ("p", "A physical inspection is needed where the photographs are poor, where the damage may be "
                          "structural or where the circumstances need to be checked."),
                ]),
                ("Repair or total loss", [
                    ("rule", V["r_asm007"]),
                    ("rule", V["r_asm017"]),
                    ("p", f"Repairs are arranged through {V['ven04']}. Total-loss vehicles are collected by "
                          f"{V['ven09']}."),
                ]),
                ("Consistency of damage", [
                    ("ul", ["Compare the height of the impact on both vehicles.",
                            "Look for paint transfer and its colour.",
                            "Check that old damage, such as rusted dents, is excluded from the estimate.",
                            "Note airbag deployment and any damage to suspension or steering."]),
                ]),
            ],
            "figures": [("car", "fig9_1"), ("table", "tab9_1")],
            "plates": [
                ("panel", "Rear-quarter dent", "Dent to the rear quarter panel with paint creasing.", {"marker": "C"}),
                ("panel", "Door panel scrape", "Scrape along the driver's door. Paint transfer from the third-party "
                 "vehicle.", {}),
                ("panel", "Bonnet crease", "Crease across the bonnet. Check the slam panel and radiator support.", {}),
                ("glass", "Windscreen star chip", "Star chip in the driver's line of sight. Replacement rather than "
                 "repair.", {}),
                ("panel", "Bumper scuff", "Bumper scuff at a height consistent with a parking contact.", {}),
                ("panel", "Old damage to exclude", "Old damage with corrosion. Exclude from the estimate.", {}),
                ("glass", "Side window shattered", "Side window shattered during a theft attempt.", {"single": True}),
                ("panel", "Wing panel misalignment", "Uneven panel gap between the wing and the door. Possible "
                 "structural damage.", {}),
                ("panel", "Roof dent from falling branch", "Dent to the roof from a falling branch.", {}),
                ("glass", "Rear screen crack", "Crack running from the edge of the rear screen.", {}),
                ("panel", "Sill damage", "Sill damage after kerbing. Check the suspension alignment.", {}),
                ("panel", "Hail damage pattern", "Multiple small dents from hail across the roof and bonnet.", {}),
            ],
        },
        {
            "num": 10, "title": "Nordic assessments (takst)", "hero": "roof",
            "intro": [
                f"In Norway, Sweden and Denmark, claims are assessed by the {V['t07']} team and by external assessors. "
                "Local terminology is used in policy wordings and customer correspondence: the assessment is a "
                "'takst', the assessor is a 'skadetakstmann' (Norway), 'besiktningsman' (Sweden) or 'taksator' "
                "(Denmark), and the excess is the 'egenandel', 'självrisk' or 'selvrisiko'.",
            ],
            "sections": [
                ("When an on-site takst is needed", [
                    ("rule", V["r_asm009"]),
                    ("p", "Frost damage and snow load are common in Nordic home claims. Check the heating and the "
                          "insulation of pipes in frost claims, and the roof structure and snow clearing in snow-load "
                          "claims."),
                ]),
                ("External assessors", [
                    ("rule", V["r_asm016"]),
                    ("p", f"{V['ven02_full']} is based in {V['ven02_loc']}. The panel contact is {V['ven02_contact']}. "
                          "The fee schedule is in Appendix B."),
                ]),
                ("Recoveries", [
                    ("p", "Where a third party is responsible, record the details so that the recoveries team can "
                          "pursue a claim against them (regress)."),
                ]),
            ],
            "figures": [("flow", "fig10_1")],
            "plates": [
                ("roof", "Snow load damage to roof", "Roof sheeting deformed under snow load. Check the rafters from the "
                 "loft.", {}),
                ("water_stain", "Frost-burst pipe in crawl space", "Frost-burst pipe in an unheated crawl space.", {}),
                ("floor", "Frost damage to floor", "Floor damaged after a frozen pipe thawed.", {}),
                ("brick", "Ice damage to masonry", "Spalled masonry after repeated freezing.", {"single": True}),
                ("flood", "Meltwater entry", "Meltwater entry at the base of an external wall.", {}),
                ("plaster", "Damp in basement wall", "Damp staining in a basement wall after snow melt.", {}),
            ],
        },
        {
            "num": 11, "title": "Reporting, timescales and quality", "hero": "plaster",
            "intro": [
                "The assessor report is the basis for the coverage decision, the reserve and the settlement. It must "
                "be complete, clear and delivered on time.",
            ],
            "sections": [
                ("Timescales", [
                    ("rule", V["r_asm005"]),
                    ("rule", V["r_asm006"]),
                    ("rule", V["r_asm013"]),
                    ("p", "Table 11.1 summarises the timescales that apply to assessment."),
                ]),
                ("Changes to the estimate", [
                    ("rule", V["r_asm014"]),
                ]),
                ("Independence", [
                    ("rule", V["r_asm010"]),
                    ("rule", V["r_asm015"]),
                ]),
                ("Contents of the report", [
                    ("ul", ["Circumstances of the loss as described by the customer.",
                            "Cause of the damage and the evidence for it.",
                            "Extent of the damage, with photographs.",
                            "Cover view, including any exclusions or conditions that may apply.",
                            "Estimate, broken down by trade or item.",
                            "Recovery potential and the details of any responsible third party.",
                            "Any concerns about the claim, recorded factually."]),
                ]),
            ],
            "figures": [("table", "tab11_1")],
            "plates": [],
        },
    ]


NOTES_BANK = [
    "Photograph the damage before any strip-out or temporary repair.",
    "Record the customer's account in their own words.",
    "Note the age and condition of the affected materials.",
    "Check whether the damage extends into adjoining rooms or voids.",
    "Record who was present at the inspection.",
    "Note any previous repairs in the same area.",
    "Compare the damage with the plates in this chapter before forming a view on cause.",
    "Record any concerns factually in the report, without speculation.",
    "Confirm that the photographs include a scale reference where detail matters.",
    "Explain to the customer what happens next and when they will hear from Corvane.",
]

GLOSSARY = [
    ("Assessor Portal", "The system through which instructions are issued to Claims Assessors and reports are "
                        "returned. Formerly the Adjuster Extranet."),
    ("Claims Assessor", "A person, internal or from a panel firm, who inspects or desk-assesses a loss and reports an "
                        "estimate and a cover view."),
    ("Desk assessment", "Assessment from photographs and documents, without a site visit."),
    ("Evidence Vault", "The store for claim documents, photographs and letters. Formerly DOCSTOR."),
    ("Ghosting", "Lines of soot deposited along the line of joists or studs, where the surface is cooler."),
    ("Loss adjuster", "An external Claims Assessor appointed from the panel."),
    ("Pin meter", "A moisture meter that measures electrical resistance between two pins pushed into the material."),
    ("Regress", "The Nordic term for recovery of a claim payment from a responsible third party (subrogation)."),
    ("Skadetakstmann", "Norwegian term for a Claims Assessor. Swedish: besiktningsman. Danish: taksator."),
    ("Takst", "Nordic term for an assessment of damage and its cost."),
    ("Tell-tale", "A device fixed across a crack to show whether it is moving."),
    ("Tide mark", "A line of staining left at the edge of an area that has been wetted and has dried."),
    ("V-pattern", "A V-shaped burn or smoke pattern on a wall, pointing down towards the origin of a fire."),
    ("WME", "Wood moisture equivalent: the moisture content that timber would show at the same reading."),
]


# Case studies (one per chapter 2-10). Illustrative; no amounts, dates or named customers.
CASE_STUDIES = {
    2: ("A fire-damaged terrace", "smoke", [
        "The assessor arrived at a mid-terrace house two days after a kitchen fire. From the hall she could see that "
        "the kitchen ceiling was sagging under the weight of fire-fighting water.",
        "She did not enter the kitchen. She photographed the room from the doorway, asked the customer's contractor "
        "to prop the ceiling and returned the following morning to complete the inspection.",
        "Lesson: a short delay to make the property safe did not affect the claim, and the photographs taken from the "
        "doorway were still usable as evidence of the condition before the ceiling was propped."]),
    3: ("A re-visit that was avoided", "plaster", [
        "A panel loss adjuster inspected a water-damaged kitchen and uploaded a full photo set, including wide shots of "
        "each wall, close-ups with a scale reference and the serial plate of the damaged dishwasher.",
        "When the customer later disputed the extent of the damage, the claims handler was able to resolve the "
        "question from the photographs alone.",
        "Lesson: a complete photo set saves a second visit and shortens the claim."]),
    4: ("Sudden or gradual?", "water_stain", [
        "A customer reported that water had suddenly come through the ceiling below the bathroom. The assessor found "
        "several tide marks on the ceiling, swollen timber around the shower tray and failed sealant.",
        "Pin meter readings in the skirting beside the shower were well above the reference reading taken in dry "
        "timber, and were interpreted using Plate 4.4. The assessor photographed every meter display.",
        "Lesson: the pattern of damage, the readings and the photographs together supported a conclusion that the "
        "damage had developed over a long period. The customer was told clearly which parts of the claim could be "
        "considered."]),
    5: ("A tumble dryer fire", "fire_char", [
        "The burn pattern in a utility room pointed down to the remains of a tumble dryer. The assessor photographed the "
        "appliance in place, recorded the serial plate and arranged for it to be kept.",
        "The recoveries team later used the evidence to pursue the manufacturer.",
        "Lesson: retaining the appliance and recording its details kept the recovery option open."]),
    6: ("Storm, or wear and tear?", "roof", [
        "After a stormy weekend a customer reported slipped tiles and water entry. The assessor found moss on the "
        "exposed battens, perished felt and old nail holes. Neighbouring houses of the same age were undamaged.",
        "The assessor recorded the condition of the roof in detail and explained to the customer what he had found.",
        "Lesson: the weather may reveal existing defects rather than cause new damage. Evidence of the condition of the "
        "roof is essential."]),
    7: ("Cracking after a dry summer", "crack", [
        "A customer reported cracks around the kitchen window and a back door that no longer closed. The cracks "
        "tapered, were wider at the top and were visible inside and outside. A large tree stood close to the rear "
        "elevation.",
        "The assessor measured each crack with a gauge, marked the measuring points, recorded the tree and followed "
        "the referral requirement shown on Plate 7.3 before any view on cover was given.",
        "Lesson: careful measurement on the first visit makes later monitoring meaningful."]),
    8: ("Inconsistent forced entry", "door", [
        "A customer reported a burglary through the back door. The assessor found damage only on the hinge side of the "
        "frame and no marks on the keep. Glass from a broken pane lay outside the door.",
        "The assessor recorded the evidence factually, with photographs and a scale reference, and told the claims "
        "handler, who considered whether a referral to SIU was appropriate.",
        "Lesson: record what you see without drawing conclusions in front of the customer."]),
    9: ("A low-speed rear impact", "panel", [
        "A customer submitted photographs of rear bumper damage after a car park collision. The photographs showed all "
        "four corners, the odometer and close-ups with the damage at a height consistent with the third-party vehicle.",
        "The claim was desk-assessed and the repair arranged through the repair network.",
        "Lesson: good customer photographs allow a quick desk assessment."]),
    10: ("A frozen pipe in a holiday cabin", "floor", [
        "A pipe burst in a Norwegian holiday cabin during a cold spell. The skadetakstmann found that the heating had "
        "been switched off and the water had not been turned off or drained.",
        "The assessor recorded the heating settings, the position of the stopcock and the extent of the damage, and "
        "referred to the safety conditions (sikkerhetsforskrifter) in the policy wording in the report.",
        "Lesson: in frost claims, record how the property was heated and protected before the loss."]),
}
