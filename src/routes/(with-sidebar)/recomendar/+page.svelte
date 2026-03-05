<script lang="ts">
	import { auth } from '$lib/stores/auth.svelte';
	
	let orcamento = $state<number>(30000);
	let tipoPreferencia = $state<'TODOS' | 'MOTORCYCLE' | 'CAR' | 'TRUCK'>('TODOS');
	let anoMinimo = $state<number>(2010);
	let anoMaximo = $state<number>(new Date().getFullYear());
	let loading = $state(false);
	let resultado = $state<any>(null);
	let erro = $state<string>('');
	
	async function buscarRecomendacoes() {
		if (!orcamento || orcamento < 5000) {
			erro = 'Digite um orçamento válido (mínimo R$ 5.000)';
			return;
		}
		
		loading = true;
		erro = '';
		resultado = null;
		
		try {
			const res = await fetch('/api/recomendar', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					orcamento,
					tipoPreferencia,
					anoMinimo,
					anoMaximo
				})
			});
			
			if (!res.ok) throw new Error('Erro ao buscar recomendações');
			
			resultado = await res.json();
		} catch (e) {
			erro = 'Erro ao gerar recomendações. Tente novamente.';
		} finally {
			loading = false;
		}
	}
	
	function formatCurrency(value: number): string {
		return new Intl.NumberFormat('pt-BR', {
			style: 'currency',
			currency: 'BRL',
			maximumFractionDigits: 0
		}).format(value);
	}
	
	function getTipoLabel(tipo: string): string {
		const labels: Record<string, string> = {
			'MOTORCYCLE': '🏍️ Moto',
			'CAR': '🚗 Carro',
			'TRUCK': '🚛 Caminhão'
		};
		return labels[tipo] || tipo;
	}
	
	function getRiscoClass(risco: string): string {
		const classes: Record<string, string> = {
			'BAIXO': 'risco-baixo',
			'MEDIO': 'risco-medio',
			'ALTO': 'risco-alto'
		};
		return classes[risco] || '';
	}
</script>

