import os
from datetime import datetime

# ====== CONFIG ======
# Change this if you want to point elsewhere later
base_dir = r"C:\Users\wsd3\OneDrive\GRoK\Projects\Port Sulphur"

# Make sure the folder exists
os.makedirs(base_dir, exist_ok=True)

today = datetime.now().strftime("%Y-%m-%d")

# ====== CONTENT ======
field_sheet_md = f"""# Port Sulphur Revetment – Field Sheet (RM ~39 AHP, West Bank)

**Site:** Former Freeport-McMoRan, Port Sulphur, LA (Plaquemines Parish)  
**River Mile:** 41.1 → 34.3 (WB) — *Your site ≈ RM 39 (inside Port Sulphur revetment reach)*  
**Prepared:** {today}

---

## 1) Quick Facts (use on deck / toolbox talk)
- **Revetment reach:** **Port Sulphur (WB) RM 41.1–34.3.**
- **USACE rules:** **No anchoring over revetted banks** (33 CFR 207.200). Treat revetment as a protected MR&T feature.
- **Penetrations:** **Do not drive piles/spuds/anchors through ACM/trenchfill** without **Corps-approved repair detail** (June 1999 drawing: *Repair Procedures when Penetrating Revetments with Piles, Caissons, and/or Pile Clusters*).
- **Permits/permissions required:** **Sec. 10/404** (Regulatory) **and** **Sec. 408** (alteration of civil works).

## 2) Coordinates & Map Notes (fill in during desktop recon)
- **Approx. site centroid (lat/long):** `_____ , _____`  
- **Bank:** West Bank (RDB).  
- **Nearest features:** Old Freeport-McMoRan dock works / Port Sulphur industrial frontage.  
- **USACE survey artifacts to collect:** 2025 Port Sulphur TIFF + XYZ multibeam (Lower Mississippi Revetment Surveys page).

> **Field reminder:** Revetment toe and mat edges vary by stage; don’t assume straight lines. Verify with latest survey and stage at Belle Chasse gauge.

## 3) Do-Not-Do List (post at gangway)
- **No anchoring or spudding on revetted bank** without an approved plan and 408 permission.  
- **No blind pile driving**. If penetration is unavoidable, submit shop drawings with the **June 1999 repair detail** and receive MVN approval **before** work.  
- **No equipment tracking/pushing on ACM** unless the mat is explicitly designed/approved as a work platform.

## 4) Desktop Overlay (QGIS/ArcGIS – steps)
1. Download **Port Sulphur (34.3–41.1 WB)** *TIFF* and 2025 *XYZ* from MVN **Revetment Surveys**.  
2. In QGIS: Add **XYZ** as *Delimited Text → Point layer* (X=Easting or Lon, Y=Northing or Lat per file headers). Build a **TIN** or use **interpolation** for a surface if needed.  
3. Add the **TIFF** survey as raster; set transparency 40–60%.  
4. Georeference your **site plan** (dock linework / proposed piles).  
5. Digitize **mat edge/toe** polylines and buffer 25–50 ft for “no-penetration” shading.  
6. Export a **field PDF** (A3/A4) with: RM ticks, toe line, proposed features, and a **red hatch “No anchor / no spud” zone**.

## 5) Contact & Submittal
- **MVN POC:** CEMVN-ED-LC (Channel Improvement / Revetment).  
- **Submittals:** Method statement, survey overlay, pile/anchor avoidance plan **or** penetration repair design citing **June 1999 drawing**.

## 6) Sources (for the spec / plan notes)
- **Revetment Locations table – Port Sulphur 41.1→34.3 (WB)** (MVN).  
- **Revetment Surveys (TIFF + 2025 multibeam XYZ), Lower MS – Port Sulphur** (MVN).  
- **Permit Requirements & Repair** pages (MVN) – June 1999 repair drawing reference.  
- **33 CFR 207.200** – anchoring prohibition over revetted banks.  
- **Revetment Types** – ACM vs trenchfill description (MVN).

---

### On-sheet Standard Notes (paste into drawings/spec)
1. *No anchoring, spudding, or pile/caisson/anchor penetrations within revetment footprint without USACE MVN approval and issued **Section 408** permission; obtain **Section 10/404** permits as applicable.*  
2. *If penetration is authorized, contractor shall implement USACE **June 1999** repair detail for piles/caissons/clusters and provide as-builts; any damage to MR&T features shall be restored to equal or better condition per MVN direction.*  
3. *Coordinate river stages and currents; verify mat position in the field prior to work using latest MVN survey products.*
"""

checklist_md = f"""# Section 408 Submittal Checklist – Port Sulphur Revetment (RM ~39 WB)

**Project:** {today} – Work over/adjacent to MR&T revetment (Port Sulphur WB RM 41.1–34.3)  
**Owner/Agent:** _______________________    **Engineer/Contractor:** _______________________

---

## A) Administrative
- [ ] Cover letter requesting **Section 408 permission** (cite MR&T revetment; include River Mile and bank).  
- [ ] Parallel **Regulatory** applications (**Section 10** / **Section 404** if any fill/stone).  
- [ ] Contact sheet (PMs, site superintendents), schedule, and emergency plan.

## B) Technical Package
- [ ] **Site plan** with RM ticks and bank, showing all proposed structures, moorings, access, and construction limits.  
- [ ] **Overlay** of latest MVN **Revetment Survey** (*TIFF + 2025 XYZ*), with digitized **mat edge/toe** and **no-anchor/no-spud** hatching.  
- [ ] **Hydro conditions** summary: controlling stages, typical velocity, scour considerations.  
- [ ] **Means & Methods**:  
  - Avoidance plan for piles/spuds/anchors **OR**  
  - **Penetration repair design** per **USACE June 1999 drawing** (“Repair Procedures when Penetrating Revetments with Piles, Caissons, and/or Pile Clusters”), including sections, collars/seals, protection stone, QA/QC and inspection.  
- [ ] **Load & stability** checks for any temporary works (dolphins, spud barges not on revetment, mooring plans).  
- [ ] **Environmental**: turbidity/containment, debris control, fuel spill response, protected species BMPs (if applicable).

## C) Field Controls & QA
- [ ] Pre-work **revettment verification** (probe/ROV/MBES passes) and stakeout of toe/edge.  
- [ ] **No-go** plan for equipment: anchor lines, spud zones, and restricted swing arcs.  
- [ ] **Damage response**: stop-work, USACE notification chain, emergency repair per MVN standard.

## D) References (cite in submittal)
- MVN **Revetment Locations**: **Port Sulphur WB RM 41.1–34.3**.  
- MVN **Revetment Surveys**: Port Sulphur (Lower MS) – **TIFF + 2025 XYZ**.  
- MVN **Permit Requirements** (June 1999 repair detail reference) and **Repair** page.  
- **33 CFR 207.200** anchoring prohibition over revetted banks.  
- MVN **Revetment Types** (ACM vs trenchfill).

---

**Notes:**  
- Stage-dependent toe position—tie survey date to mean daily stage (Belle Chasse) in the overlay legend.  
- If historical industrial works exist (old piles/sheets), include a utilities/obstruction sheet and a risk allowance for unknowns.
"""

# ====== WRITE FILES ======
field_path = os.path.join(base_dir, "Port_Sulphur_RM39_Field_Sheet.md")
checklist_path = os.path.join(base_dir, "Port_Sulphur_RM39_Section408_Checklist.md")

with open(field_path, "w", encoding="utf-8") as f:
    f.write(field_sheet_md)

with open(checklist_path, "w", encoding="utf-8") as f:
    f.write(checklist_md)

print("Files written to:", base_dir)
