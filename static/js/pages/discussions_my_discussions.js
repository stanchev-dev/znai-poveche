(function () {
  const utils = window.subjectBadgeUtils;
  if (!utils) return;

  document.querySelectorAll('.subject-badge[data-subject-name]').forEach((badge) => {
    const subject = {
      name: badge.dataset.subjectName,
      slug: badge.dataset.subjectSlug,
    };

    badge.style.cssText = utils.getSubjectBadgeStyle(subject);
  });
})();
