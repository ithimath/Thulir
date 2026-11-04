"""Grounded, Non-Predictive Policy & Rule Assistant Service.

Strict Mandate:
- THULIR is NOT an emotion detector, diagnostic tool, or dropout predictor.
- This assistant provides statutory TN School Education guidelines, THULIR rule references,
  and support intervention SOPs.
- Gracefully functions completely offline without third-party API dependencies.
"""
from typing import Dict, Any, List
import re

POLICY_KNOWLEDGE_BASE = [
    {
        "id": "attendance_75_percent",
        "keywords": ["attendance", "75", "minimum attendance", "low attendance", "att-low", "exam eligibility", "condonation"],
        "title": "TN School Education Department: Minimum Attendance & Exam Norms",
        "sources": ["Tamil Nadu Directorate of Government Examinations (TNDGE) Attendance Code", "THULIR Rule ATT-LOW"],
        "content_en": (
            "Under Tamil Nadu State Board & Government Higher Secondary School regulations, students are required to maintain a minimum of 75% attendance during the academic term for regular examination eligibility. "
            "Students falling between 65% and 74% attendance may be granted condonation only on genuine medical or compassionate grounds upon verification by the Headmaster. "
            "Under THULIR Rule ATT-LOW, any student whose latest period attendance falls below 75.0% is flagged for human review to coordinate early attendance support."
        ),
        "content_ta": (
            "தமிழ்நாடு அரசு மேல்நிலைப் பள்ளி விதிமுறைகளின்படி, பொதுத்தேர்வு மற்றும் பருவத்தேர்வுகளுக்கு தகுதி பெற மாணவர்கள் குறைந்தபட்சம் 75% வருகைப் பதிவு கொண்டிருக்க வேண்டும். "
            "65% முதல் 74% வரை வருகை உள்ள மாணவர்கள் மருத்துவச் சான்று அல்லது தகுந்த காரணங்களுக்காக தலைமை ஆசிரியர் ஒப்புதலுடன் விலக்கு பெறலாம். "
            "துளிர் (THULIR) விதி ATT-LOW இன் கீழ், வருகை 75.0% க்கு குறைவாக உள்ள மாணவர்கள் வழிகாட்டுதல் உதவிக்காக ஆசிரியர் ஆய்வுக்கு அனுப்பப்படுகிறார்கள்."
        ),
    },
    {
        "id": "consecutive_absence",
        "keywords": ["consecutive", "unexcused", "absent", "3 days", "att-consec", "missing days", "leave"],
        "title": "SOP for Consecutive Unexcused Absences",
        "sources": ["School Education Department Student Safety & Attendance SOP", "THULIR Rule ATT-CONSEC"],
        "content_en": (
            "When a student has 3 or more consecutive days of unexcused absence, school guidelines mandate prompt guardian contact. "
            "THULIR triggers rule ATT-CONSEC on >= 3 consecutive unexcused absences. "
            "Recommended standard procedure: 1) Class teacher telephonic verification with parent/guardian within 24 hours. "
            "2) If unreachable, field outreach or PTA liaison inquiry. 3) Document notes in Support Cases without recording speculative or stigmatizing remarks."
        ),
        "content_ta": (
            "மாணவர் முன்னறிவிப்பின்றி தொடர்ச்சியாக 3 அல்லது அதற்கு மேற்பட்ட நாட்கள் பள்ளிக்கு வராமல் இருந்தால், உடனடியாக பெற்றோர் அல்லது பாதுகாவலரை தொடர்பு கொள்ள வேண்டும். "
            "துளிர் விதி ATT-CONSEC இதற்கான ஆய்வுக் குறிப்பை வழங்கும். "
            "பரிந்துரைக்கப்பட்ட நடைமுறை: 1) வகுப்பு ஆசிரியர் 24 மணி நேரத்திற்குள் பெற்றோருடன் தொலைபேசியில் தொடர்பு கொள்ளுதல். "
            "2) தொடர்பு கொள்ள இயலவில்லை எனில் பெற்றோர் ஆசிரியர் கழகம் மூலம் விசாரித்தல். 3) ஊகங்களைத் தவிர்த்து உண்மைத் தகவல்களை வழக்கில் பதிவு செய்தல்."
        ),
    },
    {
        "id": "marks_pass_criteria",
        "keywords": ["pass mark", "marks", "low marks", "35", "mark-low", "cat", "continuous assessment", "failing"],
        "title": "Continuous Assessment & Passing Criteria Norms",
        "sources": ["Samacheer Kalvi Assessment Manual", "THULIR Rule MARK-LOW"],
        "content_en": (
            "The statutory pass mark in Continuous Assessment Tests (CAT) and Term Examinations is 35%. "
            "Under THULIR Rule MARK-LOW, any student scoring below 35% in their most recent subject assessment is highlighted for learning support. "
            "Recommended action: Class teacher initiates Remedial Tutoring and assigns a peer study partner. Formal support case can be opened if low scores span multiple core subjects."
        ),
        "content_ta": (
            "தொடர் மதிப்பீட்டுத் தேர்வுகள் (CAT) மற்றும் பருவத் தேர்வுகளில் தேர்ச்சி பெறுவதற்கான குறைந்தபட்ச மதிப்பெண் 35% ஆகும். "
            "துளிர் விதி MARK-LOW இன் கீழ், 35% க்கும் குறைவான மதிப்பெண் பெறும் மாணவர்கள் கூடுதல் கற்றல் உதவிக்காக குறிக்கப்படுவர். "
            "பரிந்துரைக்கப்பட்ட நடைமுறை: பாடம் கற்பிக்கும் ஆசிரியர் மூலமாக சிறப்பு பயிற்சி (Remedial Tutoring) வழங்குதல் மற்றும் குழு கற்றல் அமைத்தல்."
        ),
    },
    {
        "id": "mark_decline_trajectory",
        "keywords": ["decline", "dropping marks", "mark-decline", "trend", "falling marks", "trajectory"],
        "title": "Academic Trajectory & Mark Decline Protocol",
        "sources": ["Academic Performance Monitoring Guidelines", "THULIR Rule MARK-DECLINE"],
        "content_en": (
            "THULIR Rule MARK-DECLINE detects when a student experiences two consecutive score drops in the same subject with a cumulative decline of 15 percentage points or more. "
            "This rule highlights emerging learning challenges before a student fails. "
            "Teachers are advised to review the specific topics where understanding dipped and consult with the school counsellor if the drop correlates with recent attendance gaps."
        ),
        "content_ta": (
            "துளிர் விதி MARK-DECLINE, ஒரே பாடத்தில் தொடர்ச்சியாக இரண்டு முறை மதிப்பெண்கள் குறைந்து, மொத்த சரிவு 15 சதவீத புள்ளிகள் அல்லது அதற்கு அதிகமாக இருக்கும் போது எச்சரிக்கை செய்கிறது. "
            "மாணவர் தேர்ச்சி பெறாமல் போவதற்கு முன்பே கற்றல் இடைவெளிகளை கண்டறிந்து வழிகாட்ட இது உதவுகிறது."
        ),
    },
    {
        "id": "assignment_guidelines",
        "keywords": ["assignment", "homework", "asg-low", "asg-decline", "submission", "completion rate"],
        "title": "Assignment Completion & Formative Evaluation Norms",
        "sources": ["Curriculum Homework Policy", "THULIR Rules ASG-LOW and ASG-DECLINE"],
        "content_en": (
            "Formative assignments reinforce classroom instruction. "
            "THULIR Rule ASG-LOW triggers when assignment completion rate in the current period is strictly below 60.0% (minimum 3 assignments assigned). Late submissions count as completed. "
            "Rule ASG-DECLINE triggers when completion drops by 20.0 percentage points or more compared to the prior period."
        ),
        "content_ta": (
            "வகுப்பறை கற்றலை வலுப்படுத்த ஒப்படைப்புகள் (Assignments) வழங்கப்படுகின்றன. "
            "துளிர் விதி ASG-LOW, நடப்பு பருவத்தில் ஒப்படைப்பு முடித்தல் விகிதம் 60.0% க்கும் குறைவாக இருக்கும்போது (குறைந்தது 3 ஒப்படைப்புகள்) எச்சரிக்கை செய்கிறது. "
            "விதி ASG-DECLINE, முந்தைய பருவத்தை விட 20.0 சதவீத புள்ளிகள் சரிவு ஏற்படும் போது குறிக்கிறது."
        ),
    },
    {
        "id": "confidential_case_notes",
        "keywords": ["confidential", "privacy", "case notes", "counsellor", "sensitive", "protection", "secrecy"],
        "title": "Student Privacy & Confidential Case Notes Protocol",
        "sources": ["Protection of Children Guidelines", "THULIR Security & Data Governance Manual"],
        "content_en": (
            "To safeguard student dignity and privacy, THULIR implements a strict three-tier note confidentiality model: "
            "1) Standard case notes are visible to assigned teachers and administrators. "
            "2) Sensitive case notes (e.g. family emergencies, psychological consultations, medical disclosures) are strictly visible only to the assigned counsellor. "
            "Teachers and administrators see redacted summaries '[Confidential note on file with Counsellor]'. "
            "All access is logged in the immutable audit trail."
        ),
        "content_ta": (
            "மாணவர்களின் தனிநபர் உரிமை மற்றும் கண்ணியத்தைப் பாதுகாக்க, துளிர் மூன்று அடுக்கு பாதுகாப்புக் கொள்கையைக் கொண்டுள்ளது: "
            "1) பொதுவான குறிப்புகள் ஆசிரியர்கள் மற்றும் நிர்வாகிகளால் பார்க்க முடியும். "
            "2) குடும்பச் சூழல், மருத்துவ அல்லது மனநல ஆலோசனைகள் போன்ற முக்கிய குறிப்புகள் நியமிக்கப்பட்ட ஆலோசகரால் (Counsellor) மட்டுமே பார்க்க முடியும். "
            "ஆசிரியர்கள் மற்றும் தலைமை ஆசிரியருக்கு '[ஆலோசகரிடம் ரகசியக் குறிப்பு உள்ளது]' என்று மட்டுமே காட்டப்படும்."
        ),
    },
    {
        "id": "rules_catalog_overview",
        "keywords": ["rules", "warning engine", "how rules work", "catalog", "thresholds", "indicators"],
        "title": "THULIR Early-Warning Rule Catalog (7 Deterministic Rules)",
        "sources": ["THULIR System Architecture Documentation", "docs/RULES.md"],
        "content_en": (
            "THULIR uses 7 deterministic, auditable rules with zero machine-learning black boxes: "
            "1) ATT-LOW: Latest period attendance < 75.0%. "
            "2) ATT-DECLINE: Attendance drop >= 10.0 pp between consecutive periods. "
            "3) ATT-CONSEC: >= 3 consecutive days of unexcused absence. "
            "4) MARK-LOW: Latest exam mark < 35.0%. "
            "5) MARK-DECLINE: 2 consecutive declines in same subject totaling >= 15.0 pp. "
            "6) ASG-LOW: Current period assignment completion < 60.0% (min 3 tasks). "
            "7) ASG-DECLINE: Assignment completion drop >= 20.0 pp from prior period. "
            "Every generated indicator produces plain-language evidence and requires human staff review."
        ),
        "content_ta": (
            "துளிர் 7 வெளிப்படையான, கணக்கீட்டு விதிகளைப் பயன்படுத்துகிறது (செயற்கை நுண்ணறிவு ஊகங்கள் எதுவும் இல்லை): "
            "1) ATT-LOW: நடப்பு பருவ வருகை 75.0% க்கும் குறைவு. "
            "2) ATT-DECLINE: முந்தைய பருவத்தை விட 10.0% சரிவு. "
            "3) ATT-CONSEC: தொடர்ந்து 3 அல்லது அதற்கு மேற்பட்ட நாட்கள் விடுப்பு. "
            "4) MARK-LOW: தேர்வு மதிப்பெண் 35.0% க்கும் குறைவு. "
            "5) MARK-DECLINE: ஒரே பாடத்தில் 15.0% க்கும் அதிகமான தொடர் மதிப்பெண் சரிவு. "
            "6) ASG-LOW: ஒப்படைப்பு விகிதம் 60.0% க்கும் குறைவு. "
            "7) ASG-DECLINE: ஒப்படைப்பு விகிதத்தில் 20.0% சரிவு."
        ),
    },
]

