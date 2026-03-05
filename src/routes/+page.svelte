<script>
	import { goto } from '$app/navigation';
	import PricingCard from '$lib/components/ui/PricingCard.svelte';
	import MorphingFAQ from '$lib/components/ui/MorphingFAQ.svelte';

	const faqItems = [
		{
			icon: '🚗',
			question: 'O sistema funciona para carros e caminhões também?',
			answer: 'Sim! Use os três botões no menu lateral para trocar de categoria entre motos, carros e caminhões.'
		},
		{
			icon: '📊',
			question: 'Os dados são da tabela FIPE oficial?',
			answer: 'Sim! Todos os dados vêm diretamente da tabela FIPE oficial do Brasil, atualizada mensalmente.'
		},
		{
			icon: '👑',
			question: 'Como me tornar VIP?',
			answer: 'Após adquirir o acesso, faça login com Google usando o mesmo e-mail da compra. Seu acesso será liberado automaticamente.'
		},
		{
			icon: '🔄',
			question: 'Posso cancelar a assinatura a qualquer momento?',
			answer: 'Sim! Você pode cancelar sua assinatura quando quiser. O acesso VIP permanece ativo até o final do período pago.'
		},
		{
			icon: '💎',
			question: 'Qual a diferença entre as 2 consultas gratuitas e o VIP?',
			answer: 'Na versão gratuita você pode fazer 2 consultas por dia com acesso aos dados básicos. O VIP desbloqueia consultas ilimitadas, dados dos anos mais recentes, rankings completos e a ferramenta de comparação.'
		}
	];
</script>

<main class="landing">
	<!-- Hero Section -->
	<section class="hero">
		<div class="hero-content">
			<div class="hero-badge">🏍️ Análise FIPE Inteligente</div>
			<h1>Pare de perder dinheiro na hora de comprar ou vender motos</h1>
			<p class="hero-subtitle">
				Descubra quais motos desvalorizam menos com dados da tabela FIPE e inteligência artificial. 
				<strong>2 consultas gratuitas</strong> por dia.
			</p>
			<div class="hero-cta">
				<button class="btn-primary btn-large" onclick={() => goto('/analise')}>
					🔍 Começar Análise Grátis
				</button>
				<a href="#planos" class="btn-secondary">Ver Planos VIP</a>
			</div>
		</div>
	</section>

	<!-- How It Works -->
	<section class="section how-it-works">
		<div class="container">
			<h2 class="section-title">Como funciona</h2>
			<p class="section-subtitle">Evite pagar caro em um veículo que vai desvalorizar — em 3 passos simples</p>
			
			<div class="steps-grid">
				<div class="step">
					<div class="step-icon" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8);">1</div>
					<h3>🔍 Escolha o veículo</h3>
					<p>Selecione a <strong>Marca</strong> e depois o <strong>Modelo</strong> que você quer pesquisar na barra lateral.</p>
					<span class="step-note">💡 2 consultas gratuitas por dia</span>
				</div>
				
				<div class="step">
					<div class="step-icon" style="background: linear-gradient(135deg, #f97316, #ea580c);">2</div>
					<h3>📊 Leia o gráfico</h3>
					<p>O gráfico mostra o <strong>impacto financeiro</strong> de escolher um ano mais novo. Barras para cima = Lucro, para baixo = Desvalorização.</p>
					<div class="legend">
						<span class="legend-item good">🟢 Lucro/Valorização</span>
						<span class="legend-item ok">🟡 Desvalorização até 8%</span>
						<span class="legend-item bad">🔴 Desvalorização 8-15%</span>
						<span class="legend-item avoid">⚫ Acima de 15% - Evite</span>
					</div>
				</div>
				
				<div class="step">
					<div class="step-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706);">3</div>
					<h3>👑 Desbloqueie o VIP</h3>
					<p>Com o acesso VIP, você desbloqueia os <strong>dados dos anos mais recentes</strong>, rankings exclusivos e comparação de veículos.</p>
					<span class="step-note">🔐 Login com Google + e-mail VIP</span>
				</div>
			</div>
		</div>
	</section>

	<!-- Pricing Section -->
	<section class="section pricing" id="planos">
		<div class="container">
			<h2 class="section-title">Escolha seu plano</h2>
			<p class="section-subtitle">Desbloqueie o acesso completo e pare de perder dinheiro</p>
			
			<div class="pricing-grid">
				<PricingCard
					badge="Pessoa Física"
					title="Passaporte Anti-Bomba"
					quote="Custa menos que meio tanque de gasolina para garantir que você não vai perder R$ 4.000 na hora de revender."
					price="29,90"
					features={[
						'Acesso liberado por <strong>30 dias</strong>',
						'Consultas ilimitadas da "Bola de Cristal"',
						'Tira-Teima (Duelo de Motos)',
						'Ranking das "Moedas Fortes" e "Muro da Vergonha"'
					]}
					buttonText="Liberar Meu Acesso"
					variant="blue"
				>
					<span class="billing">Pagamento Único no PIX</span>
				</PricingCard>
				
				<PricingCard
					badge="Vendedor Independente"
					title="Garagista PRO"
					quote="Se o aplicativo evitar que você pegue UMA única moto ruim na troca este mês, ele já pagou a assinatura de 2 anos."
					price="97,90"
					period="/mês"
					features={[
						'Acesso <strong>vitalício</strong> enquanto durar assinatura',
						'Avaliação de veículos em tempo real',
						'Identificação de margem com IA'
					]}
					buttonText="Assinar Plano PRO"
					variant="amber"
				/>
				
				<PricingCard
					badge="Concessionárias Multimarcas"
					title="Agência VIP"
					quote="Blinde a sua concessionária. Dê aos seus vendedores o poder de fechar trocas lucrativas baseadas em matemática."
					price="199,90"
					period="/mês"
					features={[
						'<strong>Tudo do plano Garagista PRO, mais:</strong>',
						'<strong>Múltiplos Acessos:</strong> Dono + 3 vendedores',
						'Relatórios em PDF (em breve)'
					]}
					buttonText="Assinar Agência VIP"
					variant="vip"
					popular={true}
				/>
			</div>
		</div>
	</section>

	<!-- FAQ Section -->
	<section class="section faq">
		<div class="container">
			<h2 class="section-title">Perguntas Frequentes</h2>
			
			<div class="faq-wrapper">
				<MorphingFAQ items={faqItems} />
			</div>
		</div>
	</section>

	<!-- CTA Footer -->
	<section class="section cta-footer">
		<div class="container">
			<h2>Pronto para parar de perder dinheiro?</h2>
			<p>Comece com <strong>2 consultas gratuitas</strong> hoje mesmo</p>
			<button class="btn-primary btn-large" onclick={() => goto('/analise')}>
				🔍 Começar Análise Grátis
			</button>
		</div>
	</section>
