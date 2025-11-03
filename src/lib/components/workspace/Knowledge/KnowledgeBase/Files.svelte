<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { isFileProcessing } from '$lib/utils/file-processing';
	const dispatch = createEventDispatcher();

	import FileItem from '$lib/components/common/FileItem.svelte';

	export let selectedFileId = null;
	export let files = [];

	export let small = false;
</script>

<div class=" max-h-full flex flex-col w-full">
	{#each files as file}
		<div class="mt-1 px-2">
			<FileItem
				className="w-full"
				colorClassName="{selectedFileId === file.id
					? ' bg-gray-50 dark:bg-gray-850'
					: 'bg-transparent'} hover:bg-gray-50 dark:hover:bg-gray-850 transition"
				{small}
				item={file}
				name={file?.name ?? file?.meta?.name}
				type="file"
				size={file?.size ?? file?.meta?.size ?? ''}
				loading={isFileProcessing(file)}
				dismissible
				on:click={() => {
					if (isFileProcessing(file)) {
						return;
					}

					dispatch('click', file.id);
				}}
				on:dismiss={() => {
					if (isFileProcessing(file)) {
						return;
					}

					dispatch('delete', file.id);
				}}
			/>
		</div>
	{/each}
</div>
