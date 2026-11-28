# NIPS ontology for SITRA

This document specifies the intended ontology, not the current Neo4j schema. It uses the [NARA SITRA series](https://catalog.archives.gov/id/604416) technical documentation (`131.1DP.pdf`): the March 2004 translated layout (PDF pp. 16–18), agency field descriptions (pp. 19–47), and the October 2023 correction (p. 1).

## Data Record and Event types

A Data Record represents one logical report. An Event represents a reported occurrence, not a physical source row or a summary total.

| Source discriminator | Data Record subtype | Event |
| --- | --- | --- |
| `DATAT=S` and `SERAL` does not start with `C` | Small Scale Operation | Action, with set 2 details when present |
| `DATAT=S` and `SERAL` starts with `C` | Small Scale Operation with `isSummary=true` | None from the summary. `SC` is shorthand across two fields, not a `DATAT` value or a Weekly Summary. |
| `DATAT=E` | Enemy Initiated | Enemy Incident, with set 2 details when present |
| `DATAT=L` | Large Scale Operation | Operation. Multiple set 2 coordinates can describe one Operation. |
| `DATAT=W` | Weekly Summary | None from aggregate counts |
| Unrecognized `DATAT` | Unclassified Data Record | None inferred |

## Identity and provenance

- Set `dataRecordId` to the 12-character control group `DATE + DATAT + SERAL + CORP + PART` (translated columns 1–12). Preserve spaces, leading zeros, and original field names. Group continuation rows with the same control group into one logical Data Record, not a network of separate reports. Flag conflicting fixed fields for review instead of silently overwriting them.
- Keep the raw fixed fields (columns 13–78) on the Data Record. Preserve each populated periodic set occurrence separately, including its set number, raw line identifier, fields, and source file and row or byte offset. Line identifiers are not assumed to be numeric or unique; the PDF's sample shows set 4 identifier `2B1` on more than one row of the same logical report (PDF pp. 49–50). Neither co-location on a translated row nor matching line identifiers establish a join between sets.
- Store normalized properties separately from their raw values. Preserve blanks, zeroes, documented sentinels, and unknown codes distinctly. Use `DATE` for the report timeline, not as an exact event timestamp; do not substitute `UDATE` (last file update) for it.

## Source field mapping

In addition to the Data Record and Event subtypes above, the ontology has **Unit** (Division, Brigade, Regiment, Battalion, Company, or unresolved Unit), **Location** (Country, Province, or objective grid reference), and **Weapon**, **Ammunition**, and **Provision** catalog types. Use report-scoped observations for participation, support, material quantities, and summary totals rather than treating them as permanent attributes of shared nodes.

| Section | Source fields | Interpreted properties and destination |
| --- | --- | --- |
| Control and fixed metadata | `DATE`, `DATAT`, `SERAL`, `CORP`, `PART`, `FNATL`, `UDATE` | **Data Record**: report date (`YYMMDD`), type, serial/paragraph, tactical area, part, force the report concerns, and update date (`YYJJJ`, ordinal day of year). `CORP` is a geographic/reporting scope, not a Unit. `FNATL` is not necessarily the actor or country of occurrence. |
| Fixed operation fields | `OPNAM`, `OPCOD`, `DTEI`, `DTET`, `HOURI`, `HOURT`, `OPDAY`, `CTDAY` | **Operation**: name, `FWOPS` type, and validated initiation/termination dates. Keep `OPDAY` (battalion-days) and `CTDAY` (days of contact) report-scoped, not totals on a shared Operation. The translated layout calls columns 65–68 `HOURT` (initiation) and 75–78 `HOURI` (termination), while the agency definitions use the opposite names. Retain the raw fields and validate their positional interpretation before publishing times. |
| Fixed geography | `CNTRY`, `PRVC1`, `PRVC2`, `PRVC3` | **Country** and **Province**: historical SITRA code and decoded name. Use the `PROVS` table in its South Vietnam context. Preserve source field and rank on the geography link: `PRVC1` is primary, `PRVC2`/`PRVC3` secondary. Keep unknown `00` as a raw value; retain special entries such as the DMZ as reported areas rather than ordinary provinces. |
| Set 1 (`FSLIN`), combined operations and support | `CONAT`, `CONAM`, `NGFS`, `ARSVC`, `ARCFT` | **Operation support observation**: partner force code, partner's name for the operation, naval support mission count, aircraft service, and aircraft type. `CONAM` is an alias, not evidence of another event; `ARCFT` alone is not a Weapon. `NGFS=999` means support occurred but the count is unknown. |
| Set 2 (`SSLIN`), action and objective | `UTM`, `TYPAT`, `OBJEC`, `OBJDS` | **Action / Enemy Incident**: action type, objective code, and objective description. Use `FWOPS` for `S` detail and `ACTNS` for `E`; use `OBJES` and `OBDES` for the objective fields. `UTM` is the objective's grid reference, not necessarily the position of a Unit or the exact site of the action. Keep each raw grid reference, including those on `L` reports. Store the grid zone, constructed MGRS reference, and coordinates only if justified; leave ambiguous points unresolved. |
| Set 3 (`LINFS`), units | `DVDES`, `BRDES`, `BNID`, `COMPY`, `SVNAT`, `NOOF`, `SMTH`, `MVRSP`, `RESAC` | **Unit**: division designation (`DVDES`), brigade or regiment designation (`BRDES`), battalion ID (`BNID`), or company ID (`COMPY`). Use service/nationality (`SVNAT`) and parent context to disambiguate designations, particularly company IDs. Use an unresolved Unit when a designation is present but its echelon is unclear. On the **participation observation**, keep service as reported, maneuver/support (`MVRSP`), and active/reserve (`RESAC`). Use `NOOF` and `SMTH` for the reported number and size of unnamed units; do not create placeholder Units for each count. |
| Set 4 (`TSLIN`), loss or expenditure | `LSCAT`, `LSCLS`, `LSDSC`, `LNATL`, `NODES`, `NODAM`, `NOCAP`, `LUNIT` | **Material/loss observation**: derive `LCODE` by concatenating `LSCAT` and `LSCLS`. Use the full `CATRS` code to reference a **Weapon**, **Ammunition**, or **Provision** catalog type with a decoded label. Keep the reported description, loss nationality, quantities, and unit of measure (`LUNIT`) on the observation. Distinguish ammunition expenditure from loss. Preserve personnel, structures, and unmapped categories even without a catalog node. |
| Set 5 (`SFLIN`), action and incident statistics | `INATL`, `ISIZE`, `IACTS`, `IWCTD`, `IWOCT`, `IATT`, `ITERR`, `ISABT`, `IPROP`, `IHARR`, `IAA`, `ICTZ` | **Data Record summary observation**: force and size codes, action and incident totals, and corps area. `IWCTD` and `IWOCT` can denote with/without contact or day/night contact depending on report context; retain the source names when that context is unresolved. |
| Set 6 (`LINSS`), ratios and manpower | `RTWER`, `RTPER`, `RVNRR`, `RVNRL`, `RVNPR` | **Data Record summary observation**: friendly-to-enemy weapon-loss and personnel KIA ratios (two implied decimal places), and regular, regional, and popular RVN manpower. |
| Set 7 (`SLINS`), corps-area statistics | `LNAT`, `LNATI`, `LTYPE`, `LCTZ1`, `LCTZ2`, `LCTZ3`, `LCTZ4` | **Data Record summary observation**: force suffering the loss, force inflicting it, reported category, and separate values for corps areas 1–4. Do not treat every `LTYPE` as a casualty category or generate individual Events from these totals. |

**Set 4 correction:** `NODES` is personnel killed or material destroyed. `NODAM` is friendly personnel wounded, enemy personnel returned, or material damaged. `NOCAP` is friendly personnel missing, enemy personnel detained, enemy material captured, or friendly material lost, depending on the category and side. Preserve raw values when the context does not support a more specific label. Treat the duplicated `MU` code and NARA's suggested `MV` correction as a codebook ambiguity, not a rewrite of raw data.

## Relationships

| Relationship | Evidence and scope |
| --- | --- |
| `DataRecord → REPORTS → Event` | Record-scoped identity by default. Merge Operation identities across reports only when dates, locations, or other evidence corroborate the name. |
| `Action / Enemy Incident → PART_OF → Operation` | Add only when membership is supported, not merely because the events share a name, place, or date. |
| `DataRecord → REFERENCES_UNIT → Unit`; `Unit → PARTICIPATED_IN → Event` | Retain the report and set 3 occurrence as evidence. Add event participation only when attributable; record `MVRSP` and `RESAC` alongside it. A parent designation does not by itself establish that the parent participated. |
| `Unit → REPORTED_UNDER → Unit` | Use Company → Battalion → Brigade/Regiment → Division where supported. Retain date and provenance; do not assume permanent command or invent missing levels. |
| `DataRecord → REPORTS_GEOGRAPHY → Location`; `Event → HAS_OBJECTIVE_LOCATION → Location`; `Province → IN_COUNTRY → Country` | Keep report-level and event-level geography separate. Attach multiple set 2 references to an Operation without multiplying Events. If grid references are not represented as Location nodes, retain them on the set 2 occurrences. Do not turn service/nationality codes into geographic links. |
| `DataRecord → HAS_MATERIAL_OBSERVATION → observation → ABOUT → Weapon / Ammunition / Provision` | Preserve one observation per set 4 occurrence, with an optional Event link when attributable. Use no `ABOUT` edge for unmapped rows. The catalog node represents a type, not an individual item; a loss alone does not establish use, ownership, or who caused it. |
| `DataRecord → RELATED_TO → DataRecord` | Shared resolved unit, place, or report date may support a **possible** link, not a source-stated relationship or an identity merge. Record each shared value as evidence and retain it and the inferred origin if a link is later confirmed. Do not link aggregate summaries to individual events without supporting evidence. |

For the MVP, prioritize report-to-event, report-to-unit, and report-to-location links. Keep all periodic occurrences available even when they do not support a graph link.
