<script lang="ts">
    import { onMount } from 'svelte';
    import type { ComparisonResult, VehicleData } from '$lib/types';
    
    let vehicleA = $state<VehicleData>({ tipo: 'MOTORCYCLE', marca: '', modelo: '' });
    let vehicleB = $state<VehicleData>({ tipo: 'MOTORCYCLE', marca: '', modelo: '' });
    
    let marcasA = $state<string[]>([]);
    let marcasB = $state<string[]>([]);
    let modelosA = $state<string[]>([]);
    let modelosB = $state<string[]>([]);
    
    let resultado = $state<ComparisonResult | null>(null);
    let loading = $state(false);
    let error = $state('');
    
    let chartDiv = $state<HTMLDivElement | undefined>(undefined);
    
    async function loadMarcas(tipo: string, vehicle: 'A' | 'B') {
        try {
            const response = await fetch(`/api/marcas/${tipo.toLowerCase()}`);
            if (response.ok) {
                const data = await response.json();
                if (vehicle === 'A') marcasA = data.marcas;
                else marcasB = data.marcas;
            }
        } catch (e) {
            console.error('Error loading marcas:', e);
        }
    }
    
    async function loadModelos(tipo: string, marca: string, vehicle: 'A' | 'B') {
        try {
            const response = await fetch(`/api/modelos/${tipo.toLowerCase()}/${encodeURIComponent(marca)}`);
            if (response.ok) {
                const data = await response.json();
                if (vehicle === 'A') modelosA = data.modelos;
                else modelosB = data.modelos;
            }
        } catch (e) {
            console.error('Error loading modelos:', e);
        }
    }
    
    function handleTipoChange(vehicle: 'A' | 'B') {
        if (vehicle === 'A') {
            vehicleA.marca = '';
            vehicleA.modelo = '';
            modelosA = [];
            loadMarcas(vehicleA.tipo, 'A');
        } else {
            vehicleB.marca = '';
            vehicleB.modelo = '';
            modelosB = [];
            loadMarcas(vehicleB.tipo, 'B');
        }
    }
    
    function handleMarcaChange(vehicle: 'A' | 'B') {
        if (vehicle === 'A') {
            vehicleA.modelo = '';
            loadModelos(vehicleA.tipo, vehicleA.marca, 'A');
        } else {
            vehicleB.modelo = '';
            loadModelos(vehicleB.tipo, vehicleB.marca, 'B');
        }
    }
    
    function renderComparisonChart() {
        if (!chartDiv || !resultado) return;
        
        const yearsA = resultado.vehicleA.priceEvolution.map(p => p.year);
        const pricesA = resultado.vehicleA.priceEvolution.map(p => p.price);
        const yearsB = resultado.vehicleB.priceEvolution.map(p => p.year);
        const pricesB = resultado.vehicleB.priceEvolution.map(p => p.price);
        
        const traceA = {
            x: yearsA,
            y: pricesA,
            mode: 'lines+markers',
            name: resultado.vehicleA.modelo,
            line: { color: '#3b82f6', width: 3 },
            marker: { size: 8 }
        };
        
        const traceB = {
            x: yearsB,
            y: pricesB,
            mode: 'lines+markers',
            name: resultado.vehicleB.modelo,
            line: { color: '#ef4444', width: 3 },
            marker: { size: 8 }
        };
        
        const layout = {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#94a3b8' },
            xaxis: { 
                title: 'Ano', 
                gridcolor: '#334155',
                tickfont: { color: '#94a3b8' }
            },
            yaxis: { 
                title: 'Preço (R$)', 
                gridcolor: '#334155',
                tickfont: { color: '#94a3b8' },
                tickformat: '$,.0f'
            },
            legend: { orientation: 'h', y: -0.2, font: { color: '#94a3b8' } },
            margin: { t: 20, b: 80 },
            autosize: true
        };
        
        // @ts-ignore
        Plotly.newPlot(chartDiv, [traceA, traceB], layout, {responsive: true});
    }
    
    $effect(() => {
        if (resultado && chartDiv) {
            setTimeout(renderComparisonChart, 100);
        }
    });
    
    async function comparar() {
        if (!vehicleA.marca || !vehicleA.modelo || !vehicleB.marca || !vehicleB.modelo) {
            error = 'Selecione marca e modelo para ambos os veículos';
            return;
        }
        
        loading = true;
        error = '';
        resultado = null;
        
        try {
            const response = await fetch('/api/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    vehicleA: { tipo: vehicleA.tipo, marca: vehicleA.marca, modelo: vehicleA.modelo },
                    vehicleB: { tipo: vehicleB.tipo, marca: vehicleB.marca, modelo: vehicleB.modelo }
                })
            });
            
            if (response.ok) {
                resultado = await response.json();
            } else {
                const data = await response.json();
                error = data.error || 'Erro na comparação';
            }
        } catch (e) {
            error = 'Erro de conexão';
        } finally {
            loading = false;
        }
    }
    
    function formatCurrency(value: number): string {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }
    
    function getTipoLabel(tipo: string): string {
        return tipo === 'CAR' ? 'Carro' : tipo === 'TRUCK' ? 'Caminhão' : 'Moto';
    }
    
    onMount(() => {
        loadMarcas('MOTORCYCLE', 'A');
        loadMarcas('MOTORCYCLE', 'B');
    });