<div class="recomendar-page">
	<header class="page-header">
		<h1>🎯 Recomendador Inteligente</h1>
		<p>Descubra qual veículo comprar baseado no seu orçamento e quanto você vai perder de dinheiro</p>
	</header>
	
	<!-- Formulário -->
	<div class="form-card">
		<h2>💰 Quanto você tem para investir?</h2>
		
		<div class="form-grid">
			<div class="form-group">
				<label>Seu Orçamento (R$)</label>
				<input 
					type="number" 
					bind:value={orcamento}
					min="5000"
					step="1000"
					placeholder="30000"
				/>
				<span class="input-hint">Mínimo: R$ 5.000</span>
			</div>
			
			<div class="form-group">
				<label>Tipo de Veículo</label>
				<select bind:value={tipoPreferencia}>
					<option value="TODOS">🔄 Todos os tipos</option>
					<option value="MOTORCYCLE">🏍️ Motos</option>
					<option value="CAR">🚗 Carros</option>
					<option value="TRUCK">🚛 Caminhões</option>
				</select>
			</div>
			
			<div class="form-group">
				<label>Ano Mínimo</label>
				<input type="number" bind:value={anoMinimo} min="1990" max={anoMaximo} />
			</div>
			
			<div class="form-group">
				<label>Ano Máximo</label>
				<input type="number" bind:value={anoMaximo} min={anoMinimo} max={new Date().getFullYear()} />
			</div>
		</div>
		
		{#if erro}
			<div class="erro-msg">⚠️ {erro}</div>
		{/if}
		
		<button 
			class="btn-buscar"
			onclick={buscarRecomendacoes}
			disabled={loading}
		>
			{#if loading}
				<span class="spinner"></span>
				Buscando melhores opções...
			{:else}
				🔍 Encontrar Melhores Negócios
			{/if}
		</button>
	</div>
	
	{#if resultado}
		<!-- Resumo -->
		<div class="resumo-card">
			<div class="resumo-item">
				<span class="resumo-label">Orçamento</span>
				<span class="resumo-value">{formatCurrency(resultado.orcamento)}</span>
			</div>
			<div class="resumo-item">
				<span class="resumo-label">Opções Encontradas</span>
				<span class="resumo-value">{resultado.recomendacoes.length}</span>
			</div>
			<div class="resumo-item">
				<span class="resumo-label">Melhor Score</span>
				<span class="resumo-value highlight">{resultado.recomendacoes[0]?.scoreGeral || 0}/100</span>
			</div>
		</div>
		
		<!-- Melhor Recomendação (Destaque) -->
		{#if resultado.recomendacoes[0]}
			{@const melhor = resultado.recomendacoes[0]}
			<div class="destaque-card">
				<div class="destaque-badge">🏆 MELHOR OPÇÃO</div>
				<div class="destaque-content">
					<div class="destaque-veiculo">
						<span class="destaque-tipo">{getTipoLabel(melhor.tipo)}</span>
						<h3>{melhor.marca} {melhor.modelo}</h3>
						<span class="destaque-ano">{melhor.ano}</span>
					</div>
					
					<div class="destaque-preco">
						<span class="preco-label">Investimento</span>
						<span class="preco-value">{melhor.precoFormatado}</span>
						<span class="preco-folga">Sobra: {formatCurrency(resultado.orcamento - melhor.preco)}</span>
					</div>
					
					<div class="destaque-perda">
						<span class="perda-label">Perda Estimada (1 ano)</span>
						<span class="perda-value" class:baixa={melhor.perdaPercentual1Ano < 10} class:media={melhor.perdaPercentual1Ano >= 10 && melhor.perdaPercentual1Ano < 20} class:alta={melhor.perdaPercentual1Ano >= 20}>
							-{formatCurrency(melhor.perdaEstimada1Ano)}
							<span class="perda-percentual">({melhor.perdaPercentual1Ano}%)</span>
						</span>
					</div>
					
					<div class="destaque-scores">
						<div class="score-item">
							<span class="score-label">Custo-Benefício</span>
							<div class="score-bar">
								<div class="score-fill" style="width: {melhor.scoreCustoBeneficio}%"></div>
							</div>
							<span class="score-value">{melhor.scoreCustoBeneficio}</span>
						</div>
						<div class="score-item">
							<span class="score-label">Retenção de Valor</span>
							<div class="score-bar">
								<div class="score-fill" style="width: {melhor.scoreRetencaoValor}%"></div>
							</div>
							<span class="score-value">{melhor.scoreRetencaoValor}</span>
						</div>
					</div>
					
					<div class="destaque-recomendacao">
						<p>{melhor.recomendacao}</p>
					</div>
					
					<div class="destaque-tags">
						<span class="risco-tag {getRiscoClass(melhor.nivelRisco)}">
							Risco: {melhor.nivelRisco}
						</span>
						{#each melhor.idealPara as uso}
							<span class="uso-tag">{uso}</span>
						{/each}
					</div>
				</div>
			</div>
		{/if}
		
		<!-- Lista de Recomendações -->
		<div class="lista-section">
			<h3>📋 Outras Opções Recomendadas</h3>
			<div class="lista-grid">
				{#each resultado.recomendacoes.slice(1) as item (item.rank)}
					<div class="opcao-card">
						<div class="opcao-rank">#{item.rank}</div>
						<div class="opcao-info">
							<span class="opcao-tipo">{getTipoLabel(item.tipo)}</span>
							<h4>{item.marca} {item.modelo}</h4>
							<div class="opcao-detalhes">
								<span class="opcao-ano">{item.ano}</span>
								<span class="risco-badge {getRiscoClass(item.nivelRisco)}">
									{item.nivelRisco === 'BAIXO' ? '🔒' : item.nivelRisco === 'MEDIO' ? '⚠️' : '🔴'} {item.nivelRisco}
								</span>
							</div>
							{#if item.idealPara?.length}
								<div class="opcao-usos">
									{#each item.idealPara.slice(0, 2) as uso}
										<span class="uso-mini">{uso}</span>
									{/each}
								</div>
							{/if}
						</div>
						<div class="opcao-valores">
							<span class="opcao-preco">{item.precoFormatado}</span>
							<span class="opcao-folga">Sobra: {formatCurrency(resultado.orcamento - item.preco)}</span>
							<span class="opcao-perda" class:baixa={item.perdaPercentual1Ano < 10} class:media={item.perdaPercentual1Ano >= 10 && item.perdaPercentual1Ano < 20} class:alta={item.perdaPercentual1Ano >= 20}>
								📉 -{formatCurrency(item.perdaEstimada1Ano)}/ano ({item.perdaPercentual1Ano}%)
							</span>
						</div>
						<div class="opcao-score">
							<span class="score-badge">{item.scoreGeral}</span>
							<span class="score-label">Score</span>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.recomendar-page {
		max-width: 1000px;
		margin: 0 auto;
		padding: 1rem;
	}
	
	.page-header {
		text-align: center;
		margin-bottom: 2rem;
	}
	
	.page-header h1 {
		font-size: 1.75rem;
		color: var(--base-content);
		margin-bottom: 0.5rem;
	}
	
	.page-header p {
		color: var(--neutral-content);
		font-size: 0.9375rem;
	}
	
	.form-card {
		background: var(--base-200);
		border-radius: 1rem;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
		border: 1px solid var(--base-300);
	}
	
	.form-card h2 {
		font-size: 1.125rem;
		color: var(--base-content);
		margin-bottom: 1.25rem;
	}
	
	.form-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1rem;
		margin-bottom: 1rem;
	}
	
	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	
	.form-group label {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--neutral-content);
	}
	
	.form-group input,
	.form-group select {
		padding: 0.75rem;
		background: var(--base-100);
		border: 1px solid var(--base-300);
		border-radius: 0.5rem;
		color: var(--base-content);
		font-size: 1rem;
	}
	
	.input-hint {
		font-size: 0.75rem;
		color: var(--neutral-content);
	}
	
	.erro-msg {
		background: rgba(239, 68, 68, 0.1);
		color: var(--error);
		padding: 0.75rem;
		border-radius: 0.5rem;
		margin-bottom: 1rem;
		font-size: 0.875rem;
	}
	
	.btn-buscar {
		width: 100%;
		padding: 1rem;
		background: linear-gradient(135deg, var(--accent), oklch(from var(--accent) l c h / 0.8));
		border: none;
		border-radius: 0.5rem;
		color: var(--accent-content);
		font-size: 1rem;
		font-weight: 600;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
	}
	
	.spinner {
		width: 20px;
		height: 20px;
		border: 2px solid rgba(255,255,255,0.3);
		border-top-color: currentColor;
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}
	
	@keyframes spin {
		to { transform: rotate(360deg); }
	}
	
	.resumo-card {
		display: flex;
		gap: 1rem;
		margin-bottom: 1.5rem;
		overflow-x: auto;
	}
	
	.resumo-item {
		flex: 1;
		min-width: 150px;
		background: var(--base-200);
		padding: 1rem;
		border-radius: 0.75rem;
		text-align: center;
		border: 1px solid var(--base-300);
	}
	
	.resumo-label {
		display: block;
		font-size: 0.75rem;
		color: var(--neutral-content);
		margin-bottom: 0.25rem;
	}
	
	.resumo-value {
		display: block;
		font-size: 1.25rem;
		font-weight: 700;
		color: var(--base-content);
	}
	
	.resumo-value.highlight {
		color: var(--accent);
	}
	
	.destaque-card {
		background: linear-gradient(135deg, var(--base-200), oklch(from var(--base-200) l c h / 0.5));
		border: 2px solid var(--accent);
		border-radius: 1rem;
		padding: 1.5rem;
		margin-bottom: 1.5rem;
		position: relative;
	}
	
	.destaque-badge {
		position: absolute;
		top: -12px;
		left: 50%;
		transform: translateX(-50%);
		background: linear-gradient(135deg, #fbbf24, #f59e0b);
		color: #000;
		padding: 0.375rem 1rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 700;
	}
	
	.destaque-content {
		display: grid;
		grid-template-columns: 1fr auto auto;
		gap: 1.5rem;
		align-items: start;
	}
	
	.destaque-veiculo h3 {
		font-size: 1.5rem;
		color: var(--base-content);
		margin: 0.25rem 0;
	}
	
	.perda-value.baixa { color: #10b981; }
	.perda-value.media { color: #f59e0b; }
	.perda-value.alta { color: #ef4444; }
	
	.risco-tag.risco-baixo { background: #10b981; color: #fff; }
	.risco-tag.risco-medio { background: #f59e0b; color: #000; }
	.risco-tag.risco-alto { background: #ef4444; color: #fff; }
	
	/* Estilos da lista de opções */
	.lista-grid {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}
	
	.opcao-card {
		display: grid;
		grid-template-columns: auto 1fr auto auto;
		gap: 1rem;
		align-items: center;
		background: var(--base-200);
		padding: 1rem;
		border-radius: 0.75rem;
		border: 1px solid var(--base-300);
	}
	
	.opcao-rank {
		width: 32px;
		height: 32px;
		background: var(--base-300);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		color: var(--base-content);
		flex-shrink: 0;
	}
	
	.opcao-info {
		min-width: 0;
	}
	
	.opcao-info h4 {
		font-size: 1rem;
		color: var(--base-content);
		margin: 0 0 0.25rem 0;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	
	.opcao-tipo {
		font-size: 0.75rem;
		color: var(--neutral-content);
	}
	
	.opcao-detalhes {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin: 0.25rem 0;
	}
	
	.opcao-ano {
		font-size: 0.875rem;
		color: var(--accent);
	}
	
	.risco-badge {
		font-size: 0.625rem;
		padding: 0.125rem 0.375rem;
		border-radius: 0.25rem;
		font-weight: 600;
		text-transform: uppercase;
	}
	
	.risco-badge.risco-baixo { background: #10b981; color: #fff; }
	.risco-badge.risco-medio { background: #f59e0b; color: #000; }
	.risco-badge.risco-alto { background: #ef4444; color: #fff; }
	
	.opcao-usos {
		display: flex;
		gap: 0.25rem;
		flex-wrap: wrap;
	}
	
	.uso-mini {
		font-size: 0.625rem;
		padding: 0.125rem 0.375rem;
		background: var(--base-300);
		border-radius: 0.25rem;
		color: var(--neutral-content);
	}
	
	.opcao-valores {
		text-align: right;
	}
	
	.opcao-preco {
		display: block;
		font-weight: 600;
		color: var(--base-content);
		font-size: 1rem;
	}
	
	.opcao-folga {
		display: block;
		font-size: 0.75rem;
		color: var(--neutral-content);
		margin-bottom: 0.25rem;
	}
	
	.opcao-perda {
		display: block;
		font-size: 0.75rem;
		font-weight: 500;
	}
	
	.opcao-perda.baixa { color: #10b981; }
	.opcao-perda.media { color: #f59e0b; }
	.opcao-perda.alta { color: #ef4444; }
	
	.opcao-score {
		text-align: center;
	}
	
	.score-badge {
		width: 48px;
		height: 48px;
		background: var(--accent);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 700;
		color: var(--accent-content);
		margin: 0 auto;
	}
	
	.score-label {
		display: block;
		font-size: 0.625rem;
		color: var(--neutral-content);
		margin-top: 0.25rem;
	}
	
	@media (max-width: 768px) {
		.destaque-content {
			grid-template-columns: 1fr;
		}
	}
</style>
