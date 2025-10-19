<script lang="ts">
	import { getContext } from 'svelte';
	import CitationModal from './Citations/CitationModal.svelte';
	import { embed, showControls, showEmbeds } from '$lib/stores';

	const i18n = getContext('i18n');

	export let id = '';
	export let sources = [];
	export let readOnly = false;

	let citations = [];
	let showPercentage = false;
	let showRelevance = true;

	let citationModal = null;

	let showCitations = false;
	let showCitationModal = false;

	let selectedCitation: any = null;

	export const showSourceModal = (sourceIdx) => {
		if (citations[sourceIdx]) {
			console.log('Showing citation modal for:', citations[sourceIdx]);

			if (citations[sourceIdx]?.source?.embed_url) {
				const embedUrl = citations[sourceIdx].source.embed_url;
				if (embedUrl) {
					if (readOnly) {
						// Open in new tab if readOnly
						window.open(embedUrl, '_blank');
						return;
					} else {
						showControls.set(true);
						showEmbeds.set(true);
						embed.set({
							title: citations[sourceIdx]?.source?.name || 'Embedded Content',
							url: embedUrl
						});
					}
				} else {
					selectedCitation = citations[sourceIdx];
					showCitationModal = true;
				}
			} else {
				selectedCitation = citations[sourceIdx];
				showCitationModal = true;
			}
		}
	};

	function calculateShowRelevance(sources: any[]) {
		const distances = sources.flatMap((citation) => citation.distances ?? []);
		const inRange = distances.filter((d) => d !== undefined && d >= -1 && d <= 1).length;
		const outOfRange = distances.filter((d) => d !== undefined && (d < -1 || d > 1)).length;

		if (distances.length === 0) {
			return false;
		}

		if (
			(inRange === distances.length - 1 && outOfRange === 1) ||
			(outOfRange === distances.length - 1 && inRange === 1)
		) {
			return false;
		}

		return true;
	}

	function shouldShowPercentage(sources: any[]) {
		const distances = sources.flatMap((citation) => citation.distances ?? []);
		return distances.every((d) => d !== undefined && d >= -1 && d <= 1);
	}

	$: {
		citations = sources.reduce((acc, source) => {
			if (Object.keys(source).length === 0) {
				return acc;
			}

			// NOTE: preserve original Open WebUI citation layout.
			// The custom chunk aggregation logic we experimented with has been
			// disabled for now, but kept below for reference if we want to revisit it.
			//
			// Legacy chunking prototype (kept for future exploration):
			// source?.document?.forEach((document, index) => {
			// 	const metadata = source?.metadata?.[index];
			// 	const distance = source?.distances?.[index];
			// 	const id = metadata?.source ?? source?.source?.id ?? 'N/A';
			// 	let _source = source?.source;
			// 	if (metadata?.name) {
			// 		_source = { ..._source, name: metadata.name };
			// 	}
			// 	if (id.startsWith('http://') || id.startsWith('https://')) {
			// 		_source = { ..._source, name: id, url: id };
			// 	}
			// 	const existingSource = acc.find((item) => item.id === id);
			// 	if (existingSource) {
			// 		existingSource.document.push(document);
			// 		existingSource.metadata.push(metadata);
			// 		if (distance !== undefined) {
			// 			existingSource.distances.push(distance);
			// 		}
			// 	} else {
			// 		acc.push({
			// 			id,
			// 			source: _source,
			// 			document: [document],
			// 			metadata: metadata ? [metadata] : [],
			// 			distances: distance !== undefined ? [distance] : undefined
			// 		});
			// 	}
			// });

			acc.push(source);
			return acc;
		}, []);

		showRelevance = calculateShowRelevance(citations);
		showPercentage = shouldShowPercentage(citations);
	}

	const decodeString = (str: string) => {
		try {
			return decodeURIComponent(str);
		} catch (e) {
			return str;
		}
	};
</script>

<CitationModal
	bind:show={showCitationModal}
	citation={selectedCitation}
	{showPercentage}
	{showRelevance}
/>

