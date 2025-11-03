const COMPLETED_STATUSES = new Set([
	'completed',
	'failed',
	'ready',
	'available',
	'success',
	'skipped'
]);

const normalizeStatus = (status?: string | null): string => {
	if (!status) {
		return '';
	}
	return status.toString().trim().toLowerCase();
};

export const isProcessingStatus = (
	status?: string | null,
	progress?: number | null
): boolean => {
	const normalized = normalizeStatus(status);

	if (normalized === 'failed') {
		return false;
	}

	if (typeof progress === 'number' && !Number.isNaN(progress)) {
		if (progress >= 100) {
			return false;
		}
		if (progress < 0) {
			return true;
		}
	}

	if (!normalized) {
		// No status or progress information means we assume processing is done
		// (e.g., legacy items with no processing metadata).
		return false;
	}

	return !COMPLETED_STATUSES.has(normalized);
};

export const isFileProcessing = (
	file?: { status?: string | null; progress?: number | null }
): boolean => {
	if (!file) {
		return false;
	}
	return isProcessingStatus(file.status, file.progress ?? null);
};

export const normalizeProgress = (
	progress?: number | null
): number | null => {
	if (typeof progress !== 'number' || Number.isNaN(progress)) {
		return null;
	}
	const bounded = Math.min(100, Math.max(0, progress));
	return Math.round(bounded);
};

export const formatProcessingStage = (
	stage?: string | null,
	fallback?: string | null
): string => {
	const source = stage || fallback;
	if (!source) {
		return '';
	}

	return source
		.split(/[_\s]+/)
		.filter(Boolean)
		.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
		.join(' ');
};

export type ProcessingStep = {
	label?: string;
	status?: string;
	progress?: number;
};

export const resolveProcessingSteps = (
	details?: {
		steps?: Record<string, ProcessingStep>;
	}
): Array<[string, ProcessingStep]> => {
	if (!details?.steps) {
		return [];
	}
	return Object.entries(details.steps);
};
