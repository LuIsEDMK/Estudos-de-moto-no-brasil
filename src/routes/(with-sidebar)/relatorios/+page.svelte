<script lang="ts">
	import { auth } from '$lib/stores/auth.svelte';
	import { vehicle } from '$lib/stores/vehicle.svelte';
	import RankingTable from '$lib/components/reports/RankingTable.svelte';
	import LockedPreview from '$lib/components/reports/LockedPreview.svelte';
	import type { VipReportsResponse, VipReport } from '$lib/types';
	import { onMount } from 'svelte';

	let reports = $state<VipReportsResponse | null>(null);
	let loading = $state(false);

	async function loadReports() {
		loading = true;
		try {
			const res = await fetch(`/api/vip/reports?tipo=${vehicle.tipo}`);
			reports = await res.json();
		} catch (e) {
			console.error('Error loading reports:', e);
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadReports();
	});

	$effect(() => {
		if (vehicle.tipo) {
			loadReports();
		}
	});

	const recentesColumns = [
		{ key: 'nome_marca' as keyof VipReport, label: 'Marca' },
		{ key: 'nome_modelo' as keyof VipReport, label: 'Modelo' },
		{ key: 'ano_modelo_novo' as keyof VipReport, label: 'Ano' },
		{ key: 'preco_limpo_novo' as keyof VipReport, label: 'Preço', format: 'currency' as const },
		{ key: 'queda_anual_media' as keyof VipReport, label: 'Perda/Ano', format: 'percent' as const }
	];

	const baratasColumns = [
		{ key: 'nome_marca' as keyof VipReport, label: 'Marca' },
		{ key: 'nome_modelo' as keyof VipReport, label: 'Modelo' },
		{
			key: 'preco_limpo_novo' as keyof VipReport,
			label: 'Preço Máx.',
			format: 'currency' as const
		},
		{ key: 'queda_anual_media' as keyof VipReport, label: 'Perda/Ano', format: 'percent' as const }
	];

	const bombasColumns = [
		{ key: 'nome_marca' as keyof VipReport, label: 'Marca' },
		{ key: 'nome_modelo' as keyof VipReport, label: 'Modelo' },
		{ key: 'ano_modelo_novo' as keyof VipReport, label: 'Ano' },
		{ key: 'preco_limpo_novo' as keyof VipReport, label: 'Preço', format: 'currency' as const },
		{
			key: 'queda_anual_media' as keyof VipReport,
			label: 'Derretimento',
			format: 'percent' as const
		}
	];
</script>

<div class="page">
	<h1 class="page-title">🏆 Relatórios VIP</h1>

	{#if loading}
		<div class="loading">Carregando relatórios...</div>
	{:else if !auth.usuarioVip}
		<LockedPreview degustacao={reports?.degustacao} />
	{:else if reports?.vip}
		<div class="content">
			<section class="section">
				<h2 class="section-title">🆕 Lançamentos Recentes (2024+)</h2>
				<p class="section-desc">Veículos novos que mais seguram valor</p>
				{#if reports.recentes}
					<RankingTable data={reports.recentes} columns={recentesColumns} />
				{/if}
			</section>

			<section class="section">
				<h2 class="section-title">💰 Baratinhas (até R$ 15k)</h2>
				<p class="section-desc">Veículos acessíveis com baixa desvalorização</p>
				{#if reports.baratas}
					<RankingTable data={reports.baratas} columns={baratasColumns} />
				{/if}
			</section>

			<section class="section bombas">
				<h2 class="section-title">💣 Bombas de Desvalorização</h2>
				<p class="section-desc">Veículos que mais perdem valor - CUIDADO!</p>
				{#if reports.bombas}
					<RankingTable data={reports.bombas} columns={bombasColumns} />
				{/if}
			</section>
		</div>
	{/if}
</div>

<style>
	.page {
		background: var(--base-200);
		border: 0.5px solid var(--base-300);
	}

	.page-title {
		padding: 0.75rem 1rem;
		font-size: 1rem;
		font-weight: 700;
		border-bottom: 0.5px solid var(--base-300);
		color: var(--base-content);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.loading {
		padding: 3rem;
		text-align: center;
		color: var(--neutral-content);
	}

	.content {
		padding: 1rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.section {
		padding: 1rem;
		background: var(--base-100);
		border: 0.5px solid var(--base-300);
	}

	.section.bombas {
		border-color: var(--error);
		background: oklch(from var(--error) l c h / 0.05);
	}

	.section-title {
		font-size: 1rem;
		font-weight: 700;
		color: var(--base-content);
	}

	.section-desc {
		font-size: 0.875rem;
		color: var(--neutral-content);
		margin-bottom: 0.75rem;
	}
</style>
