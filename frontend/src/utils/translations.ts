/**
 * Translation utilities for German localization
 * Maps English values (stored in database) to German display text
 */

/**
 * Document category translations
 */
const CATEGORY_TRANSLATIONS: Record<string, string> = {
  manuals: 'Handbücher',
  specifications: 'Spezifikationen',
  guides: 'Anleitungen',
  procedures: 'Verfahren',
  safety: 'Sicherheit',
  reports: 'Berichte',
  other: 'Sonstiges',
  // Legacy support for capitalized versions
  Manuals: 'Handbücher',
  Specifications: 'Spezifikationen',
  Guides: 'Anleitungen',
  Procedures: 'Verfahren',
  Safety: 'Sicherheit',
  Reports: 'Berichte',
  Other: 'Sonstiges',
};

/**
 * User status translations
 */
const STATUS_TRANSLATIONS: Record<string, string> = {
  active: 'Aktiv',
  inactive: 'Inaktiv',
  suspended: 'Gesperrt',
  pending: 'Ausstehend',
  rejected: 'Abgelehnt',
};

/**
 * Document processing status translations
 */
const PROCESSING_STATUS_TRANSLATIONS: Record<string, string> = {
  uploading: 'Wird hochgeladen',
  processing: 'Wird verarbeitet',
  completed: 'Abgeschlossen',
  failed: 'Fehlgeschlagen',
};

/**
 * Authorization level translations
 */
const AUTH_LEVEL_TRANSLATIONS: Record<string, string> = {
  regular: 'Normaler Benutzer',
  superuser: 'Superuser',
  admin: 'Admin',
};

/**
 * Translate document category from English to German
 */
export function translateCategory(category: string | undefined | null): string {
  if (!category) return '';
  return CATEGORY_TRANSLATIONS[category] || category;
}

/**
 * Translate user status from English to German
 */
export function translateStatus(status: string | undefined | null): string {
  if (!status) return '';
  return STATUS_TRANSLATIONS[status] || status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Translate document processing status from English to German
 */
export function translateProcessingStatus(status: string | undefined | null): string {
  if (!status) return '';
  return PROCESSING_STATUS_TRANSLATIONS[status] || status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Translate authorization level from English to German
 */
export function translateAuthLevel(level: string | undefined | null): string {
  if (!level) return '';
  return AUTH_LEVEL_TRANSLATIONS[level] || level.charAt(0).toUpperCase() + level.slice(1);
}

/**
 * Get all category translations as array of {value, label} for dropdowns
 */
export function getCategoryOptions(): Array<{ value: string; label: string }> {
  return [
    { value: 'manuals', label: 'Handbücher' },
    { value: 'specifications', label: 'Spezifikationen' },
    { value: 'guides', label: 'Anleitungen' },
    { value: 'procedures', label: 'Verfahren' },
    { value: 'safety', label: 'Sicherheit' },
    { value: 'reports', label: 'Berichte' },
    { value: 'other', label: 'Sonstiges' },
  ];
}

/**
 * Get all status translations as array of {value, label} for dropdowns
 */
export function getStatusOptions(): Array<{ value: string; label: string }> {
  return [
    { value: 'active', label: 'Aktiv' },
    { value: 'suspended', label: 'Gesperrt' },
    { value: 'pending', label: 'Ausstehend' },
    { value: 'rejected', label: 'Abgelehnt' },
  ];
}