</main>

<style>
	.landing {
		background: var(--base-100);
	}

	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 0 1.5rem;
	}

	.section {
		padding: 5rem 0;
	}

	.section-title {
		font-size: 2rem;
		font-weight: 800;
		text-align: center;
		margin-bottom: 0.75rem;
		color: var(--base-content);
	}

	.section-subtitle {
		text-align: center;
		color: var(--neutral-content);
		font-size: 1.125rem;
		margin-bottom: 3rem;
	}

	/* Hero */
	.hero {
		padding: 4rem 1.5rem 5rem;
		text-align: center;
		background: linear-gradient(180deg, var(--base-200) 0%, var(--base-100) 100%);
		border-bottom: 0.5px solid var(--base-300);
	}

	.hero-content {
		max-width: 800px;
		margin: 0 auto;
	}

	.hero-badge {
		display: inline-block;
		padding: 0.5rem 1rem;
		background: var(--accent);
		color: var(--accent-content);
		font-size: 0.875rem;
		font-weight: 600;
		margin-bottom: 1.5rem;
	}

	.hero h1 {
		font-size: clamp(2rem, 5vw, 3.5rem);
		font-weight: 800;
		line-height: 1.1;
		margin-bottom: 1.5rem;
		color: var(--base-content);
	}

	.hero-subtitle {
		font-size: 1.25rem;
		color: var(--neutral-content);
		line-height: 1.6;
		margin-bottom: 2rem;
	}

	.hero-subtitle strong {
		color: var(--accent);
	}

	.hero-cta {
		display: flex;
		gap: 1rem;
		justify-content: center;
		flex-wrap: wrap;
	}

	.btn-primary {
		padding: 1rem 2rem;
		background: var(--accent);
		color: var(--accent-content);
		font-size: 1rem;
		font-weight: 700;
		border: none;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-secondary {
		padding: 1rem 2rem;
		background: transparent;
		color: var(--base-content);
		font-size: 1rem;
		font-weight: 600;
		border: 0.5px solid var(--base-300);
		text-decoration: none;
		transition: all 0.2s;
	}

	.btn-secondary:hover {
		background: var(--base-200);
	}

	.btn-large {
		font-size: 1.125rem;
		padding: 1.125rem 2.5rem;
	}

	/* How It Works */
	.how-it-works {
		background: var(--base-100);
	}

	.steps-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
		gap: 1.5rem;
	}

	.step {
		padding: 2rem;
		background: var(--base-200);
		border: 0.5px solid var(--base-300);
	}

	.step-icon {
		width: 3rem;
		height: 3rem;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-weight: 800;
		color: white;
		font-size: 1.25rem;
		margin-bottom: 1rem;
	}

	.step h3 {
		font-size: 1.25rem;
		font-weight: 700;
		margin-bottom: 0.75rem;
		color: var(--base-content);
	}

	.step p {
		color: var(--neutral-content);
		line-height: 1.6;
		margin-bottom: 1rem;
	}

	.step-note {
		display: block;
		font-size: 0.875rem;
		color: var(--accent);
		font-weight: 500;
	}

	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-top: 0.75rem;
	}

	.legend-item {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		background: var(--base-100);
		border-radius: 0.25rem;
	}

	/* Pricing */
	.pricing {
		background: var(--base-200);
	}

	.pricing-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: 1.5rem;
		align-items: stretch;
	}

	:global(.card) {
		height: 100%;
	}

	.billing {
		display: block;
		font-size: 0.75rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--neutral-content);
		margin-bottom: 1rem;
	}

	/* FAQ */
	.faq {
		background: var(--base-100);
	}

	.faq-wrapper {
		max-width: 800px;
		margin: 0 auto;
	}

	/* CTA Footer */
	.cta-footer {
		background: var(--base-200);
		text-align: center;
		border-top: 0.5px solid var(--base-300);
	}

	.cta-footer h2 {
		font-size: 2rem;
		font-weight: 800;
		margin-bottom: 0.75rem;
		color: var(--base-content);
	}

	.cta-footer p {
		font-size: 1.25rem;
		color: var(--neutral-content);
		margin-bottom: 2rem;
	}

	@media (max-width: 768px) {
		.section {
			padding: 3rem 0;
		}

		.hero {
			padding: 3rem 1rem;
		}

		.hero-cta {
			flex-direction: column;
			align-items: stretch;
		}

		.btn-secondary {
			text-align: center;
		}
	}
</style>