{#if citations.length > 0}
	{@const urlCitations = citations.filter((c) => c?.source?.name?.startsWith('http'))}
	<div class=" py-1 -mx-0.5 w-full flex gap-1 items-center flex-wrap">
		<button
			class="text-xs font-medium text-gray-600 dark:text-gray-300 px-3.5 h-8 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 transition flex items-center gap-1 border border-gray-50 dark:border-gray-850"
			on:click={() => {
				showCitations = !showCitations;
			}}
		>
			{#if urlCitations.length > 0}
				<div class="flex -space-x-1 items-center">
					{#each urlCitations.slice(0, 3) as citation, idx}
						<img
							src="https://www.google.com/s2/favicons?sz=32&domain={citation.source.name}"
							alt="favicon"
							class="size-4 rounded-full shrink-0 border border-white dark:border-gray-850 bg-white dark:bg-gray-900"
						/>
					{/each}
				</div>
			{/if}
			<div>
				{#if citations.length === 1}
					{$i18n.t('1 Source')}
				{:else}
					{$i18n.t('{{COUNT}} Sources', {
						COUNT: citations.length
					})}
				{/if}
			</div>
		</button>
	</div>
{/if}

{#if showCitations}
	<div class="py-1.5">
		<div class="flex flex-col gap-2 text-xs">
			{#each citations as citation, idx}
				<div class="space-y-2 rounded-xl border border-gray-100 dark:border-gray-850 bg-gray-50/60 dark:bg-white/5 p-2.5">
					<button
						id={`source-${id}-${idx + 1}`}
						class="no-toggle outline-hidden flex w-full items-center gap-2 text-gray-700 dark:text-gray-200 hover:text-black dark:hover:text-white transition"
						on:click={() => {
							showCitationModal = true;
							selectedCitation = citation;
						}}
					>
						<div class="font-semibold bg-white dark:bg-gray-900/60 border border-gray-200 dark:border-gray-850 rounded-md px-1.5 py-0.5">
							{idx + 1}
						</div>
						<div class="flex-1 truncate text-left">
							{decodeString(citation.source.name)}
						</div>
						<svg
							aria-hidden="true"
							class="size-3 shrink-0 text-gray-500 dark:text-gray-400"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							viewBox="0 0 24 24"
							xmlns="http://www.w3.org/2000/svg"
						>
							<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
						</svg>
					</button>

					<div class="space-y-2">
						{#each citation.document as documentText, docIdx}
							{@const metadata = citation.metadata?.[docIdx]}
							{@const distance = citation.distances?.[docIdx]}
							{@const sourceId = decodeString(metadata?.source ?? citation.id ?? 'N/A')}
							<div class="rounded-lg border border-gray-200 dark:border-gray-850 bg-white/80 dark:bg-gray-900/40 p-2 space-y-1">
								<div class="flex flex-wrap gap-x-2 gap-y-1 text-[11px] text-gray-500 dark:text-gray-400">
									<span># {sourceId}</span>
									{#if metadata?.page !== undefined}
										<span>{$i18n.t('page')} {metadata.page + 1}</span>
									{/if}
									{#if metadata?.file_name}
										<span>{metadata.file_name}</span>
									{:else if metadata?.nomor_putusan}
										<span>{metadata.nomor_putusan}</span>
									{:else if metadata?.name}
										<span>{metadata.name}</span>
									{/if}
									{#if typeof distance === 'number'}
										<span>{$i18n.t('Relevance')}: {distance.toFixed(4)}</span>
									{/if}
								</div>
								{#if metadata?.html}
									<iframe
										class="w-full border-0 rounded-md bg-white dark:bg-gray-900"
										sandbox="allow-scripts allow-forms allow-same-origin"
										srcdoc={documentText ?? ''}
										title={decodeString(citation.source.name)}
									></iframe>
								{:else}
									<pre class="text-xs text-gray-700 dark:text-gray-200 whitespace-pre-wrap max-h-56 overflow-y-auto">{documentText ?? ''}</pre>
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	</div>
{/if}
