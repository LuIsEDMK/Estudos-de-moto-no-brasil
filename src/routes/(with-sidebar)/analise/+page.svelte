<script lang="ts">
	import { page } from '$app/state';
	import { auth } from '$lib/stores/auth.svelte';
	import { ui } from '$lib/stores/ui.svelte';
	import DepreciationChart from '$lib/components/charts/DepreciationChart.svelte';
	import type { AnalysisResult } from '$lib/types';
	import { onMount } from 'svelte';

	let resultado = $state<AnalysisResult | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);

	const marca = $derived(page.url.searchParams.get('marca') || '');
	const modelo = $derived(page.url.searchParams.get('modelo') || '');
	const tipo = $derived(page.url.searchParams.get('tipo') || 'MOTORCYCLE');

	let analyzedKey = $state<string>('');

	onMount(() => {
		ui.loadAndInit();
	});

	async function analyze() {
		if (!marca || !modelo) return;

		const currentKey = `${marca}-${modelo}-${tipo}`;
		if (currentKey === analyzedKey) return;

		loading = true;
		error = null;

		try {
			const formData = new FormData();
			formData.append('marca', marca);
			formData.append('modelo', modelo);
			formData.append('tipo', tipo);
			formData.append('consultas_feitas', String(ui.consultasFeitas));

			const res = await fetch('/api/analyze', {
				method: 'POST',
				body: formData
			});

			if (res.status === 403) {
				ui.setLimiteAtingido(true);
				throw new Error('Limite de consultas atingido');
			}

			if (!res.ok) {
				throw new Error('Erro ao analisar');
			}

			resultado = await res.json();
			analyzedKey = currentKey;

			if (ui.shouldCountAsNew(currentKey)) {
				ui.incrementarConsulta(currentKey);
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Erro desconhecido';
			resultado = null;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (marca && modelo) {
			analyze();
		}
	});
</script>

{#if !marca || !modelo}
	<div class="empty-state">
		<p>Selecione uma marca e modelo na barra lateral</p>
	</div>
{:else if loading}
	<div class="loading">Analisando {marca} {modelo}...</div>
{:else if error}
	<div class="error">{error}</div>
{:else if resultado}
	<div class="analysis">
		<div class="vehicle-header">
			<h1 class="vehicle-name">{resultado.marca} {resultado.modelo}</h1>
			<div class="price-summary">
				<div class="price-item">
					<span class="label">Novo</span>
					<span class="value">{resultado.preco_novo}</span>
				</div>
				<div class="price-item">
					<span class="label">Antigo</span>
					<span class="value">{resultado.preco_velho}</span>
				</div>
				<div class="price-item">
					<span class="label">Desvalorização</span>
					<span class="value">{resultado.desvalorizacao}</span>
				</div>
			</div>
		</div>

		<div class="main-grid">
			<div class="chart-section">
				<h2 class="section-title">Gráfico de Impacto Financeiro</h2>
				<DepreciationChart data={resultado.grafico} />
			</div>

			<div class="history-section">
				<h2 class="section-title">Histórico de Preços</h2>
				<div class="table-wrapper">
					<table class="data-table">
						<thead>
							<tr>
								<th>Ano</th>
								<th>Valor FIPE</th>
							</tr>
						</thead>
						<tbody>
							{#each resultado.tabela as row}
								<tr>
									<td>{row.ano}</td>
									<td class:locked={row.valor.includes('🔒')}>{row.valor}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>

		{#if auth.usuarioVip}
			<div class="vip-section">
				<h2 class="section-title">📊 Previsões VIP</h2>
				<div class="vip-grid">
					<div class="vip-card">
						<span class="vip-label">Previsão 2026</span>
						<span class="vip-value">{resultado.vip_stats.previsao_2026}</span>
					</div>
					<div class="vip-card">
						<span class="vip-label">Previsibilidade</span>
						<span class="vip-value">{resultado.vip_stats.previsibilidade}</span>
					</div>
					<div class="vip-card">
						<span class="vip-label">Tendência Anual</span>
						<span class="vip-value">{resultado.vip_stats.tendencia_anual}</span>
					</div>
				</div>
			</div>
		{/if}
	</div>
{/if}

<style>
	.empty-state,
	.loading,
	.error {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 50vh;
		color: var(--neutral-content);
		font-size: 0.9375rem;
	}

	.error {
		color: var(--error);
	}

	.analysis {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.vehicle-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1rem;
		background: var(--base-200);
		border: 0.5px solid var(--base-300);
	}

	.vehicle-name {
		font-size: 1.125rem;
		font-weight: 700;
		color: var(--base-content);
	}

	.price-summary {
		display: flex;
		gap: 1.5rem;
	}

	.price-item {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
	}

	.price-item .label {
		font-size: 0.625rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--neutral-content);
	}

	.price-item .value {
		font-size: 0.875rem;
		font-weight: 600;
		color: var(--base-content);
	}

	.main-grid {
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 0.75rem;
		min-height: 500px;
	}

	@media (max-width: 1024px) {
		.main-grid {
			grid-template-columns: 1fr;
		}
	}

	.chart-section,
	.history-section {
		background: var(--base-200);
		border: 0.5px solid var(--base-300);
		padding: 0.75rem;
		display: flex;
		flex-direction: column;
	}

	.section-title {
		font-size: 0.75rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--neutral-content);
		margin-bottom: 0.5rem;
	}

	.chart-section :global(.chart-wrapper) {
		flex: 1;
		min-height: 0;
	}

	.table-wrapper {
		flex: 1;
		overflow-y: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.8125rem;
	}

	.data-table th,
	.data-table td {
		padding: 0.5rem 0.625rem;
		text-align: left;
		border-bottom: 0.5px solid var(--base-300);
	}

	.data-table th {
		font-weight: 600;
		color: var(--neutral-content);
		background: var(--base-100);
		position: sticky;
		top: 0;
	}

	.data-table td {
		color: var(--base-content);
	}

	.data-table td.locked {
		color: var(--neutral-content);
		font-style: italic;
	}

	.vip-section {
		background: oklch(from var(--warning) l c h / 0.05);
		border: 0.5px solid oklch(from var(--warning) l c h / 0.2);
		padding: 0.75rem;
	}

	.vip-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 0.75rem;
	}

	@media (max-width: 768px) {
		.vip-grid {
			grid-template-columns: 1fr;
		}
	}

	.vip-card {
		display: flex;
		flex-direction: column;
		padding: 0.625rem;
		background: var(--base-100);
	}

	.vip-label {
		font-size: 0.625rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--neutral-content);
	}

	.vip-value {
		font-size: 0.9375rem;
		font-weight: 600;
		color: var(--base-content);
	}
</style>
