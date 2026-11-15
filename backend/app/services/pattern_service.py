"""Multi-Indicator Pattern Analysis Service (Feature 6).

Civic Trust Rule:
THULIR never computes a single composite "risk score" or synthetic index.
Every pattern is a named, explainable correlation of concrete co-occurring
indicators designed to prompt human review and guide multi-disciplinary support.
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.app.models.models import WarningIndicator, Student, ClassSection

# Named co-occurring patterns with contextual explanations
PATTERN_DEFINITIONS = {
    "academic_attendance_compounding": {
        "pattern_name": "Academic & Attendance Compounding",
        "description": "Concurrent attendance decline and assessment failure within the same reporting period.",
        "plain_explanation": (
            "Attendance drop compounded by falling marks suggests external barriers or disengagement "
            "requiring coordinated holistic support rather than academic tutoring alone."
        ),
        "recommended_intervention_domain": "attendance_followup_and_remedial",
        "attendance_codes": {"ATT_LOW", "ATT_DECLINE", "ATT_CONSEC"},
        "academic_codes": {"MARK_LOW", "MARK_DECLINE"},
    },
    "chronic_engagement_risk": {
        "pattern_name": "Chronic Engagement Disconnection",
        "description": "Consecutive absences paired with incomplete assignments.",
        "plain_explanation": (
            "Consecutive absences paired with incomplete assignments indicates growing disconnection from coursework "
            "and routine school participation."
        ),
        "recommended_intervention_domain": "counsellor_referral_and_home_visit",
        "attendance_codes": {"ATT_CONSEC"},
        "assignment_codes": {"ASG_LOW", "ASG_DECLINE"},
    },
    "multi_subject_academic_struggle": {
        "pattern_name": "Multi-Subject Academic Struggle",
        "description": "Assessment scores falling below threshold across two or more subjects concurrently.",
        "plain_explanation": (
            "Widespread academic difficulty across multiple distinct subjects indicates foundational learning gaps "
            "or language barriers rather than single-subject difficulty."
        ),
        "recommended_intervention_domain": "foundational_literacy_numeracy_remedial",
    },
}


def analyze_indicator_patterns(
    db: Session,
    school_id: int,
    reporting_period: Optional[str] = None,
    grade: Optional[int] = None,
    section: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Identifies co-occurring indicator patterns across students in a school/period.
    Does NOT calculate any composite score. Every output is an explainable grouping.
    """
    query = (
        db.query(WarningIndicator, Student)
        .join(Student, WarningIndicator.student_id == Student.id)
        .outerjoin(ClassSection, Student.current_class_section_id == ClassSection.id)
        .filter(
            Student.school_id == school_id,
            WarningIndicator.is_superseded == False,
        )
    )

    if grade:
        query = query.filter(ClassSection.grade == grade)
    if section:
        query = query.filter(ClassSection.section == section)

    records = query.all()
    student_indicators = defaultdict(lambda: defaultdict(list))
    student_objects = {}

    for ind, stu in records:
        student_objects[stu.id] = stu
        ev = ind.supporting_evidence if isinstance(ind.supporting_evidence, dict) else {}
        period_key = ev.get("period") or ev.get("current_period") or "General"
        if reporting_period and period_key != reporting_period:
            continue
        student_indicators[stu.id][period_key].append(ind)

    # Detect patterns
    pattern_matches = {
        "academic_attendance_compounding": [],
        "chronic_engagement_risk": [],
        "multi_subject_academic_struggle": [],
    }

    for student_id, periods in student_indicators.items():
        stu = student_objects[student_id]
        stu_dict = {
            "id": stu.id,
            "full_name": stu.full_name,
            "emis_id": stu.emis_id,
            "grade": stu.class_section.grade if stu.class_section else None,
            "section": stu.class_section.section if stu.class_section else None,
        }

        for period_name, inds in periods.items():
            rule_codes = {ind.rule_code for ind in inds}

            # Check 1: Academic & Attendance Compounding
            has_att = bool(rule_codes & PATTERN_DEFINITIONS["academic_attendance_compounding"]["attendance_codes"])
            has_acad = bool(rule_codes & PATTERN_DEFINITIONS["academic_attendance_compounding"]["academic_codes"])
            if has_att and has_acad:
                matched_inds = [
                    {"id": i.id, "rule_code": i.rule_code, "priority": i.priority, "explanation": i.plain_explanation}
                    for i in inds if i.rule_code in (
                        PATTERN_DEFINITIONS["academic_attendance_compounding"]["attendance_codes"]
                        | PATTERN_DEFINITIONS["academic_attendance_compounding"]["academic_codes"]
                    )
                ]
                pattern_matches["academic_attendance_compounding"].append({
                    "student": stu_dict,
                    "reporting_period": period_name,
                    "indicators": matched_inds,
                })

            # Check 2: Chronic Engagement Risk
            has_consec = bool(rule_codes & PATTERN_DEFINITIONS["chronic_engagement_risk"]["attendance_codes"])
            has_asg = bool(rule_codes & PATTERN_DEFINITIONS["chronic_engagement_risk"]["assignment_codes"])
            if has_consec and has_asg:
                matched_inds = [
                    {"id": i.id, "rule_code": i.rule_code, "priority": i.priority, "explanation": i.plain_explanation}
                    for i in inds if i.rule_code in (
                        PATTERN_DEFINITIONS["chronic_engagement_risk"]["attendance_codes"]
                        | PATTERN_DEFINITIONS["chronic_engagement_risk"]["assignment_codes"]
                    )
                ]
                pattern_matches["chronic_engagement_risk"].append({
                    "student": stu_dict,
                    "reporting_period": period_name,
                    "indicators": matched_inds,
                })

            # Check 3: Multi-Subject Academic Struggle
            acad_inds = [i for i in inds if i.category == "academic" or i.rule_code in {"MARK_LOW", "MARK_DECLINE"}]
            if len(acad_inds) >= 2:
                pattern_matches["multi_subject_academic_struggle"].append({
                    "student": stu_dict,
                    "reporting_period": period_name,
                    "indicators": [
                        {"id": i.id, "rule_code": i.rule_code, "priority": i.priority, "explanation": i.plain_explanation}
                        for i in acad_inds
                    ],
                })

    # Assemble summary
    patterns_summary = []
    for p_key, defn in PATTERN_DEFINITIONS.items():
        matches = pattern_matches[p_key]
        patterns_summary.append({
            "pattern_key": p_key,
            "pattern_name": defn["pattern_name"],
            "description": defn["description"],
            "plain_explanation": defn["plain_explanation"],
            "recommended_intervention_domain": defn["recommended_intervention_domain"],
            "affected_students_count": len(matches),
            "matches": matches,
        })

    return {
        "reporting_period": reporting_period or "All Reporting Periods",
        "total_active_patterns": sum(len(m) for m in pattern_matches.values()),
        "patterns": patterns_summary,
        "disclaimer": (
            "Patterns represent co-occurring concrete indicators across domains. "
            "THULIR does not compute composite risk scores or automated rankings."
        ),
    }
