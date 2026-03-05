<script lang="ts">
	import Header from '$lib/components/layout/Header.svelte';
	import { auth } from '$lib/stores/auth.svelte';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		auth.init();
	});
</script>

<svelte:head>
	<title>MotoExpert AI | Consultoria</title>
	<meta
		name="description"
		content="MotoExpert AI — Análise de desvalorização FIPE para motos no Brasil."
	/>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="" />
	<link
		href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"
		rel="stylesheet"
	/>
	<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
</svelte:head>

<div class="app">
	<Header />
	{@render children()}
</div>

<style>
	/* ============================================
	   THEME SYSTEM - OKLCH
	   ============================================ */
	:global(:root) {
		/* Dark mode */
		--base-100: oklch(13% 0.028 261.692);
		--base-200: oklch(21% 0.034 264.665);
		--base-300: oklch(27% 0.033 256.848);
		--base-content: oklch(96% 0.003 264.542);

		--primary: oklch(65% 0.15 264);
		--primary-content: oklch(100% 0 0);

		--secondary: oklch(70% 0.12 293);
		--secondary-content: oklch(100% 0 0);

		--accent: oklch(75% 0.14 164);
		--accent-content: oklch(20% 0.05 164);

		--neutral: oklch(50% 0.02 264);
		--neutral-content: oklch(98% 0.003 264);

		--info: oklch(65% 0.15 241);
		--info-content: oklch(100% 0 0);

		--success: oklch(70% 0.18 145);
		--success-content: oklch(100% 0 0);

		--warning: oklch(75% 0.15 80);
		--warning-content: oklch(20% 0.05 80);

		--error: oklch(65% 0.22 25);
		--error-content: oklch(100% 0 0);

		--header-height: 3.5rem;
	}

	/* Light mode */
	:global(.light) {
		--base-100: oklch(97% 0.003 264.542);
		--base-200: oklch(93% 0.01 264.665);
		--base-300: oklch(85% 0.015 256.848);
		--base-content: oklch(25% 0.03 264.542);

		--primary: oklch(55% 0.15 264);
		--primary-content: oklch(100% 0 0);

		--secondary: oklch(60% 0.12 293);
		--secondary-content: oklch(100% 0 0);

		--accent: oklch(55% 0.14 164);
		--accent-content: oklch(100% 0 0);

		--neutral: oklch(60% 0.02 264);
		--neutral-content: oklch(25% 0.03 264);

		--info: oklch(55% 0.15 241);
		--info-content: oklch(100% 0 0);

		--success: oklch(55% 0.18 145);
		--success-content: oklch(100% 0 0);

		--warning: oklch(60% 0.15 80);
		--warning-content: oklch(100% 0 0);

		--error: oklch(55% 0.22 25);
		--error-content: oklch(100% 0 0);
	}

	/* ============================================
	   GLOBAL RESET
	   ============================================ */
	:global(*) {
		box-sizing: border-box;
		margin: 0;
		padding: 0;
	}

	:global(html) {
		font-family: 'Inter', system-ui, sans-serif;
		background: var(--base-100);
		color: var(--base-content);
	}

	:global(body) {
		min-height: 100vh;
		overflow-x: hidden;
	}

	:global(.btn) {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.5rem 1rem;
		background: var(--base-200);
		border: 0.5px solid var(--base-300);
		color: var(--base-content);
		font-size: 0.875rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	:global(.btn:hover) {
		background: var(--base-300);
	}

	:global(.btn.active) {
		background: var(--accent);
		border-color: var(--accent);
		color: var(--accent-content);
	}

	:global(.btn-primary) {
		background: var(--primary);
		border-color: var(--primary);
		color: var(--primary-content);
	}

	:global(.btn-primary:hover) {
		opacity: 0.9;
	}

	:global(.form-select) {
		width: 100%;
		padding: 0.5rem;
		background: var(--base-100);
		border: 0.5px solid var(--base-300);
		color: var(--base-content);
		font-size: 0.875rem;
	}

	:global(.form-select:focus) {
		outline: none;
		border-color: var(--accent);
	}

	/* ============================================
	   LAYOUT
	   ============================================ */
	.app {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}
</style>
