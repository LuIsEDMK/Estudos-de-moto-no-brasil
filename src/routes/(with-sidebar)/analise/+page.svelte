<script lang="ts">
	import { page } from '$app/state';
	import { auth } from '$lib/stores/auth.svelte';
	import { ui } from '$lib/stores/ui.svelte';
	import PriceEvolutionChart from '$lib/components/charts/PriceEvolutionChart.svelte';
	import ValueRetentionChart from '$lib/components/charts/ValueRetentionChart.svelte';
	import YearlyDropChart from '$lib/components/charts/YearlyDropChart.svelte';
	import type { AnalysisResult } from '$lib/types';
	import { onMount } from 'svelte';

	let resultado = $state<AnalysisResult | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);

	const marca = $derived(page.url.searchParams.get('marca') || '');
	const modelo = $derived(page.url.searchParams.get('modelo') || '');
	const tipo = $derived(page.url.searchParams.get('tipo') || 'MOTORCYCLE');

	let analyzedKey = $state<string>('');
	let lastVipState = $state<boolean>(false);

	onMount(() => {
		ui.loadAndInit();
	});

	async function analyze(force = false) {
		if (!marca || !modelo) return;

		const currentKey = `${marca}-${modelo}-${tipo}-${auth.usuarioVip}`;
		if (!force && currentKey === analyzedKey) return;

		loading = true;
		error = null;

		try {
			const formData = new FormData();
			formData.append('marca', marca);
			formData.append('modelo', modelo);
			formData.append('tipo', tipo);
			formData.append('isVip', String(auth.usuarioVip));

			const res = await fetch('/api/analyze', {
				method: 'POST',
				body: formData
			});

			if (!res.ok) {
				const err = await res.text();
				throw new Error(err || 'Erro ao analisar');
			}

			resultado = await res.json();
			analyzedKey = currentKey;
			lastVipState = auth.usuarioVip;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Erro desconhecido';
			resultado = null;
		} finally {
			loading = false;
		}
	}

	// Analisa quando marca/modelo ou VIP mudam
	$effect(() => {
		const _marca = marca;
		const _modelo = modelo;
		const _vip = auth.usuarioVip;
		
		if (_marca && _modelo) {
			const force = _vip !== lastVipState && analyzedKey !== '';
			analyze(force);
		}
	});

	function formatCurrency(value: string): string {
		return value;
	}
</script>

