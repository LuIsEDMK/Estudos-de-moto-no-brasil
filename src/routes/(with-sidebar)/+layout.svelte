<script lang="ts">
	import Sidebar from '$lib/components/sidebar/Sidebar.svelte';
	let { children } = $props();
</script>

<div class="with-sidebar">
	<aside class="sidebar">
		<Sidebar />
	</aside>

	<main class="content">
		{@render children()}
	</main>
</div>

<style>
	.with-sidebar {
		display: flex;
		flex: 1;
		overflow: hidden;
	}

	.sidebar {
		width: 16rem;
		flex-shrink: 0;
		background: var(--base-100);
		border-right: 0.5px solid var(--base-300);
		overflow-y: auto;
	}

	.content {
		flex: 1;
		min-width: 0;
		padding: 1rem;
		background: var(--base-100);
		overflow-y: auto;
	}

	@media (max-width: 768px) {
		.with-sidebar {
			flex-direction: column;
			overflow: auto;
		}

		.sidebar {
			width: 100%;
			border-right: none;
			border-bottom: 0.5px solid var(--base-300);
			max-height: 50vh;
		}
	}
</style>