SAFEGUARD_REFUSAL_EN = (
    "THULIR is strictly a non-predictive, explainable decision-support system. "
    "Under our institutional ethics policy, THULIR DOES NOT predict dropout probabilities, diagnose psychological conditions, "
    "or compute emotional scores. Every warning indicator in THULIR is an objective, rule-based notification designed to prompt timely, compassionate human review by teachers and counsellors."
)

SAFEGUARD_REFUSAL_TA = (
    "துளிர் (THULIR) ஒருபோதும் இடைநிற்றல் கணிப்புகளையோ (Dropout prediction), மனநல ஆய்வுகளையோ செய்யாது. "
    "எங்கள் கொள்கையின்படி, மாணவர்கள் இடைநிற்பார்களா என்பதை முன்கூட்டியே ஊகிக்கவோ அல்லது எண்களாக மதிப்பிடவோ அனுமதி இல்லை. "
    "அனைத்து எச்சரிக்கைகளும் ஆசிரியர்கள் மற்றும் ஆலோசகர்கள் மாணவருக்கு சரியான நேரத்தில் உதவி செய்வதற்கான மனித மதிப்பீட்டுக் குறிப்புகளே ஆகும்."
)

# Detection patterns for unauthorized predictive or diagnostic prompts
PREDICTIVE_OR_DIAGNOSTIC_REGEX = re.compile(
    r"(predict|probability|chance of dropping|dropout prediction|will (he|she|they|student) drop|mental illness|diagnos|depression score|emotion detect|psychological rating)",
    re.IGNORECASE
)

