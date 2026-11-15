import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileText,
  ShieldAlert,
  ArrowRight,
  Filter,
  User,
  Calendar,
  Lock,
  Edit3,
} from 'lucide-react';
import Badge from './Badge';

/**
 * Shared Event-Timeline Component (Locked Decision Section 3).
 * Used across:
 * - Feature 1: Evidence-to-Intervention Pipeline
 * - Feature 4: Intervention Effectiveness Tracker
 * - Feature 5: Student Support History
 */
export default function EventTimeline({ events = [], loading = false, emptyMessage = null }) {
  const { t } = useTranslation();
  const [filterType, setFilterType] = useState('all');

  const filteredEvents = events.filter((e) => {
    if (filterType === 'all') return true;
    if (filterType === 'indicators') return e.category === 'indicator' || e.category === 'review';
    if (filterType === 'cases') return e.category === 'case' || e.category === 'intervention' || e.category === 'follow_up';
    if (filterType === 'notes') return e.category === 'note';
    if (filterType === 'corrections') return e.category === 'correction';
    return true;
  });

  const getEventIcon = (event) => {
    switch (event.event_type) {
      case 'indicator_detected':
        return <AlertTriangle className="w-4 h-4 text-amber-600" />;
      case 'indicator_reviewed':
        return <CheckCircle2 className="w-4 h-4 text-teal-600" />;
      case 'case_created':
        return <FileText className="w-4 h-4 text-blue-600" />;
      case 'intervention_started':
        return <ShieldAlert className="w-4 h-4 text-indigo-600" />;
      case 'follow_up_completed':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
      case 'follow_up_scheduled':
        return <Clock className="w-4 h-4 text-amber-500" />;
      case 'case_note':
        return event.is_confidential ? (
          <Lock className="w-4 h-4 text-rose-600" />
        ) : (
          <FileText className="w-4 h-4 text-slate-600" />
        );
      case 'correction_approved':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
      case 'correction_proposed':
        return <Edit3 className="w-4 h-4 text-purple-600" />;
      default:
        return <Clock className="w-4 h-4 text-slate-500" />;
    }
  };

  const getEventColorBorder = (event) => {
    if (event.is_confidential) return 'border-rose-400 bg-rose-50';
    switch (event.category) {
      case 'indicator':
        return 'border-amber-400 bg-amber-50';
      case 'review':
        return 'border-teal-400 bg-teal-50';
      case 'case':
        return 'border-blue-400 bg-blue-50';
      case 'intervention':
        return 'border-indigo-400 bg-indigo-50';
      case 'follow_up':
        return 'border-emerald-400 bg-emerald-50';
      case 'correction':
        return 'border-purple-400 bg-purple-50';
      default:
        return 'border-slate-300 bg-slate-50';
    }
  };

  if (loading) {
    return (
      <div className="py-8 text-center text-sm text-slate-500 animate-pulse">
        {t('loadingTimeline', 'Loading chronological support history...')}
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="p-8 text-center bg-white rounded-lg border border-slate-200">
        <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
        <p className="text-sm font-medium text-slate-700">
          {emptyMessage || t('noTimelineEvents', 'No chronological timeline events recorded yet.')}
        </p>
        <p className="text-xs text-slate-400 mt-1">
          {t('timelineNotice', 'All indicators, reviews, interventions, follow-ups and verified corrections appear here.')}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
        <Filter className="w-4 h-4 text-slate-400" />
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mr-1">
          {t('filterTimeline', 'Filter Events')}:
        </span>
        {[
          { key: 'all', label: t('all', 'All') + ` (${events.length})` },
          { key: 'indicators', label: t('indicatorsAndReviews', 'Indicators & Reviews') },
          { key: 'cases', label: t('casesAndInterventions', 'Cases & Interventions') },
          { key: 'notes', label: t('notes', 'Observations & Notes') },
          { key: 'corrections', label: t('corrections', 'Data Corrections') },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilterType(tab.key)}
            className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors ${
              filterType === tab.key
                ? 'bg-slate-800 text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Vertical Timeline Track */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
        {filteredEvents.map((event) => (
          <div key={event.id} className="relative group">
            {/* Event Disc */}
            <div
              className={`absolute -left-6 top-1.5 w-5 h-5 rounded-full border-2 flex items-center justify-center bg-white z-10 ${
                event.is_confidential ? 'border-rose-500' : 'border-teal-600'
              }`}
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  event.is_confidential ? 'bg-rose-500' : 'bg-teal-600'
                }`}
              />
            </div>

            {/* Event Card */}
            <div
              className={`p-4 rounded-lg border text-sm transition-all shadow-sm hover:shadow ${getEventColorBorder(
                event
              )}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="p-1 rounded bg-white shadow-xs">{getEventIcon(event)}</span>
                  <h4 className="font-semibold text-slate-900">{event.title}</h4>
                  {event.is_confidential && (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded bg-rose-100 text-rose-800 border border-rose-200">
                      <Lock className="w-3 h-3" />
                      {t('confidential', 'Confidential Counselling')}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>{new Date(event.timestamp).toLocaleString()}</span>
                </div>
              </div>

              {/* Event Description */}
              <p className="text-xs text-slate-700 leading-relaxed mt-1">
                {event.description}
              </p>

              {/* Actor & Metadata Footer */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-2.5 mt-2.5 border-t border-slate-200/60 text-xs text-slate-500">
                <div className="flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-slate-400" />
                  <span className="font-medium text-slate-700">{event.actor}</span>
                  {event.actor_role && (
                    <span className="text-slate-400">({event.actor_role})</span>
                  )}
                </div>

                {event.status && (
                  <Badge variant={event.status === 'Needs Review' ? 'warning' : 'info'}>
                    {event.status}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

