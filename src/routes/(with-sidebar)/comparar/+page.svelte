<script lang="ts">
	import { auth } from '$lib/stores/auth.svelte';
	import { vehicle } from '$lib/stores/vehicle.svelte';
	import VehiclePicker from '$lib/components/ui/VehiclePicker.svelte';
	import VerdictCard from '$lib/components/ui/VerdictCard.svelte';
	import type { ComparisonResult } from '$lib/types';

	let motoA = $state({ marca: '', modelo: '' });
	let motoB = $state({ marca: '', modelo: '' });
	let marcas = $state<string[]>([]);
	let modelosA = $state<string[]>([]);
	let modelosB = $state<string[]>([]);
	let resultado = $state<ComparisonResult | null>(null);
	let loading = $state(false);

	$effect(() => {
		loadMarcas();
	});

	async function loadMarcas() {
		const res = await fetch(`/api/marcas/${vehicle.tipo}`);
		const data = await res.json();
		marcas = data.marcas;
	}

	async function loadModelos(lado: 'A' | 'B', marca: string) {
		if (!marca) return;
		const res = await fetch(`/api/modelos/${vehicle.tipo}/${encodeURIComponent(marca)}`);
		const data = await res.json();
		if (lado === 'A') {
			modelosA = data.modelos;
		} else {
			modelosB = data.modelos;
		}
	}

	function updateMarca(lado: 'A' | 'B', marca: string) {
		if (lado === 'A') {
			motoA = { marca, modelo: '' };
			modelosA = [];
		} else {
			motoB = { marca, modelo: '' };
			modelosB = [];
		}
		loadModelos(lado, marca);
	}

	function updateModelo(lado: 'A' | 'B', modelo: string) {
		if (lado === 'A') {
			motoA = { ...motoA, modelo };
		} else {
			motoB = { ...motoB, modelo };
		}
	}

	async function comparar() {
		if (!motoA.marca || !motoA.modelo || !motoB.marca || !motoB.modelo) {
			alert('Selecione ambos os veículos!');
			return;
		}

		loading = true;
		try {
			const formData = new FormData();
			formData.append('marca_a', motoA.marca);
			formData.append('modelo_a', motoA.modelo);
			formData.append('marca_b', motoB.marca);
			formData.append('modelo_b', motoB.modelo);
			formData.append('tipo', vehicle.tipo);

			const res = await fetch('/api/compare', {
				method: 'POST',
				body: formData
			});

			if (res.status === 403) {
				alert('Comparador exclusivo para VIP!');
				return;
			}

			resultado = await res.json();
		} catch (e) {
			alert('Erro ao comparar');
		} finally {
			loading = false;
		}
	}
</script>

<div class="page">
	<h1 class="page-title">⚔️ Tira-Teima</h1>

	{#if !auth.usuarioVip}
		<div class="locked">
			<div class="locked-icon">🔒</div>
			<h2>Recurso Exclusivo VIP</h2>
			<p>O comparador lado a lado está disponível apenas para assinantes VIP.</p>
			<a href="/" class="cta-btn">Assinar VIP</a>
		</div>
	{:else}
		<div class="content">
			<div class="selectors">
				<VehiclePicker
					title="Veículo A"
					marca={motoA.marca}
					modelo={motoA.modelo}
					{marcas}
					modelos={modelosA}
					onMarcaChange={(m) => updateMarca('A', m)}
					onModeloChange={(m) => updateModelo('A', m)}
				/>

				<div class="vs">VS</div>

				<VehiclePicker
					title="Veículo B"
					marca={motoB.marca}
					modelo={motoB.modelo}
					{marcas}
					modelos={modelosB}
					onMarcaChange={(m) => updateMarca('B', m)}
					onModeloChange={(m) => updateModelo('B', m)}
				/>
			</div>

			<button class="compare-btn" onclick={comparar} disabled={loading}>
				{loading ? 'Comparando...' : 'Comparar Veículos'}
			</button>

			{#if resultado?.veredito}
				<div class="resultado">
					<VerdictCard
						vencedor={resultado.veredito.vencedor}
						diferenca={resultado.veredito.diferenca}
					/>
				</div>
			{/if}
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

	.locked {
		padding: 4rem 1.5rem;
		text-align: center;
	}

	.locked-icon {
		font-size: 3rem;
		margin-bottom: 1rem;
	}

	.locked h2 {
		font-size: 1.25rem;
		font-weight: 700;
		margin-bottom: 0.5rem;
		color: var(--base-content);
	}

	.locked p {
		color: var(--neutral-content);
		margin-bottom: 1.5rem;
	}

	.cta-btn {
		display: inline-block;
		padding: 0.75rem 1.5rem;
		background: var(--warning);
		color: var(--warning-content);
		font-weight: 600;
		text-decoration: none;
		transition: opacity 0.15s;
	}

	.cta-btn:hover {
		opacity: 0.9;
	}

	.content {
		padding: 1.5rem;
	}

	.selectors {
		display: grid;
		grid-template-columns: 1fr auto 1fr;
		gap: 1.5rem;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	@media (max-width: 768px) {
		.selectors {
			grid-template-columns: 1fr;
		}
	}

	.vs {
		font-size: 1.5rem;
		font-weight: 800;
		color: var(--warning);
	}

	.compare-btn {
		width: 100%;
		padding: 0.875rem;
		background: var(--primary);
		color: var(--primary-content);
		font-size: 1rem;
		font-weight: 600;
		border: none;
		cursor: pointer;
		transition: opacity 0.15s;
	}

	.compare-btn:hover:not(:disabled) {
		opacity: 0.9;
	}

	.compare-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.resultado {
		margin-top: 1.5rem;
	}
</style>