def query_assistant(query: str, language: str = "en") -> Dict[str, Any]:
    """Processes user query and returns grounded institutional responses."""
    clean_query = query.strip()
    is_tamil = language.lower() == "ta" or any("\u0b80" <= char <= "\u0bff" for char in clean_query)

    # 1. Guardrail Check: Block predictive or diagnostic queries immediately
    if PREDICTIVE_OR_DIAGNOSTIC_REGEX.search(clean_query):
        return {
            "response": SAFEGUARD_REFUSAL_TA if is_tamil else SAFEGUARD_REFUSAL_EN,
            "grounded_sources": ["THULIR Non-Predictive Ethics Charter", "Section 3 Non-Negotiable Rules"],
            "confidence_type": "safeguard_refusal",
            "is_refusal": True,
            "disclaimer": "THULIR does not generate predictive probabilities or psychological diagnoses.",
        }

    # 2. Match against Grounded Knowledge Base
    query_lower = clean_query.lower()
    best_match = None
    best_score = 0

    for item in POLICY_KNOWLEDGE_BASE:
        score = 0
        for kw in item["keywords"]:
            if kw in query_lower:
                score += len(kw)
        if score > best_score:
            best_score = score
            best_match = item

    if best_match and best_score > 0:
        response_text = best_match["content_ta"] if is_tamil else best_match["content_en"]
        return {
            "response": response_text,
            "title": best_match["title"],
            "grounded_sources": best_match["sources"],
            "confidence_type": "policy_direct",
            "is_refusal": False,
            "disclaimer": "THULIR Assistant provides grounded statutory policy references. All student actions require educator judgment.",
        }

    # 3. Default Grounded Overview
    default_en = (
        "THULIR Assistant helps school staff quickly look up institutional attendance norms, pass criteria, "
        "early-warning rule formulas, and confidential support protocols. You can ask about: "
        "1) 75% attendance threshold & condonation norms. "
        "2) 3-day consecutive unexcused absence SOP. "
        "3) CAT exam 35% pass mark criteria. "
        "4) Early-warning rule indicators (ATT-LOW, MARK-DECLINE, etc.). "
        "5) Confidential case notes security model."
    )
    default_ta = (
        "துளிர் வழிகாட்டி உதவியாளர் தமிழ்நாடு அரசுப் பள்ளி வழிகாட்டுதல்கள், வருகை விதிமுறைகள், தேர்ச்சி அளவுகோல்கள் "
        "மற்றும் துளிர் எச்சரிக்கை விதிகளை அறிய உதவுகிறது. நீங்கள் பின்வருவனவற்றைப் பற்றி கேட்கலாம்: "
        "1) 75% வருகைப் பதிவு விதிகள் மற்றும் விலக்கு நெறிமுறைகள். "
        "2) 3 நாட்கள் தொடர் விடுப்பு நடைமுறைகள். "
        "3) 35% தேர்ச்சி மதிப்பெண் வழிகாட்டுதல்கள். "
        "4) துளிர் எச்சரிக்கை விதிகளின் விவரங்கள் (ATT-LOW, MARK-DECLINE போன்றவை). "
        "5) ரகசிய ஆவண பாதுகாப்பு நெறிமுறைகள்."
    )
    return {
        "response": default_ta if is_tamil else default_en,
        "title": "THULIR Policy & Guidelines Reference",
        "grounded_sources": ["THULIR Documentation", "Tamil Nadu School Education Department Guidelines"],
        "confidence_type": "overview",
        "is_refusal": False,
        "disclaimer": "THULIR Assistant provides grounded statutory policy references. All student actions require educator judgment.",
    }