</script>

<svelte:head>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
</svelte:head>

<div class="comparar-page">
    <!-- Header -->
    <div class="page-header">
        <h1>⚔️ Tira-Teima</h1>
        <p>Compare dois veículos e descubra qual é o melhor negócio</p>
    </div>

    <!-- Vehicle Selection -->
    <div class="selectors-grid">
        <!-- Vehicle A -->
        <div class="selector-card">
            <div class="selector-header">
                <span class="vehicle-icon">{vehicleA.tipo === 'CAR' ? '🚗' : vehicleA.tipo === 'TRUCK' ? '🚚' : '🏍️'}</span>
                <div>
                    <h2>Veículo A</h2>
                    <span class="subtitle">Primeira opção</span>
                </div>
            </div>
            
            <div class="form-group">
                <label for="tipo-a">Tipo</label>
                <select id="tipo-a" bind:value={vehicleA.tipo} onchange={() => handleTipoChange('A')}>
                    <option value="MOTORCYCLE">Moto</option>
                    <option value="CAR">Carro</option>
                    <option value="TRUCK">Caminhão</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="marca-a">Marca</label>
                <select id="marca-a" bind:value={vehicleA.marca} onchange={() => handleMarcaChange('A')}>
                    <option value="">Selecione...</option>
                    {#each marcasA as marca}
                        <option value={marca}>{marca}</option>
                    {/each}
                </select>
            </div>
            
            <div class="form-group">
                <label for="modelo-a">Modelo</label>
                <select id="modelo-a" bind:value={vehicleA.modelo} disabled={!vehicleA.marca}>
                    <option value="">Selecione...</option>
                    {#each modelosA as modelo}
                        <option value={modelo}>{modelo}</option>
                    {/each}
                </select>
            </div>
        </div>

        <!-- Vehicle B -->
        <div class="selector-card">
            <div class="selector-header">
                <span class="vehicle-icon">{vehicleB.tipo === 'CAR' ? '🚗' : vehicleB.tipo === 'TRUCK' ? '🚚' : '🏍️'}</span>
                <div>
                    <h2>Veículo B</h2>
                    <span class="subtitle">Segunda opção</span>
                </div>
            </div>
            
            <div class="form-group">
                <label for="tipo-b">Tipo</label>
                <select id="tipo-b" bind:value={vehicleB.tipo} onchange={() => handleTipoChange('B')}>
                    <option value="MOTORCYCLE">Moto</option>
                    <option value="CAR">Carro</option>
                    <option value="TRUCK">Caminhão</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="marca-b">Marca</label>
                <select id="marca-b" bind:value={vehicleB.marca} onchange={() => handleMarcaChange('B')}>
                    <option value="">Selecione...</option>
                    {#each marcasB as marca}
                        <option value={marca}>{marca}</option>
                    {/each}
                </select>
            </div>
            
            <div class="form-group">
                <label for="modelo-b">Modelo</label>
                <select id="modelo-b" bind:value={vehicleB.modelo} disabled={!vehicleB.marca}>
                    <option value="">Selecione...</option>
                    {#each modelosB as modelo}
                        <option value={modelo}>{modelo}</option>
                    {/each}
                </select>
            </div>
        </div>
    </div>

    <!-- Compare Button -->
    <div class="compare-action">
        <button class="compare-btn" onclick={comparar} disabled={loading || !vehicleA.modelo || !vehicleB.modelo}>
            {#if loading}
                <span class="spinner"></span>
                Analisando...
            {:else}
                ⚔️ Quem leva essa?
            {/if}
        </button>
    </div>

    {#if error}
        <div class="error-message">
            <span>⚠️</span>
            <p>{error}</p>
        </div>
    {/if}

    <!-- Results -->
    {#if resultado}
        <div class="results">
            <!-- Winner Banner -->
            <div class="winner-banner {resultado.winner === 'A' ? 'winner-a' : resultado.winner === 'B' ? 'winner-b' : 'tie'}">
                <span class="trophy">{resultado.winner === 'tie' ? '⚖️' : '🏆'}</span>
                <h3>
                    {#if resultado.winner === 'A'}
                        Veículo A venceu!
                    {:else if resultado.winner === 'B'}
                        Veículo B venceu!
                    {:else}
                        Empate técnico!
                    {/if}
                </h3>
                <p>{resultado.winner === 'A' ? resultado.vehicleA.modelo : resultado.winner === 'B' ? resultado.vehicleB.modelo : 'Ambos têm custo-benefício similar'}</p>
            </div>

            <!-- Score Cards -->
            <div class="scores-grid">
                <div class="score-card {resultado.winner === 'A' ? 'winner' : ''}">
                    <div class="score-header">
                        <span class="score-letter">A</span>
                        <div class="score-info">
                            <h4>{resultado.vehicleA.modelo}</h4>
                            <span>{resultado.vehicleA.marca}</span>
                        </div>
                        {#if resultado.winner === 'A'}
                            <span class="winner-badge">VENCEDOR</span>
                        {/if}
                    </div>
                    <div class="score-bar">
                        <div class="score-progress" style="width: {resultado.scores.A}%"></div>
                        <span class="score-value">{resultado.scores.A}/100</span>
                    </div>
                    <div class="score-details">
                        <div class="detail-item">
                            <span>💰 Preço</span>
                            <strong>{formatCurrency(resultado.vehicleA.currentPrice)}</strong>
                        </div>
                        <div class="detail-item">
                            <span>📉 Desvalorização</span>
                            <strong class={resultado.vehicleA.totalDepreciation < resultado.vehicleB.totalDepreciation ? 'positive' : 'negative'}>
                                {resultado.vehicleA.totalDepreciation.toFixed(1)}%
                            </strong>
                        </div>
                    </div>
                </div>

                <div class="score-card {resultado.winner === 'B' ? 'winner' : ''}">
                    <div class="score-header">
                        <span class="score-letter">B</span>
                        <div class="score-info">
                            <h4>{resultado.vehicleB.modelo}</h4>
                            <span>{resultado.vehicleB.marca}</span>
                        </div>
                        {#if resultado.winner === 'B'}
                            <span class="winner-badge">VENCEDOR</span>
                        {/if}
                    </div>
                    <div class="score-bar">
                        <div class="score-progress" style="width: {resultado.scores.B}%"></div>
                        <span class="score-value">{resultado.scores.B}/100</span>
                    </div>
                    <div class="score-details">
                        <div class="detail-item">
                            <span>💰 Preço</span>
                            <strong>{formatCurrency(resultado.vehicleB.currentPrice)}</strong>
                        </div>
                        <div class="detail-item">
                            <span>📉 Desvalorização</span>
                            <strong class={resultado.vehicleB.totalDepreciation < resultado.vehicleA.totalDepreciation ? 'positive' : 'negative'}>
                                {resultado.vehicleB.totalDepreciation.toFixed(1)}%
                            </strong>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Chart -->
            <div class="chart-card">
                <div class="chart-header">
                    <h3>📈 Evolução de Preços</h3>
                    <p>Comparação histórica entre os modelos</p>
                </div>
                <div class="chart-body">
                    <div bind:this={chartDiv} class="chart-container"></div>
                </div>
            </div>

            <!-- Price Table -->
            <div class="table-card">
                <h3>📋 Histórico de Preços FIPE</h3>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Ano</th>
                                <th class="text-right">{resultado.vehicleA.modelo}</th>
                                <th class="text-right">{resultado.vehicleB.modelo}</th>
                                <th class="text-right">Diferença</th>
                            </tr>
                        </thead>
                        <tbody>
                            {#each resultado.comparisonTable as row}
                                <tr>
                                    <td>{row.year}</td>
                                    <td class="text-right {row.vehicleAPrice < row.vehicleBPrice ? 'highlight' : ''}">
                                        {row.vehicleAPrice > 0 ? formatCurrency(row.vehicleAPrice) : '-'}
                                    </td>
                                    <td class="text-right {row.vehicleBPrice < row.vehicleAPrice ? 'highlight' : ''}">
                                        {row.vehicleBPrice > 0 ? formatCurrency(row.vehicleBPrice) : '-'}
                                    </td>
                                    <td class="text-right">
                                        {#if row.vehicleAPrice > 0 && row.vehicleBPrice > 0}
                                            <span class="badge {row.difference > 0 ? 'positive' : 'negative'}">
                                                {row.difference > 0 ? '+' : ''}{formatCurrency(row.difference)}
                                            </span>
                                        {:else}
                                            -
                                        {/if}
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Analysis -->
            <div class="analysis-cards">
                <div class="analysis-card">
                    <span class="icon">💰</span>
                    <h4>Diferença de Preço</h4>
                    <p>
                        {#if resultado.vehicleA.currentPrice > resultado.vehicleB.currentPrice}
                            Veículo A custa <strong>{formatCurrency(resultado.vehicleA.currentPrice - resultado.vehicleB.currentPrice)}</strong> a mais
                        {:else if resultado.vehicleB.currentPrice > resultado.vehicleA.currentPrice}
                            Veículo B custa <strong>{formatCurrency(resultado.vehicleB.currentPrice - resultado.vehicleA.currentPrice)}</strong> a mais
                        {:else}
                            Preços equivalentes
                        {/if}
                    </p>
                </div>
                <div class="analysis-card">
                    <span class="icon">📉</span>
                    <h4>Retenção de Valor</h4>
                    <p>
                        {#if resultado.vehicleA.totalDepreciation < resultado.vehicleB.totalDepreciation}
                            Veículo A retém mais valor
                        {:else if resultado.vehicleB.totalDepreciation < resultado.vehicleA.totalDepreciation}
                            Veículo B retém mais valor
                        {:else}
                            Retenção similar
                        {/if}
                    </p>
                </div>
                <div class="analysis-card">
                    <span class="icon">🎯</span>
                    <h4>Veredicto</h4>
                    <p>{resultado.analysis}</p>
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .comparar-page {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        max-width: 1200px;
        margin: 0 auto;
        padding: 1rem;
    }

    .page-header {
        text-align: center;
        padding: 2rem 0;
    }

    .page-header h1 {
        font-size: 2rem;
        font-weight: 700;
        color: var(--base-content);
        margin-bottom: 0.5rem;
    }

    .page-header p {
        color: var(--neutral-content);
    }

    /* Selectors */
    .selectors-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
    }

    .selector-card {
        background: var(--base-200);
        border-radius: 0.75rem;
        border: 1px solid var(--base-300);
        padding: 1.5rem;
    }

    .selector-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--base-300);
    }

    .vehicle-icon {
        font-size: 2rem;
    }

    .selector-header h2 {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--base-content);
    }

    .subtitle {
        font-size: 0.75rem;
        color: var(--neutral-content);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .form-group {
        margin-bottom: 1rem;
    }

    .form-group label {
        display: block;
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--neutral-content);
        margin-bottom: 0.375rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .form-group select {
        width: 100%;
        padding: 0.625rem 0.875rem;
        background: var(--base-100);
        border: 1px solid var(--base-300);
        border-radius: 0.5rem;
        color: var(--base-content);
        font-size: 0.875rem;
    }

    .form-group select:focus {
        outline: none;
        border-color: var(--accent);
    }

    .form-group select:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* Compare Button */
    .compare-action {
        display: flex;
        justify-content: center;
        padding: 1rem 0;
    }

    .compare-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.875rem 2rem;
        background: linear-gradient(135deg, var(--accent), var(--accent-content));
        color: var(--base-100);
        border: none;
        border-radius: 0.5rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }

    .compare-btn:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    .compare-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    .spinner {
        width: 16px;
        height: 16px;
        border: 2px solid rgba(255,255,255,0.3);
        border-top-color: white;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        to { transform: rotate(360deg); }
    }

    /* Error */
    .error-message {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 0.5rem;
        color: var(--error);
    }

    /* Results */
    .results {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    /* Winner Banner */
    .winner-banner {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 2rem;
        border-radius: 0.75rem;
        text-align: center;
    }

    .winner-banner.winner-a {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
    }

    .winner-banner.winner-b {
        background: linear-gradient(135deg, #ef4444, #b91c1c);
        color: white;
    }

    .winner-banner.tie {
        background: linear-gradient(135deg, #8b5cf6, #6d28d9);
        color: white;
    }

    .winner-banner .trophy {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }

    .winner-banner h3 {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }

    .winner-banner p {
        opacity: 0.9;
    }

    /* Score Cards */
    .scores-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1rem;
    }

    .score-card {
        background: var(--base-200);
        border-radius: 0.75rem;
        border: 1px solid var(--base-300);
        padding: 1.25rem;
    }

    .score-card.winner {
        border-color: var(--accent);
        box-shadow: 0 0 0 1px var(--accent);
    }

    .score-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    .score-letter {
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--accent);
        color: var(--base-100);
        font-size: 1.25rem;
        font-weight: 700;
        border-radius: 0.5rem;
    }

    .score-info h4 {
        font-size: 1rem;
        font-weight: 600;
        color: var(--base-content);
    }

    .score-info span {
        font-size: 0.75rem;
        color: var(--neutral-content);
    }

    .winner-badge {
        margin-left: auto;
        padding: 0.25rem 0.625rem;
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        font-size: 0.625rem;
        font-weight: 700;
        text-transform: uppercase;
        border-radius: 9999px;
    }

    .score-bar {
        position: relative;
        height: 8px;
        background: var(--base-300);
        border-radius: 4px;
        margin-bottom: 1rem;
        overflow: hidden;
    }

    .score-progress {
        height: 100%;
        background: linear-gradient(90deg, var(--accent), var(--accent-content));
        border-radius: 4px;
        transition: width 0.5s ease;
    }

    .score-value {
        position: absolute;
        right: 0;
        top: -18px;
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--base-content);
    }

    .score-details {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .detail-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem;
        background: var(--base-100);
        border-radius: 0.375rem;
        font-size: 0.875rem;
    }

    .detail-item span {
        color: var(--neutral-content);
    }

    .detail-item strong {
        color: var(--base-content);
    }

    .detail-item .positive {
        color: #22c55e;
    }

    .detail-item .negative {
        color: #ef4444;
    }

    /* Chart */
    .chart-card {
        background: var(--base-200);
        border-radius: 0.75rem;
        border: 1px solid var(--base-300);
        overflow: hidden;
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

    .chart-header p {
        font-size: 0.75rem;
        color: var(--neutral-content);
    }

    .chart-body {
        padding: 1rem;
    }

    .chart-container {
        width: 100%;
        height: 350px;
    }

    /* Table */
    .table-card {
        background: var(--base-200);
        border-radius: 0.75rem;
        border: 1px solid var(--base-300);
        padding: 1.5rem;
    }

    .table-card h3 {
        font-size: 1rem;
        font-weight: 600;
        color: var(--base-content);
        margin-bottom: 1rem;
    }

    .table-wrapper {
        overflow-x: auto;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.875rem;
    }

    thead {
        background: var(--base-300);
    }

    th {
        padding: 0.625rem;
        text-align: left;
        font-weight: 600;
        color: var(--base-content);
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    td {
        padding: 0.625rem;
        border-bottom: 1px solid var(--base-300);
        color: var(--base-content);
    }

    tr:hover {
        background: var(--base-300);
    }

    .text-right {
        text-align: right;
    }

    .highlight {
        color: #22c55e;
        font-weight: 600;
    }

    .badge {
        display: inline-flex;
        padding: 0.125rem 0.5rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .badge.positive {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
    }

    .badge.negative {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
    }

    /* Analysis Cards */
    .analysis-cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
    }

    .analysis-card {
        background: var(--base-200);
        border-radius: 0.75rem;
        border: 1px solid var(--base-300);
        padding: 1.25rem;
    }

    .analysis-card .icon {
        font-size: 1.5rem;
        margin-bottom: 0.5rem;
        display: block;
    }

    .analysis-card h4 {
        font-size: 0.875rem;
        font-weight: 600;
        color: var(--base-content);
        margin-bottom: 0.5rem;
    }

    .analysis-card p {
        font-size: 0.875rem;
        color: var(--neutral-content);
        line-height: 1.5;
    }
</style>
