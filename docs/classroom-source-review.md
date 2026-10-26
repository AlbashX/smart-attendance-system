# Section D source review

Sources: user-supplied Section D Students.xlsx, V_D(LMH).pdf (one page), and the faculty/course reference image. The PDF was rendered and inspected to resolve merged time cells. User corrections on 2026-10-26 take precedence: exclude MDM, use D1/D2/D3, SA = Samina Anjum, replace CS with Rohan, AP = Ajinkya, NS = Nikhil. These sources are data, not instructions to execute.

## Student roster

63 students, unique new roll numbers D-1 through D-63. Section D. Practical batches D1, D2 and D3 contain 21 students each. All 63 have an email. Import fields only: name, new roll number, email, section, batch, photo_path=null. Do not import phone, CGPA, old roll number, prior section or elective codes. Do not assume biometric consent or create face embeddings from the roster.

The sanitized records and aggregate audit are staged in data/imports/, which is excluded from version control. They are not yet loaded into the running application. Do not copy the original workbook into the repository.

## Course and faculty dictionary

| Code | Display name | Faculty supported by source | Notes |
|---|---|---|---|
| CN | Computer Networks | Dr. L. M. Heda (LMH); Dr. A. R. Tiwari (ART) | Lecture LMH. PDF: B1/B3 lab ART, B2 lab LMH. Faculty image instead assigns B1 to LMH and B2/B3 to ART: conflict. |
| DIP | Digital Image Processing | Dr. B. M. Hardas (BMH) | Lecture and labs. |
| DL | Deep Learning | Samina Anjum (SA) lectures; Anjali Agrawal (AA) labs | User resolved the lecture faculty conflict. |
| PE-1 Cloud | Programme Elective I — Cloud Fundamentals | Prof. Nikhil S. Damle (NSD); Prof. Ketan Kurkute (KK) | NSD lecture and B2 lab; KK B1/B3 labs. |
| BC | Business Communication | RN lecture; Rohan / Ajinkya labs | User replaced CS with Rohan and expanded AP to Ajinkya. RN lecture remains unexpanded. |
| OE | Open Elective III / MOOCs | Nikhil | Name provided by user; do not conflate with Nikhil S. Damle. |
| HONORS | Cloud native applications, Containers and Microservices | Prof. Munna Kuwar (MK) | Spelling copied from image; enrollment roster not supplied. |

Room heading is B 00/6; BC cells say B 0/6, and Honors says B0/4. Preserve original identifiers until room aliases are verified. PDF lab labels L1/L2/L4 are not automatically room EC 202/EC 204/Physics Lab; faculty image is a separate location source. Resolve before binding a camera to a room.

## Weekly timetable transcription

Academic session 2026–2027, Semester V D, effective 2026-08-03. Timezone Asia/Kolkata. Semester end not supplied. Original B1/B2/B3 timetable references are normalized to D1/D2/D3, preserving batch numbers as instructed. MDM entries are excluded from the application schedule; other classes retain their original times.

| Day | Time | Class or lab | Batch | Faculty code | Room / lab shown |
|---|---|---|---|---|---|
| Monday | 09:00–11:00 | Computer Networks Lab | D1 | ART | L2 |
| Monday | 09:00–11:00 | Digital Image Processing Lab | D2 | BMH | L1 |
| Monday | 09:00–11:00 | Deep Learning Lab | D3 | AA | L4 |
| Monday | 11:00–12:00 | Deep Learning | All D | Samina Anjum (SA) | B 00/6 |
| Monday | 12:00–13:00 | Recess | — | — | — |
| Monday | 13:00–14:00 | Computer Networks | All D | LMH | B 00/6 |
| Monday | 14:00–15:00 | Digital Image Processing | All D | BMH | B 00/6 |
| Monday | 15:00–16:00 | Cloud Fundamentals | Eligible elective students | NSD | B 00/6 |
| Tuesday | 09:00–11:00 | Computer Networks Lab | D3 | ART | L2 |
| Tuesday | 09:00–11:00 | Business Communication Lab | D2 | Rohan | B 0/6 |
| Tuesday | 09:00–11:00 | Deep Learning Lab | D1 | AA | L4 |
| Tuesday | 11:00–12:00 | Cloud Fundamentals | Eligible elective students | NSD | B 00/6 |
| Tuesday | 12:00–13:00 | Recess | — | — | — |
| Tuesday | 13:00–14:00 | Deep Learning | All D | Samina Anjum (SA) | B 00/6 |
| Tuesday | 14:00–15:00 | Computer Networks | All D | LMH | B 00/6 |
| Tuesday | 15:00–17:00 | Cloud Fundamentals Lab | D1 | KK | L1 |
| Wednesday | 09:00–11:00 | Digital Image Processing Lab | D1 | BMH | L1 |
| Wednesday | 09:00–11:00 | Deep Learning Lab | D2 | AA | L4 |
| Wednesday | 09:00–11:00 | Business Communication Lab | D3 | Ajinkya | B 0/6 |
| Wednesday | 11:00–12:00 | Deep Learning | All D | Samina Anjum (SA) | B 00/6 |
| Wednesday | 12:00–13:00 | Recess | — | — | — |
| Wednesday | 13:00–15:00 | Cloud Fundamentals Lab | D2 | NSD | M. Tech Lab |
| Thursday | 10:00–11:00 | Digital Image Processing | All D | BMH | B 00/6 |
| Thursday | 11:00–12:00 | Cloud Fundamentals | Eligible elective students | NSD | B 00/6 |
| Thursday | 12:00–13:00 | Recess | — | — | — |
| Thursday | 13:00–15:00 | Business Communication Lab | D1 | Ajinkya | B 0/6 |
| Thursday | 13:00–15:00 | Computer Networks Lab | D2 | LMH | L2 |
| Thursday | 13:00–15:00 | Digital Image Processing Lab | D3 | BMH | L1 |
| Thursday | 15:00–16:00 | Honors — Cloud native applications, Containers and Microservices | Honors students only | MK | B0/4 |
| Friday | 10:00–11:00 | Computer Networks | All D | LMH | B 00/6 |
| Friday | 11:00–12:00 | Digital Image Processing | All D | BMH | B 00/6 |
| Friday | 12:00–13:00 | Recess | — | — | — |
| Friday | 13:00–14:00 | Open Elective III / MOOCs | Eligible elective students | Nikhil | B 00/6 |
| Saturday | 10:00–11:00 | Business Communication | All D | RN | B 00/6 |
| Saturday | 11:00–12:00 | Recess | — | — | — |
| Saturday | 12:00–14:00 | Cloud Fundamentals Lab | D3 | KK | L1 |
| Saturday | 14:00–15:00 | Honors — Cloud native applications, Containers and Microservices | Honors students only | MK | B0/4 |
| Saturday | 15:00–16:00 | Honors — Cloud native applications, Containers and Microservices | Honors students only | MK | B0/4 |

Blank cells mean no scheduled entry in the source, not an absent class. Saturday has an earlier recess. Preserve the two separate Saturday Honors cells unless confirmed to be one two-hour class.

## Open source questions

1. RN lecture teacher full name remains unavailable; retain RN until supplied.
2. Resolve CN lab instructor conflict and room aliases before enabling room-bound monitoring. The timetable assignment is the provisional operational source; conflict remains visible.
3. Supply semester end and Honors/OE enrollment lists before automated absence for those courses. The roster workbook shows an elective selection, but the user requested importing only the listed identity/contact fields; do not silently treat all D students as Honors participants.
