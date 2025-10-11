<script>
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');
	import WebSearchResults from '../WebSearchResults.svelte';
	import Search from '$lib/components/icons/Search.svelte';
	import { t } from 'i18next';

	export let status = null;
	export let done = false;
</script>

{#if !status?.hidden}
	<div class="status-description flex items-center gap-2 py-0.5 w-full text-left">
		{#if status?.action === 'web_search' && (status?.urls || status?.items)}
			<WebSearchResults {status}>
				<div class="flex flex-col justify-center -space-y-0.5">
					<div
						class="{(done || status?.done) === false
							? 'shimmer'
							: ''} text-base line-clamp-1 text-wrap"
					>
						<!-- $i18n.t("Generating search query") -->
						<!-- $i18n.t("No search query generated") -->
						<!-- $i18n.t('Searched {{count}} sites') -->
						{#if status?.description?.includes('{{count}}')}
							{$i18n.t(status?.description, {
								count: (status?.urls || status?.items).length
							})}
						{:else if status?.description === 'No search query generated'}
							{$i18n.t('No search query generated')}
						{:else if status?.description === 'Generating search query'}
							{$i18n.t('Generating search query')}
						{:else}
							{status?.description}
						{/if}
					</div>
				</div>
			</WebSearchResults>
		{:else if status?.action === 'knowledge_search'}
			<div class="flex flex-col justify-center -space-y-0.5">
				<div
					class="{(done || status?.done) === false
						? 'shimmer'
						: ''} text-gray-500 dark:text-gray-500 text-base line-clamp-1 text-wrap"
				>
					{$i18n.t(`Searching Knowledge for "{{searchQuery}}"`, {
						searchQuery: status.query
					})}
				</div>
			</div>
		{:else if status?.action === 'web_search_queries_generated' && status?.queries}
			<div class="flex flex-col justify-center -space-y-0.5">
				<div
					class="{(done || status?.done) === false
						? 'shimmer'
						: ''} text-gray-500 dark:text-gray-500 text-base line-clamp-1 text-wrap"
				>
					{$i18n.t(`Searching`)}
				</div>

				<div class=" flex gap-1 flex-wrap mt-2">
					{#each status.queries as query, idx (query)}
						<div
							class="bg-gray-50 dark:bg-gray-850 flex rounded-lg py-1 px-2 items-center gap-1 text-xs"
						>
							<div>
								<Search className="size-3" />
							</div>

							<span class="line-clamp-1">
								{query}
							</span>
						</div>
					{/each}
				</div>
			</div>
		{:else if status?.action === 'queries_generated' && status?.queries}
			<div class="flex flex-col justify-center -space-y-0.5">
				<div
					class="{(done || status?.done) === false
						? 'shimmer'
						: ''} text-gray-500 dark:text-gray-500 text-base line-clamp-1 text-wrap"
				>
					{$i18n.t(`Querying`)}
				</div>

				<div class=" flex gap-1 flex-wrap mt-2">
					{#each status.queries as query, idx (query)}
						<div
							class="bg-gray-50 dark:bg-gray-850 flex rounded-lg py-1 px-2 items-center gap-1 text-xs"
						>
							<div>
								<Search className="size-3" />
							</div>

							<span class="line-clamp-1">
								{query}
							</span>
						</div>
					{/each}
				</div>
			</div>
		{:else if status?.action === 'sources_retrieved' && status?.count !== undefined}
			<div class="flex flex-col justify-center -space-y-0.5">
				<div
					class="{(done || status?.done) === false
						? 'shimmer'
						: ''} text-gray-500 dark:text-gray-500 text-base line-clamp-1 text-wrap"
				>
					{#if status.count === 0}
						{$i18n.t('No sources found')}
					{:else if status.count === 1}
						{$i18n.t('Retrieved 1 source')}
					{:else}
						<!-- {$i18n.t('Source')} -->
						<!-- {$i18n.t('No source available')} -->
						<!-- {$i18n.t('No distance available')} -->
						<!-- {$i18n.t('Retrieved {{count}} sources')} -->
						{$i18n.t('Retrieved {{count}} sources', {
							count: status.count
						})}
					{/if}
				</div>

				{#if status?.collections?.length}
					<div class="text-xs text-gray-500 dark:text-gray-500 mt-1">
						{$i18n.t('Collections')}: {status.collections.join(', ')}
					</div>
				{/if}

				{#if status?.documents?.length}
					<div class="text-xs text-gray-500 dark:text-gray-500 mt-0.5">
						{$i18n.t('Documents')}: {status.documents.join(', ')}
					</div>
				{/if}

				{#if status?.collections_detail?.length}
					<div class="mt-1 space-y-1">
						{#each status.collections_detail as item (item.collection)}
							<div class="rounded-md bg-gray-50 dark:bg-gray-850 p-2 text-xs text-gray-600 dark:text-gray-400">
								<div class="font-semibold text-gray-700 dark:text-gray-200">
									{item.collection}
								</div>
								{#if item.documents?.length}
									<div class="mt-0.5">
										{$i18n.t('Documents')}: {item.documents.join(', ')}
									</div>
								{/if}
								{#if Object.keys(item.metadata ?? {}).length}
									<div class="mt-0.5 space-y-0.5">
										{#each Object.entries(item.metadata ?? {}) as [key, value] (key)}
											<div>
												<span class="uppercase tracking-wide text-[10px] text-gray-400 dark:text-gray-500 mr-1">
													{key}
												</span>
												<span class="text-gray-600 dark:text-gray-300">{String(value)}</span>
											</div>
										{/each}
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{:else}
			<div class="flex flex-col justify-center -space-y-0.5">
				<div
					class="{(done || status?.done) === false
						? 'shimmer'
						: ''} text-gray-500 dark:text-gray-500 text-base line-clamp-1 text-wrap"
				>
					<!-- $i18n.t(`Searching "{{searchQuery}}"`) -->
					{#if status?.description?.includes('{{searchQuery}}')}
						{$i18n.t(status?.description, {
							searchQuery: status?.query
						})}
					{:else if status?.description === 'No search query generated'}
						{$i18n.t('No search query generated')}
					{:else if status?.description === 'Generating search query'}
						{$i18n.t('Generating search query')}
					{:else if status?.description === 'Searching the web'}
						{$i18n.t('Searching the web')}
					{:else}
						{status?.description}
					{/if}
				</div>
			</div>
		{/if}
	</div>
{/if}