{#if !marca || !modelo}
	<div class="empty-state">
		<div class="empty-icon">🏍️</div>
		<h2>Selecione um veículo</h2>
		<p>Escolha a marca e modelo na barra lateral para ver a análise completa</p>
	</div>
{:else if loading}
	<div class="loading">
		<div class="spinner"></div>
		<p>Analisando {marca} {modelo}...</p>
	</div>
{:else if error}
	<div class="error">
		<span class="error-icon">⚠️</span>
		<p>{error}</p>
	</div>
{:else if resultado}
	<div class="analysis">
		<!-- Header -->
		<div class="vehicle-header">
			<div class="vehicle-info">
				<h1 class="vehicle-name">{resultado.marca} {resultado.modelo}</h1>
				<span class="vehicle-type">{resultado.tipo === 'MOTORCYCLE' ? 'Moto' : resultado.tipo === 'CAR' ? 'Carro' : 'Caminhão'}</span>
			</div>
			<div class="price-summary">
				<div class="price-item highlight">
					<span class="label">Modelo Novo</span>
					<span class="value">{resultado.preco_novo}</span>
				</div>
				<div class="price-item">
					<span class="label">Modelo Antigo</span>
					<span class="value">{resultado.preco_velho}</span>
				</div>
				<div class="price-item alert">
					<span class="label">Desvalorização Total</span>
					<span class="value">{resultado.desvalorizacao}</span>
				</div>
			</div>
		</div>

		<!-- Insights -->
		{#if resultado.insights}
			<div class="insights-bar">
				<div class="insight-item">
					<span class="insight-label">📊 Anos Analisados</span>
					<span class="insight-value">{resultado.insights.anos_analisados}</span>
				</div>
				<div class="insight-item">
					<span class="insight-label">⭐ Ano Mais Estável</span>
					<span class="insight-value">{resultado.insights.ano_mais_estavel || 'N/A'}</span>
				</div>
				<div class="insight-item">
					<span class="insight-label">📉 Queda Média/Ano</span>
					<span class="insight-value">{resultado.insights.queda_media_anual}</span>
				</div>
			</div>
		{/if}

		<!-- Gráficos -->
		<div class="charts-grid">
			<!-- Gráfico 1: Evolução do Preço -->
			<div class="chart-card">
				<div class="chart-header">
					<h3>📈 Evolução do Preço</h3>
					<p class="chart-desc">Veja como o valor mudou ao longo dos anos</p>
				</div>
				<div class="chart-body">
					<PriceEvolutionChart 
						data={resultado.grafico_price_evolution} 
					/>
				</div>
				{#if !auth.usuarioVip}
					<div class="vip-overlay">
						<span>🔒 Dados históricos completos para VIPs</span>
					</div>
				{/if}
			</div>

			<!-- Gráfico 2: Retenção de Valor -->
			<div class="chart-card">
				<div class="chart-header">
					<h3>💎 Retenção de Valor</h3>
					<p class="chart-desc">Quanto o veículo vale comparado ao modelo mais novo</p>
				</div>
				<div class="chart-body">
					<ValueRetentionChart 
						data={resultado.grafico_value_retention}
					/>
				</div>
				{#if !auth.usuarioVip}
					<div class="vip-overlay">
						<span>🔒 Análise completa para VIPs</span>
					</div>
				{/if}
			</div>

			<!-- Gráfico 3: Queda Anual -->
			<div class="chart-card">
				<div class="chart-header">
					<h3>📉 Desvalorização Anual</h3>
					<p class="chart-desc">Identifique os anos com maior e menor queda</p>
				</div>
				<div class="chart-body">
					<YearlyDropChart 
						data={resultado.grafico_yearly_drop}
					/>
				</div>
				{#if !auth.usuarioVip}
					<div class="vip-overlay">
						<span>🔒 Projeções para VIPs</span>
					</div>
				{/if}
			</div>
		</div>

		<!-- Tabela de Preços -->
		<div class="table-section">
			<h3>📋 Histórico de Preços FIPE</h3>
			<div class="table-wrapper">
				<table class="data-table">
					<thead>
						<tr>
							<th>Ano</th>
							<th>Valor FIPE</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						{#each resultado.tabela as row}
							<tr>
								<td>{row.ano}</td>
								<td class:locked={row.valor.includes('🔒')}>{row.valor}</td>
								<td>
									{#if row.valor.includes('🔒')}
										<span class="badge locked">VIP</span>
									{:else}
										<span class="badge available">✓</span>
									{/if}
								</td>
								</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- Recomendação -->
		{#if resultado.insights?.recomendacao}
			<div class="recommendation">
				<span class="rec-icon">💡</span>
				<p>{resultado.insights.recomendacao}</p>
			</div>
		{/if}
	</div>
{/if}

<style>
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		color: var(--neutral-content);
		text-align: center;
	}

	.empty-icon {
		font-size: 4rem;
		margin-bottom: 1rem;
		opacity: 0.5;
	}

	.empty-state h2 {
		font-size: 1.5rem;
		margin-bottom: 0.5rem;
		color: var(--base-content);
	}

	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 50vh;
		gap: 1rem;
		color: var(--neutral-content);
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--base-300);
		border-top-color: var(--accent);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 50vh;
		color: var(--error);
		gap: 0.5rem;
	}

	.error-icon {
		font-size: 2rem;
	}

	.analysis {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.vehicle-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1.5rem;
		background: linear-gradient(135deg, var(--base-200), var(--base-300));
		border-radius: 0.75rem;
		border: 1px solid var(--base-300);
	}

	.vehicle-name {
		font-size: 1.75rem;
		font-weight: 700;
		color: var(--base-content);
	}

	.vehicle-type {
		font-size: 0.875rem;
		color: var(--neutral-content);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.price-summary {
		display: flex;
		gap: 2rem;
	}

	.price-item {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
	}

	.price-item .label {
		font-size: 0.75rem;
		text-transform: uppercase;
		color: var(--neutral-content);
		letter-spacing: 0.05em;
	}

	.price-item .value {
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--base-content);
	}

	.price-item.highlight .value {
		color: var(--accent);
	}

	.price-item.alert .value {
		color: var(--error);
	}

	.insights-bar {
		display: flex;
		gap: 1rem;
		padding: 1rem;
		background: var(--base-200);
		border-radius: 0.5rem;
		border: 1px solid var(--base-300);
	}

	.insight-item {
		flex: 1;
		text-align: center;
		padding: 0.5rem;
	}

	.insight-label {
		display: block;
		font-size: 0.75rem;
		color: var(--neutral-content);
		margin-bottom: 0.25rem;
	}

	.insight-value {
		display: block;
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--base-content);
	}

	.charts-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
		gap: 1.5rem;
	}

	.chart-card {
		background: var(--base-200);
		border-radius: 0.75rem;
		border: 1px solid var(--base-300);
		overflow: hidden;
		position: relative;
	}

	.chart-header {
		padding: 1rem;
		border-bottom: 1px solid var(--base-300);
	}

	.chart-header h3 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--base-content);
		margin-bottom: 0.25rem;
	}

	.chart-desc {
		font-size: 0.75rem;
		color: var(--neutral-content);
	}

	.chart-body {
		padding: 1rem;
	}

	.vip-overlay {
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		padding: 0.75rem;
		background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
		text-align: center;
		font-size: 0.875rem;
		color: var(--warning);
	}

	.table-section {
		background: var(--base-200);
		border-radius: 0.75rem;
		border: 1px solid var(--base-300);
		padding: 1.5rem;
	}

	.table-section h3 {
		font-size: 1rem;
		font-weight: 600;
		color: var(--base-content);
		margin-bottom: 1rem;
	}

	.table-wrapper {
		overflow-x: auto;
	}

	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 0.875rem;
	}

	.data-table th,
	.data-table td {
		padding: 0.75rem;
		text-align: left;
		border-bottom: 1px solid var(--base-300);
	}

	.data-table th {
		font-weight: 600;
		color: var(--neutral-content);
		background: var(--base-100);
	}

	.data-table td {
		color: var(--base-content);
	}

	.data-table td.locked {
		color: var(--neutral-content);
		font-style: italic;
	}

	.badge {
		display: inline-flex;
		align-items: center;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		font-size: 0.75rem;
		font-weight: 600;
	}

	.badge.locked {
		background: var(--warning);
		color: #000;
	}

	.badge.available {
		background: var(--success);
		color: #fff;
	}

	.recommendation {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 1rem 1.5rem;
		background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(16, 185, 129, 0.1));
		border: 1px solid rgba(59, 130, 246, 0.3);
		border-radius: 0.75rem;
	}

	.rec-icon {
		font-size: 1.5rem;
	}

	.recommendation p {
		margin: 0;
		color: var(--base-content);
		font-size: 0.9375rem;
	}

	@media (max-width: 768px) {
		.vehicle-header {
			flex-direction: column;
			gap: 1rem;
			align-items: flex-start;
		}

		.price-summary {
			width: 100%;
			justify-content: space-between;
		}

		.insights-bar {
			flex-direction: column;
		}

		.charts-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
