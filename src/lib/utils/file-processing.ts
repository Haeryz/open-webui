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

type ProcessingDetails = {
	started_at?: number | null;
	updated_at?: number | null;
	metrics?: {
		processing_time_seconds?: number | null;
	} | null;
	steps?: Record<string, unknown>;
	[key: string]: unknown;
};

export type ProcessingEta = {
	elapsedSeconds: number | null;
	remainingSeconds: number | null;
	estimatedTotalSeconds: number | null;
};

const clampSeconds = (value: number): number => {
	if (!Number.isFinite(value)) {
		return 0;
	}
	return Math.max(0, Math.round(value));
};

const toSeconds = (timestamp?: number | null): number | null => {
	if (typeof timestamp !== 'number' || Number.isNaN(timestamp)) {
		return null;
	}
	return Math.floor(timestamp);
};

const getProgressFraction = (progress?: number | null): number | null => {
	if (typeof progress !== 'number' || Number.isNaN(progress)) {
		return null;
	}
	const normalized = progress / 100;
	if (normalized <= 0 || normalized > 1) {
		return null;
	}
	return normalized;
};

export const estimateProcessingTimes = (
	details?: ProcessingDetails | null,
	progress?: number | null,
	status?: string | null
): ProcessingEta => {
	const normalizedStatus = normalizeStatus(status);
	const startedAt = toSeconds(details?.started_at);
	const updatedAt = toSeconds(details?.updated_at);
	const nowSeconds = Math.floor(Date.now() / 1000);

	let elapsedSeconds: number | null = null;
	let estimatedTotalSeconds: number | null = null;
	let remainingSeconds: number | null = null;

	if (startedAt !== null) {
		const isCompleted = COMPLETED_STATUSES.has(normalizedStatus);
		const referenceTimestamp = isCompleted
			? updatedAt ?? startedAt
			: Math.max(updatedAt ?? startedAt, startedAt, nowSeconds);
		elapsedSeconds = clampSeconds(referenceTimestamp - startedAt);

		if (isCompleted) {
			const metricsDuration = details?.metrics?.processing_time_seconds;
			if (typeof metricsDuration === 'number' && metricsDuration > 0) {
				estimatedTotalSeconds = clampSeconds(metricsDuration);
			} else {
				estimatedTotalSeconds = elapsedSeconds;
			}
			remainingSeconds = 0;
		} else {
			const fraction = getProgressFraction(progress);
			if (fraction !== null && fraction > 0) {
				const projectedTotal = elapsedSeconds / fraction;
				estimatedTotalSeconds = clampSeconds(projectedTotal);
				remainingSeconds = clampSeconds(projectedTotal - elapsedSeconds);
			}
		}
	}

	return {
		elapsedSeconds,
		remainingSeconds,
		estimatedTotalSeconds
	};
};

type DurationUnit = {
	label: string;
	seconds: number;
};

const DURATION_UNITS: DurationUnit[] = [
	{ label: 'd', seconds: 86_400 },
	{ label: 'h', seconds: 3_600 },
	{ label: 'm', seconds: 60 },
	{ label: 's', seconds: 1 }
];

export const formatDurationShort = (seconds?: number | null): string => {
	if (typeof seconds !== 'number' || Number.isNaN(seconds)) {
		return '';
	}
	const totalSeconds = clampSeconds(seconds);
	if (totalSeconds <= 0) {
		return '0s';
	}

	let remaining = totalSeconds;
	const parts: string[] = [];

	for (const unit of DURATION_UNITS) {
		if (remaining < unit.seconds) {
			continue;
		}
		const value = Math.floor(remaining / unit.seconds);
		remaining -= value * unit.seconds;
		parts.push(`${value}${unit.label}`);
		if (parts.length === 2) {
			break;
		}
	}

	if (parts.length === 0) {
		return '1s';
	}

	return parts.join(' ');
};
