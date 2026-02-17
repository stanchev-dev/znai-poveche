(function () {
  const SUBJECT_BADGE_COLORS = {
    bulgarian: '#FB923C',
    literature: '#BEEA00',
    biology: '#10B981',
    it: '#2563EB',
    history: '#EF4444',
    math: '#0EA5E9',
    physics: '#FF725E',
    chemistry: '#7C3AED',
    other: '#64748B',
  };


  const SUBJECT_KEY_ALIASES = {
    bulgarski: 'bulgarian',
    'bulgarski-ezik': 'bulgarian',
    bg: 'bulgarian',
    literatura: 'literature',
    lit: 'literature',
    biologiya: 'biology',
    biologiq: 'biology',
    info: 'it',
    informatika: 'it',
    'informacionni-tehnologii': 'it',
    it: 'it',
    istoriya: 'history',
    istoriq: 'history',
    history: 'history',
    matematika: 'math',
    math: 'math',
    fizika: 'physics',
    physics: 'physics',
    himiya: 'chemistry',
    himiq: 'chemistry',
    chemistry: 'chemistry',
    drugo: 'other',
    drugi: 'other',
    other: 'other',
  };

  const SUBJECT_NAME_TO_KEY = {
    'Български език': 'bulgarian',
    'Литература': 'literature',
    'Биология': 'biology',
    'Информационни технологии': 'it',
    'История': 'history',
    'Математика': 'math',
    'Физика': 'physics',
    'Химия': 'chemistry',
    'Други': 'other',
  };

  function normalizeSubjectKey(subject) {
    if (!subject) return 'other';

    const slugOrCode = (subject.slug || subject.code || '').toString().trim().toLowerCase();
    if (slugOrCode && SUBJECT_BADGE_COLORS[slugOrCode]) return slugOrCode;

    const aliasedKey = SUBJECT_KEY_ALIASES[slugOrCode];
    if (aliasedKey && SUBJECT_BADGE_COLORS[aliasedKey]) return aliasedKey;

    const mappedByName = SUBJECT_NAME_TO_KEY[(subject.name || '').toString().trim()];
    return mappedByName || 'other';
  }

  function getSubjectBadgePalette(subject) {
    const key = normalizeSubjectKey(subject);
    const bgColor = SUBJECT_BADGE_COLORS[key] || SUBJECT_BADGE_COLORS.other;
    const textColor = bgColor.toUpperCase() === '#BEEA00' ? '#111111' : '#FFFFFF';

    return {
      key,
      bgColor,
      textColor,
    };
  }

  function getSubjectBadgeStyle(subject) {
    const palette = getSubjectBadgePalette(subject);
    return `background-color: ${palette.bgColor}; border-color: ${palette.bgColor}; color: ${palette.textColor};`;
  }

  window.subjectBadgeUtils = {
    getSubjectBadgePalette,
    getSubjectBadgeStyle,
    normalizeSubjectKey,
  };
})();
